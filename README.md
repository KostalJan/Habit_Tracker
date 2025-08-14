# HabitTracker Mini

A Django app to track daily/weekly habits with a clean REST API, per-habit stats (current/longest streak, 7/30-day success), and a simple server-rendered UI.

---

## Features
- **Habits**: `daily` or `weekly` with `target_per_period`.
- **Logs**: unique per `(habit, date)`; weekly sums count toward targets.
- **Stats**: current & longest streak, success over last 7/30 days.
- **API**: DRF with auth, filtering, pagination.
- **UI**: Today (✓/✗ and X/Y) and Stats pages, external CSS.
- **Permissions**: users can access only their own data.
- **Tests**: models, services, API, and views.

## Stack
Django 5 • Django REST Framework • SQLite (dev) • pytest (+ pytest-django, factory_boy, freezegun) • HTML templates + `static/css/base.css`.

---

## Quick Start

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver


