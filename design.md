# HomeAtlas — Design Language

The governing document for HomeAtlas's public landing page and authenticated
product. Every visual decision answers to it.

The supplied `design (1).md` is the visual baseline. Its composition, type,
colour, surface, motion and accessibility rules are retained. This adaptation
changes the product, audience, copy, examples, screen requirements and defect
inventory to HomeAtlas.

`docs/ARCHITECTURE.md` describes the actual data flow and permissions.
`docs/VERIFICATION.md` records exercised functionality and deployment limits.
`docs/DESIGN_REFERENCES.md` records earlier references and asset provenance;
its cream/sage and serif direction describes the previous implementation,
not the visual target governed by this file. The historical measurement file
mentioned in the supplied reference is not present in this repository. Its
quoted visual values are retained here, not presented as new measurements.

Read this before writing a component. If a change conflicts with something
here, the change is wrong or this file needs a deliberate amendment — not a
quiet exception.

This is a design contract for the redesign. It does not claim that the current
interface already implements these rules. Current mismatches are in §9.5.

---

## 1. The thesis

**HomeAtlas turns the records of a home into answers someone can act on.**
The site has to look like a private product people use to find a manual,
check a warranty and remember maintenance. The evidence is the product.

That means three commitments:

1. **Evidence over adjectives.** A document page, a dated receipt, a transcript
   timestamp or a named item beats any sentence containing "cutting-edge",
   "seamless", or "leverage".
2. **Precision over polish.** Hairlines, real units, correct alignment. Not
   glow, not gradient, not bloom.
3. **Confidence over completeness.** Say less. A page that explains everything
   is a page nobody finished reading.

The reader is a renter, homeowner or household member who is **not deeply
technical** but needs to trust the details. They may be looking for a filter
number on a phone, checking a receipt while speaking to a repairer, or finding
what a contractor said. Write for them: plain sentences carrying concrete
nouns. Keep "PDF page", "source version", "transcript timestamp", "passkey"
and "credit reservation" when they help someone understand a result or a
choice. Explain an unfamiliar term once, then trust the reader.

The first impression must communicate three things: records belong to a home,
answers open their supporting source, and the household controls access.
Self-hosted inference supports that promise. It is not the headline.

---

## 2. Why the current site reads as machine-made

This section exists because "make it look less AI-generated" is unactionable.
These are the specific tells, each with the rule that replaces it. **These are
the most important rules in this document.**

### 2.1 Everything is evenly distributed

Three equal cards. Four equal stats. Equal padding on all four sides of
everything. Every gap `gap-6`.

Machines default to uniform because uniform is the average of all layouts.
Designers make one thing bigger because one thing matters more.

> **Rule — one focal point.** Every section has exactly one element that is
> clearly the most important, and it is bigger, denser, or differently
> coloured than its neighbours. If you can shuffle a section's children
> without anyone noticing, the section has no hierarchy.

> **Rule — asymmetric splits.** Two-column layouts are `7/5`, `8/4` or `5/7`.
> Never `6/6`. Three-across grids need one cell that spans differently, or
> they need to not be a three-across grid.

### 2.2 Decoration that encodes nothing

A bar chart where the bars rise because rising looks good. A squiggle in a
rounded grey box. A network graph of nothing connected to nothing.

This is the single loudest tell on the page. A real chart is *shaped by data*;
an invented one is shaped by taste, and it reads as fake instantly to anyone
who has looked at a real one.

> **Rule — no graphic ships unless it encodes something true.** Every plotted
> point, bar and line comes from a named array in the file with a comment
> saying what the numbers are. If you cannot say what the y-axis measures, the
> graphic does not ship. Delete it and use whitespace.

> **Corollary.** Real data is *ugly*. It has outliers, flat stretches, and
> noise. A monotonically rising line is a lie. Put the outlier in and annotate
> it — the annotation is what makes it look real.

### 2.3 Every section is the same shape

Eyebrow → two-tone heading → grid of cards. Fourteen times.

> **Rule — four section shapes, and no two adjacent sections share one.**
>
> | Shape | Use |
> |---|---|
> | **Statement** | Type only, wide measure, heavy whitespace. Mission, manifesto. |
> | **Split** | Copy one side, one instrument the other. Capabilities, document evidence. |
> | **Ledger** | Dense rows or a table. Maintenance, credit history, comparisons. |
> | **Field** | Full-bleed graphic with figures over it. Stats, map, marquee. |

### 2.4 Uniform texture

