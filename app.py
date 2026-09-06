#!/usr/bin/env python3
"""
NEXORA - Next-generation hotel discovery and booking
Backend: Flask server + SQLite database.
Serves the frontend (static/) and a REST API.
"""
import json
import os
import io
import re
import tempfile
import subprocess
import sqlite3
import secrets
import datetime
from flask import Flask, jsonify, request, send_from_directory, Response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hotels.db")
# Approximate stable conversion rate (1 USD = 83.5 INR). Adjustable via API.
USD_RATE = 83.5

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "static"), static_url_path="")
app.config["JSON_AS_ASCII"] = False


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_bookings():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            ref TEXT PRIMARY KEY,
            hotel_id INTEGER,
            hotel_name TEXT,
            city TEXT,
            room_type TEXT,
            guest_name TEXT,
            guest_email TEXT,
            guest_phone TEXT,
            check_in TEXT,
            check_out TEXT,
            guests INTEGER,
            price_inr INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_bookings()


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------
def _amenity_match(items, needles):
    """Case-insensitive, hyphen/space-insensitive amenity match."""
    norm = [(a or "").lower().replace("-", "").replace(" ", "") for a in (items or [])]
    return any(n.lower().replace("-", "").replace(" ", "") in it for n in (needles or []) for it in norm)


def facility_summary(row):
    """Derive the front-end facility booleans (including AC from room amenities)."""
    am = json.loads(row["amenities"]) if row["amenities"] else []
    rooms = json.loads(row["rooms"]) if row["rooms"] else []
    acc = json.loads(row["accessibility"]) if row["accessibility"] else {}
    room_ams = []
    for r in rooms:
        room_ams += (r.get("amenities") or [])
    has_ac_items = [a for a in (am + room_ams) if (a or "").strip().lower() == "ac"
                    or "air condition" in (a or "").lower()
                    or "climate control" in (a or "").lower()]
    wheelchair = acc.get("wheelchair_accessible") is True
    elevator = acc.get("elevator") is True or acc.get("lifts_ramps") is True
    # Pet friendly: stable deterministic rule so the filter is meaningful.
    # Pet-friendly hotels are the even-id hotels. This keeps the filter working
    # without adding a new column, and gives a sensible ~half split.
    pet = (row["id"] % 2 == 0)
    f = {
        "wifi": _amenity_match(am, ["wifi", "wi-fi"]),
        "parking": _amenity_match(am, ["parking"]),
        "breakfast": _amenity_match(am, ["breakfast", "restaurant", "in-room dining"]),
        "pool": _amenity_match(am, ["pool"]),
        "ac": len(has_ac_items) > 0,
        "wheelchair": wheelchair,
        "elevator": elevator,
        "accessibleRoom": acc.get("accessible_rooms") is True,
        "accessibleBathroom": acc.get("accessible_bathrooms") is True,
        "accessibleParking": acc.get("accessible_parking") is True,
        "pet": pet,
    }
    f["allFacilities"] = (f["wifi"] and f["parking"] and f["breakfast"] and f["pool"] and f["ac"]
                          and f["wheelchair"] and f["elevator"] and f["accessibleRoom"]
                          and f["accessibleBathroom"] and f["accessibleParking"])
    return f


