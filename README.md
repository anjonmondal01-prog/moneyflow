# MoneyFlow

Production-oriented personal finance and money-journal application based on the supplied specification.

## Architecture
- Backend: Python + Django + Django REST Framework
- Production database: PostgreSQL via `DATABASE_URL`
- Frontend: React + Vite
- Money math: Python `Decimal` + PostgreSQL `NUMERIC`
- Financial source of truth: active transaction ledger
- Authorization: server-side ownership filtering via authenticated user
- Critical mutations: Django `transaction.atomic()` with audit events

## Run locally
1. Create a Python virtual environment in `backend/`.
2. Install `backend/requirements.txt`.
3. Set `DATABASE_URL` to PostgreSQL for production-like use. Without it, development falls back to SQLite for local scaffolding.
4. Run `python manage.py migrate` and `python manage.py runserver 8000`.
5. In `frontend/`, install npm dependencies and run `npm run dev`.
6. Set `VITE_API_URL=http://localhost:8000/api` when needed.

## Deployment
Render can deploy the Django backend and PostgreSQL database from this repository. The frontend is a separate Vite static site and must use the deployed backend API URL.
