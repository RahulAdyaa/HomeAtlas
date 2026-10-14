# Deployment and operations

## Profiles and capacity

Native development is intended for a trusted single machine. The inspected Mac has 16 GiB unified RAM, 10 CPU cores, Node 26, Python 3.12, PostgreSQL 15.17, FFmpeg and Tesseract. Local Ollama Qwen3-VL 4B is quantized; the smaller BGE embedding/reranker keep memory within this machine's capacity. SigLIP and Whisper can be disabled/unloaded for lower-resource operation. Exact measured models/latency appear in MODELS.md and RAG_EVALUATION.md.

For a recommended dedicated GPU profile, allow 24 GiB VRAM, 32–64 GiB host RAM, at least 50 GiB initial SSD headroom plus original-file/backup capacity, and separate worker processes. The full requested BGE-M3, reranker-v2-m3, Qwen3-VL 4B, SigLIP2 and PaddleOCR profile needs its own hardware verification before claiming a performance target. Model licenses do not pay for compute, storage, bandwidth or email. No hosted model-token bill is added by HomeAtlas. Local cost is electricity + storage/backup; a monthly estimate is `average measured watts × active hours / 1000 × local electricity tariff`. Cloud cost depends on GPU uptime and the selected provider; no unverified fixed-price estimate is asserted.

## Container setup

1. Create `.env` from `.env.example`. Generate separate high-entropy auth and worker secrets; replace the PostgreSQL password. Do not commit environment files.
2. Set `BETTER_AUTH_URL` to the final HTTPS origin; passkey RP ID and allowed origin derive from it. Set SMTP and `ALLOW_LOCAL_MAIL=false`.
3. Download pinned retrieval/Whisper weights on the host and pull the tested Ollama digest. The supplied profile mounts the HF cache read-only and a private files volume shared only by web/worker.
4. Run `docker compose up --build -d`. The web image applies migrations before serving. Worker database-health can be briefly unavailable until migrations finish; the durable job loop recovers.
5. Run a TLS reverse proxy to loopback port 3000. Enforce a 50 MiB request-body cap and 5-minute upload/query timeout. Keep database, worker8001 and Ollama11434 off the public internet.
6. Verify `/api/health`, real registration/email delivery, media authorization, job processing, inference diagnostics and cross-household tests at the deployed origin.

Use one Compose project for one trusted installation. Database superuser bootstrap must be replaced with a constrained application role for shared production operations; restrict migration privileges separately. The current schema enforces tenant foreign keys and handler predicates, not database RLS. Do not grant end users direct SQL or worker access.

## Private storage and scale

Originals live under `STORAGE_ROOT/originals/{household}/{source}/{version}`. Derived evidence and query attachments remain inside private storage; query media is removed after completion. Originals are opened only through authenticated handlers, with private/no-store headers, byte-range support, and canonical source/version checks. A private shared volume supports this deployment. S3/MinIO integration is not implemented and must not be advertised as active.

Household-bounded candidate sets use exact vector comparison and PostgreSQL lexical search. This avoids index-service complexity locally but caps retrieval to 10,000 candidate chunks per household. For large libraries, implement pgvector indexes with identical household/model/version filtering and evaluate recall; an image vector must never be compared with a text vector. Redis is not a required component of this implementation: durable jobs and rate limits use PostgreSQL. Multiple worker instances can claim jobs through row locks and leases.

## Logs and health

Node handlers return `X-Request-ID` and structured error events containing request ID and error class. Owner-only `/api/admin` shows this household's job failures, attempts, permissions, usage and audit entries. Worker logs contain job ID, outcome, count and timing, without source text. `/api/health` checks the database; private worker `/health` shows database/model availability. Model availability is not equivalent to end-to-end model quality.

Monitor queued age, failed/expired leases, reservation age, refunded operations, disk space, worker/model memory and query latency. Send internal infrastructure alerts through your normal monitor. The application has in-app reminders; unattended email maintenance reminders are not implemented. SMTP is used for auth/invitations only.

## Backups and restore

Back up database and private storage together while uploads/worker publication are stopped, or use a consistent snapshot with retained immutable versions. Encrypt and restrict backup access. Backups contain private records and auth information.

Native database example:

```sh
pg_dump -h 127.0.0.1 -p 54329 -U homeatlas -Fc homeatlas > homeatlas-backup.dump
# Copy .data/storage and .env.local into an encrypted backup through your backup tool.
```

For Compose, stop web/worker, dump with `docker compose exec -T db pg_dump -U homeatlas -Fc homeatlas`, and snapshot the `private-files` volume. Preserve the original absolute storage root (`/app/.data/storage`) on restore, because canonical paths are stored in the database. Keep migration/version identifiers with the backup.

Restore into a fresh isolated database using `pg_restore --no-owner`; restore private files and matching secrets; run the migration script; start worker/web; check counts, file hashes, old citations, membership and ledger reconciliation before allowing users. Never test restore by overwriting the only live database. Restore commands and schema rollback need rehearsal in the target deployment; current rehearsal evidence is in VERIFICATION.md.

## Rollback

Record the image digest, npm lockfile, model revisions/digests, schema migration list and backup at release time. Stop web/worker, restore the prior compatible web/worker images, and leave additive schema changes in place if backward compatible. For an incompatible schema change, restore the consistent database/private-files backup into a new stack and verify before switching traffic. Never delete original versions to roll back a retrieval index. Reindex creates new evidence generations while retaining old citation rows.

## Production gates

Local success does not establish public production readiness. Before exposure, validate SMTP/TLS, origin and physical passkey behavior, constrained DB role, resource/request limits, encrypted backups and restore, model revision pinning and resource exhaustion controls. Container boot, dedicated GPU/PaddleOCR profile, external SMTP, object-store policies, and scale indexing are separate verification work; record their status accurately.
