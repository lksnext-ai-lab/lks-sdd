# Entregable derivado LKS-SDD

| Campo | Valor |
|---|---|
| Proyecto | `{{PROJECT_ID}}` |
| Audiencia | {{AUDIENCE}} |
| Propósito | {{PURPOSE}} |
| Fecha de derivación | {{DATE}} |
| Estado | Borrador pendiente de revisión y aprobación |
| Baseline | `{{BASELINE_ID}}` |

## Alcance y criterio de selección

Esta vista contiene únicamente artefactos canónicos con estado `confirmed` y clasificación `client` o `public`. Se excluyen fuentes internas, confidenciales, restringidas, no confirmadas y cualquier fuente con indicadores sensibles.

{{SECTIONS}}

## Trazabilidad de la derivación

- Artefactos fuente incluidos: {{SOURCE_IDS}}.
- Fuentes excluidas por clasificación o estado: {{EXCLUDED_COUNT}}.
- Hash de la selección y contenido fuente: `sha256:{{PROVENANCE_HASH}}`.
- La fuente de verdad continúa en `docs/lks-sdd/`; este documento es una vista derivada.

## Limitaciones y aprobación

- La generación no equivale a aprobación formal ni sustituye la revisión de exactitud, audiencia y confidencialidad.
- Las propuestas no se presentan como decisiones y las inferencias no se presentan como hechos.
- La ausencia de una fuente excluida no implica que el asunto no exista.

Checklist previo a entrega:

- [ ] Exactitud revisada contra la baseline indicada.
- [ ] Audiencia y propósito confirmados.
- [ ] Confidencialidad y datos personales revisados.
- [ ] Alcance, exclusiones, riesgos y limitaciones aceptados.
- [ ] Aprobación formal registrada fuera de este generador.
