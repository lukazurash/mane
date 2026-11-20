"""Mane: a hair salon and barbershop site with online booking and an admin panel.
Flask + SQLite; photos are resized to WebP on upload. Built on the same engine as Rose (the florist site)."""
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.parse
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)
from markupsafe import Markup, escape
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import content

BASE = Path(__file__).parent
DB_PATH = Path(os.environ.get("DB_PATH", BASE / "data" / "mane.db"))
MEDIA = Path(os.environ.get("MEDIA_DIR", BASE / "data" / "media"))
PRODUCTION = bool(os.environ.get("PRODUCTION"))
TZ = ZoneInfo("Asia/Tbilisi")
WIDTHS = (480, 960, 1600, 2400)
LANGS = ("ka", "en")
CATS = ("women", "men")
STATUSES = ("new", "confirmed", "done", "noshow", "cancelled")
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
TIME_RE = r"([01][0-9]|2[0-3]):[0-5][0-9]"


def secret_key():
    """The env var if set; on a server, a random key made once and kept beside the database; locally a dev key."""
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    if not PRODUCTION:
        return "dev-only-change-me"
    f = DB_PATH.parent / ".secret_key"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(secrets.token_hex(32))
        os.chmod(f, 0o600)
    return f.read_text().strip()


app = Flask(__name__)
app.config.update(SECRET_KEY=secret_key(),
                  MAX_CONTENT_LENGTH=15 * 1024 * 1024,
                  SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SECURE=PRODUCTION, SEND_FILE_MAX_AGE_DEFAULT=86400)
app.jinja_env.globals["zip"] = zip
if PRODUCTION:
    # behind the host's proxy: the visitor's own address and https, so the limits count each visitor apart
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)


@app.url_defaults
def static_version(endpoint, values):
    """Every link to a static file carries its change time, so an edited stylesheet reaches visitors at once."""
    if endpoint == "static" and "filename" in values:
        f = BASE / "static" / values["filename"]
        if f.is_file():
            values["v"] = int(f.stat().st_mtime)


