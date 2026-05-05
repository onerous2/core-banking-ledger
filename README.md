# Core Banking Ledger

A microservice implementing a banking ledger based on double-entry bookkeeping principles. This project demonstrates a robust way to handle financial transactions with atomicity and data integrity.

## Overview
This "Core Banking Ledger" is designed as a pet project to showcase backend development skills, specifically focusing on database consistency and the ACID principles. It provides a clean, responsive interface for managing accounts and executing transfers.

## Tech Stack
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy (ORM)
- **Database:** SQLite (default) / PostgreSQL compatible
- **Frontend:** HTML5, CSS3 (Inter UI), Vanilla JavaScript
- **Dev Tools:** Git, VS Code

## Key Features
- **Account Management:** Create new accounts with an initial owner name and a zero balance.
- **Double-Entry Ledger:** Every movement of money is recorded as a set of ledger entries linked to a single transaction, ensuring the books always balance.
- **Deposit System:** Easily top up account balances to simulate real-world cash inflows.
- **Atomic Transfers:** Perform transfers between accounts using database transactions to prevent "lost money" scenarios.
- **Responsive UI:** A modern, clean dashboard for managing accounts and viewing balances in real-time.

## Project Structure
- `app/main.py`: The FastAPI application containing all API endpoints and business logic.
- `app/models.py`: Database schema definitions (Accounts, Transactions, LedgerEntries).
- `app/database.py`: SQLAlchemy engine and session configuration.
- `static/`: Frontend assets including the HTML dashboard, CSS styles, and JavaScript logic.

## Getting Started

### 1. Prerequisites
Ensure you have Python installed. You will also need to install the following packages:
```bash
1. Install dependencies: `pip install fastapi uvicorn sqlalchemy`
2. Launch the server: `uvicorn app.main:app --reload`
3. Open `http://127.0.0.1:8000` in browser.