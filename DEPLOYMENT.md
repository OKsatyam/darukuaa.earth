# Deploying Darukaa Biodiversity Intelligence

Three pieces, three free-tier services: MongoDB Atlas (session storage),
Render or Railway (FastAPI backend), Vercel (Next.js frontend).

## 1. MongoDB Atlas

1. Create a free (M0) cluster at https://cloud.mongodb.com.
2. Database Access → add a user with a password.
3. Network Access → add `0.0.0.0/0` (allow from anywhere — fine for a demo;
   tighten to your host's IP range for anything longer-lived).
4. Get the connection string (Connect → Drivers → Python), it looks like:
   `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority`
5. Keep it handy for step 2 — it becomes `MONGODB_URI`.

If you skip this step entirely, the app still runs — `app/db.py` is
built to fail soft, so chat "just works" without cross-session memory.

## 2. Backend (Render)

1. Push this repo to GitHub (already done).
2. https://render.com → New → Blueprint → connect the repo. Render reads
   `backend/render.yaml` automatically (root dir, build/start commands
   already set).
3. Fill in the env vars Render prompts for (marked `sync: false` in the
   blueprint so they aren't hardcoded in git):
   - `MONGODB_URI` — from step 1
   - `ALLOWED_ORIGINS` — leave blank for now, come back after step 3
4. Deploy. First boot will download the small ONNX embedding model and
   build the ChromaDB index (see `app/main.py`'s startup hook) — expect
   the first deploy to take a couple of minutes longer than later ones.
5. Note the service URL, e.g. `https://darukaa-biodiversity-api.onrender.com`.
   Check `<url>/health` returns `{"status": "ok"}`.

Railway works the same way using `backend/Procfile` instead of a
blueprint: New Project → Deploy from GitHub → set root directory to
`backend` → add the same env vars → Railway auto-detects the Procfile.

## 3. Frontend (Vercel)

1. https://vercel.com → New Project → import the same GitHub repo.
2. Set **Root Directory** to `frontend`.
3. Add an env var: `NEXT_PUBLIC_API_URL` = the Render/Railway URL from
   step 2 (no trailing slash).
4. Deploy. Vercel auto-detects Next.js — no other config needed.
5. Note the frontend URL, e.g. `https://darukaa-biodiversity.vercel.app`.

## 4. Close the loop: lock down CORS

Go back to Render/Railway → env vars → set `ALLOWED_ORIGINS` to your
Vercel URL from step 3 (comma-separate if you have more than one, e.g. a
preview + production URL) → redeploy the backend. This replaces the
wide-open `*` CORS default with just your actual frontend.

## Local development (no deploy needed)

```
# backend
cd backend
cp .env.example .env        # fill in MONGODB_URI if you have one
pip install -r requirements.txt
python -m app.services.rag  # builds the ChromaDB index once
uvicorn app.main:app --reload

# frontend
cd frontend
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```
