# Phase 31 — Frontend Guide

## Stack

- React 18 + TypeScript + Vite
- react-router-dom (client-side routing)
- Plain `fetch` via `src/api.ts` (no extra HTTP client dependencies)
- CSS modules (inline styles + `src/index.css`)
- Served by nginx in production (`web/Dockerfile`)

## Run Locally

```powershell
cd web
copy .env.example .env
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to
`http://localhost:8000` (FastAPI backend).

## Build

```powershell
cd web
npm install
npm run build        # tsc + vite build -> dist/
npm run preview      # serve dist locally
```

Build output: `dist/` (~200 kB JS gzipped).

## Docker

```powershell
docker build -t fraud-dw-web -f web/Dockerfile .
docker run -p 5173:80 -e VITE_API_BASE_URL=http://host.docker.internal:8000/api fraud-dw-web
```

The `web` service is also declared in the root `docker-compose.yml` (port 5173).

## Pages

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `Overview` | Service status + recent predictions |
| `/testing` | `TransactionTesting` | Mode A (IEEE-CIS) + mode B (ecommerce-sim) forms, CSV batch, AI explain |
| `/prediction/:id` | `PredictionDetail` | Single prediction detail + input payload |
| `/history` | `PredictionHistory` | Filterable, paginated history |
| `/ai` | `AIAssistant` | Chat with AI (`?prediction=` for context) |
| `/status` | `SystemStatus` | Service status polling (15s) |

## API Client (`src/api.ts`)

- `apiJson<T>(path, opts)` — fetch JSON, throws on non-ok with `status`/`body`
- `apiRequest(path, opts)` — raw fetch wrapper
- `API_BASE_URL` — from `VITE_API_BASE_URL` env or `/api`

All types are re-exported from `api.ts` via `src/types.ts`.

## No Secrets

The frontend stores no credentials, API keys, or database connection strings.
All calls go through FastAPI on port 8000.