Same radius, same border, same `white/10`, same blur, everywhere. The eye
finds no edge to rest on, so the whole page reads as one flat surface.

> **Rule — three surface levels only, and they must differ by more than
> opacity.** Base (the section tone), raised (a real border + a real shift in
> background), and inset (a rule above/below, no box at all). Most things
> should be **inset** — boxes are expensive and we spend them badly.

> **Rule — stop drawing boxes.** A hairline rule and correct spacing separates
> content better than a border does. If a card has a border, a background, a
> radius, a shadow *and* a blur, remove three.

### 2.5 Effects stacked as a substitute for craft

Blur plus glow plus gradient plus parallax on one element.

> **Rule — one effect per element.** Pick the one doing the work. A card that
> lifts on hover does not also glow. A panel with a gradient edge does not also
> have a shadow.

### 2.6 Copy with no variance

Every heading six words. Every card body two lines. Every sentence the same
length. This is the textual equivalent of the even grid, and it is the fastest
way to be identified as generated prose.

> **Rule — vary sentence length deliberately.** A four-word sentence next to a
> twenty-word one. Fragments are allowed. Read it aloud; if it has a metronome
> rhythm, rewrite it.

> **Rule — no em-dash pile-ups.** At most one em-dash per paragraph. The
> construction "X — the thing that Y — Z" is a verbal tic and it is everywhere
> in the current copy.

> **Banned words.** seamless, leverage, robust, cutting-edge, holistic,
> empower, unlock, elevate, journey, solutions, best-in-class, transform (as an
> intransitive boast), "in today's fast-paced".

### 2.7 Placeholder content presented as real

Invented household or product metrics do more damage than missing ones — the
moment a reader suspects one number, every number is suspect.

> **Rule.** Anything not verifiably HomeAtlas's is wrapped in `<Placeholder>` /
> `<PlaceholderValue>` and carries `data-placeholder`. The marker is quiet: a
> footnote in small type, never a dashed box. The register lives in
> §9.8 of this file. Original fictional fixtures also carry a quiet demo label;
> owning the asset does not make it a real household record.

---

## 3. Composition

**Container.** Max 1344px, gutters 24px / 40px at `lg`. Dashed blueprint
guides at the container edges run the full page height.

**Vertical rhythm.** Sections are `py-24 lg:py-32`. Two exceptions worth
making: a Statement section gets `py-32 lg:py-40` (whitespace is the design),
and a Field section can go edge-to-edge with no vertical padding at all.

**Tone alternation.** `ink → white → paper → ink`. Two same-tone sections must
never touch — the doubled padding reads as one dead stretch. Components that
appear on multiple pages take a `tone` prop for exactly this reason.

**The measure.** Body copy never exceeds ~65 characters. Headings never exceed
~30 characters per line. A heading running four lines is a bug.

---

## 4. Type

One family — **Satoshi**, asking for `"Armin Grotesk"` first so dropping the
licensed pair into `public/fonts/` upgrades the site with no code change.
Weights 400 and 500. **No mono. No serif.** Uppercase mono labels were the
single strongest template tell on the first build and are permanently banned;
use 14px sans instead.

| Role | Size | Line-height | Tracking |
|---|---|---|---|
| Display (hero h1) | 56–64px | 1.15 | −0.015em |
| Statement (mission) | 40px | 1.25 | −0.015em |
| Section heading | 56px | 1.2 | −0.015em |
| h3 large | 28px | 1.4 | −0.005em |
| Lead | 18px | 1.4 | — |
| Body | 16px | 1.4 | — |
| Eyebrow / small | 14px | 1.4 | — |

**The two-tone heading.** A full-colour lead clause followed by a support
clause at `opacity: .4`, inline, reading as one sentence. It only works when
the dim half is **one short clause**. A support string that wraps past two
lines is a bug — cut it, don't shrink it.

**Numerals.** Always `tabular-nums`. A stat that reflows while counting up is
the cheapest possible mistake.

---

## 5. Colour

| Token | Hex | Role |
|---|---|---|
| `ink` | `#09122A` | Dark section base; primary text on light |
| `slate` | `#222A3F` | Raised surface on ink |
| `blue` | `#3559C7` | Primary action; stat numerals on light |
| `mint` | `#5EDD78` | Accent on dark only |
| `muted` | `#6B717F` | Secondary text on light |
| `line` | `#E6E7EA` | Hairline on light |
| `paper` | `#F8FAFC` | Alternate light base |

Two contrast facts that constrain real decisions:

