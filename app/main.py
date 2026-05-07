from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
from sqlalchemy import func
import os
import hashlib
import secrets

from . import models, database

# Инициализация БД
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Core Banking Ledger")

# Подключаем папку со статикой
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# --- Авторизация ---
class AuthRequest(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user(token: str = Header(None), db: Session = Depends(database.get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    user = db.query(models.User).filter(models.User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Неверный или устаревший токен")
    return user

@app.post("/auth/register")
def register(req: AuthRequest, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    new_user = models.User(username=req.username, password_hash=hash_password(req.password))
    db.add(new_user)
    db.commit()
    return {"status": "success"}

@app.post("/auth/login")
def login(req: AuthRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user or user.password_hash != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    user.token = secrets.token_hex(16)
    db.commit()
    return {"token": user.token, "username": user.username}

@app.get("/auth/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username}

# --- API Эндпоинты ---

@app.post("/accounts/")
def create_account(owner_name: str, initial_balance: Decimal = Decimal("0.0"), db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    db_account = models.Account(owner_name=owner_name, balance=initial_balance, user_id=current_user.id)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@app.get("/accounts/")
def list_accounts(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Показываем только активные счета текущего пользователя
    return db.query(models.Account).filter(models.Account.is_active == True, models.Account.user_id == current_user.id).order_by(models.Account.id).all()

@app.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    #Ищем счет в базе
    account=db.query(models.Account).filter(models.Account.id == account_id).first()

    #2. Если счет не найден, возвращаем ошибку
    if not account or not account.is_active or account.user_id != current_user.id:
        raise HTTPException(
            status_code = 404,
            detail="Счет не найден, уже закрыт или у вас нет к нему доступа"
        )
    #3. Реализуем soft delete: для отчетности, даже удаленные счета должны сохраняться в базе, но помечаться как неактивные
    account.is_active = False

    db.commit()

    return {"status": "success", "message": f"Счет {account_id} успешно удален (not_active)"}

@app.post("/accounts/{account_id}/deposit")
def deposit_money(account_id: int, amount: Decimal, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # ИЗМЕНЕНО: Нельзя пополнять удаленный счет
    account = db.query(models.Account).filter(models.Account.id == account_id, models.Account.is_active == True).first()
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Счет не найден или находится в архиве")
    
    new_tx = models.Transaction(description=f"Deposit to {account_id}")
    db.add(new_tx)
    db.flush()
    db.add(models.LedgerEntry(transaction_id=new_tx.id, account_id=account_id, amount=amount))
    
    account.balance += amount
    db.commit()
    return {"status": "success"}

@app.get("/accounts/{account_id}/history")
def get_account_history(account_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Проверяем, существует ли счет (оставил возможность смотреть историю удаленных счетов, 
    # так как для аудита это полезно, но можно добавить проверку на is_active, если хочешь скрыть и историю)
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Счет не найден")

    # Ищем все записи в Ledger для этого счета
    history = db.query(models.LedgerEntry).filter(
        models.LedgerEntry.account_id == account_id
    ).join(models.Transaction).order_by(models.LedgerEntry.id.desc()).all()
    
    return [
        {
            "id": entry.id,
            "amount": float(entry.amount),
            "description": entry.transaction.description,
            "date": entry.transaction.created_at.strftime("%H:%M:%S") 
        } for entry in history
    ]

@app.post("/transfer/")
def transfer_money(from_id: int, to_id: int, amount: Decimal, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    try:
        # ИЗМЕНЕНО: Проверяем, что ОБА счета активны
        sender = db.query(models.Account).filter(models.Account.id == from_id, models.Account.is_active == True).first()
        receiver = db.query(models.Account).filter(models.Account.id == to_id, models.Account.is_active == True).first()
        
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Один или оба счета не найдены (или переведены в архив)")
        
        if sender.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Вы можете переводить деньги только со своих счетов")

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
    total_ledger_sum = db.query(func.sum(models.LedgerEntry.amount)).scalar() or Decimal("0")
    total_accounts_sum = db.query(func.sum(models.Account.balance)).scalar() or Decimal("0")
    
    is_healthy = total_ledger_sum == total_accounts_sum
    
    return {
        "status": "healthy" if is_healthy else "corrupted",
        "total_in_ledger": total_ledger_sum,
        "total_on_accounts": total_accounts_sum,
        "drift": total_ledger_sum - total_accounts_sum
    }