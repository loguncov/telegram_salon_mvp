
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import logging
import json
from datetime import datetime
from pathlib import Path

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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
debug_log('backend.py:25', 'Logging configured', {}, 'B')

app = FastAPI()
debug_log('backend.py:27', 'FastAPI app created', {}, 'B')

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

# Статическая раздача HTML
@app.get("/")
async def read_root():
    debug_log('backend.py:50', 'Root endpoint called', {}, 'D')
    return FileResponse("index.html")

debug_log('backend.py:53', 'Before CORS middleware', {}, 'B')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
debug_log('backend.py:60', 'CORS middleware added', {}, 'B')

# In-memory storage prepared for future DB move
DB: Dict[str, Dict] = {
    "salons": {},  # salon_id -> {id, name, owner_id, masters: [{id, name, telegram_id}], services: [{id, name}], appointments: [{id, salon_id, master_id, service_id, client_id, datetime, status}]}
}


class SalonCreate(BaseModel):
    name: str


class MasterCreate(BaseModel):
    name: str
    telegram_id: Optional[str] = None


class MasterUpdate(BaseModel):
    name: Optional[str] = None


class ServiceCreate(BaseModel):
    name: str


class AppointmentCreate(BaseModel):
    salon_id: str
    master_id: str
    service_id: str
    datetime: str  # ISO format datetime string


def require_user_id(request: Request) -> str:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return str(user_id)


def get_owner_salon(owner_id: str) -> Optional[Dict]:
    for salon in DB["salons"].values():
        if salon["owner_id"] == owner_id:
            return salon
    return None


def get_salon_by_id(salon_id: str) -> Optional[Dict]:
    return DB["salons"].get(salon_id)


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
    for salon in DB["salons"].values():
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

    salon_id = str(uuid.uuid4())
    salon = {
        "id": salon_id,
        "name": payload.name or "Мой салон",
        "owner_id": owner_id,
        "masters": [],
        "services": [],
        "appointments": [],
    }
    DB["salons"][salon_id] = salon
    return salon


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

    master_id = str(uuid.uuid4())
    master_obj = {
        "id": master_id,
        "name": master.name,
        "telegram_id": master.telegram_id
    }
    salon["masters"].append(master_obj)
    return master_obj


@app.patch("/api/owner/masters/{master_id}")
async def owner_update_master(request: Request, master_id: str, payload: MasterUpdate):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    for m in salon["masters"]:
        if m["id"] == master_id:
            if payload.name:
                m["name"] = payload.name
            return m
    raise HTTPException(status_code=404, detail="Master not found")


@app.delete("/api/owner/masters/{master_id}")
async def owner_delete_master(request: Request, master_id: str):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    before = len(salon["masters"])
    salon["masters"] = [m for m in salon["masters"] if m["id"] != master_id]
    if len(salon["masters"]) == before:
        raise HTTPException(status_code=404, detail="Master not found")
    return {"ok": True}


# --- Services (UI placeholder for owner) ---
@app.post("/api/owner/services")
async def owner_add_service(request: Request, service: ServiceCreate):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    service_id = str(uuid.uuid4())
    service_obj = {"id": service_id, "name": service.name}
    salon["services"].append(service_obj)
    return service_obj


@app.delete("/api/owner/services/{service_id}")
async def owner_delete_service(request: Request, service_id: str):
    owner_id = require_user_id(request)
    salon = get_owner_salon(owner_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    before = len(salon["services"])
    salon["services"] = [s for s in salon["services"] if s["id"] != service_id]
    if len(salon["services"]) == before:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"ok": True}


# --- Client API ---
@app.get("/api/client/salons")
async def client_list_salons():
    """Список всех салонов (публичный)"""
    salons = []
    for salon in DB["salons"].values():
        salons.append({
            "id": salon["id"],
            "name": salon["name"],
            "masters_count": len(salon.get("masters", [])),
            "services_count": len(salon.get("services", []))
        })
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
    
    masters = []
    for master in salon.get("masters", []):
        masters.append({
            "id": master["id"],
            "name": master["name"]
        })
    return {"items": masters}


@app.get("/api/client/salons/{salon_id}/services")
async def client_get_salon_services(salon_id: str):
    """Список услуг салона"""
    salon = get_salon_by_id(salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    
    services = []
    for service in salon.get("services", []):
        services.append({
            "id": service["id"],
            "name": service["name"]
        })
    return {"items": services}


# --- Master API ---
def get_master_salon(user_id: str) -> Optional[Dict]:
    """Получить салон, в котором пользователь является мастером"""
    for salon in DB["salons"].values():
        if is_master(salon, user_id):
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
    
    appointments = salon.get("appointments", [])
    master_appointments = [
        apt for apt in appointments
        if apt.get("master_id") in master_ids
    ]
    return {"items": master_appointments}


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
    
    appointment_id = str(uuid.uuid4())
    appointment_obj = {
        "id": appointment_id,
        "salon_id": appointment.salon_id,
        "master_id": appointment.master_id,
        "service_id": appointment.service_id,
        "client_id": str(user_id),
        "datetime": appointment.datetime,
        "status": "pending"  # pending, confirmed, cancelled, completed
    }
    
    if "appointments" not in salon:
        salon["appointments"] = []
    salon["appointments"].append(appointment_obj)
    
    return appointment_obj


@app.get("/api/client/appointments")
async def client_get_appointments(request: Request):
    """Записи клиента"""
    user_id = require_user_id(request)
    all_appointments = []
    
    for salon in DB["salons"].values():
        appointments = salon.get("appointments", [])
        client_appointments = [
            apt for apt in appointments
            if apt.get("client_id") == str(user_id)
        ]
        all_appointments.extend(client_appointments)
    
    return {"items": all_appointments}


# --- User Role Detection ---
@app.get("/api/user/role")
async def get_user_role_endpoint(request: Request, salon_id: Optional[str] = None):
    """Определение роли пользователя"""
    user_id = require_user_id(request)
    role = get_user_role(user_id, salon_id)
    return {"role": role, "user_id": user_id, "salon_id": salon_id}


@app.get("/health")
async def health():
    return {"status": "ok"}