- **`mint` on white is 1.9:1.** It is a dark-section accent and nothing else.
  On ink it is 10.5:1 and is the only accent permitted to carry a numeral.
- **`blue` on ink is 3.1:1.** It is a *graphic* accent on dark — strokes,
  fills, bands. It may never carry text on ink. On white it is 7.4:1 and is
  the correct colour for a stat numeral.
- Dim text on ink bottoms out at `white/50` (5.4:1). Below that it fails AA
  even inside an `aria-hidden` subtree, because axe judges rendered pixels.

**One accent per graphic.** Everything else is a hairline. A chart using blue
*and* mint *and* amber is decoration; a chart using hairlines and one mint line
is an instrument.

---

## 6. Motion

**One signature move per page.** On the homepage that is the pinned hero. Every
other animation is support and must be quieter than it. When something new
wants to be impressive, the answer is almost always no.

**The hero** (visual values retained verbatim from the supplied design
reference; do not tidy them): a 300svh stage wrapping a sticky 100vh viewport, one scrubbed
timeline sliding the device from `x:20%, scale .6` to centre and full size
while the chassis dissolves and the copy blurs out.

**The reveal**: `y 16→0`, `opacity 0→1`, `blur(12px)→0`, 0.4s `power2.out`,
trigger `top 75%`, `toggleActions: play none none none`. We deliberately drop
the reference's `reverse` — un-revealing on scroll-up is a nervous tic.

**The scrub**: exactly one on the site, on the mission text. Per-word
`opacity .2 → 1`, `ease: none`, scrubbed. No blur, no colour change.

**Count-up**: ~1.4s `power2.out` on section enter, measured from the reference
recording. Lands on the authored string so the final value is exact.

**Hard constraints.**

- Transform, opacity and filter only. Never animate layout.
- Everything stops under `prefers-reduced-motion`, and stops in its **final**
  state — never blank, never half-drawn.
- Nothing between `<body>` and the hero may set `overflow` to anything but
  `clip`. `hidden` makes the ancestor the sticky scroll container and the
  entire pinned sequence silently dies.
- Lenis must stay wired into GSAP's ticker with `ScrollTrigger.update`, or the
  scrubbed hero lags the page and everything feels rubbery.

---

## 7. Voice

Short declaratives. Concrete nouns. No hedging.

- **Say the constraint.** "The manual names one replacement filter. Page 2."
  beats "Our intelligent assistant provides actionable appliance insights."
- **Say what the record cannot establish.** "No warranty receipt is stored for
  this item" tells someone what to add next. Missing evidence is a visible
  result, not a confident guess.
- **Name the thing.** "A200-HEPA replacement filter", "12 February 2028",
  "kitchen tap recording, 00:04". Use the actual authorised record.
- **Never invent** a household, a metric, a quote, a testimonial or a logo.
  See §2.7. Fictional examples are identified as examples.

For a non-technical reader: lead with the outcome in plain words, then name the
mechanism once. *"The sample purifier uses A200-HEPA. Open page 2 of its
manual to see the exact passage."* Both halves matter: the first answers the
question, the second lets someone check it. This example is from the fictional
AirOne fixture, not advice for a real appliance.

Public copy describes what the product does. Interface copy tells someone
what happened and what they can do next. A failed upload says whether it can
be retried. An insufficient balance shows the operation's cost. A verification
notice explains where the email was delivered.

---

## 8. Accessibility — non-negotiable

`npm run qa` must report **PASS — 0 failures**. The required check covers
console/network, axe, fonts, stranded reveal states, overflow at four
breakpoints, the placeholder inventory, and reduced motion.

**Implementation status (13 October 2026):** `npm run qa` now implements this
visual gate. It checks four viewports, both app themes, all capability panels,
auth dialogs, source viewers, fonts, axe, keyboard access and both ends of the
motion sequence. Run the original fictional browser journey first to prepare
its account/session fixture. Current results are in `docs/DESIGN_QA.md`.
Backend and model verification remain separate checks.

- Decorative visuals carry `aria-hidden="true"`.
- Large low-opacity display text is **SVG**, never an HTML text node — axe's
  contrast rule judges pixels and ignores `aria-hidden`.
- Disclosure patterns use `aria-expanded` + `aria-controls`. The capability rows
  are **not** tabs; tab semantics fail `aria-required-children` there because
  each body renders inside its own row.
- Skip link, `#main-content`, `[id] { scroll-margin-top }`, Lenis anchor
  offset −104.

---

## 9. Section specifications

