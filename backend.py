
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional, List
import uuid
import logging
import json
from datetime import datetime, timezone
from pathlib import Path
import database
from config import get_settings

# #region agent log
def debug_log(location, message, data=None, hypothesis_id=None):
    try:
        with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'location': location,
                'message': message,
                'data': data or {},
                'timestamp': int(datetime.now().timestamp() * 1000),
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': hypothesis_id
            }, ensure_ascii=False) + '\n')
    except: pass
# #endregion

# Настройка логирования
settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
debug_log("backend.py:25", "Logging configured", {"level": logger.level}, "B")

app = FastAPI(title="Salon WebApp API")
debug_log("backend.py:27", "FastAPI app created", {}, "B")
frontend_dir = Path(__file__).resolve().parent
index_path = frontend_dir / "index.html"

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    user_id = request.headers.get("X-User-Id", "unknown")
    logger.info(f"→ {request.method} {request.url.path} | User: {user_id}")
    debug_log('backend.py:35', 'Request received', {'method': request.method, 'path': request.url.path, 'user_id': user_id}, 'D')
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"← {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.3f}s")
        debug_log('backend.py:40', 'Request processed', {'method': request.method, 'path': request.url.path, 'status': response.status_code, 'time': process_time}, 'D')
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"✗ {request.method} {request.url.path} | Error: {str(e)} | Time: {process_time:.3f}s")
        debug_log('backend.py:44', 'Request error', {'method': request.method, 'path': request.url.path, 'error': str(e), 'error_type': type(e).__name__}, 'D')
        raise

static_dir = frontend_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Статическая раздача HTML
@app.get("/", include_in_schema=False)
async def read_root():
    debug_log("backend.py:50", "Root endpoint called", {}, "D")
    if not index_path.exists():
        logger.error("index.html not found at %s", index_path)
        raise HTTPException(status_code=500, detail="Frontend is missing")
    return FileResponse(index_path)

debug_log('backend.py:53', 'Before CORS middleware', {}, 'B')
allowed_origins = {
    settings.web_app_url,
    f"http://{settings.host}:{settings.port}",
    f"http://127.0.0.1:{settings.port}",
    f"http://localhost:{settings.port}",
}
allowed_origins = [origin for origin in allowed_origins if origin]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
debug_log("backend.py:60", "CORS middleware added", {"origins": allowed_origins}, "B")


@app.on_event("startup")
async def on_startup():
    database.init_db()
    logger.info("Database initialized")


class SalonCreate(BaseModel):
    name: str


class MasterCreate(BaseModel):
    name: str
    telegram_id: Optional[str] = None


class MasterUpdate(BaseModel):
    name: Optional[str] = None


class ServiceCreate(BaseModel):
    name: str
    price: Optional[float] = None
    duration: Optional[int] = None  # в минутах
    description: Optional[str] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    description: Optional[str] = None


class SalonUpdate(BaseModel):
    name: Optional[str] = None


class AppointmentCreate(BaseModel):
    salon_id: str
    master_id: str
    service_id: str
    datetime: str  # ISO format datetime string


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None


def require_user_id(request: Request) -> str:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return str(user_id)


def get_owner_salon(owner_id: str) -> Optional[Dict]:
    return database.get_owner_salon(owner_id)


def get_salon_by_id(salon_id: str) -> Optional[Dict]:
    return database.get_salon_by_id(salon_id)


def is_owner(salon: Dict, user_id: str) -> bool:
    """Проверка, является ли пользователь владельцем салона"""
    return salon.get("owner_id") == str(user_id)


def is_master(salon: Dict, user_id: str) -> bool:
    """Проверка, является ли пользователь мастером салона"""
    for master in salon.get("masters", []):
        if master.get("telegram_id") == str(user_id):
            return True
    return False


def get_user_role(user_id: str, salon_id: Optional[str] = None) -> str:
    """Определение роли пользователя: owner, master, или client"""
    if salon_id:
        salon = get_salon_by_id(salon_id)
        if salon:
            if is_owner(salon, user_id):
                return "owner"
            if is_master(salon, user_id):
                return "master"
    
    # Проверяем все салоны, если salon_id не указан
    salons = database.get_all_salons()
    for salon_data in salons:
        salon = get_salon_by_id(salon_data["id"])
        if salon:
            if is_owner(salon, user_id):
                return "owner"
            if is_master(salon, user_id):
                return "master"
    
    return "client"


