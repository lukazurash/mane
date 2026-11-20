# Mane: hair salon and barbershop site with online booking

A site for a salon and barbershop in Saburtalo, Tbilisi (Georgian and English) with real online booking
and an admin panel. Flask + SQLite, no build step. Built on the same engine as Rose (the florist site).

## What it does

- **Site:** hero with the next free time, services and prices (women / men), the four masters, a three-step
  "how a visit goes" photo story, the booking form, the salon's address and hours, privacy and photo-credit pages.
- **Booking:** the form shows only times that are really free. The server keeps each master's diary: a booking
  takes that master's time for the length of the service, "any free master" goes to whoever is free, and the
  same time can never be booked twice. The booking is saved, then WhatsApp opens with it filled in. Without
  JavaScript the form still works and goes straight to WhatsApp.
- **Admin (`/admin`):** bookings by day with status (new, confirmed, done, no-show, cancelled; cancelling frees
  the time), adding a booking taken by phone so the site stops offering it, services (names, lines, prices,
  "from" prices, minutes, hide/show), masters (photo or a coloured initial, role, women or barber, hide/show),
  the site's photos, every text in both languages, and settings (WhatsApp number, address, opening and closing
  time, slot step, days off, notice for same-day bookings, how far ahead, password).

## Run it locally

```
python -m venv venv
venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
venv\Scripts\python app.py
```

Open http://localhost:5001. The first start builds `data/mane.db` and resizes the photos in `photo-src/` into
`data/media/`. The local admin password is printed in the terminal on the first start; change it in
Admin > Settings.

Tests: `venv\Scripts\python -m pytest` (60 checks)

## Put it online (PythonAnywhere)

1. Upload the code (git clone, branch `v2`), make a virtualenv, `pip install -r requirements.txt`.
2. In the WSGI file set `PRODUCTION=1` before importing the app, then `from app import app as application`.
   The server makes its own secret key in `data/.secret_key`.
3. Static files mapping: URL `/static/` to the `static/` folder. Force HTTPS on.
4. Set the admin password in a Bash console: `venv/bin/python set_password.py`.
5. Reload. Then in the admin: the real WhatsApp number, the hours, the masters and their photos, the prices.

`DB_PATH` and `MEDIA_DIR` move the database and uploads elsewhere if needed. Back up `data/`.

## Files

- `app.py`: routes, the booking diary, database, image resizing, admin.
- `content.py`: the starting texts, services, masters and photos (used once, on the first start).
- `templates/`: the site (`base`, `home`, `page`) and `admin/`.
- `static/site.css`, `static/site.js`: the site's own styles and the booking form.
- `static/assets/`: the design kit (taste-skill) the layout is built on; do not edit.
- `photo-src/`: the stand-in photographs (Unsplash), credited on `/credits`.
