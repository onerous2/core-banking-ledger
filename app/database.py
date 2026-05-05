from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Строка подключения (соответствует настройкам в docker-compose.yml)
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/banking_ledger"

# Создаем движок SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Фабрика сессий для работы с БД в запросах
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()

# Зависимость для FastAPI, чтобы получать доступ к БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()