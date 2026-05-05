# Core Banking Ledger

Микросервис для ведения банковского реестра на основе принципов двойной записи. 

## Технологии
- **Backend:** Python, FastAPI, PostgreSQL
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** HTML5, CSS3 (Inter font), Vanilla JavaScript

## Функционал
- Создание и удаление банковских счетов.
- Пополнение баланса через эндпоинт депозита.
- Переводы между счетами с атомарными транзакциями.
- Полная история записей в Ledger (Главной книге).

## Как запустить
1. Установите зависимости: `pip install fastapi uvicorn sqlalchemy`
2. Запустите сервер: `uvicorn app.main:app --reload`
3. Откройте `http://127.0.0.1:8000` в браузере.