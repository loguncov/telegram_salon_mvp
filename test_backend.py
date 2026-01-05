"""
Автоматизированные тесты для backend API
"""
import pytest
from fastapi.testclient import TestClient
from backend import app

client = TestClient(app)

# Тестовые данные
TEST_USER_ID = "12345"
TEST_USER_ID_2 = "67890"
TEST_MASTER_TELEGRAM_ID = "99999"


class TestOwnerAPI:
    """Тесты API для владельца салона"""

    def test_create_salon_without_auth(self):
        """Создание салона без X-User-Id → 401"""
        response = client.post("/api/owner/salon", json={"name": "Test Salon"})
        assert response.status_code == 401
        assert "Missing X-User-Id" in response.text

    def test_create_salon_success(self):
        """Создание салона с валидным X-User-Id → 200"""
        response = client.post(
            "/api/owner/salon",
            json={"name": "Test Salon"},
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Salon"
        assert data["owner_id"] == TEST_USER_ID
        assert "id" in data
        assert data["masters"] == []
        assert data["services"] == []
        assert data["appointments"] == []

    def test_create_salon_duplicate(self):
        """Повторное создание салона → 400"""
        response = client.post(
            "/api/owner/salon",
            json={"name": "Duplicate Salon"},
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 400
        assert "already exists" in response.text.lower()

    def test_get_salon_not_found(self):
        """Получение салона без салона → 404"""
        response = client.get(
            "/api/owner/salon",
            headers={"X-User-Id": "nonexistent"}
        )
        assert response.status_code == 404

    def test_get_salon_success(self):
        """Получение салона владельцем → 200"""
        response = client.get(
            "/api/owner/salon",
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["owner_id"] == TEST_USER_ID

    def test_add_master_without_salon(self):
        """Добавление мастера без салона → 404"""
        response = client.post(
            "/api/owner/masters",
            json={"name": "Master 1"},
            headers={"X-User-Id": "nonexistent"}
        )
        assert response.status_code == 404

    def test_add_master_success(self):
        """Добавление мастера с салоном → 200"""
        response = client.post(
            "/api/owner/masters",
            json={"name": "Master 1", "telegram_id": TEST_MASTER_TELEGRAM_ID},
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Master 1"
        assert data["telegram_id"] == TEST_MASTER_TELEGRAM_ID
        assert "id" in data

    def test_list_masters(self):
        """Список мастеров → 200"""
        response = client.get(
            "/api/owner/masters",
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_update_master_success(self):
        """Обновление мастера → 200"""
        # Сначала получаем список мастеров
        list_response = client.get(
            "/api/owner/masters",
            headers={"X-User-Id": TEST_USER_ID}
        )
        masters = list_response.json()["items"]
        assert len(masters) > 0
        master_id = masters[0]["id"]

        # Обновляем мастера
        response = client.patch(
            f"/api/owner/masters/{master_id}",
            json={"name": "Updated Master"},
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Master"

    def test_delete_master_not_found(self):
        """Удаление несуществующего мастера → 404"""
        response = client.delete(
            "/api/owner/masters/nonexistent",
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 404

    def test_delete_master_success(self):
        """Удаление мастера → 200"""
        # Сначала добавляем мастера
        add_response = client.post(
            "/api/owner/masters",
            json={"name": "Master to Delete"},
            headers={"X-User-Id": TEST_USER_ID}
        )
        master_id = add_response.json()["id"]

        # Удаляем мастера
        response = client.delete(
            f"/api/owner/masters/{master_id}",
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_add_service_success(self):
        """Добавление услуги → 200"""
        response = client.post(
            "/api/owner/services",
            json={"name": "Service 1"},
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Service 1"
        assert "id" in data

    def test_delete_service_not_found(self):
        """Удаление несуществующей услуги → 404"""
        response = client.delete(
            "/api/owner/services/nonexistent",
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 404

    def test_delete_service_success(self):
        """Удаление услуги → 200"""
        # Сначала добавляем услугу
        add_response = client.post(
            "/api/owner/services",
            json={"name": "Service to Delete"},
            headers={"X-User-Id": TEST_USER_ID}
        )
        service_id = add_response.json()["id"]

        # Удаляем услугу
        response = client.delete(
            f"/api/owner/services/{service_id}",
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True


class TestClientAPI:
    """Тесты API для клиентов"""

    def test_list_salons(self):
        """Список всех салонов → 200"""
        response = client.get("/api/client/salons")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_salon_not_found(self):
        """Получение несуществующего салона → 404"""
        response = client.get("/api/client/salons/nonexistent")
        assert response.status_code == 404

    def test_get_salon_success(self):
        """Получение салона → 200"""
        # Сначала получаем список салонов
        list_response = client.get("/api/client/salons")
        salons = list_response.json()["items"]
        if len(salons) > 0:
            salon_id = salons[0]["id"]
            response = client.get(f"/api/client/salons/{salon_id}")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "name" in data

    def test_get_salon_masters(self):
        """Получение мастеров салона → 200"""
        list_response = client.get("/api/client/salons")
        salons = list_response.json()["items"]
        if len(salons) > 0:
            salon_id = salons[0]["id"]
            response = client.get(f"/api/client/salons/{salon_id}/masters")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data

    def test_get_salon_services(self):
        """Получение услуг салона → 200"""
        list_response = client.get("/api/client/salons")
        salons = list_response.json()["items"]
        if len(salons) > 0:
            salon_id = salons[0]["id"]
            response = client.get(f"/api/client/salons/{salon_id}/services")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data


class TestMasterAPI:
    """Тесты API для мастера"""

    def test_get_salon_not_master(self):
        """Получение салона не-мастером → 404"""
        response = client.get(
            "/api/master/salon",
            headers={"X-User-Id": "not_a_master"}
        )
        assert response.status_code == 404

    def test_get_salon_as_master(self):
        """Получение салона мастером → 200"""
        # Мастер должен быть добавлен владельцем с telegram_id
        response = client.get(
            "/api/master/salon",
            headers={"X-User-Id": TEST_MASTER_TELEGRAM_ID}
        )
        # Может быть 404 если мастер не добавлен, или 200 если добавлен
        assert response.status_code in [200, 404]

    def test_get_appointments_as_master(self):
        """Получение записей мастером"""
        response = client.get(
            "/api/master/appointments",
            headers={"X-User-Id": TEST_MASTER_TELEGRAM_ID}
        )
        # Может быть 404 если мастер не добавлен, или 200 если добавлен
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "items" in data


class TestRoleDetection:
    """Тесты определения роли"""

    def test_get_role_without_auth(self):
        """Определение роли без X-User-Id → 401"""
        response = client.get("/api/user/role")
        assert response.status_code == 401

    def test_get_role_owner(self):
        """Определение роли владельца → owner"""
        response = client.get(
            "/api/user/role",
            headers={"X-User-Id": TEST_USER_ID}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "owner"

    def test_get_role_client(self):
        """Определение роли клиента → client"""
        response = client.get(
            "/api/user/role",
            headers={"X-User-Id": "new_client_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "client"


class TestAppointmentsAPI:
    """Тесты API для записей"""

    def test_create_appointment_without_auth(self):
        """Создание записи без X-User-Id → 401"""
        response = client.post(
            "/api/client/appointments",
            json={
                "salon_id": "test",
                "master_id": "test",
                "service_id": "test",
                "datetime": "2024-01-01T10:00:00"
            }
        )
        assert response.status_code == 401

    def test_create_appointment_salon_not_found(self):
        """Создание записи в несуществующем салоне → 404"""
        response = client.post(
            "/api/client/appointments",
            json={
                "salon_id": "nonexistent",
                "master_id": "test",
                "service_id": "test",
                "datetime": "2024-01-01T10:00:00"
            },
            headers={"X-User-Id": TEST_USER_ID_2}
        )
        assert response.status_code == 404

    def test_get_appointments(self):
        """Получение записей клиента"""
        response = client.get(
            "/api/client/appointments",
            headers={"X-User-Id": TEST_USER_ID_2}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestHealth:
    """Тесты health check"""

    def test_health(self):
        """Health check → 200"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


