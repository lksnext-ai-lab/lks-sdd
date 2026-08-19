# Cobertura auditable de M3

## Hechos verificados

- `lks-sdd-adopt-existing` separa inspección, validación y escritura; el preflight no ejecuta código ni red y el informe se guarda fuera del repositorio.
- El inventario excluye dependencias, generados, binarios y valores sensibles; registra Git, alcance, exclusiones, cobertura, symlinks/junctions y limitaciones.
- La decisión confirma el hash exacto del informe, intención, reconciliación, estrategia y el único alcance de escritura permitido.
- La materialización aborta ante baseline `stale` o colisión, usa preview/hash/autorización y solo crea `.lks-sdd/` y `docs/lks-sdd/`.
- La migración soportada conserva el cuerpo humano, crea backup externo, valida el resultado y protege el rollback transaccional frente a cambios posteriores o backups corruptos.
- La vista cliente selecciona solo fuentes `confirmed` y `client`/`public`, bloquea indicadores sensibles y permanece pendiente de aprobación; las escrituras derivadas no siguen symlinks ni junctions.

## Correspondencia

| Épica | Implementación | Evidencia |
|---|---|---|
| EP-08 Adopción | Preflight, inventario externo, reconciliación, vigencia, preview y 22 artefactos materializados. | `skills/lks-sdd-adopt-existing/`, fixtures de repositorio limpio/sucio, parcial, stale y colisión |
| EP-09 Validadores y migraciones | Validación de especificación, trazabilidad, detección de versión, migración `0.9` → `1.0`, backup y rollback. | `scripts/validate_spec.py`, `scripts/check_traceability.py`, `scripts/migrate_project.py` |
| EP-11 Entregables para cliente | Plantilla, reglas de transformación, filtrado, procedencia, revisión y protección de colisiones. | `templates/client/`, `scripts/render_client_view.py` |

## Límites

- La inspección estática no acredita comportamiento productivo, seguridad, cumplimiento u homologación.
- Una estrategia de normalización o modernización no autoriza esos cambios durante la adopción.
- Solo se migra el contrato explícitamente soportado; cualquier otra versión recibe diagnóstico y bloqueo accionable.
- El borrador cliente requiere revisión y aprobación humana externas antes de entregarse.
