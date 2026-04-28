# RahatSetu - GDG Solution Challenge 2026

**Topic:** Smart Resource Allocation - Data-Driven Volunteer Coordination for Social Impact

RahatSetu is an NGO Crisis Portal designed to modernize the interface and backend operations for emergency response, volunteer deployment, and resource allocation. It provides a heatmap for tracking critical needs across different regions and offers both a user and admin dashboard for real-time monitoring and updates.

## What is in this repo

- `app.py`: Flask backend providing the API and routing.
- `templates/`: HTML templates including `index.html` (Admin Dashboard), `user_dashboard.html` (User Dashboard), `login.html`, and `emergency.html`.
- `static/`: CSS and JavaScript files, including custom login styles and dashboard interactivity.
- `storage.py`: Storage layer supporting dual backend modes (Local JSON & Supabase PostgreSQL).
- `data/`: Local JSON data fallback (`ngo_state.json`, `admins.json`, `users.json`).
- `supabase/`: Database schema (`schema.sql`) and sample data (`seed.sql`) for hosted Postgres setup.

## Try It Out

You can try out the application locally by logging into the admin console with the default credentials:

- **URL:** `http://127.0.0.1:5000/login`
- **Admin Email:** `admin@rahatsetu.org`
- **Admin Password:** `admin123`

*(Note: Users can also sign up directly from the login page to access the User Portal).*



## Features

- **Authentication:** Secure login for Admins and NGOs.
- **Real-time Dashboard:** Track total needs, volunteers, funds, and recent activities.
- **Emergency Reporting:** Log field reports with varying priority levels to update regional requirements.
- **Donation Management:** Register incoming resource and monetary donations.
- **Volunteer Deployment:** Assign volunteers to critical areas.
- **Dual Storage:** Seamlessly works with local JSON files or a cloud Supabase PostgreSQL database.
