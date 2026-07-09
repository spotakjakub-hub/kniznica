# Rodinná knižnica

Webová aplikácia na katalogizáciu rodinnej knižnice. Fáza 1 (MVP): katalóg s vyhľadávaním a filtrami, ručné pridávanie kníh, viacerí autori, umiestnenia, kategórie a štítky.

**Živá aplikácia:** https://kniznica-jet.vercel.app
**API:** https://kniznica-api.onrender.com/api (dokumentácia na `/docs`)
**Repo:** https://github.com/spotakjakub-hub/kniznica

> Backend beží na Render free tieri — po ~15 min nečinnosti zaspí a prvé načítanie môže trvať ~30–60 s.

## Architektúra

| Vrstva | Technológia | Hosting |
|---|---|---|
| Databáza | PostgreSQL | Supabase |
| Backend | Python FastAPI | Render.com |
| Frontend | React + Vite | Vercel |

## Lokálny vývoj

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # doplň DATABASE_URL (Supabase Session pooler)
python -m uvicorn app.main:app --reload --port 8000
```

API beží na http://localhost:8000, dokumentácia na http://localhost:8000/docs.

> Pozn.: ak pip zlyháva na SSL (mobilné dáta), použi
> `pip install -r requirements.txt --index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Beží na http://localhost:5173, `/api` sa proxuje na backend (port 8000).

## Nasadenie

- **Supabase:** vytvor projekt, connection string (Session pooler) patrí do `DATABASE_URL`. Tabuľky sa vytvoria automaticky pri štarte backendu, rozšírenie `unaccent` sa zapne tiež automaticky (vyhľadávanie bez diakritiky).
- **Render:** repo obsahuje `render.yaml` (Blueprint). Nastav env `DATABASE_URL` a `CORS_ORIGINS` (URL Vercel aplikácie).
- **Vercel:** root directory `frontend`, framework Vite. Nastav env `VITE_API_URL` na `https://<render-app>.onrender.com/api`.

## API prehľad

- `GET/POST /api/books/` — zoznam (q, category_id, status, language, location, sort, skip, limit) / vytvorenie
- `GET/PUT/DELETE /api/books/{id}`
- `GET/POST /api/categories/`
- `GET /api/meta/locations`, `GET /api/meta/languages`, `GET /api/meta/stats`
- `GET /api/health`

Endpointy kolekcií treba volať s lomkou na konci (`/api/books/`), inak FastAPI vráti 307.

## Ďalšie fázy

2. AI identifikácia z fotky (Gemini) + Open Library/Google Books
3. Hromadný (batch) režim s frontou
4. Export, štatistiky, výpožičky, auth
