# HomeAtlas independent security and credit review

Reviewed 11–13 October 2026 by an agent independent of the implementation agents. The review distinguishes executable tests from code inspection. It is not a penetration-test certification or a production-readiness claim.

## Threat model

An attacker can create an account and household, obtain another household's object IDs, tamper with request fields, use a viewer/editor account, upload hostile source content, replay operation IDs, and issue concurrent spending requests. Uploaded documents, filenames, extracted text, model responses, and client-supplied household IDs are untrusted. Database credentials, the worker shared key, and the host are trusted infrastructure credentials; compromise of those credentials is outside the application tenant boundary. Isolation uses server authorization, scoped SQL, and relational constraints; it does not depend on browser state.

## Executed evidence

On 13 October 2026:

```sh
npm test -- tests/security-ledger.test.ts tests/security-access.test.ts
```

**39 tests passed across 2 files, in 1.53 seconds.** These use actual PostgreSQL transactions and locks, actual Better Auth password sign-in and signed session cookies, actual route handlers, and private fixture files. Question transport tests use a deliberately controlled local HTTP server that returns adversarial worker responses. That server is **not a model or the Python ingestion worker**; these tests verify the Node authorization/accounting boundary, not inference quality.

| Area | Executed checks |
| --- | --- |
| Household isolation | Foreign household IDs supplied in query, explicit parameter, header, and JSON body are rejected. Foreign room/item/task IDs cannot mutate or link records. Other-household dashboard output excludes private IDs and evidence. |
| Roles | Viewer cannot modify records, upload, reprocess, invite, remove members, or write shared item history. Editor cannot administer membership. A household retains its last owner. Database role changes and removal take effect on the next request. |
| Private originals and citations | Foreign source, metadata, version, citation, and preview requests return 404. A valid household viewer can read the original and canonical citation. Source/version mismatch fails. Responses use private/no-store caching and omit private paths. |
| Bookmarks and exports | Viewer can save a personal bookmark, whose citations are reconstructed from authorized database rows. Browser-supplied citation text/path is discarded. Household export requires owner permission and excludes other-household data and storage paths. Credit CSV is scoped to the session household. |
| Sessions and CSRF | Missing/tampered signed sessions fail. Cross-origin, originless, and explicitly cross-site writes fail. An actual database session aged beyond 15 minutes requires successful password reauthentication. |
| Concurrent allowance | Twelve simultaneous requests costing 3 credits against an allowance of 10 produce exactly three reservations. Available/reserved amounts equal ledger deltas. |
| Idempotency | Concurrent duplicate reservations create one ledger reservation. Concurrent success/failure settlement produces one charge/refund. Retries cannot reuse an operation ID with a different actor, amount, kind, question, or scope. Operation IDs are household-scoped. Monthly grants are idempotent. |
| Ledger integrity | Non-positive amounts fail. Enclosing transaction rollback restores balances and removes reservation events. Individual ledger updates/deletes fail. Household deletion intentionally cascades household data, including its ledger. |
| Provenance constraints | Cross-household parent IDs fail. Same-household source/version mismatches fail for current versions, chunks, jobs, and image assets. |
| Question boundary | Forged scope is denied before worker invocation/reservation. Worker-supplied foreign citation IDs, fabricated quotes, and empty quotes are rejected and refunded. Concurrent replay does not invoke duplicate inference. Failure/cancellation refunds. Revocation during inference prevents returning source content. Viewer responses omit administrative diagnostics. |
| Stale recovery | A delayed response arriving after its reservation was reclaimed cannot publish a conversation or cached result. It returns 409 and retains the refund. |
| Error privacy | The fabricated-quote failure's captured general logs contain no fixture evidence, fabricated quote, session cookie, or worker key. |

Fixtures use fresh IDs and private temporary directories. Cleanup removes only fixture households/users, their rate-limit entries, and temporary files. Registration fixtures deliberately set `emailVerified` in PostgreSQL before sign-in. Therefore this suite does **not** establish email delivery or the end-user verification flow.

## Findings fixed and regression-tested

1. **Viewer could write shared item history through bookmarks.** The initial bookmark action accepted an item ID from a viewer and inserted into `maintenance_events`. The handler now rejects that operation with 403 while allowing personal bookmarks.
2. **Source/version provenance could be mismatched inside one household.** Separate household foreign keys did not bind a version to its source. Composite source/version constraints now enforce the complete relationship.
3. **Late answers could be published after stale credit recovery.** The handler previously ignored an unsuccessful settlement after another request refunded the reservation. It now requires successful settlement inside the same transaction as messages and cached results; otherwise the entire answer transaction rolls back.
4. **Empty quote passed substring verification.** An empty string was accepted by `includes`. Worker-response validation now requires at least eight quote characters, consistent with the Python evidence selector.

## Code inspection

- Python retrieval joins actor membership, household, source, and current version **before** selecting candidates for ranking/model context. It rechecks membership after inference.
- Python jobs check owner/editor membership before extraction and before publication. A claim token and row lock prevent a stale worker from publishing or settling a reclaimed job. Publication and settlement share a PostgreSQL transaction.
- The private worker requires a constant-time shared-key comparison. Upload and query paths are constrained to private storage. Originals use exclusive writes; source reads authorize household/source/version before opening a file.
- Model evidence is passed as untrusted data in a separate system/user message structure. The model selects source substrings; Python verifies those substrings before constructing an answer. Node reauthorizes the citation IDs and checks the quote again. This constrains fabricated citations; it is not proof that every malicious source instruction is harmless or that a quoted record is factually correct.
- Routine Node error logs include only an event, request ID, and error class. Worker job logs contain job IDs, counts/timing, and error class. Owners can inspect household diagnostics; general source text is not intentionally logged.
- Better Auth is configured for verified-email password access, password-reset session revocation, passkeys, TOTP, database rate limiting, HttpOnly/Lax cookies, and secure cookies when configured with HTTPS. No CSRF/origin checks are disabled.

## Limits and remaining verification

- This review's automated suite does not exercise physical passkey authenticators, TOTP recovery-code use, external SMTP delivery, browser-level cookie behavior under production TLS, or deployed object-store policy. Separate backend/browser verification should be read alongside this report.
- Synthetic worker responses are used solely to attack the server boundary. Real OCR/transcription, model inference, retrieval quality, and prompt-injection resistance need the worker/evaluation evidence; no score for those capabilities is inferred from these 39 tests.
- Worker claim recovery and ingestion refunds were inspected here but were not executed by this suite. The worker's own integration tests must provide that evidence.
- Production reverse-proxy request limits, transport security, service-key distribution, database privileges, backups/restores, monitoring, and external exposure were not exercised by these local tests.
