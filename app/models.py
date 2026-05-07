from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from .database import Base  # Импорт Base строго из database.py

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    token = Column(String, unique=True, index=True)

    accounts = relationship("Account", back_populates="owner")

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String, nullable=False)
    # Используем Numeric(18, 2) для точности до копеек (до 18 знаков всего, 2 после запятой)
    balance = Column(Numeric(precision=18, scale=2), default=0.0)
    # ПОЛЕ ДЛЯ SOFT DELETE:
    is_active = Column(Boolean, default=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="accounts")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    
    # Связь с записями в журнале (LedgerEntry)
    entries = relationship("LedgerEntry", back_populates="transaction")

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    # Сумма проводки: отрицательная — списание, положительная — зачисление
    amount = Column(Numeric(precision=18, scale=2), nullable=False)

    transaction = relationship("Transaction", back_populates="entries")
