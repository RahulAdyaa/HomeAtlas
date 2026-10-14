# Third-party licenses and provenance

The original home artwork, room geometry, furniture, CSS and test content were made in this repository. 21st.dev and Dribbble were design-reference sources; no third-party artwork or premium template was bundled. The optional agent installers in the original request were not installed.

React, Next.js, Three.js, React Three Fiber, Drei, Radix, Better Auth, Lucide and the other npm dependencies carry their own distribution notices in installed packages. Preserve those licenses when distributing a build. Pinned dependencies are in package-lock.json. Model licenses/artifact pins are in MODELS.md. The fixture PDFs identify their fictional content and CC0 status.

PyMuPDF is licensed under AGPL-3.0 or a separately purchased commercial license. It is used for PDF extraction and rendering; the available repository source must remain available to users when operating under its AGPL terms. This project has not purchased a commercial PyMuPDF license. FFmpeg licensing depends on the configured build/codecs; the tested local FFmpeg includes GPL codecs used only for original test-video encoding. Review distribution obligations for the exact deployed runtime.

## Design dependencies and font assets

Satoshi comes directly from [Fontshare](https://www.fontshare.com/fonts/satoshi). The downloaded package includes ITF Free Font License v2.0 (17 August 2026), retained in `public/fonts/FFL.txt`. This website self-hosts the unmodified Regular/Medium webfonts for its own interface. Font binaries are excluded from the source repository; another operator obtains their own official copy with `scripts/setup-fonts.mjs`. Do not redistribute the fonts as a font library or offer them as a selectable third-party design service.

GSAP uses its [standard no-charge license](https://gsap.com/standard-license/), not MIT. Lenis is MIT. World Atlas and TopoJSON Client are ISC; d3-geo is ISC. Their Natural Earth source geography is public domain. Preserve installed dependency license notices and the geography provenance when distributing the website. Axe-core is MPL-2.0 and used only by the development QA command.