Concrete briefs for HomeAtlas's public page and application screens. Everything
above is law; this section is the application of it. Product requirements do
not authorise new visual tokens, a different font or extra animation effects.

### 9.1 Capabilities — the copy rewrite

HomeAtlas helps someone organise a home and retrieve evidence. Its public page
must demonstrate that work with records, not open with model names or a
consultancy list. The reader is a household member (§1), so precise nouns stay
but they stop being the opening move.

**The layering rule: plain sentence leads, concrete nouns follow as specifics.**

```
WRONG (jargon-first — excludes the household member)
  "Multimodal RAG with hybrid candidate fusion and local reranking."

WRONG (vague — gives the reader nothing to inspect)
  "Your intelligent home companion remembers everything."

RIGHT (plain lead, nouns intact)
  "Find the filter your purifier needs, with the manual page beside it.
   Answers link to an exact PDF region or transcript timestamp in your
   household records."
```

Four-part model per capability — which gives the row a real typographic
hierarchy instead of one undifferentiated paragraph:

```ts
{
  title:  string    // the capability
  plain:  string    // ONE sentence, zero jargon — the focal line (§2.1)
  detail: string    // 1–2 sentences naming the real product behaviour
  terms:  string[]  // concrete capabilities, kept in full
  gives:  string    // what the household member can find or do
}
```

Approved copy. Maintain the deliberate length variance (§2.6).

**01 · Rooms and inventory**

- **plain** — "Keep each appliance with the room it belongs to."
- **detail** — "Store the make, model, serial number, purchase date and warranty date. Attach records to the item and find it through the room list or the 3D Home View."
- **terms** — `Rooms` · `Appliance records` · `Purchase and warranty dates` · `Item notes and history` · `3D Home View`
- **gives** — "An item record with its documents."

**02 · Private document library**

- **plain** — "Put the manual, receipt and contractor note in one place."
- **detail** — "Upload PDFs, photos, audio and video to a private household library. Processing retains PDF pages and regions, transcribed timestamps and source versions; its status stays visible."
- **terms** — `PDF pages and regions` · `Photo and scan OCR` · `Audio and video transcripts` · `Source versions` · `Processing and retry`
- **gives** — "Records you can open and trace."

**03 · Answers with evidence**

- **plain** — "Ask about your home. Check the source beside the answer."
- **detail** — "Use text, a photo or a voice question to search your household records. Open the exact cited page, image or transcript moment; missing or conflicting evidence stays explicit."
- **terms** — `Text, photo and voice questions` · `Exact citations` · `Household-scoped retrieval` · `Missing-evidence results` · `Saved answers`
- **gives** — "A finding you can check."

**04 · Maintenance and warranties**

- **plain** — "See what needs attention before you forget it."
- **detail** — "Track warranty dates, schedule recurring maintenance and keep completed work in the item's history. The calendar shows the tasks entered by your household; it does not invent a maintenance schedule."
- **terms** — `Warranty dates` · `In-app reminders` · `Recurring tasks` · `Maintenance calendar` · `Completion history`
- **gives** — "The next task, with its date."

**05 · Household control**

- **plain** — "Share your home records with the people you choose."
- **detail** — "Invite editors and viewers, then manage household roles. Manage passkeys, two-factor authentication and sessions, inspect internal credit usage, and export or delete the household's records."
- **terms** — `Owner, editor and viewer roles` · `Passkeys and two-factor authentication` · `Session management` · `Credit ledger` · `Export and deletion`
- **gives** — "Access and usage you can account for."

**Layout.** Split shape (§2.3): disclosure rows left, one instrument right, at
`7/5` — not `6/6` (§2.1). `plain` is the focal line at lead size; `detail` sits
at body in support colour; `terms` are inset chips; `gives` is a single ruled
line closing the open row. Semantics stay `aria-expanded` + `aria-controls` —
tab roles fail `aria-required-children` here because each body renders inside
its own row.

The instrument corresponds to the open capability: an item and its receipt,
a real processing state, a cited passage, a maintenance row, or a role/credit
record. Use authorised household data inside the app and labelled fixtures on
the public page. It must not be a generic graph of an AI network.

### 9.2 Home-records band — new, on the public landing page

Field shape (§2.3), retaining the reference's inline figures and dot-matrix
world-map treatment. This is a labelled example of the product's scope, not
an adoption claim or a live map of people's homes.