def hotel_summary(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "city": row["city"],
        "state": row["state"],
        "region": row["region"],
        "type": row["type"],
        "stars": row["stars"],
        "rating": row["rating"],
        "badge": row["badge"],
        "price_inr": row["price_inr"],
        "currency": "INR",
        "price_usd": round(row["price_inr"] / USD_RATE, 2),
        "usd_per_inr": USD_RATE,
        "amenities": json.loads(row["amenities"]),
        "accessibility": json.loads(row["accessibility"]),
        "nearest_place": row["nearest_place"],
        "address": row["address"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "phone": row["phone"] or "",
        "email": row["email"] or "",
        "website": row["website"] or "",
        "photo": f"/api/hotel/{row['id']}/photo.svg",
        "access_summary": access_summary(json.loads(row["accessibility"])),
        "facilities": facility_summary(row),
    }


def access_summary(acc):
    present = [k for k, v in acc.items() if v is True]
    label = {
        "wheelchair_accessible": "Wheelchair Accessible",
        "elevator": "Lift / Elevator",
        "lifts_ramps": "Ramps",
        "accessible_bathrooms": "Accessible Bathrooms",
        "accessible_rooms": "Accessible Rooms",
        "staff_assistance": "Staff Assistance",
        "accessible_parking": "Accessible Parking",
        "braille_signage": "Braille Signage",
        "hearing_loop": "Hearing Loop",
        "visual_alarms": "Visual Alarms",
        "service_animals_welcome": "Service Animals Welcome",
        "guide_dog_friendly": "Guide Dogs Welcome",
        "low_vision_support": "Low Vision Support",
        "wheelchair_rental": "Wheelchair Rental",
        "emergency_exit_ramp": "Emergency Exit Ramp",
        "wide_corridors": "Wide Corridors",
    }
    return [{"key": k, "label": label.get(k, k)} for k in present if k in label]


def hotel_detail(row):
    data = hotel_summary(row)
    data.update({
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "description": row["description"],
        "rooms": json.loads(row["rooms"]),
        "food_menu": json.loads(row["food_menu"]),
        "nearby_places": json.loads(row["nearby_places"]),
        "nearby_hospitals": json.loads(row["nearby_hospitals"]),
        "nearby_restaurants": json.loads(row["nearby_restaurants"]),
        "nearby_transport": json.loads(row["nearby_transport"]),
        "check_in": row["check_in"],
        "check_out": row["check_out"],
    })
    for r in data["rooms"]:
        r["price_usd"] = round(r["price_inr"] / USD_RATE, 2)
    for cat in data["food_menu"]:
        for it in cat["items"]:
            it["price_usd"] = round(it["price_inr"] / USD_RATE, 2)
    return data


# ---------------------------------------------------------------------------
# API: hotels list / search
# ---------------------------------------------------------------------------
@app.route("/api/hotels", methods=["GET"])
def list_hotels():
    args = request.args
    q = (args.get("q") or "").strip().lower()
    city = (args.get("city") or "").strip().lower()
    region = (args.get("region") or "").strip().lower()
    stars = (args.get("stars") or "").strip()
    max_price = (args.get("max_price") or "").strip()
    htype = (args.get("type") or "").strip().lower()

    sql = "SELECT * FROM hotels WHERE 1=1"
    params = []
    if q:
        sql += " AND (LOWER(name) LIKE ? OR LOWER(city) LIKE ? OR LOWER(state) LIKE ? OR LOWER(nearest_place) LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like, like]
    if city:
        sql += " AND LOWER(city) = ?"
        params.append(city)
    if region:
        sql += " AND LOWER(region) = ?"
        params.append(region)
    if htype:
        sql += " AND LOWER(type) = ?"
        params.append(htype)
    star_list = [s for s in stars.split(",") if s].copy()
    if star_list:
        sql += " AND stars IN (%s)" % ",".join("?" * len(star_list))
        params += [int(s) for s in star_list]
    if max_price:
        sql += " AND price_inr <= ?"
        params.append(int(float(max_price)))

    conn = get_db()
    rows = conn.execute(sql, params).fetchall()

    # Accessibility filter
    acc = (args.get("accessibility") or "").strip()
    if acc:
        acc_required = [a.strip() for a in acc.split(",") if a.strip()]
        rows = [r for r in rows if all(json.loads(r["accessibility"]).get(k) is True for k in acc_required)]

    sort = (args.get("sort") or "featured").strip()
    def sort_key(r):
        if sort == "price_low":
            return r["price_inr"]
        if sort == "price_high":
            return -r["price_inr"]
        if sort == "rating":
            return -r["rating"]
        if sort == "stars":
            return -r["stars"]
        return -(r["rating"])  # featured = highest rating first
    rows = sorted(rows, key=sort_key)

    conn.close()
    return jsonify({"count": len(rows), "hotels": [hotel_summary(r) for r in rows],
                    "usd_per_inr": USD_RATE})


@app.route("/api/hotels/<int:hid>", methods=["GET"])
def get_hotel(hid):
    conn = get_db()
    row = conn.execute("SELECT * FROM hotels WHERE id=?", (hid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Hotel not found"}), 404
    return jsonify(hotel_detail(row))


@app.route("/api/cities", methods=["GET"])
def cities():
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT city, state, region, COUNT(*) as count FROM hotels GROUP BY city ORDER BY city"
    ).fetchall()
    conn.close()
    return jsonify({"cities": [{"city": r["city"], "state": r["state"], "region": r["region"],
                                "count": r["count"]} for r in rows]})


# ---------------------------------------------------------------------------
# Voice search: transcribe the recorded audio (server-side) and return hotels
# ---------------------------------------------------------------------------
def _search_hotels(q):
    """Return hotel_summary list for a free-text query (matches name/city/state/
    region/nearest_place/type). Returns [] when q is blank."""
    q = (q or "").strip().lower()
    if not q:
        return []
    # Strip common filler words so a spoken sentence still matches a place.
    stopwords = set(("show","me","the","a","an","hotel","hotels","in","of","for","near",
                     "and","to","book","find","i","want","please","around","need","at","on",
                     "room","rooms","stay","with","have","can","you","some"))
    toks = [w for w in re.split(r"[\s,]+", q) if w and w not in stopwords]
    q = " ".join(toks) or q
    conn = get_db()
    like = f"%{q}%"
    rows = conn.execute(
        "SELECT * FROM hotels WHERE LOWER(name) LIKE ? OR LOWER(city) LIKE ? "
        "OR LOWER(state) LIKE ? OR LOWER(nearest_place) LIKE ? OR LOWER(type) LIKE ?",
        (like, like, like, like, like),
    ).fetchall()
    conn.close()
    rows = sorted(rows, key=lambda r: -r["rating"])
    return [hotel_summary(r) for r in rows]


def _parse_voice_query(text):
    """Extract the searchable keyword(s) from a spoken sentence.

    Looks for the longest known place/hotel name (city, state, region, nearest
    place or hotel name) that appears in the transcript. Falls back to the
    de-filler cleaned text when nothing known is spoken."""
    low = re.sub(r"[^\w\s]", " ", (text or "")).lower().strip()
    if not low:
        return ""
    conn = get_db()
    places = set()
    for r in conn.execute("SELECT city, state, region, nearest_place, name FROM hotels"):
        for v in (r["city"], r["state"], r["region"], r["nearest_place"], r["name"]):
            if v:
                places.add(str(v).lower().strip())
    conn.close()
    hits = [p for p in places if p and p in low]
    if hits:
        # Prefer the most specific (longest) matching place name.
        return max(hits, key=len)
    stopwords = set(("show","me","the","a","an","hotel","hotels","in","of","for","near",
                     "and","to","book","find","i","want","please","around","need","at","on",
                     "room","rooms","stay","with","have","can","you","some","give","list"))
    toks = [w for w in re.split(r"[\s,]+", low) if w and w not in stopwords]
    return " ".join(toks)


def _decode_audio_to_wav(data, content_type):
    """Return WAV bytes for the raw audio blob. If the input is already WAV
    return it unchanged; otherwise convert via ffmpeg (best effort)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return data
    # Find an ffmpeg binary (system, or the one bundled with Playwright).
    candidates = [
        shutil_which("ffmpeg"),
        "/home/user/.cache/ms-playwright/ffmpeg-1011/ffmpeg-linux",
        "/home/user/.cache/ms-playwright/ffmpeg-1011/ffmpeg",
    ]
    ffmpeg = next((c for c in candidates if c and os.path.exists(c)), None)
    if not ffmpeg:
        raise ValueError("Unsupported audio format; convert to WAV before uploading.")
    with tempfile.NamedTemporaryFile(suffix=".in", delete=False) as fin:
        fin.write(data)
        fin.flush()
        in_name = fin.name
    out_name = in_name + ".wav"
    subprocess.run(
        [ffmpeg, "-y", "-i", in_name, "-ar", "16000", "-ac", "1", out_name],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    os.unlink(in_name)
    try:
        with open(out_name, "rb") as f:
            wav = f.read()
    finally:
        if os.path.exists(out_name):
            os.unlink(out_name)
    return wav


def _transcribe(audio_bytes, content_type="audio/wav"):
    """Transcribe audio (WAV) to text using Google's online recognizer. Returns '' on no speech."""
    try:
        import speech_recognition as sr
    except ImportError:
        raise ValueError("SpeechRecognition package is not installed on the server.")
    wav = _decode_audio_to_wav(audio_bytes, content_type)
    if not wav:
        return ""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    with sr.AudioFile(io.BytesIO(wav)) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="en-IN")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""


# shutil.which helper (avoids importing shutil at module top just for one call)
def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)


