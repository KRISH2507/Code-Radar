# 1-Day Action Plan

Goal: run Code-Radar in a production-like local environment and validate the core SaaS flow.

## 1) Prepare environment

```powershell
cd D:\code-radar\Code-Radar
copy backend\.env.example backend\.env
```

Update `backend\.env` with real values:
- `DATABASE_URL`
- `JWT_SECRET` (32+ chars)
- `REDIS_URL`
- `ALLOWED_ORIGINS`
- OAuth + email keys as needed

## 2) Start production-like stack

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

## 3) Verify backend readiness

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Expected: `status` should be `healthy` (or at minimum not `error` for required services).

## 4) Run frontend production build check

```powershell
cd D:\code-radar\Code-Radar\code-radar-saa-s-dashboard
npm install
npm run build
```

## 5) Validate end-to-end manually

1. Open `http://localhost:3000/signup`
2. Create account -> verify OTP -> obtain JWT session
3. Submit GitHub URL or ZIP in Repositories page
4. Poll repository status until completed
5. Open dashboard and confirm repository/issue metrics are visible

## 6) Run quick backend sanity checks

```powershell
cd D:\code-radar\Code-Radar\backend
python -m compileall app
```

## 7) Single command to prove core system path

Run this from repo root after services are up:

```powershell
docker compose -f docker-compose.prod.yml ps
```

Then confirm:
- `frontend`, `backend`, `worker`, `postgres`, and `redis` are all `Up`
- `/health` and `/ready` return healthy/degraded but not failing startup
