# Deployment Guide

This deploys the project using entirely free tiers: **Neon** (Postgres),
**Render** (backend API), and **Vercel** (frontend). Total time: ~20 minutes.

## Step 1 — Database (Neon)

1. Go to https://neon.tech, sign up (free), create a new project.
2. Copy the **connection string** it gives you, looks like:
   ```
   postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require
   ```
3. Keep this open, you'll need it in Step 2.

## Step 2 — Backend (Render)

1. Push this repo to GitHub first (see `README.md` if you haven't).
2. Go to https://render.com, sign up (free), click **New > Web Service**.
3. Connect your GitHub repo. Render will detect the `backend/render.yaml`
   blueprint automatically (or manually set **Root Directory** to `backend`
   and **Runtime** to Docker if it doesn't).
4. Fill in the environment variables it asks for (marked `sync: false` in
   `render.yaml`, meaning Render won't guess them for you):
   - `GROQ_API_KEY` — from https://console.groq.com/keys
   - `DATABASE_URL` — the Neon connection string from Step 1
   - `CORS_ORIGINS` — leave blank for now, you'll fill this in after Step 3
     once you know your Vercel URL
5. Click **Create Web Service**. First deploy takes a few minutes.
6. Once live, note your backend URL, looks like
   `https://ai-eval-system-backend.onrender.com`.
7. Test it: visit `https://your-backend-url.onrender.com/health` in a
   browser, you should get a JSON response.

## Step 3 — Frontend (Vercel)

1. Go to https://vercel.com, sign up (free), click **Add New > Project**.
2. Import the same GitHub repo. Set **Root Directory** to `frontend`.
3. Add an environment variable:
   - `VITE_API_BASE_URL` = your Render backend URL from Step 2 (no trailing slash)
4. Click **Deploy**.
5. Once live, note your frontend URL, looks like
   `https://ai-eval-system.vercel.app`.

## Step 4 — Connect them

Go back to Render, open your backend service's environment variables, and
set:
```
CORS_ORIGINS=https://your-frontend-url.vercel.app
```
Save, this triggers a redeploy. Once it's back up, open your Vercel URL,
sign up for an account, and the full app should work end to end.

## Known limitation: ChromaDB storage on the free tier

Render's free tier has an ephemeral filesystem, anything written to
disk (including the ChromaDB knowledge base used for RAG document uploads)
is wiped on every redeploy or when the free instance spins down from
inactivity. This does not affect evaluation scoring or the dashboard
(that data lives in Neon Postgres, which persists normally), only
previously-uploaded RAG source documents would need to be re-uploaded
after a redeploy.

To fix this permanently: upgrade to a Render paid plan with a persistent
disk mounted at `backend/data/chroma`, or swap ChromaDB for a hosted
vector store (e.g. Pinecone, Qdrant Cloud) in a future iteration.

## Local testing before you deploy

Confirm everything works locally against your real Neon database before
pushing:
```bash
cd backend
# .env should point DATABASE_URL at your Neon connection string
uvicorn app.main:app --reload --port 8000
```
Sign up through the local frontend, run an evaluation, confirm it shows
up in Neon's dashboard (Neon has a built-in SQL editor to check).
