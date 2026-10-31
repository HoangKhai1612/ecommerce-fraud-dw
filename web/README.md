# web — Phase 31 Frontend

React + TypeScript + Vite frontend for the Integrated Fraud Detection Testing
Platform. Calls the FastAPI backend (`api/`, port 8000) over HTTP only. No
database credentials, no mock data, no static-only UI.

## Structure

```
web/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── Dockerfile
├── .env.example
├── README.md
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── api.ts          # HTTP client (fetch) against FastAPI
    ├── types.ts        # TypeScript schemas
    ├── components/     # Layout (sidebar + topbar)
    └── pages/          # Overview, TransactionTesting, PredictionDetail,
                        # PredictionHistory, AIAssistant, SystemStatus
```

## Run locally

Prerequisites: Node.js (>=18), npm, and the FastAPI backend running on
`http://localhost:8000` (see repository runbook).

```powershell
cd web
copy .env.example .env
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to `http://localhost:8000`.

## Build

```powershell
cd web
npm install
npm run build        # tsc + vite build -> dist/
npm run preview      # serve dist locally for testing
```

## Docker

Built and served with nginx:

```powershell
docker build -t fraud-dw-web -f web/Dockerfile .
docker run -p 5173:80 -e VITE_API_BASE_URL=http://host.docker.internal:8000 fraud-dw-web
```

The `web` service is also declared in the root `docker-compose.yml`.

## Pages

- `/` Overview — service status (API, XGBoost, PostgreSQL, AI, Ollama) and
  recent predictions.
- `/testing` Transaction Testing — mode A (IEEE-CIS, samples/CSV/form) and
  mode B (simplified e-commerce form mapped to verified raw columns). Real
  XGBoost inference via `POST /predictions`.
- `/prediction/:id` Prediction Detail — model result, input payload, AI
  explanation.
- `/history` Prediction History — filters, pagination.
- `/ai` AI Assistant — chat grounded in the real prediction context.
- `/status` System Status.

No secrets are stored in the frontend. All calls go through FastAPI.
