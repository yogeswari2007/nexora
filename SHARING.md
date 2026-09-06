# How to Share NEXORA with Other People

There are several ways to let others see NEXORA. Pick the one that matches your goal.

> **Quick answer:**
> - **Show a friend right now (demo):** use the **live preview link** you already have, or spin up a **tunnel** (ngrok) for a temporary public URL.
> - **Let friends on the same Wi-Fi open it on their phones:** run it on your own computer and share your **LAN IP**.
> - **Get a permanent public link anyone can open:** **deploy** it to a free cloud host (Render / Railway / PythonAnywhere).
> - **Let others run it themselves / collaborate:** **share the code** (GitHub repo or a zip).

---

## Option 1 — Live preview link (what you see now)

The Arena agent preview is the easiest for a quick look. It's already live:
**`{port}-{sandboxId}.e2b.app`** (visible in your browser at the preview panel).

- ✅ Zero setup, phone-friendly.
- ⚠️ This URL is **session-scoped** — it belongs to this sandbox session and is typically **not** a permanent public address others can rely on. Use it for a quick demo, not as your "real" link.

---

## Option 2 — Same Wi-Fi on your own computer (phones/tablets on your network)

Run NEXORA on **your** laptop/PC and let people on the **same Wi-Fi** open it. This works great for family/friends at home.

1. On your computer, inside the `nexora` folder:
   ```bash
   pip install flask
   python seed.py
   python app.py
   ```
2. Find your computer's **local IP**:
   - Windows:  `ipconfig`  → look for the **IPv4 Address** (e.g. `192.168.1.23`)
   - macOS:    `ipconfig getifaddr en0`
   - Linux:    `hostname -I`
3. Make sure **`python app.py` binds to 0.0.0.0** (it already does).
4. On any phone/tablet/laptop on the same Wi-Fi, open:
   ```
   http://192.168.1.23:8080
   ```
   (replace the IP with yours)

> **Windows Firewall:** if devices can't connect, allow port **8080** through the firewall for private networks.

---

## Option 3 — Temporary public link (tunnel) — great for a 1-off demo

Tunnel your local server through a public URL. No account needed for a quick try with ngrok.

```bash
# inside the nexora folder, with `python app.py` running:
ngrok http 8080
```

- ngrok prints a **public HTTPS URL** (e.g. `https://abc123.ngrok-free.app`).
- Anyone can open that URL on any device. It works until you stop it.
- **Alternative:** `cloudflared tunnel --url http://localhost:8080` (Cloudflare), or **localtunnel** (`npx localtunnel --port 8080`).

> The tunnel URL is temporary (dies when you close the tunnel / your machine sleeps). For a permanent link, deploy (Option 4).

---

## Option 4 — Permanent public deployment (FREE) — best for real sharing

Take NEXORA live so anyone can open a stable URL 24/7. I already added the files you need:

- `requirements.txt`
- `wsgi.py` (production entrypoint)
- `Procfile` (Heroku / generic)
- `render.yaml` (Render one-click Blueprint)
- `.gitignore`

### A) Render — easiest (free tier)
1. Push the `nexora` folder to a **GitHub** repo.
2. Go to **render.com** → **New → Blueprint** → pick your repo (it reads `render.yaml`).
3. Render builds (`pip install` + `python seed.py` to create the DB) and starts gunicorn.
4. You get a URL like `https://nexora.onrender.com`. Share that link.

> **Note on SQLite on free hosts:** the free-tier disk is **ephemeral** — the database is recreated on each deploy, and saved bookings reset. The 55 hotels are seeded automatically, so the site always works; just don't treat it as persistent storage. For real persistence you'd add a DB like PostgreSQL (and I can add that for you).

### B) Railway (free tier)
1. Push to GitHub.
2. **railway.app** → **New Project → Deploy from GitHub repo**.
3. Add a start command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2`
4. Root directory set to the `nexora` folder.

### C) PythonAnywhere (great for Python, free tier)
1. Upload / clone the project.
2. Create a Web App → manual config → WSGI file pointing to `wsgi:app`.

### D) Fly.io
```bash
flyctl launch
flyctl deploy
```
(free allowance for small apps.)

---

## Option 5 — Share the code so others can run it themselves

- Push to **GitHub** and share the repo link (the `README.md` has full setup instructions).
- Or **zip the `nexora` folder** (include `hotels.db`) and send it — the other person runs:
  ```bash
  pip install flask
  python seed.py
  python app.py
  ```

---

## Summary — which should I use?

| Goal                                   | Best option                      |
|----------------------------------------|----------------------------------|
| Quick demo a friend should see now      | Live preview link / ngrok tunnel |
| Family on the same Wi-Fi                | LAN IP (Option 2)                |
| Permanent URL people can save & revisit | Deploy to Render/Railway/PA      |
| Let them run it themselves / cooperate  | GitHub repo or zip             |

---

## What I can do to help next
I can:
- **Add PostgreSQL** so bookings persist on free hosts.
- **Prepare a deploy-ready zip** of the project for you to download.
- **Add a "share" button** in the app that copies a shareable link to a hotel.
- **Write a GitHub Actions workflow** for auto-deployment.

Just tell me which you'd like!
