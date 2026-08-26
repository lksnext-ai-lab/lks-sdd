---
artifact_id: ART-UX
artifact_type: ux-accessibility
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.11.0"
project_id: "{{PROJECT_ID}}"
baseline_id: "{{BASELINE_ID}}"
status: draft
classification: internal
audience:
  - delivery-team
owners:
  - pending-assignment
source_of_truth: true
last_updated: "{{DATE}}"
---

# UX, interfaz, accesibilidad y prototipado

## Inventario de pantallas

| ID | State | Screen | Purpose | Users | Content | Main actions | Requirements | Acceptance | Increment |
|---|---|---|---|---|---|---|---|---|---|

## Detalle contractual por pantalla

| Screen | Entry and exit | Information hierarchy | Secondary actions | Permissions and role variants | Responsive and priority devices | Accessibility | Pending content |
|---|---|---|---|---|---|---|---|

## Estados por pantalla

| Screen | Loading | Empty | Error | No permission | Confirmation | Recovery |
|---|---|---|---|---|---|---|

## Flujos, interacciones, estados y diálogos

| ID | State | Flow or interaction | User | Screens | Entry or trigger | Expected steps or response | Alternate, error or recovery path | Dialog or confirmation | Accessibility | Acceptance | Increment |
|---|---|---|---|---|---|---|---|---|---|---|---|

Documente según aplicabilidad carga, vacío, error, falta de permisos, éxito, confirmación, recuperación, validaciones y acciones destructivas. Convierta términos como intuitivo o accesible en criterios observables.

## Dirección visual

| ID | State | Aspect | Proposal | Rationale | Constraints | Human validation | Decision | Increment |
|---|---|---|---|---|---|---|---|---|

Incluya marca, tono, jerarquía, densidad, color, tipografía, componentes, responsive y referencias permitidas. Una propuesta no se convierte en decisión por aparecer en una imagen.

## Prototipos visuales

| ID | State | Asset | Format | Viewport | Screens or flow | Requirements | Source | Generated on | Prompt or brief | SHA-256 | Human validation | Confirmation scope | Limitations | Decision | Increment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Use IDs `VIS-###` y assets PNG/JPG bajo `docs/lks-sdd/03-solution/ui-prototypes/`. Enlace cada archivo con Markdown relativo, compruebe existencia, dimensiones y SHA-256, y mantenga `State=proposal` hasta validación humana explícita. Si ImageGen o la transferencia no están disponibles, no cree una fila `VIS-###`: registre `Visual mode=pending` y `Visual prototype=pending` en `ART-INCREMENTS` y el brief e impacto en `ART-OPEN`, sin inventar archivo ni checksum.

En `Human validation`, use `pending` o el formato comprobable `user-confirmed; role=<rol-o-alias-no-identificativo>; date=AAAA-MM-DD; ref=ADR-###`. No invente una identidad ni autoridad. Genere entre una y tres propuestas; para una aplicación nueva o rediseño material presente normalmente dos o tres direcciones comparables, y justifique en el brief cuando una sola sea suficiente. Para extender una dirección ya confirmada puede bastar un prototipo fiel.

Los Markdown confirmados mandan sobre comportamiento, copy exacto, datos, reglas, estados y aceptación. La imagen confirmada solo gobierna la dirección visual declarada; cualquier contradicción se convierte en punto abierto.