- Centred statement headline with count-up numerals inline (§6 timing).
- One supporting sentence beneath, muted, two lines maximum.
- Below it a **dot-matrix world map**: small circles on a grid, `blue/25` on
  white, with pins at located points. Not a filled vector map — the dot matrix
  preserves the plotted, instrument-drawn quality of the supplied design.
- Map is `aria-hidden`; every figure also exists as text.
- Sits on **white**, so the ink page hero above supplies the tonal break.

HomeAtlas-specific content: "6 rooms. 2 documents. One answer you can check."
These are declared sample counts: the six default starter rooms, the two
original AirOne fixture PDFs, and one saved supported question. A named
`demoHouseholdSummary` array or object must supply them. The fixture includes
that question before the count is displayed; the statement is not a count of
registered users, processed customer documents or worldwide homes.

Map dots come from declared geographic data. Pins come from a named
`demoLocations` array of public geographic example coordinates. Their caption
states that locations are illustrative. Do not use private addresses, device
locations, household membership data or fabricated customer coverage. The
world-map treatment belongs only to this public explanatory band; the
private Home View remains the user's room map (§9.6).

> **Provenance (§2.7).** Sample figures and example locations ship wrapped in
> `<Placeholder>` / `<PlaceholderValue>` with `data-placeholder` and a quiet
> "Illustrative home and locations" footnote. There are no verified public
> adoption figures. See §9.8.

### 9.3 Evidence panels — the lit-panel treatment

Applied to the capability media panels only. The palette does not change.

- A soft bloom behind the panel — radial `blue/18`, heavily blurred — so it
  reads as lit rather than pasted onto the section.
- A 1px **gradient** edge, `white/20` at top-left falling to `white/05` at
  bottom-right, instead of a flat uniform border. This is the panel's one
  effect (§2.5) — it therefore gets no shadow and no hover glow.
- Inside, the instrument obeys §2.2: every point comes from a named array.
- Registration corner marks are a **signature, not a texture**: at most two
  panels per page carry them.

The lead is the finding or document detail someone came to inspect. A source
title, page number, version and timestamp are supporting facts. A preview is
an actual authorised source region or a labelled fixture, not a made-up
waveform or decorative receipt.

### 9.4 The contrast ladder

§5 sets which colours are legal. This sets how many of each may appear, and it
is what fixes the "everything is dim, nothing is dominant" failure — the
HomeAtlas evidence panels currently live entirely in the bottom two tiers.

| Tier | On ink | Use | Budget per panel |
|---|---|---|---|
| **Lead** | `white` / `mint` | the one number or line the panel exists to show | **exactly 1** |
| **Body** | `white/85` | titles, axis values you must be able to read | ≤ 5 |
| **Support** | `white/50` | secondary labels, captions | unlimited |
| **Structure** | `white/10`–`white/22` | gridlines, rules, frames | unlimited |

A panel with no Lead element is unfinished, however correct its hairlines are.

### 9.5 Implementation checklist

The seven confirmed migration issues from the previous interface are resolved
in the current redesign. The visual values in §3–§6 remain unchanged.

1. **Palette:** ink/blue/mint tokens govern the landing page and app; dark
   navigation, light record surfaces and the corresponding app dark theme.
2. **Typography:** official Satoshi Regular and Medium are self-hosted,
   with no serif or mono UI and readable labels/forms.
3. **Measure:** the retained display scale, line-height, tracking and content
   measures govern the public page; dense app screens retain legible hierarchy.
4. **Composition:** asymmetric sections, a geographic Field, capability
   disclosure Split, mission Statement and maintenance Ledger replace the
   interchangeable feature cards. App records use ruled rows.
5. **Motion:** GSAP/Lenis implement the 300svh pinned hero, exact x/scale
   values, reveals, mission scrub and count-up. Phone/tablet vertical placement
   is calculated from the copy and preview bounds to prevent overlap. Only
   transforms are animated; reduced motion shows full content. Faded hero
   controls become inert; persistent header actions remain available.
6. **Evidence:** the public preview opens the actual original sample manual.
   Fictional data and geographic examples carry the required quiet labels;
   the private app continues to use authorised household records.
7. **Access:** skip link, main-content target, focusable ledger, disclosure
   semantics, 3D image/group roles, keyboard controls and visual QA are present.

The scope and measured results are recorded in `docs/DESIGN_QA.md` and
`docs/VERIFICATION.md`; they do not establish public deployment readiness.

### 9.6 Screen requirements — the complete HomeAtlas product

