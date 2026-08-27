# SecureHire Flask recruitment app

A complete dummy recruitment platform with Flask-Login authentication, role-based dashboards, Flask-SQLAlchemy models, CSRF-protected Flask-WTF forms, validated resume uploads, and Bootstrap 5 templates.

## Run locally

From `recruitment-site`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r flask_app\requirements.txt
$env:SECRET_KEY = "replace-with-a-long-random-value"
flask --app flask_app.app run --debug
```

The default development database is `sqlite:///securehire.db`, created in the Flask instance folder. For PostgreSQL, set `DATABASE_URL` before starting:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/securehire"
flask --app flask_app.app run
```

The app creates its tables and sample records on first start. Demo accounts:

- Admin: `admin@securehire.com` / `Admin123!`
- Recruiter: `recruiter@securehire.com` / `Recruiter123!`
- Tester: `tester@securehire.com` / `Tester123!`

## Routes

- `/`, `/jobs`, `/login`, `/register`, `/profile`
- `/admin`: user management, statistics, activity and alerts
- `/recruiter`: job posting, applications and interview scheduling
- `/tester`: test cases, vulnerability scan simulation and security reports

Resume files are stored outside the static directory with randomized names. In production, use HTTPS, a strong secret, PostgreSQL, a reverse proxy, a managed file store, and a real malware scanner before accepting uploads.
