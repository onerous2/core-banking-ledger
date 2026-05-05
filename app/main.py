from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from sqlalchemy import func
import os

from . import models, database

# Инициализация БД
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Core Banking Ledger")

# Подключаем папку со статикой
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# --- API Эндпоинты ---

@app.post("/accounts/")
def create_account(owner_name: str, initial_balance: Decimal = Decimal("0.0"), db: Session = Depends(database.get_db)):
    db_account = models.Account(owner_name=owner_name, balance=initial_balance)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@app.get("/accounts/")
def list_accounts(db: Session = Depends(database.get_db)):
    # Сортировка по ID, чтобы список не прыгал
    return db.query(models.Account).order_by(models.Account.id).all()

@app.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(database.get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    # Удаляем историю операций перед удалением счета
    db.query(models.LedgerEntry).filter(models.LedgerEntry.account_id == account_id).delete()
    db.delete(account)
    db.commit()
    return {"status": "success"}

@app.post("/accounts/{account_id}/deposit")
def deposit_money(account_id: int, amount: Decimal, db: Session = Depends(database.get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")
    
    new_tx = models.Transaction(description=f"Deposit to {account_id}")
    db.add(new_tx)
    db.flush()
    db.add(models.LedgerEntry(transaction_id=new_tx.id, account_id=account_id, amount=amount))
    
    account.balance += amount
    db.commit()
    return {"status": "success"}

@app.get("/accounts/{account_id}/history")
def get_account_history(account_id: int, db: Session = Depends(database.get_db)):
    # Проверяем, существует ли счет
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счет не найден")

    # Ищем все записи в Ledger для этого счета
    # Используем .join, чтобы сразу получить описание транзакции
    history = db.query(models.LedgerEntry).filter(
        models.LedgerEntry.account_id == account_id
    ).join(models.Transaction).order_by(models.LedgerEntry.id.desc()).all()
    
    # Форматируем данные для фронтенда
    return [
        {
            "id": entry.id,
            "amount": float(entry.amount),
            "description": entry.transaction.description,
            "date": entry.transaction.created_at.strftime("%H:%M:%S") 
        } for entry in history
    ]

@app.post("/transfer/")
def transfer_money(from_id: int, to_id: int, amount: Decimal, db: Session = Depends(database.get_db)):
    try:
        sender = db.query(models.Account).filter(models.Account.id == from_id).first()
        receiver = db.query(models.Account).filter(models.Account.id == to_id).first()
        
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Счет не найден")
        if sender.balance < amount:
            raise HTTPException(status_code=400, detail="Недостаточно средств")

        new_tx = models.Transaction(description=f"Transfer {from_id} -> {to_id}")
        db.add(new_tx)
        db.flush()

        db.add(models.LedgerEntry(transaction_id=new_tx.id, account_id=from_id, amount=-amount))
        db.add(models.LedgerEntry(transaction_id=new_tx.id, account_id=to_id, amount=amount))
        
        sender.balance -= amount
        receiver.balance += amount
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise e
    
@app.get("/system/health")
def check_system_integrity(db: Session = Depends(database.get_db)):
    # 1. Проверка: Сумма всех LedgerEntry должна быть равна 0 (при переводах)
    # Если есть только депозиты, то сумма LedgerEntry == Сумма балансов всех аккаунтов
    total_ledger_sum = db.query(func.sum(models.LedgerEntry.amount)).scalar() or Decimal("0")
    total_accounts_sum = db.query(func.sum(models.Account.balance)).scalar() or Decimal("0")
    
    is_healthy = total_ledger_sum == total_accounts_sum
    
    return {
        "status": "healthy" if is_healthy else "corrupted",
        "total_in_ledger": total_ledger_sum,
        "total_on_accounts": total_accounts_sum,
        "drift": total_ledger_sum - total_accounts_sum
    }