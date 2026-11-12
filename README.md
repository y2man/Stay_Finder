# StayFinder

A full-stack accommodation marketplace built with React, TypeScript, FastAPI and PostgreSQL. It includes guest booking, host listing management, account security, reviews, favorites, messaging, notifications, AI travel assistance and optional Stripe/SMTP integrations.

## Feature overview

- **Discovery:** destination search, filters, sorting, pagination, property details, availability filtering and map links.
- **Accounts:** guest/host registration, Argon2 password hashing, JWT access tokens, rotating refresh sessions, logout, email verification and password reset.
- **Bookings:** server-calculated quotes, minimum-stay/guest validation, database-level overlapping-date protection, host approval/decline, trip history and cancellation.
- **Host tools:** create/edit/unpublish/delete listings, upload listing images, manage booking requests and view guest details.
- **Community:** favorites, verified-stay reviews and guest/host direct messages (inbox refreshes every five seconds).
- **Operations:** notifications, admin overview, user role management and property moderation.
- **Integrations:** optional Stripe Checkout + signed webhook, SMTP email, Groq AI assistant, and OpenStreetMap location links.

## Requirements

- Node.js 20 or newer
- Python 3.12 (recommended; backend Docker image uses Python 3.12)
- PostgreSQL 16 or a dedicated PostgreSQL database such as Neon
- Git and VS Code are recommended

Docker is optional. Redis is not required by the current application.

## Run locally on Windows (without Docker)

### 1. Configure PostgreSQL

Create a database named `stayfinder` and a PostgreSQL user/password for it. Make sure the account can create the `btree_gist` extension (or have a database administrator enable it).

### 2. Configure the backend

Open PowerShell in the `stayfinder` project folder:

```powershell
cd backend
Copy-Item .env.example .env
```

Edit `backend/.env` and set `DATABASE_URL` to your local PostgreSQL connection, for example:

```dotenv
DATABASE_URL=postgresql+psycopg://stayfinder:YOUR_PASSWORD@localhost:5432/stayfinder
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
```

Create and activate the virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation for this terminal, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

Apply migrations, seed demo listings, and start the API:

```powershell
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs  
Health check: http://127.0.0.1:8000/api/v1/health

Demo host account: `host@stayfinder.dev` / `password123`. Change or remove this demo account before any public deployment.

### 3. Configure and run the frontend

Open a **second** PowerShell terminal:

```powershell
cd path\to\stayfinder\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open http://localhost:5173.

### 4. Run tests

With PostgreSQL running and the backend virtual environment active:

```powershell
cd backend
pytest
```

## Optional integrations

All secrets belong in `backend/.env`, never in frontend source code or Git.

| Integration | Environment variables | Behavior without credentials |
|---|---|---|
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Verification/reset tokens are returned for local development; emails are not sent. |
| Payments | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Checkout endpoint returns HTTP 503 until configured. |
| AI assistant | `GROQ_API_KEY`, `GROQ_MODEL` | Assistant endpoint returns HTTP 503 until configured. |
| Admin bootstrap | `ADMIN_EMAILS` | Comma-separated emails receive the admin role when they register. |

### Stripe webhook

Configure the Stripe webhook endpoint as `https://YOUR_API_HOST/api/v1/payments/webhook` and subscribe to `checkout.session.completed`. Put the signing secret in `STRIPE_WEBHOOK_SECRET`. Use Stripe test keys and test cards until the integration is verified. Never use real payment credentials in a public repository.

### Email

Use an SMTP provider's app password or API-based SMTP credential. Configure the sender address and test both verification and password-reset emails before production.

### Groq AI

Set `GROQ_API_KEY` and optionally `GROQ_MODEL`. The assistant is instructed not to claim live availability or make bookings; it is a planning helper.

## Deploying (Render + Vercel + Neon)

The repository includes `render.yaml` and `vercel.json` as deployment starting points. These files do not contain private credentials.

### 1. Database (Neon PostgreSQL)

