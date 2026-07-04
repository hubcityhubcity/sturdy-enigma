# Titan Clipper AI deployment checklist

This checklist turns the tested MVP into a production service. Complete the items in order; do not expose the app publicly while local-only storage or development defaults are still active.

## 1. Choose production services

- **Web hosting:** Deploy `apps/web` to a Next.js-capable host.
- **API and worker hosting:** Deploy `services/api` and `services/worker` to a container-capable host. The API and render worker must run as separate processes.
- **Database:** Use managed PostgreSQL instead of the default SQLite file.
- **Media storage:** Use durable object storage for uploads and rendered clips. Local disk is only appropriate for development.
- **Domain:** Point a custom domain at the web deployment and configure HTTPS.

## 2. Configure production environment variables

Set these values in the hosting provider’s secret/environment-variable interface, never in committed source files.

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/titan_clipper
NEXT_PUBLIC_API_BASE_URL=https://api.YOUR_DOMAIN/api/v1
TITAN_REQUIRE_WORKSPACE_KEY=true
TITAN_DEVELOPMENT_WORKSPACE_KEY=remove-or-replace-in-production
TRANSCRIPTION_PROVIDER=mock
WHISPER_MODEL=base
```

Use a real generated secret for any production workspace bootstrap or administrative process. Do not retain the local-development fallback key in a public environment.

## 3. Apply the database schema

From `services/api` with production `DATABASE_URL` configured:

```bash
alembic upgrade head
```

Confirm the application can create tables and that the API health endpoint responds before routing public traffic.

## 4. Configure allowed browser origins

Before public launch, configure FastAPI CORS to allow only the production web domain and approved preview domains. Do not use an unrestricted allow-all browser-origin setting with a credentialed production API.

## 5. Set up rendering dependencies

The API/worker environment needs:

- Python 3.11+
- FFmpeg and FFprobe
- Enough temporary disk space for source files and rendered clips
- A worker process that stays running and can access the same database and media storage as the API

## 6. Turn on billing only after payment setup

The app contains plan definitions and enforces workspace limits, but it does not charge customers yet.

Before enabling a paid upgrade button:

1. Create the payment-provider account.
2. Create the Creator and Studio products/prices.
3. Store the provider secret key and webhook secret in the host’s secret manager.
4. Implement a signed webhook that updates `plan_code` only after a verified payment/subscription event.
5. Add cancellation, failed-payment, refund, and downgrade handling.
6. Test with the provider’s sandbox before live mode.

Never let a browser request set a paid plan directly.

## 7. Pre-launch smoke test

After deployment, test a real non-sensitive media file end-to-end:

1. Open the web app from a phone and desktop browser.
2. Create a workspace and a project.
3. Upload a short source file with confirmed rights.
4. Confirm source validation, transcript generation, ranked candidates, and Titan Brain breakdowns.
5. Approve one candidate and create a render.
6. Verify the MP4, SRT, VTT, metadata, and publishing package download/open correctly.
7. Confirm free-plan source-minute and export limits return a clear message at the limit.
8. Confirm the render worker resumes correctly after a restart.
9. Review GitHub Actions for green API tests and web build.

## 8. Operational baseline

- Back up PostgreSQL on a schedule.
- Add object-storage lifecycle rules for abandoned source uploads and old render files.
- Add error tracking for the API, worker, and web app.
- Monitor render-job failure rate, queue depth, storage use, and monthly processing minutes.
- Rotate secrets and review access to hosting, database, and GitHub at regular intervals.

## Current code-release status

The current release branch has a passing API test suite and passing Next.js production build. Deployment, payment processing, production hosting, and public-domain ownership are external setup steps that require the owner’s accounts and credentials.
