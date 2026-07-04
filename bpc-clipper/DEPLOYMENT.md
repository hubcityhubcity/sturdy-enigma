# Titan Clipper AI deployment checklist

This checklist turns the tested MVP into a production service. Complete the items in order; do not expose the app publicly while local-only storage or development defaults are still active.

## 1. Choose production services

- **Web hosting:** Deploy `apps/web` to a Next.js-capable host.
- **API and worker hosting:** Deploy the `services/api` container twice: once as the API and once with the `python render_worker.py` command. They must run as separate processes.
- **Database:** Use managed PostgreSQL instead of the default SQLite file.
- **Media storage:** Use durable object storage for uploads and rendered clips before running more than one API/worker machine. The included shared volume is suitable for a single-host deployment only.
- **Domain:** Point a custom domain at the web deployment and configure HTTPS.

## 2. Use the included production runtime stack

For a single-host launch, the repository now includes:

- `services/api/Dockerfile` — one FFmpeg-equipped image for both API and worker processes.
- `services/api/production_entrypoint.py` — strict configurable CORS for the deployed API.
- `services/api/render_worker.py` — persistent queue consumer for `render_export` jobs.
- `docker-compose.production.yml` — PostgreSQL, API, and render-worker services with shared media storage.
- `.env.production.example` — safe environment-variable template.

To run that stack on a server with Docker Compose:

```bash
cd bpc-clipper
cp .env.production.example .env.production
# Replace every placeholder in .env.production.
docker compose --env-file .env.production -f docker-compose.production.yml up --build -d
```

This starts the API at port `8000`. Place a reverse proxy or host load balancer in front of it for HTTPS and your API subdomain.

## 3. Configure production environment variables

Set these values in the hosting provider’s secret/environment-variable interface, never in committed source files.

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/titan_clipper
STORAGE_ROOT=/data/storage
NEXT_PUBLIC_API_BASE_URL=https://api.YOUR_DOMAIN/api/v1
ALLOWED_ORIGINS=https://app.YOUR_DOMAIN
TITAN_REQUIRE_WORKSPACE_KEY=true
TITAN_DEVELOPMENT_WORKSPACE_KEY=replace_with_a_long_random_workspace_secret
RENDER_WORKER_POLL_SECONDS=2
TRANSCRIPTION_PROVIDER=mock
WHISPER_MODEL=base
```

Use a real generated secret for any production workspace bootstrap or administrative process. Do not retain the local-development fallback key in a public environment.

## 4. Apply the database schema

The application creates its current SQLAlchemy tables automatically at startup. For a managed PostgreSQL deployment, run the API once against the production `DATABASE_URL`, then confirm the health endpoint responds before routing public traffic.

When schema migrations are introduced for a future release, apply them before deploying that release.

## 5. Configure allowed browser origins

Set `ALLOWED_ORIGINS` to the exact production web origin, for example `https://app.example.com`. For previews, add only the specific approved origins as a comma-separated list.

The production entrypoint rejects `*` because the API accepts credentialed browser requests. Do not bypass this safeguard.

## 6. Set up rendering dependencies

The supplied container image includes Python 3.11, FFmpeg, and FFprobe. The API and render worker must share:

- the same `DATABASE_URL`
- the same `STORAGE_ROOT` or durable object-storage implementation
- enough temporary disk space for source files and rendered clips

Start with **one** render-worker replica. The current queue claim is deliberately single-worker until distributed locking is added.

## 7. Turn on billing only after payment setup

The app contains plan definitions and enforces workspace limits, but it does not charge customers yet.

Before enabling a paid upgrade button:

1. Create the payment-provider account.
2. Create the Creator and Studio products/prices.
3. Store the provider secret key and webhook secret in the host’s secret manager.
4. Implement a signed webhook that updates `plan_code` only after a verified payment/subscription event.
5. Add cancellation, failed-payment, refund, and downgrade handling.
6. Test with the provider’s sandbox before live mode.

Never let a browser request set a paid plan directly.

## 8. Pre-launch smoke test

After deployment, test a real non-sensitive media file end-to-end:

1. Open the web app from a phone and desktop browser.
2. Create a workspace and a project.
3. Upload a short source file with confirmed rights.
4. Confirm source validation, transcript generation, ranked candidates, and Titan Brain breakdowns.
5. Approve one candidate and create a render.
6. Verify the MP4, SRT, VTT, metadata, and publishing package download/open correctly.
7. Confirm free-plan source-minute and export limits return a clear message at the limit.
8. Confirm the render worker resumes correctly after a restart.
9. Review GitHub Actions for green API tests, web build, and API container build.

## 9. Operational baseline

- Back up PostgreSQL on a schedule.
- Add object-storage lifecycle rules for abandoned source uploads and old render files.
- Add error tracking for the API, worker, and web app.
- Monitor render-job failure rate, queue depth, storage use, and monthly processing minutes.
- Rotate secrets and review access to hosting, database, and GitHub at regular intervals.

## Current code-release status

The code-release branch includes a passing API test suite, passing Next.js production build, and CI validation of the API/worker container image. Deployment, payment processing, production hosting, and public-domain ownership are external setup steps that require the owner’s accounts and credentials.
