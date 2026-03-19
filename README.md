# Code Radar

Full-stack code analysis platform with a FastAPI backend, Celery workers, Redis queueing, PostgreSQL persistence, and a Next.js dashboard.

## Current Project Status

This project is in active development and is **working for local development workflows**.

### ✅ Implemented and Working

- FastAPI backend with modular API routes (`auth`, `repo`, `analysis`, `dashboard`, `admin`, `payments`)
- JWT-based authentication flow with OTP verification
- CORS setup for local frontend/backend integration with credentialed requests
- Repository ingestion:
  - GitHub repository submission
  - ZIP upload support
- Background scanning architecture using Celery + Redis
- Dashboard/statistics endpoints
- Frontend app (Next.js App Router) with auth screens, dashboard pages, and protected-route patterns
- Basic rate limiting and upload size limit middleware in backend

### ⚠️ Important Notes

- Some roadmap and analysis documents in the repo list production-hardening items that are not fully completed yet.
- Current state is suitable for local/dev testing; production deployment should follow the hardening guides in the docs.

## Monorepo Structure

```text
Code-Radar/
├── backend/                       # FastAPI + Celery + SQLAlchemy backend
│   ├── app/
│   │   ├── api/                   # Route modules
│   │   ├── core/                  # Config, DB, JWT, Celery setup
│   │   ├── middleware/            # Rate limit and related middleware
│   │   ├── models/                # SQLAlchemy models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # Analysis and repo processing services
│   │   └── workers/               # Background worker logic
│   └── requirements.txt
└── code-radar-saa-s-dashboard/    # Next.js frontend
    ├── app/
    ├── components/
    ├── context/
    ├── hooks/
    └── lib/
```

## Local Development Setup

## 1) Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## 2) Celery Worker

From `backend/` (with env activated):

```bash
celery -A app.core.celery_app worker --pool=solo --loglevel=info
```

## 3) Frontend

```bash
cd code-radar-saa-s-dashboard
npm install
npm run dev
```

Frontend URL:

- App: `http://localhost:3000`

## Environment Variables

Create `.env` files for both backend and frontend.

Backend (`backend/.env`) typically includes:

- `DATABASE_URL`
- `JWT_SECRET`
- `REDIS_URL`
- Email/OAuth variables as required

Frontend (`code-radar-saa-s-dashboard/.env`) typically includes:

- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- client-side OAuth/public variables as required

## Useful Docs in This Repo

- `DEPLOYMENT_STATUS.md`
- `PRODUCTION_ANALYSIS.md`
- `PRODUCTION_REFACTORING.md`
- `CORS_AND_AUTH_GUIDE.md`
- `backend/README.md`

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Celery, Redis, PostgreSQL
- Frontend: Next.js 15, React 18, TypeScript, Tailwind CSS
- Auth/Security: JWT, OTP flow, CORS controls, rate limiting

## License

Add your preferred license before public release.