@app.get("/api/owner/salon")
async def owner_get_salon(request: Request):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    return salon


@app.post("/api/owner/salon")
async def owner_create_salon(request: Request, payload: SalonCreate):
    owner_id = require_user_id(request)
    if get_owner_salon(owner_id):
        raise HTTPException(status_code=400, detail="Salon already exists")

    salon = database.create_salon(payload.name or "Мой салон", owner_id)
    return salon


@app.patch("/api/owner/salon")
async def owner_update_salon(request: Request, payload: SalonUpdate):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    updated_salon = database.update_salon(salon["id"], payload.name)
    return updated_salon


# --- Masters ---
@app.get("/api/owner/masters")
async def owner_list_masters(request: Request):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    return {"items": salon["masters"]}


@app.post("/api/owner/masters")
async def owner_add_master(request: Request, master: MasterCreate):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    master_obj = database.create_master(salon["id"], master.name, master.telegram_id)
    return master_obj


@app.patch("/api/owner/masters/{master_id}")
async def owner_update_master(request: Request, master_id: str, payload: MasterUpdate):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Проверяем, что мастер принадлежит салону
    master_ids = [m["id"] for m in salon.get("masters", [])]
    if master_id not in master_ids:
        raise HTTPException(status_code=404, detail="Master not found")
    
    updated_master = database.update_master(master_id, payload.name)
    if not updated_master:
        raise HTTPException(status_code=404, detail="Master not found")
    return updated_master


