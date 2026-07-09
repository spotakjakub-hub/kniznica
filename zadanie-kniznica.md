# Zadávací dokument: Systém katalogizácie rodinnej knižnice

## 1. Kontext a cieľ projektu

Máme zdedenú veľkú knižnicu — **stovky až tisíce kníh**, prevažne v slovenčine a češtine, mnohé staré a **bez ISBN**. Cieľom je webová aplikácia, ktorá umožní knihy rýchlo zkatalogizovať s minimom ručného prepisovania a následne v katalógu vyhľadávať, filtrovať a spravovať ho viacerými členmi rodiny z ľubovoľného zariadenia (iPhone, iPad, Mac, PC) cez prehliadač.

**Kľúčová myšlienka:** fotka obálky (prípadne titulného listu/tiráže) → AI identifikácia → automatické doplnenie metadát z internetu → používateľ len skontroluje a potvrdí.

## 2. Používatelia a prístup

- Aplikácia je **zdieľaná online** (nie lokálna) — prístupná cez URL z ľubovoľného zariadenia
- 2–5 používateľov, môžu pracovať súčasne
- **Bez autentifikácie v prvej verzii** (rodinné použitie, jednoduchosť je priorita) — prípadne len jednoduché zdieľané heslo/link. Architektúra má umožniť doplniť auth neskôr bez prepisovania.

## 3. Hlavné funkcie (priorita zostupne)

### 3.1 AI identifikácia z fotky (KĽÚČOVÁ FUNKCIA)
- Nahranie fotky obálky z telefónu (kamera) alebo súboru
- Fotka sa pošle do **Google Gemini API** (vision) s promptom na extrakciu štruktúrovaných metadát: názov, podtitul, autor(i), vydavateľ, rok vydania, jazyk, edícia — návrat ako JSON
- Voliteľne druhá fotka (titulný list / tiráž) pre presnejšie údaje
- Gemini zvolený kvôli bezplatnej úrovni (Anthropic API kľúč nemáme)
- AI výsledok sa skombinuje s vyhľadaním v Open Library API a Google Books API (podľa ISBN ak sa našlo, inak podľa názov+autor)
- Predvyplnený formulár na kontrolu → uloženie jedným klikom

### 3.2 Hromadný (batch) režim
- Nahrať naraz **desiatky fotiek** (drag & drop, multi-select z galérie telefónu)
- Spracovanie prebieha na pozadí (fronta), používateľ nemusí čakať
- Obrazovka "Na potvrdenie": zoznam spracovaných kníh s predvyplnenými údajmi, rýchle potvrdenie/oprava/zamietnutie po jednej
- Toto je zásadné pre efektivitu — fotenie políc oddelené od potvrdzovania

### 3.3 Ďalšie spôsoby pridania
- ISBN lookup (ručné zadanie čísla → automatické metadáta)
- Vyhľadanie podľa názvu + autora
- Plne ručné pridanie

### 3.4 Katalóg
- Mriežka kníh s obálkami, responzívna (mobil aj desktop)
- Fulltextové vyhľadávanie (názov, autor, vydavateľ, ISBN) — musí zvládať slovenskú diakritiku
- Filtre: kategória, jazyk, stav, umiestnenie
- Detail knihy so všetkými údajmi a fotkou
- Úprava a mazanie záznamov

### 3.5 Evidencia umiestnenia
- Každá kniha má pole umiestnenie (napr. "Obývačka — polica A3")
- Filtrovanie/zoskupenie podľa umiestnenia

## 4. Dátový model

Tabuľka `books` (hlavné polia):
- id (uuid), title, subtitle, isbn, isbn13
- publisher, published_year, language (default "sk"), pages, edition
- description, notes
- cover_image_url (fotka v cloud úložisku)
- location (umiestnenie v knižnici), condition (fyzický stav)
- status (available / missing / damaged)
- category_id (FK), created_at, updated_at
- ai_confidence (voliteľné — istota AI identifikácie)

