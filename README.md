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

## AI identification (Phase 2)

- `POST /api/scan/identify` — cover photo (+ optional title page) -> Gemini vision -> merged with Open Library/Google Books; the photo is stored in Supabase Storage (public bucket `covers`)
- `GET /api/scan/isbn/{isbn}` — metadata lookup by ISBN
- `GET /api/scan/search?title=&author=` — candidate search
- Backend env: `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, optional `GEMINI_MODEL` (falls back through gemini-3.5-flash -> flash-latest -> 3.1-flash-lite -> 2.0-flash)

## Batch mode (Phase 3)

- **Review page** (`/review`): drop dozens of cover photos; they upload to Supabase Storage, queue in the `scan_jobs` table and get identified by an in-process background worker (no separate dyno on Render's free tier — the worker resumes pending jobs on startup). Confirm/edit/reject one by one; an optional batch-wide shelf location is applied to every photo.
- `POST /api/queue/upload` (multipart `files[]` + optional `location`), `GET /api/queue/`, `POST /api/queue/{id}/retry`, `DELETE /api/queue/{id}`
- Photos are downscaled client-side (max 1600 px JPEG) before upload.

## Phase 4: export, lending, auth

- `GET /api/export/csv` — full catalog export (UTF-8 BOM, `;`-separated for European Excel); ⬇ CSV button on the Books page
- **Lending:** `POST /api/books/{id}/lend`, `POST /api/loans/{id}/return`, `GET /api/loans/active`; lending card with history on the book detail page
- **Richer stats:** by category, top authors, by decade, active loans — shown on the Overview page
- **Optional shared password:** set the `LIBRARY_PASSWORD` env var on the backend to require it; the frontend shows an unlock screen and sends the password as the `X-Library-Key` header. Unset = open access.
