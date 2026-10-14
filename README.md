# HomeAtlas

A private, responsive home-records application built with Next.js, TypeScript, Better Auth, PostgreSQL, React Three Fiber, and a local Python ingestion/retrieval service. HomeAtlas lives in this directory; the parent repository's attendance prototype is separate.

## Local setup

Prerequisites: Node 22.16+ (tested with Node 26), npm, Python 3.12, PostgreSQL 15+, FFmpeg/FFprobe, Tesseract, and a running Ollama service. The application binds to loopback by default. The native development database has a distinct port/data directory and uses loopback-only trust authentication; do not expose this development configuration on a network.

From `homeatlas/`:

```sh
npm run setup
```

The setup initializes the isolated database at port 54329 if needed, generates private local secrets, installs the locked JS/Python dependencies, applies Better Auth and application migrations, and starts the worker and website. Open http://localhost:3000. The first dev/build run prepares Satoshi webfonts from the official Fontshare source when absent, then serves them locally. The script preserves existing data and `.env.local`. Stop the foreground command with Ctrl+C; PostgreSQL persists. Stop the owned database separately with `pg_ctl -D .data/postgres stop` when needed.

For genuine neural retrieval, local vision inference and transcription, explicitly download the free model artifacts once:

```sh
bash scripts/models.sh
```

Models consume several GB of disk and RAM. Missing local models do not trigger hosted inference. The worker reports the available components and uses explicit extractive evidence or abstention when it cannot ground an answer. See [models](docs/MODELS.md) for pinned artifacts, licenses, tested profile, and GPU profile.

### Development email

Registration requires verified email. In the local development setup, enter your account email and password on the sign-in form, then click **Open verification email**. The button checks your password and opens a fresh verification link for your own unverified account. It is available only in development on loopback, with `ALLOW_LOCAL_MAIL=true` and no SMTP configured; it is disabled in production. Verification/reset/invitation messages remain private JSON files in `.data/mail/`. Do not commit or expose this directory. To deliver real email, configure the SMTP variables from `.env.example`. `ALLOW_LOCAL_MAIL=true` allows local spool delivery during a production-build smoke test; real deployment must use SMTP and set it to false.

### Original test records

`tests/fixtures/` contains two clearly fictional, original CC0 AirOne appliance PDFs and a page scan. Upload these to an item to exercise the manual/receipt journey. They are not manuals or repair advice for any real appliance. `scripts/create-fixtures.py` reproduces them.

## Verification

```sh
npm run typecheck
node --env-file=.env.local --import tsx scripts/backend-migrate.ts
node --env-file=.env.local node_modules/vitest/vitest.mjs run
HOMEATLAS_DB_TESTS=1 worker/.venv/bin/python -m pytest tests/test_worker.py tests/test_worker_db.py
npm run build
node scripts/journey.mjs
node scripts/journey-mobile.mjs
npm run qa
node scripts/passkey-check.mjs
```

The design QA command uses the fictional account/session produced by the browser journey above and refreshes that fixture once before its app checks. It audits four viewports, both app themes, fonts, axe accessibility, keyboard access, placeholder labels, WebGL controls and motion states.

Browser checks require installed Playwright Chromium. Set `PLAYWRIGHT_EXECUTABLE_PATH` if using an existing compatible Chrome binary; otherwise run `npx playwright install chromium` and omit the override. Local browser scripts create isolated test accounts/households using original sample documents. Their credentials/session files go only into ignored `.data/`. They never email a real external recipient. The virtual-authenticator test exercises WebAuthn protocol, not physical-device syncing.

The latest full-site audit and fixes are in [FULL_SITE_AUDIT.md](docs/FULL_SITE_AUDIT.md). The repeatable expanded checks are `node scripts/feature-audit.mjs` and `node scripts/ingestion-audit.mjs`, after running the browser journey.

Detailed exercised results and remaining limitations are in [verification](docs/VERIFICATION.md), [security review](docs/SECURITY_REVIEW.md), and [RAG evaluation](docs/RAG_EVALUATION.md). Screenshots live in `docs/screenshots/`.

## Data and inference

Uploads are signature/type/size checked, stored as private immutable originals, queued in PostgreSQL, and processed asynchronously. PDFs retain page and region coordinates; OCR scans/photos retain provenance; local Whisper produces timestamped audio/video segments; FFmpeg samples video frames. Citation opening always rechecks household membership and source/version IDs.

Retrieval filters by household and permissions before assembling candidates. Lexical and local text-vector search are fused/reranked; image vectors occupy a separate compatible space. Local Qwen produces evidence-reviewed explanations with verified quotations and supporting PDF page images. A second model pass reviews each section; see [detailed answers](docs/DETAILED_ANSWERS.md) for the limits of visual interpretation. Answers without adequate evidence abstain. Hazardous-work queries recommend a qualified professional.

Household owners manage membership, editors organize records, and viewers read/ask/save private bookmarks. No public file URLs exist. Application authorization and tenant foreign keys provide isolation; the application database role is a trusted service credential. A database-superuser or host compromise is outside that boundary.

Credits are internal allowances. The server reserves credits atomically before work and settles a charge/refund once; an append-only ledger records balance/reservation deltas. Prices and monthly grants are environment-configurable. There is no payment service.

## Architecture and operations

- [Architecture, data flow and checklist](docs/ARCHITECTURE.md)
- [Design language and screen requirements](design.md)
- [Design references and asset provenance](docs/DESIGN_REFERENCES.md)
- [Deployment, backup/restore and rollback](docs/DEPLOYMENT.md)
- [Progress and unresolved work](docs/PROGRESS.md)

Docker Compose is included. Copy `.env.example` to `.env`, replace every secret placeholder, and configure SMTP, then use `docker compose up --build`. PostgreSQL/worker stay on the private Compose network; only loopback port 3000 is published. Ollama runs on the host in this profile, and pinned HF artifacts are mounted read-only. Use an HTTPS reverse proxy for deployment. The current Docker runtime verification status is recorded in `docs/VERIFICATION.md`.

## Important implementation choices

The local profile uses a PostgreSQL durable queue with leased claims and atomic credit publication, private filesystem volumes, and household-bounded vector arrays. These make genuine development possible on the inspected 16 GiB Mac without requiring a Docker daemon, Redis, or MinIO. Queue claims use `FOR UPDATE SKIP LOCKED`; vectors are never mixed across model revisions or text/image spaces. Scale requires pgvector indexed search and object-storage integration; the Compose database image supports pgvector, but the current application does not claim to use ANN indexes or MinIO. See deployment limitations before sharing the service outside a single trusted host.

No paid or hosted model APIs, payment providers, third-party agent installers, or end-user agent tools are required.
