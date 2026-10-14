# Visual references and asset provenance

Reviewed 13 October 2026. The current visual contract is `../design.md`: Satoshi, ink/blue/mint, asymmetric sections, ruled records and a pinned product preview. The earlier cream/sage and serif treatment has been replaced. References below describe component and asset provenance, not an alternative palette.

## 21st.dev

- [3D collection](https://21st.dev/community/components/explore/21-3d): reviewed perspective cards, room/object presentations, and 3D folders. This informed the original `components/ui/DepthCard.tsx` and earlier perspective treatments. The redesigned landing page now uses the signature pinned GSAP sequence required by design.md; the retained depth-card file is not used there. Keyboard equivalents for 3D selection remain.
- [3D Card Effect](https://ui.aceternity.com/components/3d-card-effect), catalogued on 21st: reviewed the perspective/elevation pattern. HomeAtlas implements its own small CSS-variable pointer handler rather than copying the premium template or assuming every registry item shares a license.
- [21st spotlight performance guide](https://news.21st.dev/blog/react-spotlight-effect-components): reviewed why pointer state should be written to CSS variables and why effects should remain enhancements. No React state updates on every pointer movement; no required hover interaction on touch; reduced-motion disables perspective effects.

Some older direct component URLs could not be retrieved by the web tool. No paid 21st account, API key, registry installer, or external inference integration was used. 21st was used for component discovery and design reference, not as a runtime service.

## Dribbble

- [Dovlet's Smart Home Dashboard](https://dribbble.com/shots/25764617-Smart-Home-Dashboard): reviewed the isometric cutaway and the relationship between the home map and its controls. The house illustration, geometry, furniture, and interface were created originally in this repository. Dribbble images were not downloaded, bundled, or copied.

## Open-source 3D

- [React Three Fiber](https://github.com/pmndrs/react-three-fiber) and [Drei](https://github.com/pmndrs/drei): installed with the npm lockfile, MIT licenses. Used declarative geometry, RoundedBox, OrthographicCamera, OrbitControls, ContactShadows. The scene uses local procedural geometry and canvas labels; it fetches no remote textures, font, GLTF model, or HDR environment.
- [Drei staging](https://drei.docs.pmnd.rs/staging/stage) and [Float documentation](https://drei.docs.pmnd.rs/staging/float) reviewed for lighting and animation. The home uses a finite damped entrance and demand rendering, not a continuously floating architectural map. Motion stops when idle and is disabled for reduced-motion.
- Three.js is MIT licensed. Dependency license files remain in installed packages and notices must accompany redistribution.

## Originals

The SVG home illustration, procedural 3D rooms and furniture, and fictional AirOne PDF/scan fixtures are original. Test fixtures state CC0 and clearly identify fictional appliance terms. The fixture PDFs are not manuals for real products. No third-party manual has been scraped or bundled.

## Current design implementation

- Satoshi Regular/Medium: official Fontshare download, unmodified files self-hosted for this website under the included ITF FFL v2.0. Font binaries are ignored by Git; `scripts/setup-fonts.mjs` obtains them from the official source before dev/build when absent. There are no runtime font-CDN requests.
- GSAP ScrollTrigger and Lenis: installed dependencies drive the single hero timeline, mission text, finite reveals and sample count-up. Reduced motion displays complete final content; scoped cleanup removes timelines and the ticker when leaving the landing page.
- Natural Earth 1:110m land boundaries via World Atlas: `scripts/generate-world-dots.mjs` generates the named geographic dot array. Public city-centre pins are explicitly illustrative. No household addresses or customer-location claims are used.
- The product preview uses the original fictional AirOne manual/receipt. Its page image is rendered directly from the original page; it is not third-party artwork or a fabricated customer result.