These are screen states, not an invented set of public URLs. The current
client presents the public page, onboarding and authenticated screens at `/`.
The actual screen keys are `overview`, `home`, `items`, `library`, `ask`,
`maintenance`, `credits` and `settings`. Room/item details and evidence open
from those states. Preserve functional navigation while applying this design.

| Screen | One focal point | Required content and behaviour |
|---|---|---|
| **Public landing** | A real product finding in the pinned hero | Describe private home records and cited answers. Primary action: create an account; returning users can sign in. Use the approved capability copy, labelled demonstration data and alternating section shapes. No sales consultation, invented customer logos or payment CTA. |
| **Account and verification** | The next authentication step | Name/email/password signup, verification, password sign-in/reset, passkeys, TOTP and recovery codes. Notices explain where email was delivered and what to do next. Pending, validation, expired-link and denied states remain readable. |
| **Household setup** | Create the user's household | Home/apartment name, optional address and starter rooms. Create real membership and the configured monthly credit grant. A private address is not public marketing content. |
| **Overview** | The next useful action for this household | Actual rooms/items, ready or processing documents, upcoming maintenance, recent activity and available credits. A new home gets a useful add-room/item/document empty state, not fabricated activity. |
| **Interactive Home View** | The selected room or item | Stylised React Three Fiber/Three.js home or apartment, linked to user-maintained rooms and item markers. Lazy load; immediate static preview; equivalent 2D room/item controls; keyboard rotation/reset; WebGL fallback. It is not an architectural scan or a dimensionally accurate floor plan. |
| **Room and item details** | The item and its identifying facts | Room, make, model, serial number, purchase/warranty dates, notes, linked photos/documents and maintenance/saved-answer history. Search/filter inventory. Owner/editor edits and viewer reads remain distinct. |
| **Upload library** | The document and its real processing state | PDFs, images, audio and video; room/item association; upload progress; queued, processing, ready and failed states; actionable retry; new source versions. Uploaded does not mean ready for retrieval. |
| **Question workspace** | The finding with supporting evidence | Text, photo and voice input, item/room scope when available, cost before submission, supported answer or explicit lack/conflict of evidence. Save/bookmark a question and answer; permitted users can attach it to item history. This is a home-record workspace, not a generic chatbot landing screen. |
| **Evidence viewer** | The exact cited passage | Authorised original source/version, PDF page and region, image preview, transcript span or audio/video timestamp. Inspect beside the answer on desktop and in a source drawer on phone. Keep the answer context when closing the viewer. |
| **Maintenance** | The next due task | Calendar, warranty dates, recurring tasks, item/room context, completion and history. Data comes from entered dates and actual completed work. Reminders are currently in-app. |
| **Credits and usage** | Available credits and the cost of an action | Server-supplied allowance/prices, available and reserved amounts, dated grants/reservations/charges/refunds, actors and operation IDs, CSV export. Credits are internal usage allowances, never money or a subscription checkout. |
| **Account and household settings** | The selected account or household control | Household selection, invitations/members/roles, account security, passkeys, TOTP/recovery codes, active sessions and sign-out of other devices, recent authentication for sensitive changes, export and confirmed household deletion. |
| **Owner administration** | The processing issue or audit event being inspected | Authorised job states/failures/retry information, credit usage and audit records. Diagnostic data stays owner-only; household source content is not exposed through public panels or general logs. |

The public hero's device is a viewport displaying HomeAtlas's interface. Its
chassis and motion follow §6. HomeAtlas does not sell a physical home hub.
The authenticated 3D Home View is useful navigation, not another competing
marketing animation. Its selected state, labels and controls follow the same
type, palette, surface and motion constraints.

Use the source's light and ink tones to support both light and dark themes.
Do not add a separate theme palette. Design phone, tablet, laptop and desktop
states deliberately; dense application tables and forms are not marketing
sections with an arbitrary fixed minimum height.

### 9.7 Functional states and trust requirements

**The core path.** Create and verify an account → create a household → add a
room and appliance → upload a manual and receipt → wait for genuine ingestion
→ ask a text or photo question → inspect the exact citation → create a
maintenance reminder → inspect the correct credit balance and transactions.
This whole path must work on a phone. A second household must not see the
first household's records at any point.

**Authentication.** Keep the established Better Auth/PostgreSQL flow. Email
verification remains required. The development-only **Open verification
email** button checks the unverified account's own password and retrieves only
that request's fresh message; it is enabled only on explicitly opted-in
loopback development without SMTP and disabled in production. The normal
notice directs someone to their email provider when SMTP is configured.
Never expose a household-wide inbox or use an email address alone to return
verification/reset tokens.

