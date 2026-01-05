"""
Модуль для работы с базой данных SQLite
"""
import sqlite3
import json
import uuid
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

DB_PATH = Path("salon.db")


def get_db_connection():
    """Получить соединение с БД"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация БД - создание таблиц"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица салонов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salons (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_id TEXT NOT NULL
        )
    """)
    
    # Таблица мастеров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS masters (
            id TEXT PRIMARY KEY,
            salon_id TEXT NOT NULL,
            name TEXT NOT NULL,
            telegram_id TEXT,
            FOREIGN KEY (salon_id) REFERENCES salons(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица услуг
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY,
            salon_id TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL,
            duration INTEGER,
            description TEXT,
            FOREIGN KEY (salon_id) REFERENCES salons(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица записей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            salon_id TEXT NOT NULL,
            master_id TEXT NOT NULL,
            service_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            datetime TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (salon_id) REFERENCES salons(id) ON DELETE CASCADE,
            FOREIGN KEY (master_id) REFERENCES masters(id) ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
        )
    """)
    
    # Индексы для производительности
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_salons_owner ON salons(owner_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_masters_salon ON masters(salon_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_masters_telegram ON masters(telegram_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_salon ON services(salon_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_salon ON appointments(salon_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_master ON appointments(master_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_client ON appointments(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_datetime ON appointments(datetime)")
    
    conn.commit()
    conn.close()


# Функции для работы с салонами
def create_salon(name: str, owner_id: str) -> Dict:
    """Создать салон"""
    salon_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO salons (id, name, owner_id) VALUES (?, ?, ?)",
        (salon_id, name, owner_id)
    )
    conn.commit()
    conn.close()
    return get_salon_by_id(salon_id)


def get_salon_by_id(salon_id: str) -> Optional[Dict]:
    """Получить салон по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM salons WHERE id = ?", (salon_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    salon = dict(row)
    salon["masters"] = get_salon_masters(salon_id)
    salon["services"] = get_salon_services(salon_id)
    salon["appointments"] = get_salon_appointments(salon_id)
    return salon


def get_owner_salon(owner_id: str) -> Optional[Dict]:
    """Получить салон владельца"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM salons WHERE owner_id = ?", (owner_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    salon_id = row["id"]
    salon = dict(row)
    salon["masters"] = get_salon_masters(salon_id)
    salon["services"] = get_salon_services(salon_id)
    salon["appointments"] = get_salon_appointments(salon_id)
    return salon


def update_salon(salon_id: str, name: Optional[str] = None) -> Optional[Dict]:
    """Обновить салон"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if name:
        cursor.execute("UPDATE salons SET name = ? WHERE id = ?", (name, salon_id))
    
    conn.commit()
    conn.close()
    return get_salon_by_id(salon_id)


def get_all_salons() -> List[Dict]:
    """Получить все салоны (для клиентов)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM salons")
    rows = cursor.fetchall()
    conn.close()
    
    salons = []
    for row in rows:
        salon = dict(row)
        salon["masters_count"] = len(get_salon_masters(salon["id"]))
        salon["services_count"] = len(get_salon_services(salon["id"]))
        salons.append(salon)
    
    return salons


# Функции для работы с мастерами
def create_master(salon_id: str, name: str, telegram_id: Optional[str] = None) -> Dict:
    """Создать мастера"""
    master_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO masters (id, salon_id, name, telegram_id) VALUES (?, ?, ?, ?)",
        (master_id, salon_id, name, telegram_id)
    )
    conn.commit()
    conn.close()
    return {"id": master_id, "name": name, "telegram_id": telegram_id}


def get_salon_masters(salon_id: str) -> List[Dict]:
    """Получить мастеров салона"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, telegram_id FROM masters WHERE salon_id = ?", (salon_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_master(master_id: str, name: Optional[str] = None) -> Optional[Dict]:
    """Обновить мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if name:
        cursor.execute("UPDATE masters SET name = ? WHERE id = ?", (name, master_id))
    
    conn.commit()
    cursor.execute("SELECT id, name, telegram_id FROM masters WHERE id = ?", (master_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def delete_master(master_id: str) -> bool:
    """Удалить мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM masters WHERE id = ?", (master_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# Функции для работы с услугами
def create_service(salon_id: str, name: str, price: Optional[float] = None, 
                   duration: Optional[int] = None, description: Optional[str] = None) -> Dict:
    """Создать услугу"""
    service_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO services (id, salon_id, name, price, duration, description) VALUES (?, ?, ?, ?, ?, ?)",
        (service_id, salon_id, name, price, duration, description)
    )
    conn.commit()
    conn.close()
    return {"id": service_id, "name": name, "price": price, "duration": duration, "description": description}


def get_salon_services(salon_id: str) -> List[Dict]:
    """Получить услуги салона"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, duration, description FROM services WHERE salon_id = ?", (salon_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_service(service_id: str, name: Optional[str] = None, price: Optional[float] = None,
                   duration: Optional[int] = None, description: Optional[str] = None) -> Optional[Dict]:
    """Обновить услугу"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if price is not None:
        updates.append("price = ?")
        params.append(price)
    if duration is not None:
        updates.append("duration = ?")
        params.append(duration)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if updates:
        params.append(service_id)
        cursor.execute(f"UPDATE services SET {', '.join(updates)} WHERE id = ?", params)
    
    conn.commit()
    cursor.execute("SELECT id, name, price, duration, description FROM services WHERE id = ?", (service_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def delete_service(service_id: str) -> bool:
    """Удалить услугу"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# Функции для работы с записями
def create_appointment(salon_id: str, master_id: str, service_id: str, 
                      client_id: str, datetime_str: str, status: str = "pending") -> Dict:
    """Создать запись"""
    appointment_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO appointments (id, salon_id, master_id, service_id, client_id, datetime, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (appointment_id, salon_id, master_id, service_id, client_id, datetime_str, status)
    )
    conn.commit()
    conn.close()
    return {
        "id": appointment_id,
        "salon_id": salon_id,
        "master_id": master_id,
        "service_id": service_id,
        "client_id": client_id,
        "datetime": datetime_str,
        "status": status
    }


def get_salon_appointments(salon_id: str) -> List[Dict]:
    """Получить все записи салона"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE salon_id = ?", (salon_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_master_appointments(master_ids: List[str]) -> List[Dict]:
    """Получить записи мастера"""
    if not master_ids:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(master_ids))
    cursor.execute(f"SELECT * FROM appointments WHERE master_id IN ({placeholders})", master_ids)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_client_appointments(client_id: str) -> List[Dict]:
    """Получить записи клиента"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE client_id = ?", (client_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_appointment(appointment_id: str, status: Optional[str] = None) -> Optional[Dict]:
    """Обновить запись"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
    
    conn.commit()
    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_appointment_by_id(appointment_id: str) -> Optional[Dict]:
    """Получить запись по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


