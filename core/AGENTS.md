# Instrucciones para mantener LKS-SDD

- Las fuentes de contrato están en `specs/canonical/`; no las edites para resolver diferencias de implementación.
- Conserva la separación entre hechos, inferencias, propuestas, decisiones y pendientes.
- No añadas MCP, conectores, hooks, apps ni agentes ejecutables durante M0–M5.
- En M5 están implementadas las seis skills: `lks-sdd-help`, `lks-sdd-define`, `lks-sdd-adopt-existing`, `lks-sdd-assess-readiness`, `lks-sdd-implement` y `lks-sdd-verify`. No crees entrypoints vacíos para capacidades futuras.
- Mantén la invocación implícita activa y las descripciones orientadas a objetivos sin solapamiento.
- Los Markdown del proyecto consumidor son canónicos; `.lks-sdd/project.json` es un índice.
- No selecciones la pila preferente automáticamente y no generes código si falta una decisión crítica.
- Ejecuta las validaciones de `docs/VALIDATION.md` y revisa el diff antes de entregar cambios.
- Una release candidate puede cerrar la automatización M4, pero nunca presentes canales semánticos, humanos o de piloto `not-run` como superados.
- El marketplace M5 se genera como bundle externo reproducible; no crees una instalación activa, no registres identidades o datos reales y no marques el piloto como ejecutado sin evidencia.
- No publiques, instales, hagas push o crees commits salvo autorización explícita separada.