@app.delete("/api/owner/masters/{master_id}")
async def owner_delete_master(request: Request, master_id: str):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    deleted = database.delete_master(master_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Master not found")
    return {"ok": True}


# --- Services (UI placeholder for owner) ---
@app.post("/api/owner/services")
async def owner_add_service(request: Request, service: ServiceCreate):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    service_obj = database.create_service(
        salon["id"], 
        service.name, 
        service.price, 
        service.duration, 
        service.description
    )
    return service_obj


@app.patch("/api/owner/services/{service_id}")
async def owner_update_service(request: Request, service_id: str, payload: ServiceUpdate):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    # Проверяем, что услуга принадлежит салону
    service_ids = [s["id"] for s in salon.get("services", [])]
    if service_id not in service_ids:
        raise HTTPException(status_code=404, detail="Service not found")
    
    updated_service = database.update_service(
        service_id,
        payload.name,
        payload.price,
        payload.duration,
        payload.description
    )
    if not updated_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated_service


@app.delete("/api/owner/services/{service_id}")
async def owner_delete_service(request: Request, service_id: str):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    deleted = database.delete_service(service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"ok": True}


# --- Client API ---
@app.get("/api/client/salons")
async def client_list_salons():
    """Список всех салонов (публичный)"""
    salons = database.get_all_salons()
    return {"items": salons}


@app.get("/api/client/salons/{salon_id}")
async def client_get_salon(salon_id: str):
    """Информация о салоне для клиента"""
    salon = get_salon_by_id(salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    return {
        "id": salon["id"],
        "name": salon["name"],
        "masters_count": len(salon.get("masters", [])),
        "services_count": len(salon.get("services", []))
    }


@app.get("/api/client/salons/{salon_id}/masters")
async def client_get_salon_masters(salon_id: str):
    """Список мастеров салона"""
    salon = get_salon_by_id(salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    masters = database.get_salon_masters(salon_id)
    # Убираем telegram_id из ответа для клиентов
    for master in masters:
        master.pop("telegram_id", None)
    return {"items": masters}


@app.get("/api/client/salons/{salon_id}/services")
async def client_get_salon_services(salon_id: str):
    """Список услуг салона"""
    salon = get_salon_by_id(salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    services = database.get_salon_services(salon_id)
    return {"items": services}


@app.get("/api/client/salons/{salon_id}/available-slots")
async def client_get_available_slots(salon_id: str, master_id: str, date: str):
    """Получение доступных слотов времени для мастера на указанную дату"""
    salon = get_salon_by_id(salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    # Проверка существования мастера
    master_exists = any(m["id"] == master_id for m in salon.get("masters", []))
    if not master_exists:
        raise HTTPException(status_code=404, detail="Master not found")
    
    # Парсинг даты
    try:
        target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        if target_date.tzinfo:
            target_date = target_date.replace(tzinfo=None)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (e.g., 2024-01-01)")
    
    # Получаем все записи мастера на эту дату
    appointments = database.get_salon_appointments(salon_id)
    booked_times = []
    for apt in appointments:
        if apt.get("master_id") == master_id and apt.get("status") not in ["cancelled", "completed"]:
            try:
                apt_datetime = datetime.fromisoformat(apt.get("datetime", "").replace('Z', '+00:00'))
                if apt_datetime.tzinfo:
                    apt_datetime = apt_datetime.replace(tzinfo=None)
                if apt_datetime.date() == target_date.date():
                    booked_times.append(apt_datetime)
            except (ValueError, AttributeError):
                continue
    
    # Генерируем доступные слоты (каждый час с 9:00 до 18:00)
    available_slots = []
    start_hour = 9
    end_hour = 18
    
    for hour in range(start_hour, end_hour):
        slot_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
        # Проверяем, не занят ли слот
        is_booked = any(
            abs((slot_time - booked_time).total_seconds()) < 3600  # В пределах часа
            for booked_time in booked_times
        )
        if not is_booked and slot_time > datetime.now():
            available_slots.append(slot_time.isoformat())
    
    return {"items": available_slots}


# --- Master API ---
def get_master_salon(user_id: str) -> Optional[Dict]:
    """Получить салон, в котором пользователь является мастером"""
    salons = database.get_all_salons()
    for salon_data in salons:
        salon = get_salon_by_id(salon_data["id"])
        if salon and is_master(salon, user_id):
            return salon
    return None


@app.get("/api/master/salon")
async def master_get_salon(request: Request):
    """Получить салон мастера"""
    user_id = require_user_id(request)
    salon = get_master_salon(user_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found or user is not a master")
    
    return {
        "id": salon["id"],
        "name": salon["name"],
        "masters": salon.get("masters", []),
        "services": salon.get("services", [])
    }


@app.get("/api/master/appointments")
async def master_get_appointments(request: Request):
    """Записи мастера"""
    user_id = require_user_id(request)
    salon = get_master_salon(user_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found or user is not a master")
    
    # Найти ID мастера по telegram_id
    master_ids = [m["id"] for m in salon.get("masters", []) if m.get("telegram_id") == str(user_id)]
    if not master_ids:
        return {"items": []}
    
    appointments = database.get_master_appointments(master_ids)
    return {"items": appointments}


@app.patch("/api/master/appointments/{appointment_id}")
async def master_update_appointment(request: Request, appointment_id: str, payload: AppointmentUpdate):
    """Изменение статуса записи мастером"""
    user_id = require_user_id(request)
    salon = get_master_salon(user_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found or user is not a master")
    
    # Найти ID мастера по telegram_id
    master_ids = [m["id"] for m in salon.get("masters", []) if m.get("telegram_id") == str(user_id)]
    if not master_ids:
        raise HTTPException(status_code=404, detail="Master not found")
    
    # Найти запись мастера
    appointment = database.get_appointment_by_id(appointment_id)
    if not appointment or appointment.get("master_id") not in master_ids:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Валидация статуса
    current_status = appointment.get("status")
    if not payload.status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {valid_statuses}")
    
    # Проверка допустимых переходов статуса
    if current_status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot change status of cancelled appointment")
    if current_status == "completed" and payload.status != "completed":
        raise HTTPException(status_code=400, detail="Cannot change status of completed appointment")
    
    # Обновление статуса
    updated_appointment = database.update_appointment(appointment_id, payload.status)
    return updated_appointment


# --- Appointments API ---
@app.post("/api/client/appointments")
async def client_create_appointment(request: Request, appointment: AppointmentCreate):
    """Создание записи клиентом"""
    user_id = require_user_id(request)
    salon = get_salon_by_id(appointment.salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    # Проверка существования мастера и услуги
    master_exists = any(m["id"] == appointment.master_id for m in salon.get("masters", []))
    service_exists = any(s["id"] == appointment.service_id for s in salon.get("services", []))
    
    if not master_exists:
        raise HTTPException(status_code=404, detail="Master not found")
    if not service_exists:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Валидация времени записи
    try:
        # Поддержка разных форматов ISO datetime
        dt_str = appointment.datetime
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        elif '+' not in dt_str and dt_str.count(':') == 2:
            # Если нет timezone, считаем локальным временем
            pass
        appointment_datetime = datetime.fromisoformat(dt_str)
        # Если нет timezone информации, считаем локальным временем
        if appointment_datetime.tzinfo is None:
            # Сравниваем с локальным временем
            now = datetime.now()
        else:
            # Конвертируем в локальное время для сравнения
            now = datetime.now(appointment_datetime.tzinfo)
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format. Use ISO format (e.g., 2024-01-01T10:00:00). Error: {str(e)}")
    
    # Проверка, что время не в прошлом
    # Нормализуем оба времени для сравнения
    if appointment_datetime.tzinfo:
        now = datetime.now(appointment_datetime.tzinfo)
    else:
        now = datetime.now()
        appointment_datetime = appointment_datetime.replace(tzinfo=None)
    
    if appointment_datetime <= now:
        raise HTTPException(status_code=400, detail="Cannot book appointment in the past")
    
    # Проверка на конфликты времени (мастер уже занят в это время)
    appointments = database.get_salon_appointments(appointment.salon_id)
    conflicting_appointments = [
        apt for apt in appointments
        if apt.get("master_id") == appointment.master_id
        and apt.get("status") not in ["cancelled", "completed"]
        and apt.get("datetime") == appointment.datetime
    ]
    
    if conflicting_appointments:
        raise HTTPException(status_code=409, detail="Master is already booked at this time")
    
    appointment_obj = database.create_appointment(
        appointment.salon_id,
        appointment.master_id,
        appointment.service_id,
        str(user_id),
        appointment.datetime,
        "pending"
    )
    
    return appointment_obj


@app.get("/api/client/appointments")
async def client_get_appointments(request: Request):
    """Записи клиента"""
    user_id = require_user_id(request)
    appointments = database.get_client_appointments(str(user_id))
    return {"items": appointments}


@app.patch("/api/client/appointments/{appointment_id}")
async def client_update_appointment(request: Request, appointment_id: str, payload: AppointmentUpdate):
    """Отмена записи клиентом"""
    user_id = require_user_id(request)
    
    # Найти запись
    appointment = database.get_appointment_by_id(appointment_id)
    if not appointment or appointment.get("client_id") != str(user_id):
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Клиент может только отменить запись
    if payload.status and payload.status != "cancelled":
        raise HTTPException(status_code=400, detail="Client can only cancel appointments")
    
    # Проверка, что запись можно отменить
    current_status = appointment.get("status")
    if current_status in ["cancelled", "completed"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel appointment with status: {current_status}")
    
    # Обновление статуса
    updated_appointment = database.update_appointment(appointment_id, "cancelled")
    return updated_appointment


# --- User Role Detection ---
@app.get("/api/owner/appointments")
async def owner_get_appointments(request: Request, master_id: Optional[str] = None, status: Optional[str] = None):
    """Список всех записей салона с фильтрацией"""
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    appointments = database.get_salon_appointments(salon["id"])
    
    # Фильтрация по мастеру
    if master_id:
        appointments = [apt for apt in appointments if apt.get("master_id") == master_id]
    
    # Фильтрация по статусу
    if status:
        appointments = [apt for apt in appointments if apt.get("status") == status]
    
    return {"items": appointments}


@app.patch("/api/owner/appointments/{appointment_id}")
async def owner_update_appointment(request: Request, appointment_id: str, payload: AppointmentUpdate):
    """Изменение статуса записи владельцем"""
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    # Найти запись
    appointment = database.get_appointment_by_id(appointment_id)
    if not appointment or appointment.get("salon_id") != salon["id"]:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Валидация статуса
    if not payload.status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {valid_statuses}")
    
    # Обновление статуса
    updated_appointment = database.update_appointment(appointment_id, payload.status)
    return updated_appointment


@app.get("/api/user/role")
async def get_user_role_endpoint(request: Request, salon_id: Optional[str] = None):
    """Определение роли пользователя"""
    user_id = require_user_id(request)
    role = get_user_role(user_id, salon_id)
    return {"role": role, "user_id": user_id, "salon_id": salon_id}


@app.get("/health")
async def health():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return {"status": "ok", "time": now.isoformat().replace("+00:00", "Z")}
