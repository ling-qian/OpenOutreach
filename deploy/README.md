# Cloudflare Container deployment

This deployment runs Django and the OpenOutFind CLI in one Cloudflare Container. Django's
business database and each workspace's OpenOutFind database remain SQLite files under
`/data`. The Container filesystem is ephemeral, so the application restores a single
SQLite archive from R2 at startup and uploads a new archive after each successful
mutating HTTP request.

## Cloudflare resources

1. Create an R2 bucket, for example `acquisition-agent-state`.
2. Create an R2 API token with read/write access to that bucket.
3. Use a Workers Paid plan with Containers enabled.
4. Install Docker Desktop (or another working Docker daemon) and Node.js.

The Durable Object SQLite database declared in `wrangler.jsonc` is Cloudflare's
Container lifecycle state; it is not the Django database. Application SQLite files are
stored in R2 snapshots because Container disks are ephemeral.

## Install and configure

```bash
npm install
npx wrangler login
```

Set these Worker secrets. Do not commit them or paste them into source files:

```bash
npx wrangler secret put DJANGO_SECRET_KEY
npx wrangler secret put BOOTSTRAP_ADMIN_USERNAME
npx wrangler secret put BOOTSTRAP_ADMIN_EMAIL
npx wrangler secret put BOOTSTRAP_ADMIN_PASSWORD
npx wrangler secret put R2_ACCOUNT_ID
npx wrangler secret put R2_ACCESS_KEY_ID
npx wrangler secret put R2_SECRET_ACCESS_KEY
npx wrangler secret put R2_BUCKET_NAME
npx wrangler secret put OPENOUTFIND_BETTERCONTACT_API_KEY
npx wrangler secret put OPENOUTFIND_AI_MODEL
npx wrangler secret put OPENOUTFIND_LLM_API_KEY
```

The bootstrap administrator is created only if that username does not already exist.
Use a strong unique password and keep it in Cloudflare Secrets. The app does not expose
a public registration route in this MVP.

Optional settings:
- `DJANGO_ALLOWED_HOSTS`: comma-separated hosts; default allows `.workers.dev`.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated origins; default allows `https://*.workers.dev`.
- `OPENOUTFIND_LLM_API_BASE`: custom LLM API base URL.
- `R2_STATE_OBJECT_KEY`: archive object key; default `acquisition-agent/state.tar.gz`.

Deploy:

```bash
npx wrangler deploy
npx wrangler containers list
```

The first deployment builds and uploads the Docker image and may take several minutes.
Wait for the Container to become ready before testing the Worker URL.

## SQLite durability model and limits

- One named Durable Object routes all application requests to one Container.
- Gunicorn uses one synchronous worker so only one request mutates SQLite at a time.
- The R2 archive is uploaded after successful POST/PUT/PATCH/DELETE responses.
- A crash between a database commit and the completed R2 upload can lose the latest
  request's changes. This is request-boundary snapshotting, not synchronous write-through.
- R2 is object storage, not a shared filesystem or live SQLite volume. Do not run
  multiple independent Containers against the same archive.
- Before enabling multiple instances or concurrent background jobs, replace this
  single-container snapshot design with a transactional shared database or serialized
  storage service.

## Local development

For local development without R2 only, set `ALLOW_EPHEMERAL_SQLITE=true` and
`ACQUISITION_DATA_DIR=./var/local-data`. Never enable ephemeral mode in production.
