# Acquisition Agent Web

A web runtime added alongside the original OpenOutreach CLI. The CLI entrypoint and its settings remain unchanged.

## Run locally

```bash
uv pip install -e ".[dev]"
export DJANGO_SETTINGS_MODULE=webapp.settings
export DJANGO_SECRET_KEY="replace-this-for-local-development"
python web_manage.py migrate
python web_manage.py createsuperuser
python web_manage.py runserver
```

Open http://127.0.0.1:8000/admin/ to create a user, then create a Workspace in Django shell or admin (admin registration is the next small task).

## Architecture

- Existing `openoutreach.settings` remains the CLI host configuration.
- `webapp.settings` adds sessions, auth middleware, templates and the product web app.
- `webapp.core` owns SaaS-facing Workspace, ServiceProfile, Company, Evidence, Opportunity and OutreachDraft records.
- The initial release intentionally does not change OpenOutFind/OpenOutSend packages or the original CLI flow.
