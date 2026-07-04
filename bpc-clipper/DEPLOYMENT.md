# Titan Clipper AI deployment checklist

This checklist turns the tested MVP into a production service. Complete the real-media validation gate in `VALIDATION.md` before creating a staging or public deployment.

## 1. Choose production services

- **Web hosting:** Deploy `apps/web` to a Next.js-capable host.
- **API and worker hosting:** Deploy the `services/api` container twice: once as the API and once with the `python render_worker.py` command. They must run as separate processes.
- **Database:** Use managed PostgreSQL instead of the default SQLite file.
- **Media storage:** Use durable object storage for uploads and rendered clips before running more than one API/worker machine. The included shared volume is suitable for a single-host deployment only.
- **Domain:** Point a custom domain at the web deployment and configure HTTPS.

## 2. Use the included production runtime stack

For a single-host launch, the repository includes:

- `services/api/Dockerfile` — one FFmpeg-equipped image for both API and worker processes.
- `services/api/production_entrypoint.py` — strict configurable CORS for the deployed API.
- `services/api/render_worker.py` — persistent queue consumer for `render_export` jobs.
- `docker-compose.production.yml` — PostgreSQL, API, render worker, and web app services with shared media storage.
- `.env.production.example` — non-secret environment-variable template.

To run that stack on a server with Docker Compose:

```bash
cd bpc-clipper
cp .env.production.example .env.production
# Replace every placeholder in .env.production.
docker compose --env-file .env.production -f docker-compose.production.yml up --build -d
```

This starts the API at port `8000` and the web app at port `3000`. Place a reverse proxy or host load balancer in front of them for HTTPS and your public domains.

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
TRANSCRIPTION_PROVIDER=whisper
WHISPER_MODEL=base
```

`TRANSCRIPTION_PROVIDER=mock` is reserved for explicit demo and developer tests. It must never be used to process a creator upload. An unconfigured provider now produces an honest configuration error instead of a fabricated transcript.

## 4. Configure real transcription before launch

The repository includes an optional local Whisper adapter in `requirements-whisper.txt`. Before setting `TRANSCRIPTION_PROVIDER=whisper`:

1. Install that optional dependency in the API and worker runtime.
2. Confirm the selected Whisper model can load in the deployed environment.
3. Run the real-media validation checklist using an owner-approved test clip.
4. Confirm transcript text matches the clip’s spoken words before allowing creator uploads.

## 5. Apply the database schema

The application creates its current SQLAlchemy tables automatically at startup. For a managed PostgreSQL deployment, run the API once against the production `DATABASE_URL`, then confirm the health endpoint responds before routing public traffic.

When schema migrations are introduced for a future release, apply them before deploying that release.

## 6. Configure allowed browser origins

Set `ALLOWED_ORIGINS` to the exact production web origin, for example `https://app.example.com`. For previews, add only the specific approved origins as a comma-separated list.

The production entrypoint rejects `*` because the API accepts credentialed browser requests. Do not bypass this safeguard.

## 7. Set up rendering dependencies

The supplied container image includes Python 3.11, FFmpeg, and FFprobe. The API and render worker must share:

- the same `DATABASE_URL`
- the same `STORAGE_ROOT` or durable object-storage implementation
- enough temporary disk space for source files and rendered clips

Start with **one** render-worker replica. The current queue claim is deliberately single-worker until distributed locking is added.

A creator export must end in a playable `.mp4`. Placeholder outputs are no longer reported as completed creator exports.

## 8. Turn on billing only after payment setup

The app contains plan definitions and enforces workspace limits, but it does not charge customers yet.

Before enabling a paid upgrade button:

1. Create the payment-provider account.
2. Create the Creator and Studio products/prices.
3. Store the provider secret key and webhook secret in the host’s secret manager.
4. Implement a signed webhook that updates `plan_code` only after a verified payment/subscription event.
5. Add cancellation, failed-payment, refund, and downgrade handling.
6. Test with the provider’s sandbox before live mode.

Never let a browser request set a paid plan directly.

## 9. Operational baseline

- Back up PostgreSQL on a schedule.
- Add object-storage lifecycle rules for abandoned source uploads and old render files.
- Add error tracking for the API, worker, and web app.
- Monitor render-job failure rate, queue depth, storage use, and monthly processing minutes.
- Rotate secrets and review access to hosting, database, and GitHub at regular intervals.

## Current code-release status

The deployment runtime is prepared but intentionally not the next step. Product validation with a real source, real transcript, and real MP4 export comes first.
