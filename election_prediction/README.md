# Election Prediction Dashboard

A unified UI that combines two trained, fully-developed prediction systems:

- **Tamil Nadu** — 234 constituency / 38 district 2026 Assembly projections
- **Kerala** — 140 constituency / 14 district 2026 Assembly projections

A single landing page (Poppins + glass-morphism, matching both dashboard
themes) lets the user choose which state's dashboard to open. Each
state's existing frontend and backend run unchanged — the launcher just
wires them together on different ports and points each frontend at its
own backend.

## Folder layout

```
election_prediction/
├── .gitignore               # shared ignore rules for Python + Node artifacts
├── README.md                # this file
├── requirements.txt         # combined Python deps for both backends
├── run_all.py               # one-command launcher (starts everything)
├── landing_page/            # unified landing page (static)
│   ├── index.html
│   └── landing.css
├── tamilnadu/               # untouched — fully trained Tamil Nadu system
│   ├── backend/
│   ├── frontend/
│   └── ...
└── kerala/                  # untouched — fully trained Kerala system
    ├── backend/
    ├── frontend/
    └── ...
```

## Ports used by `run_all.py`

| Service                | Default port | Override env var       |
| ---------------------- | ------------ | ---------------------- |
| Landing page (entry)   | 5173         | `LANDING_PORT`         |
| Tamil Nadu frontend    | 5174         | `TN_FRONTEND_PORT`     |
| Kerala frontend        | 5175         | `KL_FRONTEND_PORT`     |
| Tamil Nadu backend API | 8101         | `TN_BACKEND_PORT`      |
| Kerala backend API     | 8201         | `KL_BACKEND_PORT`      |
| Bind host              | 0.0.0.0      | `HOST`                 |

The launcher injects `VITE_API_BASE_URL` into each frontend so it talks to
its own backend — no code changes are needed in either dashboard.

## Prerequisites

- **Python 3.10+** (for both backends)
- **Node.js 18+ / npm 9+** (for the Vite-based frontends)
- ~3–4 GB free disk space (PyTorch + node_modules)

Verify:

```bash
python --version
node --version
npm --version
```

## Installation

From the `election_prediction/` folder:

### 1. Python dependencies (one-time)

```bash
# Optional but recommended — create a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate            # Windows PowerShell

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Node dependencies

`run_all.py` will run `npm install` automatically the first time it sees
that a frontend is missing `node_modules`. To do it manually:

```bash
cd tamilnadu/frontend && npm install && cd -
cd kerala/frontend && npm install && cd -
```

## Git hygiene

The root `.gitignore` now covers common local/dev artifacts for the whole
workspace:

- Python caches and virtual environments (`__pycache__/`, `.venv/`, etc.)
- Node artifacts (`node_modules/`, `.vite/`, frontend `dist/`)
- Local env/secrets (`.env*`, with `.env.example` kept)
- IDE/OS junk (`.vscode/`, `.idea/`, `.DS_Store`, temp swap files)
- Model training runtime outputs (`*/backend/checkpoints/`, `*/train_run.log`)

If large files were committed before ignore rules were added, remove them
from Git tracking once (without deleting local files):

```bash
git rm -r --cached .
git add .
git commit -m "chore: refresh tracked files using updated .gitignore"
```

## Running the unified UI

From the `election_prediction/` folder:

```bash
python run_all.py
```

Then open the landing page:

```
http://127.0.0.1:5173
```

Click **Tamil Nadu** or **Kerala** to open the corresponding dashboard.
Press **Ctrl+C** in the launcher terminal to stop every server cleanly.

### Custom ports

```bash
LANDING_PORT=4000 \
TN_BACKEND_PORT=9101 KL_BACKEND_PORT=9201 \
TN_FRONTEND_PORT=4174 KL_FRONTEND_PORT=4175 \
python run_all.py
```

### LAN access

The launcher binds to `0.0.0.0` by default and prints the LAN URLs on
startup. Open the landing page from another device on the same network
using:

```
http://<your-lan-ip>:5173/?tn=http://<your-lan-ip>:5174&kl=http://<your-lan-ip>:5175
```

(The optional `?tn=` / `?kl=` query parameters override the dashboard
URLs the cards link to — useful when the launcher machine is not the
visitor's `localhost`.)

## Running each piece individually (optional)

If you only want one state up, skip the launcher and run the
state-specific entry point directly:

```bash
# Tamil Nadu
cd tamilnadu
python backend/server.py        # backend on :8001
cd frontend && npm run dev      # frontend on :5173

# Kerala
cd kerala
python run.py                   # backend on :8001 + frontend on :5173
```

## Theme / design

The landing page mirrors both dashboards exactly:

- **Font**: Poppins (Google Fonts), 400/600/700/800
- **Background**: soft navy/grey radial gradient with two blurred orbs
- **Cards**: glass-morphism (`backdrop-filter: blur(28px) saturate(200%)`)
  with the same shadow tokens used by both dashboards
- **CTA pill**: `linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7)` —
  identical to the active-tab gradient already used in both apps
- **Title color**: `--color-navy: #0b1b6f` matching both hero titles
- Smooth entrance animations + `prefers-reduced-motion` respect

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `npm not found` | Install Node.js 18+ and reopen the terminal |
| `Module not found: torch` | Re-run `pip install -r requirements.txt` inside the active venv |
| Only one dashboard opens (e.g. Kerala works, Tamil Nadu does not) | Look at the `[ready]` / `[warn]` lines `run_all.py` prints after boot. Any line marked `FAIL` shows which service didn't come up — usually a port conflict or a missing Python module in that backend. |
| Card opens but dashboard says "Failed to load predictions" | Make sure the backend on the matching port is also running (check the `run_all.py` log lines) |
| Port already in use | Set the relevant `*_PORT` env var (see table above) |
| Stale predictions | Stop launcher, regenerate `predictions_2026.csv` inside each backend, restart |

## License & credits

Both `tamilnadu/` and `kerala/` keep their own README and license. This
top-level folder only adds the unified launcher and landing page.
