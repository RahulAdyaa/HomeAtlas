# Design implementation verification

13 October 2026. Applied the governing [design language](../design.md) to the public page and authenticated application.

## Results

| Check | Result |
|---|---|
| `npm run qa` | PASS — 0 failures; 142 named checks |
| Responsive coverage | 390×844, 768×1024, 1024×900 and1440×1050 |
| Public page | All five disclosures, fixture labels, fonts, axe, overflow, skip link and light/dark auth dialogs |
| Motion | Exact300svh stage and x20%/scale0.6→centre/1; both ends at all four sizes; live reduced-motion teardown; no stranded reveals; exact count values restored when reduced motion changes during count-up |
| App | Eight screens in both themes; citation viewer; focusable credit history; mobile escape/focus; 3D keyboard controls |
| Browser errors/network | No unexpected errors in the final QA run |
| TypeScript and production build | Passed; standalone sanitizer excludes environment files, private data and model weights |
| Backend regression | 56 tests in5 files passed,2.00s |
| Complete phone flow | Actual account verification, household/room/item, PDF ingestion, text/photo answers, citations, bookmark, recurring reminder,85-credit/five-charge reconciliation and clean 3D mount/unmount |
| Actual inference modes | Supported text/photo answers: `local-model-grounded`; missing evidence: `abstention` |
| WebGL fallback | Disabled-WebGL, keyboard room selection and reduced-motion check passed |
| Standalone runtime | Hydrated landing, local fonts, disclosure, disabled production verification helper and zero browser exceptions passed on a temporary loopback port |
| Font preparation | Official Regular/Medium and license bytes preserved in an isolated clean-preparation check |

## Implemented visual system

Self-hosted Satoshi400/500; ink/blue/mint; retained type and spacing rules; asymmetric section shapes; exact source-backed product preview; geography derived from Natural Earth; restrained GSAP/Lenis motion; ruled inventory/library/credit rows; responsive forms and an evidence drawer; neutral 3D materials with one accent. Header actions remain available through the hero. Faded hero controls become inert, and reduced motion presents complete content in normal reading order.

Public figures, map pins and records are explicitly labelled original fictional examples. The public page keeps the prescribed branded tone alternation; its footer selects the authenticated app and auth-dialog theme. Household records remain private and server-authorised.

## Review images

- [Initial desktop hero](screenshots/redesign-motion-desktop.png), [phone hero](screenshots/redesign-motion-phone.png)
- [Full public page, desktop](screenshots/redesign-landing-desktop.png), [phone](screenshots/redesign-landing-phone.png)
- [Dashboard, desktop](screenshots/redesign-dashboard-desktop.png), [phone](screenshots/redesign-dashboard-phone.png)
- [Evidence, phone](screenshots/evidence-phone.png), [3D home](screenshots/home-3d-phone.png)

Run the original browser journey once to prepare its fictional account/session before `npm run qa`. Raw test credentials and detailed runtime reports remain only in ignored private `.data/`. These checks cover the enumerated local scenarios. Physical authenticators, public SMTP/TLS, Docker/GPU deployment and scale-storage verification limits remain in [VERIFICATION.md](VERIFICATION.md).
