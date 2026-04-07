# Masaža Indir Mujić — Full Web App

## Project Structure
```
massage_app/
├── app.py              ← Main Flask app + all routes
├── requirements.txt    ← Python dependencies
├── Procfile            ← Render.com start command
├── init_db.py          ← Run once to set up database
├── templates/
│   ├── index.html      ← Public website
│   └── admin/
│       ├── base.html
│       ├── login.html
│       ├── dashboard.html
│       ├── appointments.html
│       ├── massages.html
│       ├── hours.html
│       ├── gallery.html
│       └── settings.html
├── static/
│   ├── css/style.css
│   └── images/         ← Put your images here
└── uploads/            ← Gallery uploads go here (auto-created)
```

## Admin Login
- URL: yoursite.com/admin
- Username: admin
- Password: admin123
⚠️ CHANGE THIS immediately in /admin/settings after first login!

## Running Locally
```bash
pip install -r requirements.txt
python init_db.py
python app.py
```
Then open http://localhost:5000

## Deploying to Render.com
1. Push this folder to a GitHub repository
2. Go to render.com → New → Web Service
3. Connect your GitHub repo
4. Set these:
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app
5. Add Environment Variables:
   - SECRET_KEY = (any long random string, e.g. from https://randomkeygen.com)
   - DATABASE_URL = (Render will give you this if you add a PostgreSQL database)
6. Click Deploy

## Adding a Database on Render
1. Render Dashboard → New → PostgreSQL
2. Create a free database
3. Copy the "Internal Database URL"
4. Add it as DATABASE_URL environment variable in your web service

## Images
Put your original images in static/images/:
- selfie.jfif
- massage-room-600px.jpg
- massage.webp
- masser.jpg

Or upload them via the admin gallery panel — they'll show on the site automatically.

## Features
✅ Booking system with real-time slot availability
✅ Admin dashboard — view & manage appointments
✅ Confirm / cancel / delete appointments
✅ Manage massage types (add/edit/delete, all 3 languages)
✅ Manage working hours (live on site and booking form)
✅ Gallery management (upload/delete photos)
✅ Contact info editable in admin
✅ Admin password changeable
✅ 3 languages (SL/DE/EN)
✅ Dark/Light theme
✅ Mobile responsive