**Permissions.** The interface reflects the server's current membership;
hiding a button is not authorisation.

| Role | Product actions |
|---|---|
| Owner | Household records, uploads, maintenance, questions, private bookmarks and shared item history; invitations, members, role changes, export/deletion and owner diagnostics. |
| Editor | Organise rooms/items, upload records, maintain tasks, ask questions and save permitted item history. No owner membership or administration controls. |
| Viewer | Read household records, open authorised sources, ask questions and keep personal bookmarks. Cannot edit records or write shared item history. |

Sensitive member changes and deletion require recent authentication. Private
files, citation previews, original versions, export and retrieval must all
resolve the authenticated household on the server. Keep internal file paths,
service keys and other households' IDs out of the interface.

**Uploads.** Keep file type/signature, size and media-duration validation.
Display actual upload progress and distinct processing states. A ready state
requires published extraction/indexing results. Failure explains the next
action without exposing internal paths. Retry/reprocessing preserves the
original file, source version and older citations. A changed preview is not
permission to rewrite an old quoted passage.

**Answers.** All generation, OCR, embeddings, retrieval, reranking and
transcription run locally or on self-hosted infrastructure. No paid or hosted
model API is introduced by the redesign. Model names belong in relevant admin
or setup information, not everyday product choices.

The current tested lower-resource profile is Qwen3-VL 4B Instruct,
BGE-small-en-v1.5, BGE-reranker-base, SigLIP2, local Whisper tiny and Tesseract.
Exact artifact pins and hardware assumptions live in `docs/MODELS.md`. The
larger BGE-M3/reranker-v2-m3/PaddleOCR profile is an unverified deployment
profile, not an extra user-facing capability to claim.

Treat uploaded instructions as untrusted record content. Answers name their
finding, evidence and uncertainty. Cite only canonical authorised source
versions and exact spans. Do not invent warranty terms, lease obligations,
part compatibility or repair steps. Missing or conflicting evidence gets a
clear result and a useful next action. Electrical, gas and structural work
must identify when a qualified professional is needed. A visually similar
photo is not proof of part compatibility; arbitrary damaged-part matching
has not been established by the current verification.

**Credits.** Read the configured allowance and operation price from the
server. Show cost before upload/text/photo/voice work begins. Reflect atomic
reservation, success charge and failure/cancellation release or refund, with
idempotent retries and no concurrent overspending. Display pending funds as
reserved, not as already spent. Keep the append-only transaction history and
CSV export. There is no payment provider and no invented monetary value.

**Saved records.** Personal bookmarks retain the question, answer and working
citations. Saving to shared item history obeys owner/editor permissions.
The brief requests saved searches; the current implementation stores saved
questions/answers as bookmarks, not a separately verified saved-filter search
feature. Do not label an absent standalone feature as implemented.

**Maintenance.** Show actual entered warranty dates, due dates, recurrence and
completion history. Recurring tasks create the next real due task. Do not
advertise unattended email maintenance reminders: the current product has
in-app scheduling; an automated email delivery worker is not implemented.

**Resilience and access.** Skeletons, empty states, pending submissions,
validation errors, unavailable models, missing sources, credit exhaustion,
revoked membership and unavailable WebGL all have an actionable final state.
Preserve visible keyboard focus, accessible names, touch-friendly controls and
source-drawer navigation. Every 3D action exists outside the canvas. Stop
motion in its final state under reduced-motion preferences (§6), including
when an animation dependency or WebGL fails.

**Public claims.** Local functionality is exercised; public production
readiness is not established. External SMTP/TLS, real hardware passkey sync,
Docker boot, full GPU profile, object-store integration and scale indexing
have separate limits in `docs/VERIFICATION.md`. The redesign must not invent
throughput, global reach, security certification or successful deployment
claims to fill a panel. Compute, storage, bandwidth and email can cost money
although no hosted inference-token bill is introduced.

### 9.8 Data, examples and provenance register

The marker remains the quiet footnote prescribed in §2.7. A sample is not a
customer endorsement, a real warranty promise or a claim about another home.

