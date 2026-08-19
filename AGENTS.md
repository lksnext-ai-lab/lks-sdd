# Instrucciones para mantener LKS-SDD

- Las fuentes de contrato están en `specs/canonical/`; no las edites para resolver diferencias de implementación.
- Conserva la separación entre hechos, inferencias, propuestas, decisiones y pendientes.
- No añadas MCP, conectores, hooks, apps, agentes ni perfiles ejecutables durante M0–M1.
- Solo `lks-sdd-help`, `lks-sdd-define` y `lks-sdd-assess-readiness` están implementadas. No crees entrypoints vacíos para las skills de backlog.
- Mantén la invocación implícita activa y las descripciones orientadas a objetivos sin solapamiento.
- Los Markdown del proyecto consumidor son canónicos; `.lks-sdd/project.json` es un índice.
- No selecciones la pila preferente automáticamente y no generes código si falta una decisión crítica.
- Ejecuta las validaciones de `docs/VALIDATION.md` y revisa el diff antes de entregar cambios.
- No publiques, instales, hagas push o crees commits salvo autorización explícita separada.
