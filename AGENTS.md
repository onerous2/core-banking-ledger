# Core Banking Ledger Agent Instructions

## Project Overview
Pet project demonstrating backend development using ACID principles and double-entry bookkeeping for financial transactions.

See [README.md](README.md) for full details.

## Tech Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy ORM
- Database: PostgreSQL (Docker) / SQLite (local)
- Frontend: HTML5, CSS3, Vanilla JavaScript
- Deployment: Docker & docker-compose

## How to Run
- Local development: `pip install -r requirements.txt; uvicorn app.main:app --reload`
- Docker: `docker-compose up`

## Architecture
Three-layer design:
- Database layer ([app/database.py](app/database.py)): SQLAlchemy engine with environment-based DB selection
- ORM models ([app/models.py](app/models.py)): Account, Transaction, LedgerEntry tables with relationships
- API layer ([app/main.py](app/main.py)): FastAPI endpoints with dependency injection
- Frontend ([static/](static/)): SPA with account management and transaction history

Key principle: Double-entry ledger where every transfer creates one transaction with two ledger entries.

## Conventions
- Use `Decimal` type for all financial calculations to avoid floating-point precision issues
- Error messages in Russian
- Timestamps stored server-side, formatted as HH:MM:SS for UI
- Database selection via `DATABASE_URL` environment variable

## Key Files
- [app/main.py](app/main.py): All API logic and endpoints
- [app/models.py](app/models.py): ORM schema definitions
- [app/database.py](app/database.py): Database engine and session management
- [static/script.js](static/script.js): Frontend API calls and DOM updates
- [requirements.txt](requirements.txt): Python dependencies
- [docker-compose.yml](docker-compose.yml): Container orchestration

## Pitfalls
- Always validate account existence before operations (return 404 if missing)
- Ensure transfer operations are atomic with proper rollback on errors
- Check sender balance before allowing transfers
- Cascading deletes remove ledger entries when accounts are deleted
- Ledger integrity check: total ledger sum should equal total account balance