1. Create a dedicated PostgreSQL project/database for StayFinder. Do not reuse a database that contains another application's tables.
2. Copy the pooled or direct PostgreSQL connection string. Ensure it is compatible with psycopg 3; use the `postgresql+psycopg://` scheme.
3. Set it as `DATABASE_URL` in the Render backend environment. The database role must be able to create the `btree_gist` extension, or the extension must be enabled by the database owner before migrations.

### 2. Backend (Render)

1. Push this repository to GitHub.
2. In Render, create a Blueprint from the repository and review `render.yaml`, or create a Python web service with `backend` as its root directory.
3. Set `DATABASE_URL`, `CORS_ORIGINS` and `FRONTEND_URL`. Set `CORS_ORIGINS` to the exact deployed Vercel origin (no trailing slash).
4. Keep the generated `SECRET_KEY`; do not replace it with a public value. Add SMTP, Stripe, Groq and Cloudinary secrets only in Render's environment settings.
5. The health endpoint is `/api/v1/health`.

### 3. Frontend (Vercel)

1. Import the repository into Vercel and set the project root to `frontend`.
2. Set `VITE_API_URL` to the deployed backend origin, for example `https://your-api.onrender.com` (no trailing slash).
3. Deploy. `vercel.json` provides the SPA fallback for React Router.
4. Copy the final Vercel origin into the Render `CORS_ORIGINS` and `FRONTEND_URL` variables, then redeploy the backend.

### 4. Email provider (SMTP)

Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USE_SSL`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM`. For providers using STARTTLS on port 587, set `SMTP_USE_SSL=false`. For implicit TLS on port 465, set it to `true`. Test registration verification and password reset. In production, development tokens are never returned by the API when email is not configured.

### 5. Stripe payments

Start with Stripe test-mode credentials. Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `PAYMENT_CURRENCY`. Register `https://YOUR_API_HOST/api/v1/payments/webhook` as a webhook endpoint and subscribe to `checkout.session.completed` and `checkout.session.async_payment_succeeded`. Confirm that successful test payments update the booking only after Stripe's signed webhook is received.

### 6. Groq AI

Set `GROQ_API_KEY` and optionally `GROQ_MODEL`. The key belongs only in the backend environment, never in `VITE_*` variables.

### 7. Maps and image storage

Property maps use OpenStreetMap embeds and do not require an API key. Hosts can enter latitude/longitude for a listing. For persistent production image storage, set `UPLOAD_PROVIDER=cloudinary` and provide `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`. If Cloudinary is not configured, uploads use local disk; local disk may be ephemeral on hosted services and should be used only for development.

### 8. Production checklist

- Use a dedicated production database and strong generated `SECRET_KEY`.
- Set exact frontend CORS origin and production frontend URL.
- Set `ENVIRONMENT=production`; never enable debug development tokens.
- Configure SMTP and test email verification/password recovery.
- Use Stripe live keys only after test-mode checkout and webhook verification pass.
- Configure Cloudinary (or another durable object store) before accepting real user uploads.
- Set `ADMIN_EMAILS` before the intended administrator registers; remove demo accounts and change demo credentials.
- Back up the database and review hosting costs/limits before launch.
- Set frontend build environment variable `VITE_API_URL` to the backend origin, e.g. `https://your-api.onrender.com` (no trailing slash).
- Set backend `CORS_ORIGINS` to the exact frontend origin and `FRONTEND_URL` to that origin.
- Run `alembic upgrade head` as a release/pre-deploy command, then run `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Configure a persistent disk or external object storage for uploaded images. The current upload endpoint writes to the backend's `app/uploads` folder, which is suitable for local development but ephemeral on many hosting platforms.
- Set a strong random `SECRET_KEY`; remove the demo host account; configure rate limiting, backups, monitoring and HTTPS before public use.

## Docker (optional)

Copy the root `.env.example` to `.env`, change all secrets/passwords, then run:

```bash
docker compose up --build
```

UI: http://localhost:5173  
API docs: http://localhost:8000/docs

## Important production notes

This is a portfolio project, not a certified production booking/payment platform. Before handling real customers or money, add rate limiting and abuse protection, stronger audit logging, privacy/terms pages, cancellation/refund policy handling, durable object storage, backup/restore testing, and a security review. Stripe webhook confirmation is signature-verified; do not mark a booking paid from a frontend redirect alone.
