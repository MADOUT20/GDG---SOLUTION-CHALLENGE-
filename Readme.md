# GDG Solution Challenge 2026

Topic: Smart Resource Allocation - Data-Driven Volunteer Coordination for Social Impact

## What is in this repo

- `ngo_problem_solution.html`: original standalone NGO-themed UI draft
- `SRAS/GDG Solution/`: teammate SRAS prototype with operational feature ideas
- `app.py`: Flask backend that combines the preferred NGO presentation style with backend-backed actions
- `templates/index.html`: live Flask-rendered frontend
- `static/`: CSS and JavaScript for the connected dashboard
- `data/ngo_state.json`: local fallback data store used when Supabase is not configured
- `storage.py`: storage layer that switches between local JSON and Supabase
- `supabase/schema.sql`: database schema for the hosted Postgres setup
- `supabase/seed.sql`: starter data that mirrors the current JSON dataset

## Run locally

1. `python3 -m pip install -r requirements.txt`
2. `python3 app.py`
3. Open `http://127.0.0.1:5000`

## Enable Supabase

1. Create a Supabase project.
2. In the SQL editor, run `supabase/schema.sql`.
3. Run `supabase/seed.sql` if you want the hosted database to start with the same sample data.
4. Copy `.env.example` to `.env`.
5. Fill in `SUPABASE_URL` and a server-side key such as `SUPABASE_SECRET_KEY`.
6. Restart Flask.

If `.env` is missing or incomplete, the app automatically falls back to `data/ngo_state.json`.

## Backend actions included

- Add new data batches
- Log field reports
- Register donations
- Update volunteer deployments

Every action updates the same dashboard data so the UI is connected to the Flask backend instead of being a static demo. The backend now supports both local JSON storage and Supabase-backed persistence.
