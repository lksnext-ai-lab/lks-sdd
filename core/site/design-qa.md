# Design QA · LKS-SDD Site

## Scope and method

- Routes verified: `/` and `/por-dentro`.
- Browser: Codex in-app browser (IAB), with DOM inspection, interaction testing, console review and screenshots.
- Desktop comparison viewport: CSS viewport 1440 × 900. Responsive checks: 390 × 844 and the default Codex desktop viewport.
- Reference and implementation images were opened together in the same comparison input for the hero, Mendiara, Jira and the technical interior.
- Reference keyframes:
  - `exec-db6e74b2-9bf6-4648-a17e-1cd284096283.png` — hero.
  - `exec-594ad393-d782-44f3-b1d6-8d13d85fd52d.png` — dirección visual de la escena del reto.
  - `exec-a6f03111-c8b2-40c6-96a5-3c9c7eea24e7.png` — Mendiara.
  - `exec-9d2e15b4-2823-41ef-99bb-9c655c62f5fb.png` — Jira.
  - `exec-56392256-a025-45be-90ba-630e0a8602b1.png` — interior técnico.
- Implementation evidence is stored in `.qa/`.

## Comparison results

1. Hero and above the fold: the light LKS Next composition, orange accent, oversized editorial title and specification-to-application imagery preserve the approved direction. Three HTML polygon layers follow the orange path and add motion without baking copy into the image.
2. Challenge scene: a dedicated generated background moves from fragmented shards to controlled trajectories. Six semantic polygon layers assemble on scroll; the final arrangement keeps copy, convergence and control chain readable at desktop and under the dedicated 760 px responsive treatment.
3. Palette and rhythm: light scenes dominate the narrative, with petrol sections used as deliberate contrast rather than as the default background. Orange remains the interaction and traceability color.
4. Mendiara: the fictitious corporate application uses a real generated photographic asset, a branded navigation system, realistic fleet data, live tabs and an annotation-to-new-requirement loop.
5. Jira: the implementation preserves board, ticket detail, repository projection, controlled receipts and the explicit boundary that Jira is not the source of truth. The human transition is interactive and two-step.
6. Technical interior: the interactive six-layer stack preserves the approved exploded architecture concept while adapting it to a usable route with complementary sections for skills, contracts, repository authority and gates.
7. Motion and accessibility: the fixed Three.js energy field, scroll reveals and interaction transitions work; `prefers-reduced-motion` disables non-essential motion. Semantic controls, focusable actions, labels and alt text were checked.
8. Responsive behavior: horizontal overflow was removed at 390 px on both routes. The opening also has a dedicated treatment at 760 px so its image, copy and six fragments remain legible in the narrow Codex preview.

## Above-fold copy check

Required copy is present without semantic drift:

- `LKS-SDD · SPEC-ANCHORED`
- `Desarrollo SDD con CODEX`
- `Un plugin de LKS Next para CODEX que convierte las especificaciones en un contrato vivo para dirigir, implementar y verificar el desarrollo.`
- Navigation: `Visión`, `Cómo se trabaja`, `Jira`, `Por dentro`
- CTAs: `Ver el proceso` and `Explorar el enfoque`

## Intentional deviations

- The hero uses the clean approved standalone image instead of embedding the complete application screen. The application appears later as its own interactive scene, following the approved decision to separate scenes.
- The technical keyframe's full repository tree and external peers are distributed across the route instead of forced into one dense viewport. This improves legibility and interaction while preserving the architecture.
- Jira is implemented as a faithful fictitious operational projection, not as a branded clone or a live integration.

## Interaction and technical verification

- Mendiara: switched to `Rutas`, verified `Planificación de rutas`, hid and restored the interface annotation.
- Jira: selected `MDM-43`, returned to `MDM-41`, executed the two-step `Pasar a hecho` / `Confirmar transición humana` flow and verified the confirmed state.
- Technical route: selected layer 06 and verified the repository detail panel.
- Navigation between routes works; both routes return HTTP 200.
- Fresh-browser console pass: no warnings or errors.
- Opening motion check: fragment labels were observed dispersed on entry and at `translate3d(0, 0, 0)` with full opacity when the challenge scene reached its sticky state.
- `npm run lint`: passed with zero warnings.
- `npm run build`: passed.
- `npm audit --omit=dev`: zero production vulnerabilities after updating Next.js to 16.3.3.

final result: passed
