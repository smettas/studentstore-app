# StudentStore — Phase 1

Phase 1 creates the modular project skeleton for the StudentStore Django REST backend and Expo React Native mobile app. Business models and APIs are intentionally deferred to later phases.

## Requirements
- Python 3.11+ recommended
- Node.js LTS and npm
- Git
- PostgreSQL for normal local development (or a disposable test database for verification)
- VS Code

## Folder map
- `backend/` — Django project, split settings, and 11 modular Django apps
- `mobile/` — Expo/React Native app skeleton with separate screen, component, navigation, service, state, hook, utility, and constant folders
- `.env.example` — environment variable template (copy to `.env`; never commit `.env`)

## Windows setup (PowerShell)
1. Install Python, Node.js LTS, Git, and PostgreSQL.
2. Open this folder in VS Code.
3. Create and activate a virtual environment:
   ```powershell
   cd backend
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
   If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.
4. Edit `backend/.env` with your local PostgreSQL database credentials. Create the database and user in PostgreSQL first.
5. Run:
   ```powershell
   python manage.py check
   python manage.py migrate
   python manage.py runserver
   ```
6. In a second terminal, start the Expo app:
   ```powershell
   cd mobile
   npm install
   npx expo start
   ```
   Expo may generate/update platform-specific files on first run. Use the Expo Go app to scan the QR code, or press `a` if Android Studio/emulator is configured.

## macOS/Linux differences
Use `python3 -m venv .venv` and `source .venv/bin/activate`; copy env with `cp .env.example .env`. Install PostgreSQL and Node.js using your preferred package manager. Commands otherwise remain similar.

## Phase boundaries
- Phase 1: structure and configuration only.
- Phase 2: database models, migrations, and admin registration.
- Later phases add APIs, payment integrations, screens, deployment, and security hardening.

## Notes
- The app is designed as an open store: study levels and categories are discovery tags, not purchase restrictions.
- Do not put production secrets in source control.
- Razorpay, SMS OTP, push notifications, Cloudflare R2, and Railway credentials are configured in later phases.

## Reviewed Phase 1 corrections
- The delivered ZIP contains source only; create your own `.venv` and `.env` locally.
- `backend/.env.example` is the source for the PowerShell `Copy-Item .env.example .env` command after entering `backend`.
- The project opens directly at the ZIP root, without duplicate enclosing folders.
- Set a strong `DJANGO_SECRET_KEY` before deploying. Never use local settings in production.
- Phase 1 is a skeleton: product models, APIs, and real mobile flows are not implemented yet.
