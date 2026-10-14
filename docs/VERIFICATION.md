# HomeAtlas verification and delivery report

13 October 2026. This is a working local application with explicit production/deployment limits below.

## Implemented

Next.js/TypeScript application with public landing, verified-email onboarding, household setup, rooms/items, real private uploads and asynchronous ingestion states/retry/new versions, question workspace with text/photo/voice inputs, canonical page-region and timestamp citations, bookmarks/saved searches, item history, recurring tasks/calendar, household credit ledger/CSV export, members/invitations/roles, settings/passkeys/TOTP/sessions, owner processing/audit views, household JSON export and deletion. The lazy 3D home has original furniture, room/item selection, keyboard controls, static WebGL fallback, reduced-motion support and an equivalent room/item list. Light/dark and phone/desktop layouts are implemented.

Migrations, Node/Python tests, locked dependencies, local startup, Compose/Dockerfiles, architecture, security, model/evaluation records and deployment/backup/rollback guides are in the repository. The unrelated parent attendance project remains separate.

## Exercised journeys and commands

| Check | Command/evidence | Result |
| --- | --- | --- |
| TypeScript | `npm run typecheck` | Passed |
| Backend/auth/source/isolation/credits | `node --env-file=.env.local node_modules/vitest/vitest.mjs run` | 56 tests in5 files passed; latest combined run2.00s |
| Worker OCR/PDF/permissions/credit publication | `HOMEATLAS_DB_TESTS=1 worker/.venv/bin/python -m pytest tests/test_worker.py tests/test_worker_db.py -q` | 17 tests passed; final0.65s; PyMuPDF emitted upstream SWIG deprecation warnings |
| Isolated dependency set | `worker/.venv/bin/python -m pip check` | No broken requirements; virtual environment does not inherit global packages |
| Browser core journey | `node scripts/journey-mobile.mjs` | Full phone journey passed, including signup/real local email link, household/room/appliance, manual+receipt→ready, cited text/photo answers, zero-evidence abstention, bookmark, reminder and85-credit reconciliation; final model-required phone rerun also passed with zero browser errors |
| Design QA | `npm run qa` | See DESIGN_QA.md for the current four-viewport, light/dark, motion/font/axe/keyboard and source-viewer gate |
| Local verification button | `node scripts/local-email-check.mjs` + seven development-email tests | Desktop1440px and phone390px signup → password-checked local verification → signed-in onboarding passed; wrong/other-account passwords, cross-site requests, production/SMTP/host restrictions, concurrent delivery isolation and verified-account rejection passed |
| Passkeys | `node scripts/passkey-check.mjs` | Actual browser WebAuthn registration and passwordless sign-in passed using virtual CTAP2 resident-key authenticator |
| Authentication lifecycle | Included backend-auth tests | Verification, one-use password reset/revocation, other-session revocation, TOTP challenge and one-use recovery codes passed through real handlers and database |
| WebGL/keyboard fallback | `node scripts/fallback-check.mjs` | Disabled WebGL, keyboard room selection and reduced motion passed |
| Screenshots | `node scripts/capture-screens.mjs` | Main screens at1440×1050 and390×844, no horizontal overflow or browser errors |
| Real multimodal media | `node scripts/media-check.mjs` | Original7-second spoken note/video→ready, authorized byte ranges206, local Whisper transcription and timestamped citations passed |
| RAG | `node scripts/rag-evaluate.mjs` | 5/5 scoped cases passed with real Instruct model for supported answers; source recall4/4, exact canonical citation checks5/5; see evaluation limits |
| Inference safety | `PYTHONPATH=. worker/.venv/bin/python scripts/inference-safety.py` | Actual local source-instruction/conflict cases passed |
| Startup | Stop owned web/worker, `npm run setup` | Locked JS/Python installation, migrations and localhost startup passed; `/api/health` returned database/worker ok |
| Database backup/restore | `bash scripts/backup-check.sh` | Disposable restored database matched household/member/source/version/chunk/credit rows and ledger deltas; test database removed |
| Compose | `docker compose config --quiet` | Configuration validation passed |
| Production artifact | `npm run build` | Passed; sanitizer verifies standalone excludes environment files/private data/model weights |
| Production server | `node scripts/production-smoke.mjs` | Standalone root,9 JS/CSS assets and database/worker health passed at localhost3100; public TLS/auth-origin deployment remains unverified |

The independent review found and regression-tested four issues: viewer history write, source/version mismatch, late answer after credit refund, and empty quote acceptance. See SECURITY_REVIEW.md. Actual device/system processes, database and local-model calls were used where reported; the Node adversarial-worker tests are clearly identified as synthetic transport-boundary tests.