# ---------------------------------------------------------------- database
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_):
    con = g.pop("db", None)
    if con:
        con.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS texts(key TEXT PRIMARY KEY, ka TEXT NOT NULL, en TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS images(stem TEXT PRIMARY KEY, w INTEGER, h INTEGER, widths TEXT,
    phone INTEGER DEFAULT 0, credit TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, cat TEXT, name_ka TEXT, name_en TEXT, desc_ka TEXT, desc_en TEXT,
    price INTEGER, from_price INTEGER DEFAULT 0, mins INTEGER, active INTEGER DEFAULT 1, sort INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS masters(id INTEGER PRIMARY KEY, cat TEXT, name_ka TEXT, name_en TEXT, role_ka TEXT, role_en TEXT,
    about_ka TEXT, about_en TEXT, photo TEXT DEFAULT '', color TEXT DEFAULT '#5a4a3f', active INTEGER DEFAULT 1,
    sort INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY, created TEXT, service_id INTEGER, service TEXT, cat TEXT,
    price INTEGER, from_price INTEGER, mins INTEGER, master_id INTEGER, master TEXT, any_master INTEGER DEFAULT 0,
    day TEXT, start TEXT, name TEXT, phone TEXT, note TEXT, lang TEXT, source TEXT DEFAULT 'site', status TEXT DEFAULT 'new');
CREATE INDEX IF NOT EXISTS bookings_day ON bookings(day);
"""


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    # new keys arrive on update; what the owner already edited stays
    con.executemany("INSERT OR IGNORE INTO texts(key,ka,en) VALUES(?,?,?)",
                    [(k, ka, en) for k, (ka, en) in content.TEXTS.items()])
    con.executemany("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", content.SETTINGS.items())
    if not con.execute("SELECT 1 FROM settings WHERE key='admin_hash'").fetchone():
        pw = os.environ.get("ADMIN_PASSWORD")
        if not pw and not PRODUCTION:
            pw = "mane-admin"
            print("Admin password for this local copy: mane-admin (change it in Admin > Settings)")
        if pw:
            con.execute("INSERT INTO settings(key,value) VALUES('admin_hash',?)", (generate_password_hash(pw),))
        else:  # on a server the owner sets it with set_password.py; until then nobody can sign in
            print("No admin password yet: run  python set_password.py")
    if not con.execute("SELECT 1 FROM services").fetchone():
        con.executemany("INSERT INTO services(cat,name_ka,name_en,desc_ka,desc_en,price,from_price,mins,active,sort)"
                        " VALUES(?,?,?,?,?,?,?,?,1,?)", [(*s, i) for i, s in enumerate(content.SERVICES)])
    if not con.execute("SELECT 1 FROM masters").fetchone():
        con.executemany("INSERT INTO masters(cat,name_ka,name_en,role_ka,role_en,about_ka,about_en,color,active,sort)"
                        " VALUES(?,?,?,?,?,?,?,?,1,?)", [(*m, i) for i, m in enumerate(content.MASTERS)])
    src = BASE / "photo-src"
    for slot, (file, phone, fx, fy) in content.PHOTOS.items():
        if not con.execute("SELECT 1 FROM settings WHERE key=?", (f"photo_{slot}",)).fetchone():
            stem = seed_image(con, src / file, phone=phone, focus=(fx, fy))
            con.execute("INSERT INTO settings(key,value) VALUES(?,?)", (f"photo_{slot}", stem))
    con.commit()
    con.close()


def seed_image(con, path, phone=False, focus=(0.5, 0.5)):
    credit = content.CREDITS.get(path.name, content.UNSPLASH)
    with open(path, "rb") as f:
        stem, w, h, widths, ph = make_image(f, phone=phone, focus=focus, quality=82, method=6)
    con.execute("INSERT INTO images(stem,w,h,widths,phone,credit) VALUES(?,?,?,?,?,?)",
                (stem, w, h, ",".join(map(str, widths)), int(ph), credit))
    return stem


# ---------------------------------------------------------------- images
def make_image(fileobj, phone=False, focus=(0.5, 0.5), quality=80, method=4):
    """Save one picture as WebP at the widths it can fill (never upscaled). Raises ValueError on a bad file."""
    try:
        im = Image.open(fileobj)
        im.verify()  # catches truncated and fake files before decoding
        fileobj.seek(0)
        im = Image.open(fileobj)
        if im.format not in ("JPEG", "PNG", "WEBP"):
            raise ValueError("format")
        im = ImageOps.exif_transpose(im).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError) as e:
        raise ValueError("image") from e
    stem = secrets.token_hex(6)
    w, h = im.size
    widths = sorted({x for x in WIDTHS if x < w} | {min(w, WIDTHS[-1])})
    for tw in widths:
        out = im if tw == w else im.resize((tw, round(h * tw / w)), Image.LANCZOS)
        out.save(MEDIA / f"{stem}-{tw}.webp", "WEBP", quality=quality, method=method)
    made_phone = False
    if phone:  # a 4:5 crop round the subject, so a phone's tall hero frame is never blown up
        cw = min(w, round(h * 4 / 5))
        ch = round(cw * 5 / 4)
        if cw >= 600:
            x = min(max(round(w * focus[0] - cw / 2), 0), w - cw)
            y = min(max(round(h * focus[1] - ch / 2), 0), h - ch)
            crop = im.crop((x, y, x + cw, y + ch)).resize((780, 975), Image.LANCZOS)
            crop.save(MEDIA / f"{stem}-phone.webp", "WEBP", quality=quality, method=method)
            made_phone = True
    top = widths[-1]
    return stem, top, round(h * top / w), widths, made_phone


def image_row(stem):
    cache = g.setdefault("images", {})
    if stem not in cache:
        cache[stem] = db().execute("SELECT * FROM images WHERE stem=?", (stem,)).fetchone()
    return cache[stem]


def media_url(stem, width):
    return url_for("media", name=f"{stem}-{width}.webp")


@app.template_global()
def pic(stem, alt="", sizes="100vw", cls="", lazy=True, attrs=""):
    """An <img> with every width this picture was saved at."""
    row = image_row(stem) if stem else None
    if not row:
        return Markup("")
    widths = [int(x) for x in row["widths"].split(",")]
    srcset = ", ".join(f"{media_url(stem, x)} {x}w" for x in widths)
    mid = next((x for x in widths if x >= 960), widths[-1])
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high"'
    return Markup(f'<img class="{escape(cls)}" src="{media_url(stem, mid)}" srcset="{srcset}" sizes="{escape(sizes)}" '
                  f'width="{row["w"]}" height="{row["h"]}" alt="{escape(alt)}" {load} {attrs}>')


@app.template_global()
def phone_src(stem):
    row = image_row(stem)
    return url_for("media", name=f"{stem}-phone.webp") if row and row["phone"] else ""


@app.get("/media/<path:name>")
def media(name):
    resp = send_from_directory(MEDIA, name, max_age=31536000)
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"  # a new upload gets a new name
    return resp


def delete_image(stem):
    """Remove a picture's files when nothing on the site uses it any more."""
    con = db()
    used = con.execute("SELECT 1 FROM masters WHERE photo=? UNION SELECT 1 FROM settings WHERE value=?",
                       (stem, stem)).fetchone()
    if used or not re.fullmatch(r"[0-9a-f]{12}", stem or ""):
        return
    for f in MEDIA.glob(f"{stem}-*.webp"):
        f.unlink(missing_ok=True)
    con.execute("DELETE FROM images WHERE stem=?", (stem,))


def save_upload(file, phone=False):
    stem, w, h, widths, ph = make_image(file.stream, phone=phone)
    db().execute("INSERT INTO images(stem,w,h,widths,phone,credit) VALUES(?,?,?,?,?,'')",
                 (stem, w, h, ",".join(map(str, widths)), int(ph)))
    return stem


# ---------------------------------------------------------------- language, texts, settings
def lang():
    return request.cookies.get("lang") if request.cookies.get("lang") in LANGS else "ka"


def texts():
    if "texts" not in g:
        g.texts = {r["key"]: r for r in db().execute("SELECT * FROM texts")}
    return g.texts


def facts():
    """Numbers the copy quotes, read from the salon's own data so a text never disagrees with the booking form."""
    if "facts" not in g:
        g.facts = {"ahead": S("days_ahead"), "open": S("open"), "close": S("close"),
                   "from": db().execute("SELECT COALESCE(MIN(price),0) FROM services WHERE active=1").fetchone()[0]}
    return g.facts


@app.template_global()
def t(key, **kw):
    row = texts().get(key)
    s = (row[lang()] or row["ka"]) if row else key
    if "{" in s:
        for k, v in {**facts(), **kw}.items():
            s = s.replace("{" + k + "}", str(v))
    return s


def S(key):
    if "settings" not in g:
        g.settings = {r["key"]: r["value"] for r in db().execute("SELECT * FROM settings")}
    return g.settings.get(key, content.SETTINGS.get(key, ""))


@app.template_global()
def loc(row, field):
    return row[f"{field}_{lang()}"] or row[f"{field}_ka"]


@app.template_global()
def price_label(row):
    return t("price_from", p=row["price"]) if row["from_price"] else f"{row['price']} ₾"


def hours_rows():
    rows = []
    for line in S("hours").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 4 and parts[3]:
            rows.append({"days": parts[0], "label": parts[1] if lang() == "ka" else parts[2], "time": parts[3]})
    return rows


def wa_link(text):
    return f"https://wa.me/{re.sub(r'[^0-9]', '', S('whatsapp'))}?text={urllib.parse.quote(text)}"


def map_link():
    city = S(f"city_{lang()}")
    q = " ".join(x for x in (S("street"), S(f"district_{lang()}"), city) if x)
    return "https://www.openstreetmap.org/search?query=" + urllib.parse.quote(q)


def credits_in_use():
    return db().execute(
        "SELECT DISTINCT i.credit FROM images i WHERE i.credit != '' AND (i.stem IN (SELECT photo FROM masters WHERE active=1)"
        " OR i.stem IN (SELECT value FROM settings WHERE key LIKE 'photo_%'))").fetchall()


@app.context_processor
def inject():
    if request.path.startswith(("/media", "/static")):
        return {}
    # only the admin needs a session; public pages set no cookie
    csrf = session.setdefault("csrf", secrets.token_hex(16)) if request.path.startswith("/admin") else ""
    return {"lang": lang(), "S": S, "hours": hours_rows, "wa_link": wa_link, "map_link": map_link,
            "csrf": csrf, "year": datetime.now(TZ).year, "cats": CATS,
            "has_credits": lambda: bool(credits_in_use())}


@app.after_request
def headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    if PRODUCTION:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000"
    return resp


@app.get("/lang/<code>")
def set_lang(code):
    nxt = request.args.get("next", "/")
    if not nxt.startswith("/") or nxt.startswith("//"):
        nxt = "/"
    resp = redirect(nxt)
    if code in LANGS:
        resp.set_cookie("lang", code, max_age=365 * 86400, samesite="Lax")
    return resp


# ---------------------------------------------------------------- the diary: which times are free
def services(cat=None):
    rows = db().execute("SELECT * FROM services WHERE active=1 ORDER BY sort, id").fetchall()
    return [s for s in rows if not cat or s["cat"] == cat]


def masters(cat=None, active=True):
    rows = db().execute("SELECT * FROM masters" + (" WHERE active=1" if active else "") + " ORDER BY sort, id").fetchall()
    return [m for m in rows if not cat or m["cat"] == cat]


def now():
    return datetime.now(TZ)


def mins(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def day_open(day):
    """Whether the salon takes bookings on this day at all: in range and not a day off."""
    today = now().date()
    if day < today or day > today + timedelta(days=int(S("days_ahead") or 30)):
        return False
    return DAYS[day.weekday()] not in S("days_off").split(",")


def grid(service, day, lead=True):
    """Every start time on this day's grid that fits the service before closing (and, today, after the notice)."""
    first, last, step = mins(S("open")), mins(S("close")), max(5, int(S("step") or 30))
    earliest = 0
    if lead and day == now().date():
        n = now()
        earliest = n.hour * 60 + n.minute + int(S("lead") or 0)
    return [m for m in range(first, last - service["mins"] + 1, step) if m >= earliest]


def taken(day):
    """Each master's booked stretches on a day, as (start, end) minutes; cancelled bookings free their time."""
    out = {}
    for b in db().execute("SELECT master_id, start, mins FROM bookings WHERE day=? AND status!='cancelled'",
                          (day.isoformat(),)):
        s = mins(b["start"])
        out.setdefault(b["master_id"], []).append((s, s + b["mins"]))
    return out


def free_master(service, master_ids, start, busy):
    """The first of these masters who is free from start for the service's length, or None."""
    end = start + service["mins"]
    for mid in master_ids:
        if all(end <= s or e <= start for s, e in busy.get(mid, [])):
            return mid
    return None


def candidates(service, master_id):
    """The masters a booking may go to: the one asked for, else everyone who does this kind of service."""
    ids = [m["id"] for m in masters(service["cat"])]
    if master_id:
        return [master_id] if master_id in ids else []
    return ids


def free_times(service, master_id, day):
    if not day_open(day):
        return []
    ids, busy = candidates(service, master_id), taken(day)
    return [m for m in grid(service, day) if free_master(service, ids, m, busy) is not None]


def next_free():
    """The soonest free time today or in the next week, for the shortest service with anyone: the hero says it."""
    svc = db().execute("SELECT * FROM services WHERE active=1 ORDER BY mins LIMIT 1").fetchone()
    if not svc:
        return None
    every = [m["id"] for m in masters()]
    for i in range(8):
        day = now().date() + timedelta(days=i)
        if not day_open(day):
            continue
        busy = taken(day)
        for m in grid(svc, day):
            if free_master(svc, every, m, busy) is not None:
                return day, hhmm(m)
    return None


# ---------------------------------------------------------------- public pages
@app.get("/")
def home():
    every = services()
    pick = request.args.get("s", type=int)
    if pick not in {s["id"] for s in every}:
        pick = every[0]["id"] if every else None
    master = request.args.get("m", type=int)
    chosen = next((m for m in masters() if m["id"] == master), None)
    if not chosen:
        master = None
    elif every and next(s for s in every if s["id"] == pick)["cat"] != chosen["cat"]:
        pick = next((s["id"] for s in every if s["cat"] == chosen["cat"]), pick)  # Giorgi cuts men's hair: start there
    nxt = next_free()
    notice = ""
    if nxt:
        day, at = nxt
        notice = t("hero_today", next=at) if day == now().date() else t("hero_later", next=f"{day.strftime('%d.%m')}, {at}")
    first = nxt[0] if nxt else now().date()  # the form opens on the first day that still has a free time
    return render_template("home.html", services=every, women=services("women"), men=services("men"),
                           masters=masters(), pick=pick, master=master, notice=notice,
                           today=now().date().isoformat(), first=first.isoformat(),
                           last=(now().date() + timedelta(days=int(S("days_ahead") or 30))).isoformat())


@app.get("/slots")
def slots():
    """The free start times for a service, a master (or anyone) and a day, for the booking form."""
    s = db().execute("SELECT * FROM services WHERE id=? AND active=1", (request.args.get("service", type=int),)).fetchone()
    try:
        day = date.fromisoformat(request.args.get("day", ""))
    except ValueError:
        day = None
    if not s or not day:
        return jsonify(times=[], closed=False), 400
    master_id = request.args.get("master", type=int)
    resp = jsonify(times=[hhmm(m) for m in free_times(s, master_id, day)], closed=not day_open(day))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/privacy")
def privacy():
    return render_template("page.html", h1=t("privacy_h1"), body=t("privacy_body"))


@app.get("/credits")
def credits():
    rows = []
    for r in credits_in_use():
        who, _, link = r["credit"].partition("|")
        rows.append((who, link))
    return render_template("page.html", h1=t("credits_h1"), credits=rows)


@app.errorhandler(404)
def not_found(_):
    if request.path.startswith(("/static/", "/media/")):
        return "Not found", 404
    return render_template("page.html", h1=t("nf_h1"), body=t("nf_line"), home_link=True), 404


@app.get("/robots.txt")
def robots():
    return app.response_class("User-agent: *\nDisallow: /admin\n", mimetype="text/plain")


# ---------------------------------------------------------------- booking
HITS = {}
HITS_LOCK = threading.Lock()
BOOK_LOCK = threading.Lock()


def too_many(bucket, limit, window=600, add=True):
    """A small in-memory limiter per client address (one process; enough for a salon's traffic)."""
    key = (bucket, request.remote_addr)
    t_now = time.time()
    with HITS_LOCK:
        hits = [x for x in HITS.get(key, []) if t_now - x < window]
        if add:
            hits.append(t_now)
        HITS[key] = hits
        return len(hits) > limit if add else len(hits) >= limit


def same_origin():
    origin = request.headers.get("Origin")
    return not origin or urllib.parse.urlparse(origin).netloc == request.host


def clean(s, n):
    return re.sub(r"\s+", " ", (s or "")).strip()[:n]


def check_contact(f, errors):
    name, phone = clean(f.get("name"), 60), clean(f.get("phone"), 30)
    if not name:
        errors["name"] = t("e_name")
    if phone and not re.fullmatch(r"\+?[0-9 ()-]{6,30}", phone):
        errors["phone"] = t("e_phone")
    return name, phone


def reply(ok, url=None, errors=None, message=""):
    """JSON for the page's script; without script the browser follows the form to WhatsApp or sees the errors."""
    if request.is_json or "application/json" in request.headers.get("Accept", ""):
        status = 200 if ok else (429 if errors == "busy" else 400)
        return jsonify(ok=ok, url=url, message=message, errors=errors if isinstance(errors, dict) else {}), status
    if ok:
        return redirect(url, 303)
    msgs = list(errors.values()) if isinstance(errors, dict) else [t("e_busy")]
    return render_template("page.html", h1=t("bk_fix", n=len(msgs)), items=msgs, home_link=True), 400


def check_slot(f, errors, lead=True):
    """Service, master, day and time from a form; the master is the one who will actually do it."""
    con = db()
    sid = str(f.get("service", ""))
    s = con.execute("SELECT * FROM services WHERE id=? AND active=1", (sid,)).fetchone() if sid.isdigit() else None
    if not s:
        errors["service"] = t("e_service")
    raw = str(f.get("master", "") or "any")
    master_id = int(raw) if raw.isdigit() else None
    if raw != "any" and (not master_id or not s or master_id not in candidates(s, None)):
        errors["master"] = t("e_master")
    try:
        day = date.fromisoformat(str(f.get("day", "")))
    except ValueError:
        day = None
    # the site keeps to the open days ahead; the desk (lead=False) may write in any day from today on
    if not day or (not day_open(day) if lead else day < now().date()):
        off = day and day >= now().date() and DAYS[day.weekday()] in S("days_off").split(",")
        errors["day"] = t("e_closed") if off else t("e_day")
    at = str(f.get("time", ""))
    if not re.fullmatch(TIME_RE, at):
        errors["time"] = t("e_time")
    if errors:
        return None
    start = mins(at)
    if start not in grid(s, day, lead=lead):
        errors["time"] = t("e_time")
        return None
    mid = free_master(s, candidates(s, master_id), start, taken(day))
    if mid is None:
        errors["time"] = t("e_taken")
        return None
    return s, mid, master_id is None, day, at


@app.post("/book")
def book():
    if not same_origin():
        abort(403)
    if too_many("book", 8):
        return reply(False, errors="busy")
    f = request.get_json(silent=True) or request.form
    errors = {}
    note = clean(f.get("note"), 200)
    if len(note) > 120:
        errors["note"] = t("e_note")
    name, phone = check_contact(f, errors)
    with BOOK_LOCK:  # two people choosing the same time: the second is told it was just taken
        picked = check_slot(f, errors)
        if errors:
            return reply(False, errors=errors)
        s, mid, anyone, day, at = picked
        m = db().execute("SELECT * FROM masters WHERE id=?", (mid,)).fetchone()
        sname, mname = loc(s, "name"), loc(m, "name")
        con = db()
        cur = con.execute("INSERT INTO bookings(created,service_id,service,cat,price,from_price,mins,master_id,master,any_master,"
                          "day,start,name,phone,note,lang) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (now().isoformat(timespec="seconds"), s["id"], sname, s["cat"], s["price"], s["from_price"],
                           s["mins"], mid, mname, int(anyone), day.isoformat(), at, name, phone, note, lang()))
        con.commit()
    n = cur.lastrowid
    msg = "\n".join(x for x in [
        t("m_hi"), f"{t('m_booking')} #{n}", f"{t('m_service')}: {sname} ({price_label(s)}, ~{s['mins']} {t('min')})",
        f"{t('m_master')}: {mname}", f"{t('m_when')}: {day.strftime('%d.%m.%Y')}, {at}", f"{t('m_name')}: {name}",
        phone and f"{t('m_phone')}: {phone}", note and f"{t('m_note')}: {note}"] if x)
    return reply(True, wa_link(msg), message=t("bk_sent", n=n))


# ---------------------------------------------------------------- admin
def check_csrf():
    token = session.get("csrf", "")
    if not token or not secrets.compare_digest(request.form.get("csrf", ""), token):
        abort(400)


def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        if request.method == "POST":
            check_csrf()
        return view(*a, **kw)
    return wrapped


@app.context_processor
def admin_counts():
    if not request.path.startswith("/admin") or not session.get("admin"):
        return {}
    n = db().execute("SELECT COUNT(*) FROM bookings WHERE status='new'").fetchone()[0]
    return {"new_bookings": n, "statuses": STATUSES}


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        check_csrf()
        if too_many("login-fail", 5, add=False):
            flash("ძალიან ბევრი მცდელობა. სცადე 10 წუთში.")
            return render_template("admin/login.html"), 429
        if not S("admin_hash"):
            flash("ადმინის პაროლი ჯერ არ არის დაყენებული: გაუშვი set_password.py.")
            return render_template("admin/login.html")
        if check_password_hash(S("admin_hash"), request.form.get("password", "")):
            with HITS_LOCK:
                HITS.pop(("login-fail", request.remote_addr), None)
            session.clear()
            session["admin"] = True
            session["csrf"] = secrets.token_hex(16)
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/admin") and not nxt.startswith("/admin/login") else url_for("admin_bookings"))
        too_many("login-fail", 5)
        flash("პაროლი არასწორია.")
    return render_template("admin/login.html")


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.get("/admin")
@admin_required
def admin_home():
    return redirect(url_for("admin_bookings"))


@app.get("/admin/bookings")
@admin_required
def admin_bookings():
    st = request.args.get("status")
    view = request.args.get("view", "upcoming")
    sql, args = "SELECT * FROM bookings WHERE 1=1", []
    if st in STATUSES:
        sql += " AND status=?"
        args.append(st)
    if view == "upcoming":
        sql += " AND day>=? ORDER BY day, start"
        args.append(now().date().isoformat())
    else:
        sql += " ORDER BY day DESC, start DESC"
    rows = db().execute(sql + " LIMIT 400", args).fetchall()
    days = {}
    for r in rows:
        days.setdefault(r["day"], []).append(r)
    return render_template("admin/bookings.html", days=days, st=st, view=view, services_all=services(),
                           masters_all=masters(), today=now().date().isoformat(), count=len(rows))


@app.post("/admin/bookings/add")
@admin_required
def admin_booking_add():
    """A booking taken by phone or at the desk, so the site stops offering that time."""
    f = request.form
    errors = {}
    name = clean(f.get("name"), 60) or "—"
    phone = clean(f.get("phone"), 30)
    picked = check_slot(f, errors, lead=False)
    if errors:
        for e in errors.values():
            flash(e)
        return redirect(url_for("admin_bookings"))
    s, mid, anyone, day, at = picked
    m = db().execute("SELECT * FROM masters WHERE id=?", (mid,)).fetchone()
    db().execute("INSERT INTO bookings(created,service_id,service,cat,price,from_price,mins,master_id,master,any_master,"
                 "day,start,name,phone,note,lang,source,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'ka','desk','confirmed')",
                 (now().isoformat(timespec="seconds"), s["id"], s["name_ka"], s["cat"], s["price"], s["from_price"], s["mins"],
                  mid, m["name_ka"], int(anyone), day.isoformat(), at, name, phone, clean(f.get("note"), 120)))
    db().commit()
    flash(f"ჩაწერა დაემატა: {day.strftime('%d.%m')} {at}, {m['name_ka']}.")
    return redirect(url_for("admin_bookings"))


@app.post("/admin/bookings/<int:rid>/status")
@admin_required
def admin_status(rid):
    st = request.form.get("status")
    if st not in STATUSES:
        abort(400)
    db().execute("UPDATE bookings SET status=? WHERE id=?", (st, rid))
    db().commit()
    return redirect(request.referrer if (request.referrer or "").startswith(request.host_url) else url_for("admin_bookings"))


@app.route("/admin/services", methods=["GET", "POST"])
@admin_required
def admin_services():
    con = db()
    if request.method == "POST":
        f = request.form
        if f.get("delete", type=int):
            con.execute("DELETE FROM services WHERE id=?", (f.get("delete", type=int),))
        else:
            cols = {k: f.getlist(k) for k in ("id", "cat", "name_ka", "name_en", "desc_ka", "desc_en", "price",
                                               "from_price", "mins", "active")}
            skipped = 0
            for i, sid in enumerate(cols["id"]):
                get = lambda k: cols[k][i] if i < len(cols[k]) else ""
                nka = clean(get("name_ka"), 60)
                price, length = get("price").strip(), get("mins").strip()
                if not nka and sid == "new":
                    continue
                if not nka or not price.isdigit() or not length.isdigit() or not 5 <= int(length) <= 600:
                    skipped += 1
                    continue
                row = (get("cat") if get("cat") in CATS else "women", nka, clean(get("name_en"), 60),
                       clean(get("desc_ka"), 120), clean(get("desc_en"), 120), int(price),
                       int(get("from_price") == "1"), int(length), int(get("active") != "0"))
                if sid == "new":
                    con.execute("INSERT INTO services(cat,name_ka,name_en,desc_ka,desc_en,price,from_price,mins,active,sort)"
                                " VALUES(?,?,?,?,?,?,?,?,?,99)", row)
                elif sid.isdigit():
                    con.execute("UPDATE services SET cat=?,name_ka=?,name_en=?,desc_ka=?,desc_en=?,price=?,from_price=?,"
                                "mins=?,active=?,sort=? WHERE id=?", (*row, i, int(sid)))
            if skipped:
                flash(f"{skipped} რიგი არ შეინახა: სახელი, ფასი და წუთები (5–600) სავალდებულოა.")
        con.commit()
        flash("შენახულია.")
        return redirect(url_for("admin_services"))
    rows = con.execute("SELECT * FROM services ORDER BY cat DESC, sort, id").fetchall()
    return render_template("admin/services.html", rows=rows)


@app.get("/admin/masters")
@admin_required
def admin_masters():
    return render_template("admin/masters.html", rows=masters(active=False))


@app.route("/admin/masters/new", methods=["GET", "POST"])
@app.route("/admin/masters/<int:mid>", methods=["GET", "POST"])
@admin_required
def admin_master(mid=None):
    con = db()
    m = con.execute("SELECT * FROM masters WHERE id=?", (mid,)).fetchone() if mid else None
    if mid and not m:
        abort(404)
    if request.method == "POST":
        f = request.form
        vals = {k: clean(f.get(k), n) for k, n in (("name_ka", 40), ("name_en", 40), ("role_ka", 40), ("role_en", 40),
                                                    ("about_ka", 120), ("about_en", 120))}
        errs = []
        if not vals["name_ka"]:
            errs.append("ქართული სახელი სავალდებულოა.")
        photo = m["photo"] if m else ""
        up = request.files.get("photo")
        if up and up.filename:
            try:
                photo = save_upload(up)
            except ValueError:
                errs.append("ფოტო ვერ წავიკითხე. ატვირთე JPG, PNG ან WEBP.")
        if "remove_photo" in f and not (up and up.filename):
            photo = ""
        if errs:
            for e in errs:
                flash(e)
            return render_template("admin/master.html", m=m, form=f), 400
        color = f.get("color", "") if re.fullmatch(r"#[0-9a-fA-F]{6}", f.get("color", "")) else "#5a4a3f"
        row = (f.get("cat") if f.get("cat") in CATS else "women", vals["name_ka"], vals["name_en"], vals["role_ka"],
               vals["role_en"], vals["about_ka"], vals["about_en"], photo, color, int("active" in f), f.get("sort", type=int) or 0)
        if m:
            old = m["photo"]
            con.execute("UPDATE masters SET cat=?,name_ka=?,name_en=?,role_ka=?,role_en=?,about_ka=?,about_en=?,photo=?,"
                        "color=?,active=?,sort=? WHERE id=?", (*row, mid))
            if old and old != photo:
                delete_image(old)
        else:
            con.execute("INSERT INTO masters(cat,name_ka,name_en,role_ka,role_en,about_ka,about_en,photo,color,active,sort)"
                        " VALUES(?,?,?,?,?,?,?,?,?,?,?)", row)
        con.commit()
        flash("შენახულია.")
        return redirect(url_for("admin_masters"))
    return render_template("admin/master.html", m=m, form=None)


@app.post("/admin/masters/<int:mid>/delete")
@admin_required
def admin_master_delete(mid):
    con = db()
    m = con.execute("SELECT photo FROM masters WHERE id=?", (mid,)).fetchone()
    if m:
        con.execute("DELETE FROM masters WHERE id=?", (mid,))
        if m["photo"]:
            delete_image(m["photo"])
        con.commit()
        flash("ოსტატი წაიშალა. მისი ძველი ჩაწერები სიაში რჩება.")
    return redirect(url_for("admin_masters"))


PHOTO_SLOTS = [("hero", "მთავარი ფოტო (ზედა)"), ("visit", "სალონი და მისამართი"), ("women", "ქალის მომსახურება"),
               ("men", "ბარბერი"), ("ch1", "ვიზიტი 1: დაბანა"), ("ch2", "ვიზიტი 2: შეჭრა"), ("ch3", "ვიზიტი 3: დასრულება")]


@app.route("/admin/photos", methods=["GET", "POST"])
@admin_required
def admin_photos():
    con = db()
    if request.method == "POST":
        slot = request.form.get("slot")
        up = request.files.get("photo")
        if slot not in dict(PHOTO_SLOTS) or not up or not up.filename:
            flash("აირჩიე ფოტო ასატვირთად.")
        else:
            try:
                stem = save_upload(up, phone=(slot == "hero"))
                old = S(f"photo_{slot}")
                con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (f"photo_{slot}", stem))
                delete_image(old)
                con.commit()
                flash("ფოტო განახლდა.")
            except ValueError:
                flash("ფოტო ვერ წავიკითხე. ატვირთე JPG, PNG ან WEBP.")
        return redirect(url_for("admin_photos"))
    return render_template("admin/photos.html", slots=PHOTO_SLOTS)


TEXT_GROUPS = [("ზედა ნაწილი და მენიუ", ("meta_", "nav_", "cta_", "hero_", "lang_", "skip")),
               ("სალონი და მისამართი", ("visit_", "ev_")), ("მომსახურება", ("sv_", "cat_", "price_", "min")),
               ("ოსტატები", ("tm_",)), ("ვიზიტის ისტორია", ("ch",)), ("ჩაწერა", ("bk_", "e_")),
               ("WhatsApp შეტყობინება", ("m_",)),
               ("ბოლო ნაწილი და გვერდები", ("close_", "foot_", "credits_", "privacy_", "nf_", "back_")),
               ("ფოტოების აღწერა", ("alt_",))]


@app.route("/admin/texts", methods=["GET", "POST"])
@admin_required
def admin_texts():
    con = db()
    rows = con.execute("SELECT * FROM texts ORDER BY key").fetchall()
    if request.method == "POST":
        for r in rows:
            ka, en = request.form.get(f"ka_{r['key']}"), request.form.get(f"en_{r['key']}")
            if ka is not None and en is not None and ka.strip():
                con.execute("UPDATE texts SET ka=?, en=? WHERE key=?", (ka.strip()[:600], en.strip()[:600], r["key"]))
        con.commit()
        flash("ტექსტები შენახულია.")
        return redirect(url_for("admin_texts"))
    groups, seen = [], set()
    for title, prefixes in TEXT_GROUPS:
        items = [r for r in rows if r["key"].startswith(prefixes) and r["key"] not in seen]
        seen |= {r["key"] for r in items}
        groups.append((title, items))
    groups.append(("სხვა", [r for r in rows if r["key"] not in seen]))
    return render_template("admin/texts.html", groups=[x for x in groups if x[1]])


SETTING_FIELDS = [("shop_name", "სალონის სახელი"), ("whatsapp", "WhatsApp ნომერი (995...)"),
                  ("street", "ქუჩა (ცარიელი = მხოლოდ უბანი)"), ("district_ka", "უბანი (ქართ.)"),
                  ("district_en", "უბანი (ინგლ.)"), ("city_ka", "ქალაქი (ქართ.)"), ("city_en", "ქალაქი (ინგლ.)"),
                  ("open", "პირველი ჩაწერის დრო (სს:წწ)"), ("close", "დახურვის დრო (სს:წწ)"),
                  ("step", "ჩაწერის ბიჯი (წუთი, მაგ. 30)"), ("lead", "დღეს ჩაწერა მინიმუმ ამდენი წუთით ადრე"),
                  ("days_ahead", "რამდენი დღით ადრე შეიძლება ჩაწერა")]


@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    con = db()
    if request.method == "POST":
        f = request.form
        errs = []
        if not re.fullmatch(r"[0-9]{8,15}", re.sub(r"[^0-9]", "", f.get("whatsapp", ""))):
            errs.append("WhatsApp ნომერი დაწერე საერთაშორისო ფორმატით, მაგ. 995599123456.")
        if not all(re.fullmatch(TIME_RE, f.get(k, "")) for k in ("open", "close")) or \
                (re.fullmatch(TIME_RE, f.get("open", "")) and re.fullmatch(TIME_RE, f.get("close", ""))
                 and mins(f["open"]) >= mins(f["close"])):
            errs.append("დრო დაწერე ასე: 10:00, და დახურვა გახსნის შემდეგ უნდა იყოს.")
        for k in ("step", "lead", "days_ahead"):
            if not f.get(k, "").isdigit():
                errs.append("ბიჯი, წუთები და დღეები დაწერე რიცხვით.")
                break
        else:
            if not 5 <= int(f["step"]) <= 120 or not 1 <= int(f["days_ahead"]) <= 180:
                errs.append("ბიჯი 5-დან 120 წუთამდე, დღეები 1-დან 180-მდე.")
        new_pw = f.get("new_password", "")
        if new_pw and len(new_pw) < 8:
            errs.append("ახალი პაროლი მინიმუმ 8 სიმბოლო უნდა იყოს.")
        if errs:
            for e in errs:
                flash(e)
            return render_template("admin/settings.html", fields=SETTING_FIELDS, days=DAYS), 400
        for k, _ in SETTING_FIELDS:
            v = clean(f.get(k), 80)
            if k == "whatsapp":
                v = re.sub(r"[^0-9]", "", v)
            con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
        off = ",".join(d for d in DAYS if d in f.getlist("days_off"))
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('days_off',?)", (off,))
        hours = "\n".join(line.strip() for line in f.get("hours", "").splitlines() if line.count("|") == 3)
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('hours',?)", (hours,))
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('hours_assumed',?)",
                    ("0" if "hours_confirmed" in f else "1",))
        if new_pw:
            con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('admin_hash',?)",
                        (generate_password_hash(new_pw),))
        con.commit()
        flash("პარამეტრები შენახულია.")
        return redirect(url_for("admin_settings"))
    return render_template("admin/settings.html", fields=SETTING_FIELDS, days=DAYS)


init_db()

if __name__ == "__main__":
    app.run(debug=not PRODUCTION, port=int(os.environ.get("PORT", 5001)))
