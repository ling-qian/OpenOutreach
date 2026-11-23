# Acquisition Agent Web

The Web runtime is added alongside the original OpenOutreach CLI. The original `openoutreach` console command and `openoutreach.settings` are intentionally unchanged.

## Run locally

```bash
uv pip install -e ".[dev]"
export DJANGO_SECRET_KEY="replace-this-for-local-development"
python web_manage.py migrate
python web_manage.py createsuperuser
python web_manage.py runserver
```

Open http://127.0.0.1:8000/accounts/login/ and sign in. A workspace is created automatically for each authenticated user. Use /admin/ to manage sample companies, evidence and opportunities while discovery and research integrations are being connected.

## Architecture

- `webapp.settings` layers web middleware, sessions, authentication and templates over the original Django host settings.
- `webapp.core` owns Workspace, ServiceProfile, Company, Evidence, Opportunity and OutreachDraft.
- User-facing querysets are scoped to the authenticated user's workspace.
- The original CLI flow and OpenOutFind/OpenOutSend packages are not modified.