## Screenshots

- [Desktop dashboard](screenshots/dashboard-desktop.png), [phone dashboard](screenshots/dashboard-phone.png)
- [Desktop home view](screenshots/home-desktop.png), [phone home view](screenshots/home-phone.png)
- [Desktop library](screenshots/library-desktop.png), [phone library](screenshots/library-phone.png)
- [Desktop evidence](screenshots/evidence-desktop.png), [phone evidence](screenshots/evidence-phone.png)
- [Desktop inventory](screenshots/inventory-desktop.png), [phone inventory](screenshots/inventory-phone.png)
- [Desktop maintenance](screenshots/maintenance-desktop.png), [phone maintenance](screenshots/maintenance-phone.png)
- [Desktop credits](screenshots/credits-desktop.png), [phone credits](screenshots/credits-phone.png)
- [Desktop settings](screenshots/settings-desktop.png), [phone settings](screenshots/settings-phone.png)
- [Landing](screenshots/landing-desktop.png), [phone landing](screenshots/landing-phone.png)

These are actual application screenshots with original sample records. Credits change as additional evaluation requests are charged, so later screenshots may show a different correct balance from the initial85-credit journey assertion.

## Exact models and hardware

The tested profile uses Qwen3-VL4B **Instruct** Q4_K_M, BGE-small-en-v1.5, BGE-reranker-base, SigLIP2-base-patch16-224, Whisper-tiny and Tesseract. Digests, HF revisions, licenses and runtime versions are in MODELS.md. The original generic4b Ollama tag was the thinking variant; it was replaced with explicit Instruct after evaluation. The 16 GiB/10-core Mac runs this lower-resource profile. Full BGE-M3/reranker-v2-m3/PaddleOCR and dedicated24GiB GPU configuration remain unverified. Operating-cost assumptions and capacity guidance are in DEPLOYMENT.md; no paid model API or payment provider is used.

## Tools and design provenance

Used native subagents with disjoint file ownership and independent security review, durable architecture/progress checklist, native goal tracking until usage-limited, npm/Python tools, local PostgreSQL/Ollama/FFmpeg/Tesseract, Playwright, browser preview and web research. No invented Ultraagent/Oh My Codex workflow ran. Code-review graph tools were not callable; no third-party agent installer was added to the application.

The Sites skill's local preview guidance was used; self-hosted services run in the requested local repository. 21st.dev's3D component collection and performance guidance informed original depth-card/hover treatments. Dribbble was an isometric-design reference. MIT Three.js/R3F/Drei components supply rendering and controls; no copied Dribbble art or premium21st template is bundled. See DESIGN_REFERENCES.md and THIRD_PARTY_NOTICES.md.

## Incomplete or unverified

- External SMTP, production HTTPS cookies/origins, physical biometrics/hardware keys and cross-device passkey syncing were not exercised. Local verification/reset/invitation email is real private spool delivery.
- Docker daemon was unavailable. Compose parses, but complete container build/boot and production/GPU deployment were not exercised.
- MinIO/S3 storage and pgvector ANN indexes are not implemented. The documented local/deployment profile uses a private shared volume, PostgreSQL leased queue/rate limits, and household-bounded exact vectors. This is a deliberate local-resource decision and a scale/deployment limit.
- Unattended email maintenance reminders are not implemented; reminders and recurring schedules are in-app. SMTP auth/invitation delivery is configurable.
- Full BGE-M3/reranker-v2-m3/PaddleOCR, arbitrary damaged-part matching, multilingual accuracy, long-video/load limits and a broad adversarial RAG benchmark remain unverified.
- Database restore was rehearsed; a fresh-host encrypted private-file/secret restore was documented but not independently rehearsed.

These limits prevent a public production-readiness claim. The core local success journey and isolation/accounting checks are verified; deployment gates must be exercised on the intended host.

## Design implementation continuation

The new `design.md` language is applied to the public landing and authenticated screens: Satoshi, ink/blue/mint, asymmetric layout, pinned evidence preview, source-backed sample panels, ruled records and responsive forms/ledgers. The complete phone journey was repeated after this redesign and passed with local-model-grounded text and photo answers, explicit abstention, exact page previews, reminders and an85-credit/five-charge reconciliation. All56 backend tests and the production build passed. Current design-specific evidence is in DESIGN_QA.md.

## Full-site regression audit

The subsequent full-site audit fixed invitation, calendar, account-state, recovery, voice-scope, bookmark and permission-control defects. It added 17 browser feature checks and 9 live ingestion checks, plus an M4A signature regression. See [FULL_SITE_AUDIT.md](FULL_SITE_AUDIT.md) for current results, reproducible commands and remaining limits.
