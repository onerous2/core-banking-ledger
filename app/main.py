from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from decimal import Decimal
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