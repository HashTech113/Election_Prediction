# Election Prediction 2026

Constituency-level Indian assembly election predictions for **Kerala** and
**Tamil Nadu**, served via a unified React frontend that talks to two
independent backends.

```
.
├── frontend/                 ← React + Vite, deployed on Vercel
│   └── src/
│       ├── routes/           ← Landing, KeralaApp, TamilNaduApp (lazy)
│       ├── modules/
│       │   ├── kerala/       ← Kerala dashboard (FastAPI client)
│       │   └── tamilnadu/    ← Tamil Nadu dashboard (stdlib HTTP client)
│       ├── shared/           ← cross-module config, components
│       └── styles/           ← scoped landing.css
│
├── backend/
│   ├── kerala/               ← Railway service #1 (FastAPI)
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── data/csv/         ← all Kerala CSVs (training + predictions)
│   │   └── …
│   └── tamilnadu/            ← Railway service #2 (stdlib HTTP)
│       ├── server.py
│       ├── dataset/, data/, data_files/, models/, checkpoints/
│       └── …
│
├── scripts/
│   └── dev.sh                ← runs all 3 services locally
└── docs/
```

## Local development

Prerequisites: Python 3.11, Node 18+.

```bash
# install backend deps (do this once per backend, in their own virtualenvs)
python -m venv .venv && source .venv/bin/activate
pip install -r backend/kerala/requirements.txt
pip install -r backend/tamilnadu/requirements.txt

# install frontend deps
cd frontend && npm install && cd ..

# copy env templates
cp frontend/.env.example       frontend/.env.local
cp backend/kerala/.env.example backend/kerala/.env
cp backend/tamilnadu/.env.example backend/tamilnadu/.env

# run all three services together
chmod +x scripts/dev.sh
./scripts/dev.sh
```

| Service             | URL                          |
|---------------------|------------------------------|
| Frontend            | http://localhost:5173        |
| Kerala backend      | http://localhost:8001        |
| Tamil Nadu backend  | http://localhost:8002        |

## Deployment

### Frontend → Vercel
- Root directory: `frontend`
- Framework: Vite (auto-detected)
- Env vars (Production): `VITE_API_KERALA_URL`, `VITE_API_TN_URL`

### Kerala backend → Railway
- Root directory: `backend/kerala`
- Watch Paths: `backend/kerala/**`
- Env vars: `CORS_ORIGINS` (set to your Vercel domain)
- `Procfile` and `railway.json` are already in place.

### Tamil Nadu backend → Railway
- Root directory: `backend/tamilnadu`
- Watch Paths: `backend/tamilnadu/**`
- Env vars: `CORS_ALLOW_ORIGIN` (set to your Vercel domain)
- `Procfile` and `railway.json` are already in place.

## API surface

| State       | Native routes (relative to its Railway domain)                          |
|-------------|-------------------------------------------------------------------------|
| Kerala      | `/api/health`, `/api/predictions`, `/api/predictions/meta`, `/api/predictions/kerala/...`, `/docs` |
| Tamil Nadu  | `/api/health`, `/api/predictions`, `/api/historical/results`, `/api/sentiment/...`         |
