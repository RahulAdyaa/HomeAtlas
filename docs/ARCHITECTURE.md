# HomeAtlas architecture and implementation checklist

## Decisions
Build in `homeatlas/`, preserving the unrelated attendance prototype. Next.js + TypeScript, Better Auth, React Three Fiber, PostgreSQL, private file storage locally / S3 in deployment, and a Python ingestion and retrieval worker. Native subagents are used; no ultragoal CLI is available. The Mac has 16 GiB unified memory and 10 CPU cores. Docker is installed but not running. A native PostgreSQL development profile avoids requiring Docker Desktop; Docker Compose remains the deployment-shaped setup. SQL-backed durable jobs use `FOR UPDATE SKIP LOCKED`, keeping queue claiming and credit settlement in one database transaction; Redis is reserved for deployment rate limiting, not required to run development. Never call a hosted model API.

## Flow
Browser → same-origin Next.js handlers → Better Auth session → household membership/role → PostgreSQL transaction. Upload → validate → private immutable original → version + credit reservation + queued job → Python worker → page/region or timestamp chunks + model embeddings → ready + charge, or failed + released reservation. Questions are authorized in Node, sent with a private service key to the Python worker and household scope, searched with tenant predicates before context assembly, and return evidence with immutable source-version IDs. All file and citation reads reauthorize membership.

## Permission model
Owner manages members and household; editor changes records/uploads/tasks; viewer reads and asks questions. Every ID is resolved inside the session household. Membership cannot be supplied by a browser claim. Sensitive account changes require recent password verification; Better Auth owns password hashing, session cookies, passkeys and TOTP. Invitations are expiring, hashed, single-use tokens. Originals are never public URLs. No confidential source text in routine logs. Retrieval documents are untrusted data, never instructions.

## Integration contract
GET `/api/atlas` returns `{user,household,membership,rooms,items,sources,tasks,activity,credits,members,bookmarks}`. POST `/api/atlas` accepts `{action,...fields}`. Actions: createHousehold, addRoom, addItem, updateItem, addTask, completeTask, invite, acceptInvite, updateMember, removeMember, bookmark, deleteHousehold. Sources upload POST `/api/sources` multipart `file`, optional `itemId`, `roomId`; retry POST `/api/sources/{id}/retry`; authorized original GET `/api/sources/{id}?version=...`. Questions POST `/api/ask` multipart `question`, optional `image`, `itemId`, `roomId`, `operationId`. Return `{answer,citations,confidence,mode,diagnostics?}`. Citation `{id,sourceId,versionId,title,page,bbox,text,start,end}`. Credits CSV GET `/api/credits/export`; export GET `/api/export`. API errors `{error}` with appropriate status.

Python `/health`, POST `/query` internal authenticated by `X-Worker-Key` and containing `{householdId,question,itemId?,roomId?,imagePath?}`. Node only passes privately validated paths. SQL schema will be finalized by backend owner and communicated to worker owner.

## Stages
- [x] Auth, household membership, real database and ledger
- [x] Records, uploads, genuine worker ingestion and citation access
- [x] Retrieval and self-hosted inference, missing-evidence abstention
- [x] Responsive UI, 3D home, accessible room list, evidence drawer
- [x] Tasks, credits, settings, exports and member management
- [x] Independent isolation/credit review and regression tests
- [x] Browser journeys, phone/desktop screenshots, production build
- [x] Setup, backup/restore, deployment, rollback and final capability report

## Final verified profile

The complete local core journey, independent isolation/accounting tests, production build/runtime smoke, and documented native startup passed on13 October2026. Production/deployment features and full model-profile limits are recorded separately in VERIFICATION.md; checked stages refer to this explicit local profile. Stored source versions and active evidence generations preserve old citations. The test Instruct tag is explicit, not the generic thinking alias.
