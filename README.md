# Family Library

Web app for cataloguing a family book library. Phase 1 (MVP): catalog with search and filters, manual book entry, multiple authors per book, locations, categories and tags.

**Live app:** https://kniznica-jet.vercel.app
**API:** https://kniznica-api.onrender.com/api (docs at `/docs`)
**Repo:** https://github.com/spotakjakub-hub/kniznica

> The backend runs on Render's free tier — it sleeps after ~15 min of inactivity and the first load may take ~30–60 s.

## Architecture

| Layer | Technology | Hosting |
|---|---|---|
| Database | PostgreSQL | Supabase |
| Backend | Python FastAPI | Render.com |
| Frontend | React + Vite | Vercel |

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL (Supabase Session pooler)
python -m uvicorn app.main:app --reload --port 8000
```

API runs at http://localhost:8000, docs at http://localhost:8000/docs. Without `DATABASE_URL` it falls back to a local SQLite file (dev only).

> Note: if pip fails on SSL (mobile data), use
> `pip install -r requirements.txt --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at http://localhost:5173; `/api` is proxied to the backend (port 8000).

## Deployment

- **Supabase:** create a project; the Session pooler connection string goes into `DATABASE_URL`. Tables are created automatically on backend startup, and the `unaccent` extension is enabled automatically (diacritics-insensitive search).
- **Render:** the repo contains `render.yaml` (Blueprint). Set the `DATABASE_URL` and `CORS_ORIGINS` (Vercel app URL) env vars.
- **Vercel:** root directory `frontend`, framework Vite. Set `VITE_API_URL` to `https://<render-app>.onrender.com/api`.

## API overview

- `GET/POST /api/books/` — list (q, category_id, status, language, location, sort, skip, limit) / create
- `GET/PUT/DELETE /api/books/{id}`
- `GET/POST /api/categories/`
- `GET /api/meta/locations`, `GET /api/meta/languages`, `GET /api/meta/stats`
- `GET /api/health`

Collection endpoints must be called with a trailing slash (`/api/books/`), otherwise FastAPI returns a 307 redirect.

## Next phases

2. AI identification from a cover photo (Gemini) + Open Library/Google Books lookup
3. Batch mode with a background queue
4. CSV export, statistics, lending, auth