| Content | Source | Required treatment |
|---|---|---|
| Six starter rooms | `app/api/atlas/route.ts`: Living room, Kitchen, Bedroom, Bathroom, Laundry, Study | In a public sample, bind the count to declared demo data and mark it illustrative. In the app, use the selected household's actual room records. |
| AirOne AP-200 appliance | Original fictional fixtures and item records created for verification | `<Placeholder>` / `data-placeholder`; quiet "Fictional sample appliance" footnote. Never suggest that this is a real product specification. |
| Replacement filter A200-HEPA | `tests/fixtures/AirOne-AP200-manual.pdf`, page 2 | The quoted passage and citation must match that page. Mark the public example fictional; no real-appliance repair advice. |
| Warranty expiry 12 February 2028 | `tests/fixtures/AirOne-purchase-receipt.pdf`, page 1 | Mark the public example fictional and open that receipt. Real item dates require the household's own record. |
| Contractor audio/video | Original fixture media in `tests/fixtures/` | Identify sample content; preserve the actual transcript/timestamp and licensed fixture provenance. |
| Public world-map pins | Named `demoLocations` array with public geographic example coordinates | Illustrative locations only; no real household addresses, customer pins or implied adoption. |
| Public sample counts | Named `demoHouseholdSummary` data, derived from declared sample records | `<PlaceholderValue>` / `data-placeholder`; count-up lands on the exact sample string. No fabricated usage/adoption metrics. |
| Private counts, activity and credits | Authorised `/api/atlas` response and server credit ledger | Use real household data. Do not seed activity into an empty user's home or round a live balance for visual appeal. |
| 3D geometry | Original procedural Home View linked to rooms/items | Identify it as a stylised user-maintained map; do not imply measured dimensions, detected appliances or live sensor readings. |
| Testimonials, customer logos, geographic adoption and performance claims | No verified public dataset supplied | Omit or explicitly mark placeholder content. Never present it as established fact. |

The existing design-discovery references to 21st.dev, Dribbble, Three.js,
React Three Fiber and Drei remain provenance, not permission to overwrite this
visual language. Use them for suitable component patterns and rendering
primitives. Verify the license of any added component/asset, and retain its
notice. Do not copy premium templates or Dribbble artwork. Keep household
records off third-party demo services. The previous warm/serif treatment is
historical, not an amendment to §4–§5.

### 9.9 Verification required for the redesign

The current repository has exercised backend/authentication, household
isolation, credits, ingestion/citations, responsive browser flows and 3D
fallback. As of this adaptation, `docs/VERIFICATION.md` records 56 Node tests,
17 worker tests and desktop/phone local-verification checks. Those results
belong to the existing implementation, not a redesigned screen that has not
yet been built.

Before declaring the redesign complete:

1. Run `npm run qa` with every check in §8. Test phone, tablet, laptop
   and desktop, including the existing 390px and 1440px browser viewports.
2. Verify the retained fonts, sizes, spacing, palette and animation values;
   inspect both themes, keyboard use, reduced motion and WebGL fallback.
3. Repeat the core path in §9.7 with actual services and source citations.
   Verify password recovery, passkeys, TOTP/recovery and session controls
   appropriate to any changed authentication interface.
4. Run the appropriate backend/worker regression checks for changed flows,
   preserving cross-household isolation, roles, reservation/charge/refund
   accounting and retry idempotency. A visual redesign cannot replace them
   with a mock response.
5. Run TypeScript and the production build, inspect browser errors/network
   failures, and capture the changed public and application screens at phone
   and desktop sizes. Record remaining limits in the verification report.

---

## 10. The ship checklist

Before any section is called done, answer these out loud. A "no" is a bug.

1. Can I name the one focal point?
2. Does every graphic encode data I can point at in the source?
3. Is this section's shape different from the one above it?
4. Have I removed at least one box, border or effect since the first draft?
5. Do the sentences vary in length when read aloud?
6. Is there anything here I'd be embarrassed to have a household member inspect
   beside the original source?
7. Does `npm run qa` still pass?

---

## 11. Amendments

This document changes by decision, not by drift. Record what changed and why.

| Date | Change | Why |
|---|---|---|
| 2026-10-13 | Adapted the supplied design language to HomeAtlas's audience, capabilities, examples and complete screen/state requirements. | The imported consultancy content does not describe private home records, household permissions or cited answers. |
| 2026-10-13 | Retained the composition, type, colour, surface and motion rules, including the original numeric values and contrast ladder. | The user's instruction is to preserve the supplied design while replacing project-specific content. |
| 2026-10-13 | Replaced the foreign component defect list, mapped real fixtures and recorded the missing visual QA gate and current deployment limits. | A governing document must distinguish the redesign target from current implementation and tested behaviour. |
| 2026-10-13 | Implemented the visual language and replaced the historical migration defects with their verified status. | The landing page and app now use this design contract; the visual values remain unchanged. |