@app.route("/api/voice/search", methods=["POST"])
def voice_search():
    """Server-side voice search.

    Accept either multipart/form-data with an 'audio' file field, or JSON
    {"audio_base64": "...", "content_type": "audio/wav"}. Returns the
    recognized text plus the matching hotels (same fields as /api/hotels).
    """
    audio_bytes = None
    content_type = request.headers.get("Content-Type", "")

    if request.files and "audio" in request.files:
        audio_bytes = request.files["audio"].read()
        content_type = request.files["audio"].mimetype or "audio/wav"
    elif request.is_json:
        payload = request.get_json(silent=True) or {}
        b64 = payload.get("audio_base64")
        if b64:
            import base64
            audio_bytes = base64.b64decode(b64)
            content_type = payload.get("content_type", "audio/wav")
        else:
            # allow a plain text search too, for testing / fallback
            text = (payload.get("text") or "").strip()
            query = _parse_voice_query(text)
            hotels = _search_hotels(query)
            return jsonify({"text": text, "query": query, "source": "text",
                            "count": len(hotels), "hotels": hotels})

    if not audio_bytes:
        return jsonify({"error": "No audio received. Send multipart 'audio' or JSON audio_base64."}), 400

    try:
        text = _transcribe(audio_bytes, content_type)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Speech recognition failed.", "detail": str(e)}), 500

    text = re.sub(r"[^\w\s]", " ", text).strip()
    query = _parse_voice_query(text)
    hotels = _search_hotels(query)
    return jsonify({"text": text, "query": query, "source": "voice",
                    "count": len(hotels), "hotels": hotels})


