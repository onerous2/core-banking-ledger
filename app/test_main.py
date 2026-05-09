from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from .main import app
from .database import Base, get_db

# Создаем базу данных в памяти специально для тестов
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Важно для in-memory SQLite, чтобы тесты не теряли данные
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы в тестовой базе
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Подменяем зависимость базы данных в приложении на нашу тестовую
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_system_health():
    response = client.get("/system/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_user_registration_and_login():
    # 1. Проверяем успешную регистрацию
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 2. Проверяем, что нельзя зарегистрировать пользователя с таким же именем
    response_duplicate = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response_duplicate.status_code == 400

    # 3. Проверяем вход в систему (логин)
    response_login = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response_login.status_code == 200
    assert "token" in response_login.json()