# HomeAtlas full-site audit

13 October 2026. This audit exercised the running local website, PostgreSQL, ingestion worker, Ollama, OCR and speech models. It used fictional accounts and original sample files. Existing user households were not modified. Disposable ingestion and deletion-test households were removed through the application.

## Bugs fixed

| Area | Failure | Repair and regression coverage |
| --- | --- | --- |
| Calendar dates | A reminder stored for 24 October displayed as 23 October in a browser west of UTC. | Date-only fields use local calendar dates; verified with an America/Los_Angeles browser. |
| Sending invitations | The sender's generated invitation URL also opened the recipient acceptance dialog. | Outgoing links and incoming invitation tokens have separate state. |
| Joining a household | Verification lost a new recipient's invitation; multi-household acceptance could choose the last household instead of the invited household. | Verification preserves the validated invitation token. Acceptance returns and opens the exact household ID. New and existing recipients tested. |
| Account boundaries | Questions, answers and selected records could remain in client memory across account changes. | Sign-out reloads the application; session expiry and household changes clear private state. Revoked household links fall back to an authorized household. |
| Password recovery | Reloading after a successful reset reopened the reset form because its used token remained in the URL. | Successful reset removes the token and reset flag. Reset, session revocation, new login and reload tested. |
| Voice questions | Recorded questions omitted the selected item filter. Microphone tracks could stay active after leaving the question screen. | Voice submission includes the item ID; navigation/unmount stops recording and releases tracks. Recording uses an appropriate M4A filename when the browser returns MP4 audio. |
| Saved questions and answers | Long question titles exceeded the bookmark limit; editing a question before saving its previous answer could attach the wrong question or item. | Titles are bounded; answers retain their submitted question and item. Viewers save private bookmarks without attempting a shared item-history write. |
| Role controls | Viewers were offered upload/reminder buttons and owner-only export links that would fail authorization. | Controls now match permissions. Server denial remains enforced and tested. |
| Populated notes | The notes textarea's existing content interfered with its exact accessible label. | An explicit Notes label works for editing existing records. |
| M4A uploads | Files declared as audio/x-m4a were rejected despite supported M4A contents. | Normalize the alias to audio/mp4 while retaining signature checks; verified with an actual converted M4A file and a malformed-file regression. |
| Answer status and reminder copy | Conflicting records were labelled as a normal grounded answer; reminder copy implied SMTP alone enabled scheduled delivery. | Conflicting evidence has an explicit status; reminder copy accurately describes in-app delivery. |

## Test evidence

| Suite | Coverage | Result |
| --- | --- | --- |
| Backend | Auth, reset, sessions, TOTP, recovery codes, role/tenant isolation, immutable sources, signature checks, idempotency, concurrency, credits/refunds, malicious worker output, local email | 57 tests passed |
| Python worker | Real PDF extraction/OCR, provenance, permissions, vector-space isolation, abstention, fabricated quotes, conflict handling and transactional queue publication | 17 tests passed |
| Expanded browser | Invitations, roles, inventory edits/search, voice scope/microphone lifecycle, bookmarks, recurrence/history, export, household switching, revocation, sign-out, reset, two-factor lifecycle and household deletion | 17 checks passed; zero browser exceptions |
| Ingestion audit | Unsupported files, corrupt PDF failure/refund, failed retry, corrected versions, idempotent reprocessing, original-version access, standalone image and scanned-PDF OCR, scoped retrieval, canonical citations/previews and ledger reconciliation | 9 checks passed |
| Core phone journey | Signup/verification, household/room/item creation, PDF ingestion, text/photo answers, citation page, bookmarks, reminders, credits, 3D and phone navigation | Passed; expected 85 credits and five settled charges |
| Multimodal media | Real WAV, MP4 and M4A ingestion, authenticated byte ranges, Whisper voice query and timestamped citations | Passed |
| RAG evaluation | Filter, warranty, reset instructions, missing evidence and photo question; canonical source/version/page/quote checks | 5/5 passed; supported answers used the real local model |
| Inference safety | Instructions embedded in source text and conflicting warranty evidence | 2/2 passed using the real local model |
| Passkeys | Browser WebAuthn registration and passwordless login with a virtual CTAP2 resident-key authenticator | Passed |
| Design/accessibility | Four viewport sizes, both themes, public motion/reduced motion, keyboard navigation, axe checks, app screens and evidence viewer | 142 checks passed; zero failures |
| Dependencies | npm audit | Zero reported vulnerabilities |
| Production | TypeScript, optimized build and exclusion of environment secrets/private data/model weights | Passed; standalone assets, health, access denial, disabled development verification, local fonts and hydrated signup dialog also passed |

The voice form regression intercepts the browser request only to inspect its item scope; it is explicitly a transport test. Actual transcription and timestamped RAG are independently tested in `media-check.mjs`. Adversarial backend tests deliberately simulate untrusted worker responses. The ordinary RAG/OCR/media evaluations use real local services.

## Reproducing the audit

Start the local services, then run from `homeatlas/`:

```sh
node --env-file=.env.local node_modules/vitest/vitest.mjs run
HOMEATLAS_DB_TESTS=1 worker/.venv/bin/python -m pytest tests/test_worker.py tests/test_worker_db.py -q
node scripts/journey-mobile.mjs
node scripts/feature-audit.mjs
node scripts/ingestion-audit.mjs
node scripts/media-check.mjs
node scripts/rag-evaluate.mjs
PYTHONPATH=. worker/.venv/bin/python scripts/inference-safety.py
node scripts/passkey-check.mjs
npm run qa
node scripts/fallback-check.mjs
npm run build
node --env-file=.env.local scripts/production-audit.mjs
npm audit --audit-level=high
```

Run the browser/data suites sequentially when reproducing them: the core journey creates the private fixture credentials/session that subsequent suites read. The feature audit creates additional fictional members and checks deletion only on its disposable member household. The ingestion audit generates its own scanned PDF from an original fixture and removes its disposable household. Detailed regression results are stored under ignored `.data/`.

## Limits

These results establish the tested local behavior; they cannot guarantee that every possible input, device or deployment is defect-free. The browser automation used Chromium, including phone-sized viewports, rather than physical iOS/Android devices. Physical biometrics and passkey syncing, external SMTP delivery, production HTTPS/origins, Docker boot, production/GPU deployment, long-media/load testing, multilingual accuracy and a large adversarial retrieval benchmark remain unverified. Automated email maintenance reminders remain unimplemented; reminders are in-app. See VERIFICATION.md and DEPLOYMENT.md for the existing scale/storage limits.