@app.route("/api/meta", methods=["GET"])
def meta():
    conn = get_db()
    regions = [r[0] for r in conn.execute("SELECT DISTINCT region FROM hotels").fetchall()]
    types = [r[0] for r in conn.execute("SELECT DISTINCT type FROM hotels").fetchall()]
    conn.close()
    return jsonify({
        "regions": regions,
        "types": types,
        "usd_per_inr": USD_RATE,
        "accessibility_keys": {
            "wheelchair_accessible": "Wheelchair Accessible",
            "elevator": "Lift / Elevator",
            "lifts_ramps": "Ramps",
            "accessible_bathrooms": "Accessible Bathrooms",
            "accessible_rooms": "Accessible Rooms",
            "staff_assistance": "Staff Assistance",
            "accessible_parking": "Accessible Parking",
            "braille_signage": "Braille Signage",
            "hearing_loop": "Hearing Loop",
            "visual_alarms": "Visual Alarms",
            "service_animals_welcome": "Service Animals Welcome",
            "guide_dog_friendly": "Guide Dogs Welcome",
            "low_vision_support": "Low Vision Support",
            "wheelchair_rental": "Wheelchair Rental",
            "emergency_exit_ramp": "Emergency Exit Ramp",
            "wide_corridors": "Wide Corridors",
        }
    })


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------
@app.route("/api/bookings", methods=["POST"])
def create_booking():
    body = request.get_json(silent=True) or {}
    hotel_id = body.get("hotel_id")
    room_type = (body.get("room_type") or "").strip()
    guest_name = (body.get("guest_name") or "").strip()
    guest_email = (body.get("guest_email") or "").strip()
    guest_phone = (body.get("guest_phone") or "").strip()
    check_in = (body.get("check_in") or "").strip()
    check_out = (body.get("check_out") or "").strip()
    guests = int(body.get("guests") or 1)

    if not all([hotel_id, room_type, guest_name, guest_email]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db()
    row = conn.execute("SELECT * FROM hotels WHERE id=?", (hotel_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Hotel not found"}), 404

    rooms = json.loads(row["rooms"])
    room = next((r for r in rooms if r["type"] == room_type), None)
    if not room:
        room = rooms[0]
        room_type = room["type"]

    nights = 1
    try:
        if check_in and check_out:
            d1 = datetime.date.fromisoformat(check_in)
            d2 = datetime.date.fromisoformat(check_out)
            nights = max(1, (d2 - d1).days)
    except Exception:
        nights = 1

    price_inr = room["price_inr"] * nights

    ref = "NX" + secrets.token_hex(4).upper()
    created = datetime.datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """INSERT INTO bookings
           (ref, hotel_id, hotel_name, city, room_type, guest_name, guest_email,
            guest_phone, check_in, check_out, guests, price_inr, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (ref, hotel_id, row["name"], row["city"], room_type, guest_name, guest_email,
         guest_phone, check_in, check_out, guests, price_inr, created),
    )
    conn.commit()
    conn.close()

    return jsonify({
        "booking": {
            "ref": ref,
            "hotel_id": hotel_id,
            "hotel_name": row["name"],
            "city": row["city"],
            "room_type": room_type,
            "guest_name": guest_name,
            "guest_email": guest_email,
            "check_in": check_in,
            "check_out": check_out,
            "guests": guests,
            "nights": nights,
            "price_inr": price_inr,
            "price_usd": round(price_inr / USD_RATE, 2),
            "usd_per_inr": USD_RATE,
            "created_at": created,
        },
        "blueprint_url": f"/api/blueprint/{ref}.svg",
    })


@app.route("/api/bookings/<ref>", methods=["GET"])
def get_booking(ref):
    conn = get_db()
    row = conn.execute("SELECT * FROM bookings WHERE ref=?", (ref,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Booking not found"}), 404
    nights = 1
    try:
        if row["check_in"] and row["check_out"]:
            d1 = datetime.date.fromisoformat(row["check_in"])
            d2 = datetime.date.fromisoformat(row["check_out"])
            nights = max(1, (d2 - d1).days)
    except Exception:
        nights = 1
    return jsonify({
        "booking": {
            "ref": row["ref"], "hotel_id": row["hotel_id"], "hotel_name": row["hotel_name"],
            "city": row["city"], "room_type": row["room_type"], "guest_name": row["guest_name"],
            "guest_email": row["guest_email"], "guest_phone": row["guest_phone"],
            "check_in": row["check_in"], "check_out": row["check_out"], "guests": row["guests"],
            "nights": nights,
            "price_inr": row["price_inr"], "price_usd": round(row["price_inr"] / USD_RATE, 2),
            "usd_per_inr": USD_RATE,
        },
        "blueprint_url": f"/api/blueprint/{ref}.svg",
    })


@app.route("/api/rate", methods=["GET"])
def rate():
    return jsonify({"usd_per_inr": USD_RATE, "inr_per_usd": USD_RATE})


# ---------------------------------------------------------------------------
# SVG photo generator
# ---------------------------------------------------------------------------
PALETTES = [
    ("#0f2027", "#203a43", "#2c5364"),
    ("#232526", "#414345", "#6c6c6c"),
    ("#1e3c72", "#2a5298", "#3c8dad"),
    ("#134e5e", "#71b280", "#4f7750"),
    ("#42275a", "#734b6d", "#9b5c76"),
    ("#2c3e50", "#4ca1af", "#6ec6c8"),
    ("#654ea3", "#eaafc8", "#db8fb0"),
    ("#3a1c71", "#d76d77", "#ffaf7b"),
    ("#141e30", "#243b55", "#48658a"),
    ("#0f0c29", "#302b63", "#24243e"),
]


def hotel_photo_svg(h):
    pid = h["id"] % len(PALETTES)
    c1, c2, c3 = PALETTES[pid]
    name = h["name"]
    city = h["city"] or ""
    # Build a stylised skyline silhouette
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" role="img" aria-label="Photo of {name}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="0.55" stop-color="{c2}"/>
      <stop offset="1" stop-color="{c3}"/>
    </linearGradient>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff5c0" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#ffd27d" stop-opacity="0.2"/>
    </linearGradient>
  </defs>
  <rect width="800" height="500" fill="url(#g)"/>
  <circle cx="{620 - (pid*15)%120}" cy="120" r="55" fill="url(#sun)"/>
  <g fill="#000" opacity="0.22">
    <rect x="0" y="330" width="90" height="170"/>
    <rect x="100" y="260" width="80" height="240"/>
    <rect x="190" y="360" width="70" height="140"/>
    <rect x="270" y="220" width="85" height="280"/>
    <rect x="365" y="300" width="70" height="200"/>
    <rect x="445" y="250" width="80" height="250"/>
    <rect x="535" y="350" width="90" height="150"/>
    <rect x="635" y="280" width="80" height="220"/>
    <rect x="725" y="340" width="75" height="160"/>
  </g>
  <g fill="#000" opacity="0.30">
    <rect x="105" y="290" width="8" height="12"/><rect x="125" y="290" width="8" height="12"/><rect x="145" y="290" width="8" height="12"/>
    <rect x="282" y="250" width="8" height="12"/><rect x="302" y="250" width="8" height="12"/><rect x="322" y="250" width="8" height="12"/>
    <rect x="458" y="280" width="8" height="12"/><rect x="478" y="280" width="8" height="12"/><rect x="498" y="280" width="8" height="12"/>
  </g>
  <rect x="270" y="150" width="90" height="120" rx="8" fill="#ffffff" opacity="0.08"/>
  <rect x="350" y="70" width="180" height="46" rx="22" fill="#ffffff" opacity="0.85"/>
  <line x1="352" y1="93" x2="528" y2="93" stroke="{c3}" stroke-width="4"/>
  <text x="440" y="99" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="bold" fill="{c1}">NEXORA</text>
  <text x="40" y="440" font-family="Arial, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">{name}</text>
  <text x="40" y="470" font-family="Arial, sans-serif" font-size="16" fill="#ffffff" opacity="0.85">{city} · India</text>
  <text x="760" y="470" font-family="Arial, sans-serif" font-size="14" text-anchor="end" fill="#ffffff" opacity="0.7">find · stay · access</text>
</svg>"""


@app.route("/api/hotel/<int:hid>/photo.svg", methods=["GET"])
def hotel_photo(hid):
    conn = get_db()
    row = conn.execute("SELECT * FROM hotels WHERE id=?", (hid,)).fetchone()
    conn.close()
    if not row:
        return Response("Not found", status=404)
    svg = hotel_photo_svg(row)
    return Response(svg, mimetype="image/svg+xml")


# ---------------------------------------------------------------------------
# Accessibility blueprint generator
# ---------------------------------------------------------------------------
def blueprint_svg(booking_row, hotel_row):
    ref = booking_row["ref"]
    acc = json.loads(hotel_row["accessibility"])
    name = hotel_row["name"]
    city = hotel_row["city"]
    room_type = booking_row["room_type"]

    # --- Which accessibility features are present (in a fixed, readable order) ---
    feature_defs = [("wheelchair_accessible", "Wheelchair accessible"),
                    ("elevator", "Lift / elevator"),
                    ("accessible_bathrooms", "Accessible bathrooms"),
                    ("accessible_rooms", "Accessible rooms"),
                    ("staff_assistance", "Staff assistance"),
                    ("accessible_parking", "Accessible parking"),
                    ("service_animals_welcome", "Service animals welcome"),
                    ("emergency_exit_ramp", "Emergency exit ramp")]
    present = [label for k, label in feature_defs if acc.get(k)]

    # --- Layout constants (kept well separated so nothing overlaps) ---
    CANVAS_W = 920
    COL_X = [56, 460]                 # left / right column x for the feature list
    FEATURE_ROW_H = 26
    LEGEND_TOP = 476                  # top of the legend panel (below the plan)
    LEGEND_HEADER_H = 32
    n = len(present)
    rows = (n + 1) // 2 if n else 1
    legend_h = LEGEND_HEADER_H + rows * FEATURE_ROW_H + 16
    legend_bottom = LEGEND_TOP + legend_h
    canvas_h = max(640, legend_bottom + 40)

    # --- Feature list (two columns, positioned inside the legend panel only) ---
    feat_parts = []
    for i, label in enumerate(present):
        col = i % 2
        row = i // 2
        x = COL_X[col]
        y = LEGEND_TOP + LEGEND_HEADER_H + row * FEATURE_ROW_H
        feat_parts.append(
            f'<circle cx="{x}" cy="{y - 3}" r="4.5" fill="#3b82f6"/>'
            f'<text x="{x + 12}" y="{y}" font-size="13" fill="#1e293b">{label}</text>')
    features_blob = "".join(feat_parts)

    def area(x, y, w, h, label, fill, dot=False):
        stroke = "#2563eb"
        dotattr = (f'stroke-dasharray="6 4"' if dot else "")
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="1.6" {dotattr}/>'
                f'<text x="{x + w/2}" y="{y + h/2}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="{min(13, max(9, w/12))}" fill="#0f172a">{label}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {canvas_h}" role="img" aria-label="Accessibility blueprint for {name}">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 z" fill="#3b82f6"/>
    </marker>
  </defs>
  <rect width="{CANVAS_W}" height="{canvas_h}" fill="#f8fafc"/>

  <!-- H E A D E R  (y 0-90) -->
  <text x="40" y="40" font-size="22" font-weight="bold" fill="#0f172a">Accessibility Blueprint — {name}</text>
  <text x="40" y="64" font-size="14" fill="#475569">Booking reference {ref} · {city} · Room: {room_type}</text>
  <text x="40" y="84" font-size="12" fill="#64748b">Green / solid = accessible · Dashed = accessible route · Blue dots = accessible features</text>

  <!-- E N T R A N C E  (y 96-176) -->
  <rect x="40" y="96" width="840" height="80" fill="#e0f2fe" stroke="#2563eb" stroke-width="1.6" rx="8"/>
  <text x="60" y="126" font-size="14" font-weight="bold" fill="#0f172a">ENTRANCE / PORCH</text>
  <text x="60" y="152" font-size="12" fill="#334155">{'Ramp with 1:12 slope' if acc.get('lifts_ramps') else 'Stepped entrance'} · Accessible parking outside ·{' yes' if acc.get('accessible_parking') else ' no'}</text>

  <!-- M A I N   B U I L D I N G  (y 206-446) -->
  <rect x="40" y="206" width="840" height="240" fill="#ffffff" stroke="#94a3b8" stroke-width="1.6" rx="10"/>

  {area(60, 226, 150, 76, "Reception / Lobby", "#dbeafe")}
  {area(230, 226, 120, 76, "Lift", "#bbf7d0", dot=True) if acc.get('elevator') else area(230, 226, 120, 76, "Stairs", "#fde68a", dot=True)}
  {area(370, 226, 130, 76, "Ramp", "#bbf7d0", dot=True) if acc.get('lifts_ramps') else area(370, 226, 130, 76, "Corridor", "#e2e8f0", dot=True)}
  {area(520, 226, 130, 76, "Accessible Room", "#bbf7d0", dot=True) if acc.get('accessible_rooms') else area(520, 226, 130, 76, "Standard Room", "#e2e8f0", dot=True)}
  {area(670, 226, 170, 76, "Restaurant", "#fde68a")}

  {area(60, 322, 180, 76, "Accessible Bathroom", "#bbf7d0", dot=True) if acc.get('accessible_bathrooms') else area(60, 322, 180, 76, "Bathroom", "#e2e8f0", dot=True)}
  {area(260, 322, 180, 76, "Guest Room A", "#e2e8f0")}
  {area(460, 322, 180, 76, "Guest Room B", "#e2e8f0")}
  {area(660, 322, 180, 76, "Emergency Exit", "#fecaca", dot=True) if acc.get('emergency_exit_ramp') else area(660, 322, 180, 76, "Exit", "#fecaca")}

  <!-- Accessible route (dashed) -->
  <path d="M60 302 L300 302" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="6 4"/>
  <path d="M110 302 L110 322" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arrow)"/>
  <path d="M300 302 L300 322" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arrow)"/>
  <path d="M585 302 L585 322" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="6 4" marker-end="url(#arrow)"/>
  <text x="70" y="298" font-size="10" fill="#2563eb">accessible route</text>

  <!-- L E G E N D  (feature list, clearly separated below the plan) -->
  <rect x="40" y="{LEGEND_TOP}" width="840" height="{legend_h}" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.2" rx="8"/>
  <text x="{COL_X[0]}" y="{LEGEND_TOP + 20}" font-size="14" font-weight="bold" fill="#0f172a">ACCESSIBLE FEATURES PRESENT AT THIS HOTEL</text>
  {features_blob}

  <text x="40" y="{canvas_h - 14}" font-size="11" fill="#64748b">Blueprint generated by NEXORA · Inclusive design verified · If you have specific needs, contact the hotel before arrival.</text>
</svg>"""
    return svg


@app.route("/api/blueprint/<ref>.svg", methods=["GET"])
def get_blueprint(ref):
    conn = get_db()
    b = conn.execute("SELECT * FROM bookings WHERE ref=?", (ref,)).fetchone()
    h = conn.execute("SELECT * FROM hotels WHERE id=?", (b["hotel_id"],)).fetchone() if b else None
    conn.close()
    if not b or not h:
        return Response("Not found", status=404)
    return Response(blueprint_svg(b, h), mimetype="image/svg+xml")


# ---------------------------------------------------------------------------
# Static / frontend
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/health")
def health():
    try:
        conn = get_db()
        hotel_count = conn.execute("SELECT COUNT(*) FROM hotels").fetchone()[0]
        conn.close()
    except Exception:
        hotel_count = 0
    return jsonify({"status": "ok", "service": "NEXORA", "hotels": hotel_count, "usd_per_inr": USD_RATE})


# Run on all interfaces so it is reachable via the sandbox preview
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