Ďalšie tabuľky: `authors` (M:N cez `book_authors`, s rolou author/editor/translator), `categories`, `tags` (M:N cez `book_tags`).

Formulár aj API musia podporovať viacerých autorov na knihu.

## 5. Technická architektúra

| Vrstva | Technológia | Poznámka |
|---|---|---|
| Databáza | **Supabase** (PostgreSQL) | bezplatná úroveň, spravované |
| Úložisko fotiek | **Supabase Storage** alebo Cloudflare R2 | obálky kníh |
| Backend | **Python FastAPI** | nasadené na Render.com alebo Railway |
| Frontend | **React + Vite** | nasadené na Vercel |
| AI identifikácia | **Google Gemini API** (vision, free tier) | kľúč v env premennej |
| Metadáta | Open Library API + Google Books API | bezplatné |

Alternatíva na zváženie: celé postaviť na Supabase (DB + Storage + Edge Functions) a zjednodušiť backend — nechávam na posúdenie pri implementácii.

## 6. Dôležité technické poznámky (poučenia z predchádzajúceho vývoja)

Existuje lokálny prototyp v `~/Downloads/library-system/` (FastAPI + PostgreSQL + React/Vite v Docker Compose) — dá sa použiť ako základ (schéma, OCR logika, React komponenty). Pri práci s ním pozor:

1. **pip v Dockeri:** na tomto Macu/sieti zlyháva pypi.org (SSL proxy pri mobilných dátach). Funkčné riešenie: `--index-url https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`. Pri cloud nasadení (Render/Railway) tento problém odpadá.
2. **bcrypt:** musí byť pinnutý `bcrypt==4.0.1` (nekompatibilita passlib s novším bcrypt) — relevantné len ak sa pridá auth.
3. **uvicorn:** spúšťať cez `python -m uvicorn`, nie priamo `uvicorn`.
4. **FastAPI trailing slash:** endpointy volať s lomkou na konci (`/api/books/`), inak 307 redirect.
5. **Docker frontend cache:** po zmenách frontendu treba `docker rmi library-system-frontend && docker compose up --build` — pri Verceli odpadá.
6. Tesseract OCR (slk+ces+eng) je v prototype funkčný — môže ostať ako záložná metóda popri Gemini.

## 7. UI/UX požiadavky

- Slovenčina ako jazyk rozhrania
- Mobile-first pre pridávanie kníh (fotenie telefónom), desktop pre správu katalógu
- Čistý, príjemný dizajn (existujúci prototyp má knižničnú estetiku — Playfair Display, teplé farby — možno prevziať)
- Minimálny počet klikov: fotka → kontrola → uložiť

## 8. Postup implementácie (návrh fáz)

1. **Fáza 1 — MVP:** Supabase setup, základný katalóg (CRUD, vyhľadávanie, filtre), ručné pridávanie, nasadenie na Vercel + Render
2. **Fáza 2 — AI:** Gemini identifikácia z jednej fotky, kombinácia s Open Library/Google Books, potvrdzovacie UI
3. **Fáza 3 — Batch:** hromadné nahrávanie, fronta na pozadí, obrazovka "Na potvrdenie"
4. **Fáza 4 — vylepšenia:** export (CSV), štatistiky, prípadné výpožičky, auth

## 9. Čo pripraviť pred štartom (manuálne kroky používateľa)

- [ ] Založiť účet na supabase.com a vytvoriť projekt (zadarmo)
- [ ] Získať Google Gemini API kľúč na aistudio.google.com (zadarmo)
- [ ] Účet na vercel.com a render.com (zadarmo, prihlásiť cez GitHub)
- [ ] GitHub repozitár pre projekt

## 10. Kritériá úspechu

- Pridanie knihy s fotkou obálky trvá **pod 30 sekúnd** aktívneho času používateľa
- Hromadný režim: 50 kníh nafotených za ~15 minút, potvrdených za ~20 minút
- AI správne identifikuje ≥80 % bežných slovenských/českých kníh z čitateľnej fotky obálky
- Katalóg je dostupný online z mobilu aj desktopu bez inštalácie
