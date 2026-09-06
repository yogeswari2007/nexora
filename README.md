# NEXORA — Next-Generation Hotel Discovery & Booking

> **find · stay · access**

A responsive, accessible hotel-finder web app for India. NEXORA lets travellers search inclusive,
accessibility-friendly hotels, compare rooms & food menus, see prices in **₹ INR** with instant
**$ USD** conversion, review accessibility features and nearby services, and book a stay — then
download an **accessibility blueprint** of the hotel.

---

## ✨ Features

- **Hotel search & discovery** — by destination, type, region, star rating, price and sort.
- **Accessibility-first** — every hotel lists verified features: wheelchair access, lifts,
  ramps, accessible bathrooms & rooms, staff assistance, accessible parking, braille signage,
  hearing loops, guide-dog friendliness and more. Filter by any of them.
- **Rich detail page** — hotel photos, room types & prices, food menu (veg/non-veg), nearby famous
  places, nearby hospitals, nearby restaurants and nearby transport (airport / railway / local).
- **INR ⇄ USD** — one-tap currency toggle across the whole site (1 USD = 83.5 INR).
- **Booking + Accessibility Blueprint** — after booking you get a booking reference and an
  automatically generated SVG blueprint showing entrances, ramps, lifts, accessible rooms and routes.
- **Responsive & accessible** — semantic HTML, ARIA labels, keyboard navigation, `:focus-visible`,
  `prefers-reduced-motion`, skip-link, and layouts that adapt to phones, tablets and laptops.
- **Database-driven** — 55 hotels across 40+ destinations in India stored in SQLite, served by a
  Flask REST API and rendered by a vanilla-JS single-page frontend.

---

## ⚙️ Tech Stack

| Layer      | Technology                                   |
|------------|----------------------------------------------|
| Backend    | Python **Flask**                             |
| Database   | **SQLite** (file: `hotels.db`)               |
| Frontend   | Vanilla **HTML / CSS / JS** (no build step)  |
| Graphics   | Generated **SVG** hotel photos + blueprints  |
| Testing    | **Playwright** (headless Chromium)           |

---

## 🚀 Run locally

```bash
cd nexora

# 1) Install Flask
pip install flask

# 2) Seed the database (creates hotels.db with 55 hotels)
python seed.py

# 3) Start the server
python app.py
# -> serving on http://0.0.0.0:8080
```

Open `http://127.0.0.1:8080` in your browser. On a phone, visit your machine's LAN IP on port 8080.

> **Environment variable:** `PORT` overrides the default port (default `8080`).

---

## 🌐 API Endpoints

| Method | Endpoint                        | Description                                        |
|--------|---------------------------------|----------------------------------------------------|
| GET    | `/api/hotels`                   | Search / filter hotels                             |
| GET    | `/api/hotels/<id>`              | Full detail for one hotel                          |
| GET    | `/api/cities`                   | Distinct cities with state & hotel counts          |
| GET    | `/api/meta`                     | Regions, types, accessibility labels, USD rate     |
| POST   | `/api/bookings`                 | Create a booking                                   |
| GET    | `/api/bookings/<ref>`           | Look up a booking                                  |
| GET    | `/api/hotel/<id>/photo.svg`     | Generated hotel photo (SVG)                        |
| GET    | `/api/blueprint/<ref>.svg`      | Accessible blueprint for a booking (SVG)           |
| GET    | `/api/rate`                     | Current INR→USD rate                               |
| GET    | `/health`                       | Health check                                       |

### Search / filter query params (`/api/hotels`)
`q`, `city`, `region`, `type`, `stars` (comma-separated), `max_price`,
`accessibility` (comma-separated feature keys), `sort` (`featured|rating|price_low|price_high|stars`)

---

## 🗂️ Project Structure

```
nexora/
├── app.py             # Flask backend + REST API + SVG generators
├── seed.py            # Seeds hotels.db (55 hotels, 40+ cities)
├── hotels.db          # SQLite database (generated)
├── README.md
└── static/
    ├── index.html     # Single-page frontend
    ├── styles.css     # Responsive, accessible styling
    ├── app.js         # Frontend logic
    └── favicon.svg    # Site icon
```

---

## 🧪 Testing

An end-to-end Playwright script is included (`e2e_test.py`). It loads the home page, searches,
toggles USD, opens a hotel, completes a booking and captures the blueprint, and checks the mobile
layout.

```bash
pip install playwright && python -m playwright install chromium
LD_LIBRARY_PATH=/path/to/libs python e2e_test.py   # adjust libs as needed on your OS
```

---

## 📝 Notes

- Prices are indicative and shown in INR (₹) with a USD (≈$) conversion at 1 USD = 83.5 INR.
- The accessibility blueprint is a design-reference diagram generated for each confirmed booking.
- The dataset is illustrative sample data for demonstration.

---

**NEXORA** · Made for inclusive travel across India. 🎉
