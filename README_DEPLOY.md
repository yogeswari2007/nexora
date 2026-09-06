# NEXORA — Get a permanent shared link (deploy via GitHub)

This app is a **Flask + SQLite** application, which means GitHub Pages alone
**cannot** run it — GitHub Pages only serves static files, but NEXORA needs the
Python backend and the database to power hotel search, the map, and
voice search.

The good news: you still do everything **through GitHub**, and the permanent
link comes from a free hosting service (Render) that auto‑deploys from your
GitHub repo. When you push code, your live site updates automatically.

If you do want GitHub Pages, see the "Alternate: GitHub Pages only" section.

---

## Before you start
Make sure you have:
- A free **GitHub** account (https://github.com/signup)
- **Git** installed on your machine (`git --version`)
- A free **Render** account (https://render.com) — created with GitHub

---

## Step 1 — Push the code to GitHub

Open a terminal and run these from the project folder (`nexora/`):

```bash
cd nexora

# 1. Create the local repository
git init

# 2. Add all project files (the .gitignore keeps junk out)
git add .
git commit -m "NEXORA: hotel search, map + voice search"

# 3. Create an empty repo on GitHub (no README) and note its URL, e.g.
#    https://github.com/YOUR_USERNAME/nexora.git
git branch -M main

# 4. Connect and push
git remote add origin https://github.com/YOUR_USERNAME/nexora.git
git push -u origin main
```

> Replace `YOUR_USERNAME` with your GitHub username.

Now your code is on GitHub. Next we turn it into a **live, permanent link**.

---

## Step 2 — Deploy it on Render (permanent HTTPS link)

1. Log in to **https://render.com** → **New** → **Blueprint**.
2. Connect your **GitHub** account.
3. Select the **nexora** repository.
4. Render reads `Procfile` (`gunicorn app:app`) and `requirements.txt`.
   Set/review these values:
   - **Plan:** Free
   - **Instance type:** Free
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4`
5. Click **Apply / Create Web Service**. Render builds and starts the app.
6. After ~1–2 minutes you get a permanent link like:

   **`https://nexora-XXXX.onrender.com`**

That URL now works on **any device** (phone, tablet, laptop) and can be **shared**
with anyone. Copy it and send it. When you `git push` changes later, Render
redeploys automatically.

> **Note:** the demo SQLite database lives on the server's disk, so a free
> instance can be reset on redeploys (the data re‑seeds from `seed.py`). That's
> fine for a demo/prototype.

---

## Step 3 — Open on any device and share

- Open the **`https://nexora-XXXX.onrender.com`** URL in the browser of any
  phone, tablet or computer.
- Share it by messaging / emailing the same URL — nobody needs to install
  anything.
- Voice search and the live map need **HTTPS** (which the Render link gives you)
  and microphone permission — click **Allow** when the browser asks.

---

## Video/walkthrough alternatives

- **Railway** (https://railway.app) — similar "Deploy from GitHub" flow.
- **Fly.io** (https://fly.io) — `fly launch` then deploy.
- **PythonAnywhere / Replit** — good for quick demos but friendlier for
  prototype sharing.

All of these read from the GitHub repo, so your code stays "through GitHub".

---

## Alternate: GitHub Pages only (static frontend)

If you specifically want a **github.io** URL, you must host the backend
separately, because Pages won't run Flask. Two ways:

**A. Host the frontend on GitHub Pages + backend on Render**
1. Deploy the backend to Render (Step 2) → you get an API URL.
2. Edit `static/index.html` so every `fetch()` and API call goes to that URL
   (e.g. change `/api/hotels` → `https://nexora-XXXX.onrender.com/api/hotels`).
3. Commit, enable **Settings → Pages** on the repo → publish the `master/main`
   branch (or the `docs/` folder).
4. Your shared link becomes `https://YOUR_USERNAME.github.io/nexora/`.

**B. Seed a fully static version (loses live backend)**
Export the data and drop the API. Not recommended — you lose voice search,
the map, and search filtering.

> **Recommendation:** use Step 2 (Render). It's the same amount of work, gives
> one permanent link, and keeps every feature working.

---

## Important notes for a successful deploy

- `requirements.txt` includes `Flask`, `SpeechRecognition`, `requests`,
  `gunicorn`. Installed automatically by the host.
- The frontend **records your microphone and encodes it as WAV**, so the
  backend needs **no ffmpeg** to transcribe. (The backend also converts other
  formats with ffmpeg if a non-WAV file is uploaded, but the built‑in path is
  WAV.)
- Voice search sends audio to `/api/voice/search`, which transcribes it
  server‑side (Google's recognizer, no API key needed) and returns matching
  hotels. Works best in Chrome/Edge. On browsers that support the native
  Web Speech API, the app uses that instead (also server‑free).
- Set `PORT` if the host needs it (Render sets `$PORT` automatically; your
  `Procfile` uses it).
