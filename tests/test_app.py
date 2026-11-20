"""End-to-end checks for Mane, against a throwaway database and media folder."""
import importlib
import io
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def app_mod(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mane")
    os.environ.update(DB_PATH=str(tmp / "t.db"), MEDIA_DIR=str(tmp / "media"), ADMIN_PASSWORD="test-pass-123")
    sys.path.insert(0, str(ROOT))
    mod = importlib.import_module("app")
    mod.app.config["TESTING"] = True
    return mod


@pytest.fixture
def client(app_mod):
    app_mod.HITS.clear()
    return app_mod.app.test_client()


def admin(client):
    client.get("/admin/login")
    with client.session_transaction() as s:
        token = s["csrf"]
    r = client.post("/admin/login", data={"password": "test-pass-123", "csrf": token})
    assert r.status_code == 302
    with client.session_transaction() as s:
        return s["csrf"]


def jpeg(w=1000, h=1250, color=(120, 90, 60)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "JPEG")
    buf.seek(0)
    return buf


def day(mod, n):
    """A day n days from now; each test books on its own day so they never share a diary."""
    return (datetime.now(mod.TZ).date() + timedelta(days=n)).isoformat()


def sql(mod, q, args=()):
    with mod.app.app_context():
        con = mod.db()
        rows = con.execute(q, args).fetchall()
        con.commit()
        return rows


def ids(mod, cat):
    return [r["id"] for r in sql(mod, "SELECT id FROM masters WHERE cat=? AND active=1 ORDER BY sort, id", (cat,))]


def svc(mod, cat="women"):
    return sql(mod, "SELECT * FROM services WHERE cat=? AND active=1 ORDER BY sort, id", (cat,))[0]


def book(client, mod, n, time="10:00", master="any", cat="women", **kw):
    body = {"service": svc(mod, cat)["id"], "master": master, "day": day(mod, n), "time": time, "name": "Nino", **kw}
    return client.post("/book", json=body)


def free(client, mod, n, master=None, cat="women"):
    q = f"/slots?service={svc(mod, cat)['id']}&day={day(mod, n)}" + (f"&master={master}" if master else "")
    return client.get(q).get_json()["times"]


# ---------------------------------------------------------------- public pages
@pytest.mark.parametrize("path", ["/", "/?s=9", "/?m=3", "/privacy", "/credits", "/robots.txt"])
def test_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert b"Traceback" not in r.data


def test_public_pages_set_no_cookie(client):
    assert "Set-Cookie" not in client.get("/").headers


def test_unknown_page_is_404(client):
    assert client.get("/no-such-page").status_code == 404


def test_language_switch(client):
    r = client.get("/lang/en?next=/privacy")
    assert r.status_code == 302 and r.headers["Location"].endswith("/privacy")
    assert b'lang="en"' in client.get("/").data


def test_language_switch_refuses_offsite_redirect(client):
    assert client.get("/lang/en?next=//evil.example").headers["Location"] == "/"


def test_copy_numbers_follow_the_data(client):
    html = client.get("/").data.decode()
    assert "{from}" not in html and "{next}" not in html and "20 ₾" in html


def test_hero_says_the_next_free_time(client):
    html = client.get("/").data.decode()
    assert "hero-notice" in html


def test_security_headers(client):
    h = client.get("/").headers
    assert h["X-Frame-Options"] == "DENY" and "default-src 'self'" in h["Content-Security-Policy"]


def test_price_from_reads_right_in_both_languages(client, app_mod):
    assert "120 ₾-დან" in client.get("/").data.decode()
    client.get("/lang/en")
    assert "from 120 ₾" in client.get("/").data.decode()


# ---------------------------------------------------------------- the diary
def test_slots_fill_the_day_and_stop_before_closing(client, app_mod):
    times = free(client, app_mod, 2)
    assert times[0] == "10:00" and times[-1] == "20:00"  # a 60-minute cut must end by 21:00


def test_booking_takes_the_time_from_that_master_only(client, app_mod):
    nino, ana = ids(app_mod, "women")
    assert book(client, app_mod, 3, master=nino).get_json()["ok"]
    assert "10:00" not in free(client, app_mod, 3, nino) and "10:30" not in free(client, app_mod, 3, nino)
    assert "11:00" in free(client, app_mod, 3, nino)          # the hour is over
    assert "10:00" in free(client, app_mod, 3, ana)           # Ana is still free
    assert "10:00" in free(client, app_mod, 3)                # so "anyone" still offers it


def test_any_master_fills_up_then_the_time_goes(client, app_mod):
    first, second = book(client, app_mod, 4), book(client, app_mod, 4)
    assert first.get_json()["ok"] and second.get_json()["ok"]
    rows = sql(app_mod, "SELECT master_id, any_master FROM bookings WHERE day=?", (day(app_mod, 4),))
    assert {r["master_id"] for r in rows} == set(ids(app_mod, "women")) and all(r["any_master"] for r in rows)
    assert "10:00" not in free(client, app_mod, 4)
    third = book(client, app_mod, 4)
    assert third.status_code == 400 and "time" in third.get_json()["errors"]


def test_barber_and_salon_diaries_are_apart(client, app_mod):
    book(client, app_mod, 5), book(client, app_mod, 5)          # both women's masters busy at 10:00
    assert "10:00" in free(client, app_mod, 5, cat="men")


def test_cancelled_booking_frees_the_time(client, app_mod):
    nino = ids(app_mod, "women")[0]
    r = book(client, app_mod, 6, master=nino).get_json()
    assert "10:00" not in free(client, app_mod, 6, nino)
    token = admin(client)
    bid = sql(app_mod, "SELECT MAX(id) FROM bookings")[0][0]
    client.post(f"/admin/bookings/{bid}/status", data={"status": "cancelled", "csrf": token})
    assert r["ok"] and "10:00" in free(client, app_mod, 6, nino)


def test_days_off_close_the_diary(client, app_mod):
    target = datetime.now(app_mod.TZ).date() + timedelta(days=7)
    name = app_mod.DAYS[target.weekday()]
    sql(app_mod, "UPDATE settings SET value=? WHERE key='days_off'", (name,))
    try:
        r = client.get(f"/slots?service={svc(app_mod)['id']}&day={target.isoformat()}").get_json()
        assert r["times"] == [] and r["closed"]
        res = book(client, app_mod, 7)
        assert res.status_code == 400 and "day" in res.get_json()["errors"]
    finally:
        sql(app_mod, "UPDATE settings SET value='' WHERE key='days_off'")


def test_today_offers_no_time_already_gone(client, app_mod):
    now = datetime.now(app_mod.TZ)
    earliest = now.hour * 60 + now.minute + 30
    for t in free(client, app_mod, 0):
        h, m = map(int, t.split(":"))
        assert h * 60 + m >= earliest


# ---------------------------------------------------------------- booking
def test_booking_saves_and_returns_whatsapp_link(client, app_mod):
    r = book(client, app_mod, 8, time="12:30", phone="599 12 34 56", note="Long hair")
    data = r.get_json()
    assert r.status_code == 200 and data["ok"] and data["url"].startswith("https://wa.me/")
    b = sql(app_mod, "SELECT * FROM bookings ORDER BY id DESC")[0]
    assert b["name"] == "Nino" and b["start"] == "12:30" and b["status"] == "new" and b["note"] == "Long hair"
    assert f"%23{b['id']}" in data["url"]  # the booking number travels in the message


def test_price_and_length_come_from_the_server(client, app_mod):
    book(client, app_mod, 9, price=1, mins=5)
    b = sql(app_mod, "SELECT * FROM bookings ORDER BY id DESC")[0]
    s = svc(app_mod)
    assert b["price"] == s["price"] and b["mins"] == s["mins"]


@pytest.mark.parametrize("field,payload", [
    ("name", {"name": ""}),
    ("phone", {"phone": "call me"}),
    ("day", {"day": "2001-01-01"}),
    ("day", {"day": "not-a-date"}),
    ("service", {"service": 99999}),
    ("master", {"master": 99999}),
    ("time", {"time": "10:07"}),
    ("time", {"time": "23:30"}),
    ("time", {"time": "late"}),
    ("note", {"note": "x" * 150}),
])
def test_booking_errors_name_the_field(client, app_mod, field, payload):
    body = {"service": svc(app_mod)["id"], "master": "any", "day": day(app_mod, 10), "time": "10:00", "name": "A", **payload}
    r = client.post("/book", json=body)
    assert r.status_code == 400 and field in r.get_json()["errors"]


def test_a_barber_cannot_be_booked_for_colouring(client, app_mod):
    r = book(client, app_mod, 10, master=ids(app_mod, "men")[0], cat="women")
    assert r.status_code == 400 and "master" in r.get_json()["errors"]


def test_booking_without_script_redirects_to_whatsapp(client, app_mod):
    r = client.post("/book", data={"service": str(svc(app_mod)["id"]), "master": "any", "day": day(app_mod, 11),
                                   "time": "15:00", "name": "A"})
    assert r.status_code == 303 and r.headers["Location"].startswith("https://wa.me/")


def test_booking_from_another_site_is_refused(client, app_mod):
    r = client.post("/book", json={"service": 1}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_bookings_are_rate_limited(client, app_mod):
    codes = [client.post("/book", json={"name": ""}).status_code for _ in range(10)]
    assert codes[-1] == 429


# ---------------------------------------------------------------- admin
def test_admin_needs_login(client):
    for path in ["/admin", "/admin/bookings", "/admin/services", "/admin/masters", "/admin/texts", "/admin/settings"]:
        r = client.get(path)
        assert r.status_code == 302 and "/admin/login" in r.headers["Location"]


def test_wrong_password_then_lockout(client):
    client.get("/admin/login")
    with client.session_transaction() as s:
        token = s["csrf"]
    for _ in range(5):
        assert client.post("/admin/login", data={"password": "nope", "csrf": token}).status_code == 200
    r = client.post("/admin/login", data={"password": "test-pass-123", "csrf": token})
    assert r.status_code == 429  # even the right password waits once locked


def test_admin_post_without_csrf_is_refused(client):
    admin(client)
    assert client.post("/admin/bookings/1/status", data={"status": "done"}).status_code == 400


@pytest.mark.parametrize("path", ["/admin/bookings", "/admin/bookings?view=all", "/admin/bookings?status=new",
                                  "/admin/services", "/admin/masters", "/admin/masters/new", "/admin/masters/1",
                                  "/admin/photos", "/admin/texts", "/admin/settings"])
def test_admin_pages_render(client, path):
    admin(client)
    r = client.get(path)
    assert r.status_code == 200 and b"Traceback" not in r.data


def test_status_change_and_bad_status(client, app_mod):
    book(client, app_mod, 12)
    token = admin(client)
    bid = sql(app_mod, "SELECT MAX(id) FROM bookings")[0][0]
    client.post(f"/admin/bookings/{bid}/status", data={"status": "confirmed", "csrf": token})
    assert sql(app_mod, "SELECT status FROM bookings WHERE id=?", (bid,))[0][0] == "confirmed"
    assert client.post(f"/admin/bookings/{bid}/status", data={"status": "hacked", "csrf": token}).status_code == 400


def test_desk_booking_blocks_the_site(client, app_mod):
    token = admin(client)
    nino = ids(app_mod, "women")[0]
    client.post("/admin/bookings/add", data={"csrf": token, "service": svc(app_mod)["id"], "master": nino,
                                             "day": day(app_mod, 13), "time": "14:00", "name": "Phone client"})
    b = sql(app_mod, "SELECT * FROM bookings ORDER BY id DESC")[0]
    assert b["source"] == "desk" and b["status"] == "confirmed" and b["start"] == "14:00"
    assert "14:00" not in free(client, app_mod, 13, nino)


def test_services_edit_add_hide_delete(client, app_mod):
    token = admin(client)
    rows = sql(app_mod, "SELECT * FROM services ORDER BY cat DESC, sort, id")
    cols = ("cat", "name_ka", "name_en", "desc_ka", "desc_en", "price", "from_price", "mins", "active")
    data = {"csrf": token, "id": [str(r["id"]) for r in rows] + ["new"]}
    for c in cols:
        data[c] = [str(r[c]) for r in rows] + [""]
    data["price"][0] = "55"                      # the first women's service costs more now
    data["name_ka"][-1], data["name_en"][-1], data["price"][-1], data["mins"][-1] = "ფრჩხილები", "Nails", "40", "50"
    data["cat"][-1], data["from_price"][-1], data["active"][-1] = "women", "0", "1"
    client.post("/admin/services", data=data)
    assert sql(app_mod, "SELECT price FROM services WHERE id=?", (rows[0]["id"],))[0][0] == 55
    new = sql(app_mod, "SELECT * FROM services WHERE name_en='Nails'")[0]
    assert new["mins"] == 50 and "ფრჩხილები" in client.get("/").data.decode()
    # hidden: off the site and not bookable
    data["id"][-1] = str(new["id"])
    data["active"][-1] = "0"
    client.post("/admin/services", data=data)
    assert "ფრჩხილები" not in client.get("/").data.decode()
    r = client.post("/book", json={"service": new["id"], "master": "any", "day": day(app_mod, 14), "time": "10:00", "name": "A"})
    assert "service" in r.get_json()["errors"]
    client.post("/admin/services", data={"csrf": token, "delete": str(new["id"])})
    assert not sql(app_mod, "SELECT 1 FROM services WHERE id=?", (new["id"],))


def test_bad_service_row_is_skipped_not_saved(client, app_mod):
    token = admin(client)
    r = client.post("/admin/services", data={"csrf": token, "id": ["new"], "cat": ["men"], "name_ka": ["ცუდი"],
                                              "name_en": [""], "desc_ka": [""], "desc_en": [""], "price": ["abc"],
                                              "from_price": ["0"], "mins": ["45"], "active": ["1"]}, follow_redirects=True)
    assert not sql(app_mod, "SELECT 1 FROM services WHERE name_ka='ცუდი'") and "არ შეინახა" in r.data.decode()


def test_master_create_with_photo_hide_delete(client, app_mod):
    token = admin(client)
    r = client.post("/admin/masters/new", data={
        "csrf": token, "cat": "men", "name_ka": "დათო", "name_en": "Dato", "role_ka": "ბარბერი", "role_en": "Barber",
        "about_ka": "", "about_en": "", "color": "#334455", "sort": "9", "active": "on",
        "photo": (jpeg(), "d.jpg")}, content_type="multipart/form-data")
    assert r.status_code == 302
    m = sql(app_mod, "SELECT * FROM masters WHERE name_en='Dato'")[0]
    widths = sql(app_mod, "SELECT widths FROM images WHERE stem=?", (m["photo"],))[0][0]
    assert widths == "480,960,1000" and (app_mod.MEDIA / f"{m['photo']}-960.webp").exists()
    assert "დათო" in client.get("/").data.decode()
    assert m["id"] in ids(app_mod, "men")
    # hidden: off the site and out of the diary
    client.post(f"/admin/masters/{m['id']}", data={"csrf": token, "cat": "men", "name_ka": "დათო", "name_en": "Dato"})
    assert "დათო" not in client.get("/").data.decode()
    assert book(client, app_mod, 15, master=m["id"], cat="men").status_code == 400
    old = m["photo"]
    client.post(f"/admin/masters/{m['id']}/delete", data={"csrf": token})
    assert not sql(app_mod, "SELECT 1 FROM masters WHERE id=?", (m["id"],))
    assert not list(app_mod.MEDIA.glob(f"{old}-*.webp"))


def test_bad_upload_is_refused(client, app_mod):
    token = admin(client)
    r = client.post("/admin/masters/new", data={
        "csrf": token, "cat": "men", "name_ka": "x", "photo": (io.BytesIO(b"<?php echo 1; ?>"), "evil.jpg")},
        content_type="multipart/form-data")
    assert r.status_code == 400 and not sql(app_mod, "SELECT 1 FROM masters WHERE name_ka='x'")


def test_site_photo_upload(client, app_mod):
    token = admin(client)
    r = client.post("/admin/photos", data={"csrf": token, "slot": "hero", "photo": (jpeg(2600, 1700), "h.jpg")},
                    content_type="multipart/form-data")
    assert r.status_code == 302
    with app_mod.app.app_context():
        stem = app_mod.S("photo_hero")
    assert (app_mod.MEDIA / f"{stem}-phone.webp").exists()
    assert Image.open(app_mod.MEDIA / f"{stem}-phone.webp").size == (780, 975)


def test_texts_edit_shows_on_site_escaped(client, app_mod):
    token = admin(client)
    data = {"csrf": token}
    for r in sql(app_mod, "SELECT * FROM texts"):
        data[f"ka_{r['key']}"] = r["ka"]
        data[f"en_{r['key']}"] = r["en"]
    data["ka_hero_h1"] = "ახალი სათაური <script>"
    client.post("/admin/texts", data=data)
    assert "ახალი სათაური &lt;script&gt;" in client.get("/").data.decode()


def test_settings_validate_and_save(client, app_mod):
    token = admin(client)
    with app_mod.app.app_context():
        base = {k: app_mod.S(k) for k, _ in app_mod.SETTING_FIELDS}
    hours = "mon-sun|ყოველდღე|Every day|10:00–21:00"
    for bad in ({"whatsapp": "abc"}, {"open": "22:00"}, {"step": "0"}, {"close": "9pm"}):
        assert client.post("/admin/settings", data={**base, "csrf": token, "hours": hours, **bad}).status_code == 400
    good = {**base, "csrf": token, "whatsapp": "+995 599 11 22 33", "close": "19:00", "hours": hours, "hours_confirmed": "on"}
    assert client.post("/admin/settings", data=good).status_code == 302
    html = client.get("/").data.decode()
    assert "wa.me/995599112233" in html and "data-open-now" in html
    assert free(client, app_mod, 16)[-1] == "18:00"   # closing at 19:00 ends the last hour-long cut at 18:00
    client.post("/admin/settings", data={**base, "csrf": token, "hours": hours})


def test_password_change(client, app_mod):
    token = admin(client)
    with app_mod.app.app_context():
        base = {k: app_mod.S(k) for k, _ in app_mod.SETTING_FIELDS}
    hours = "mon-sun|ყოველდღე|Every day|10:00–21:00"
    client.post("/admin/settings", data={**base, "csrf": token, "hours": hours, "new_password": "brand-new-pass"})
    client.post("/admin/logout", data={"csrf": token})
    client.get("/admin/login")
    with client.session_transaction() as s:
        t2 = s["csrf"]
    assert client.post("/admin/login", data={"password": "brand-new-pass", "csrf": t2}).status_code == 302
    with client.session_transaction() as s:
        t3 = s["csrf"]
    client.post("/admin/settings", data={**base, "csrf": t3, "hours": hours, "new_password": "test-pass-123"})
