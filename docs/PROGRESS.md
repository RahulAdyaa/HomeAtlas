# Progress

- Repository and hardware inspected. Existing attendance code preserved.
- Native subagents + durable checklist chosen; no third-party agent installers used.
- Docker daemon unavailable initially; local PostgreSQL tools present.
- No application journey verified yet.

## 13 October continuation

- The saved browser journey exercised verified signup, household/room/item creation, two PDF uploads to ready, cited retrieval, bookmark, recurring reminder and 89-credit reconciliation. It failed final clean-browser check on a 3D HTML-label unmount exception. This is not yet a fully passed journey.
- Replaced DOM-mounted scene labels with canvas sprites; added all-room layout, item markers with equivalent buttons, keyboard rotation/reset, entry easing, demand rendering and reduced-motion behavior. Verification pending.
- 21st.dev, Dribbble, Drei and React Three Fiber references researched; original depth-card and restrained transitions added. See DESIGN_REFERENCES.md.
- TypeScript passed after integration fixes. First production build passed but emitted private-files tracing warnings; addressing before final packaging.
- Independent security suite currently 39 passed. Backend additionally exercised email verification/reset, TOTP and recovery via real auth handlers. Full combined rerun and report pending.

- Full phone journey passed cleanly: signup/verification, household, room/item, PDFs→ready, text/photo citations, missing-evidence abstention, bookmark, recurring reminder, ledger balance85, 3D repeated mount/unmount, mobile drawer/navigation and no horizontal overflow.
- Virtual WebAuthn registration and sign-in passed. Combined backend/security suite49 and isolated worker suite16 passed.
- Real local audio/video ingestion and byte-range access passed; local Whisper voice question returned timestamped citations.
- Native pg_dump/restore rehearsal passed in a disposable database; row counts and ledger reconciliation matched. Compose configuration validated; Docker daemon remains unavailable.
- Final production build compiled without warnings. Found Next standalone explicitly copies .env outside file tracing; added build sanitation and asserted deployment output excludes secrets/private data/model weights.
- RAG evaluation exposed that Ollama's generic qwen3-vl:4b tag is the thinking variant. Switching to explicit4b-instruct; final inference evaluation subsequently passed. Earlier fallback answers were labeled extractive and are not counted as successful instruct inference.

## Final verified state

- Explicit Qwen3-VL4B Instruct digest pinned; all5 scoped RAG cases passed in actual model mode for supported answers. Real hostile-instruction and conflict checks also passed.
- Final complete phone journey required model answers and passed with zero browser errors; registration through85-credit reconciliation exercised.
- Tests:49 Node/backend/security +17 Python worker passed. Final production build and standalone root/9 assets/health passed.
- Native one-command setup was exercised from stopped web/worker services; migrations/install/startup and API health passed.
- Screenshot and report index: VERIFICATION.md. Deployment limits: no tested Docker boot/SMTP/TLS/physical keys/full GPU profile; no MinIO/ANN indexes or unattended email reminders.

## Local signup clarification

- Replaced the inaccessible development-inbox notice with an **Open verification email** action. It requires the unverified account’s own password, captures only the fresh delivery for that request, and is disabled outside explicitly opted-in loopback development with no SMTP.
- Desktop and phone signup flows passed through the button into signed-in onboarding. Seven new security tests passed; full Node suite now56 tests in5 files. TypeScript and production build passed.

## Design implementation

- Applied design.md to the public page and authenticated product. Self-hosted Satoshi400/500, exact brand palette, asymmetric section types, pinned GSAP/Lenis evidence preview, geographic sample field and source-backed capability disclosures.
- Updated record screens, forms, sidebar, ledgers, source drawer, calendar and 3D materials. Fixed inherited low-contrast text, short-screen sidebar overflow, ledger focus, canvas/group roles, and expired-session feedback.
- Complete phone journey repeated successfully with actual local-model-grounded text/photo answers and abstention, working citations, reminders,85 credits and five settled charges. Backend56 tests passed. Final design/build evidence is recorded in DESIGN_QA.md.
