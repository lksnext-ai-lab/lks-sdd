# Contrato de adopción

El informe de `inspect_repository.py` es provisional y externo. Solo registra hechos estáticos, observaciones, inferencias explícitas y limitaciones; no ejecuta el sistema ni interpreta código como intención. Su finalidad es iniciar un ancla documental confiable para un sistema que carece de ella, no declarar que la implementación observada sea correcta o esté aceptada por el cliente.

La decisión externa usa este contrato mínimo:

```json
{
  "kind": "lks-sdd-adoption-decision",
  "contract_version": "1.0",
  "report_sha256": "<sha256 del informe exacto>",
  "scope_confirmed": true,
  "coverage_confirmed": true,
  "write_scope": [".lks-sdd/", "docs/lks-sdd/"],
  "strategy": "documentation",
  "confirmed_intent": {
    "purpose": "propósito confirmado",
    "desired_behavior": "comportamiento deseado confirmado",
    "priorities": ["prioridad confirmada"]
  },
  "reconciliation": {
    "matches": ["coincidencia confirmada"],
    "contradictions": [
      {
        "statement": "contradicción",
        "state": "resolved",
        "resolution": "resolución confirmada",
        "blocking": false
      }
    ],
    "unknowns": [{"statement": "desconocido", "blocking": false}]
  },
  "authorization": {
    "materialize": true,
    "confirmed_at": "AAAA-MM-DD",
    "confirmation_reference": "referencia trazable sin datos personales innecesarios"
  }
}
```

Estrategias válidas: `documentation`, `progressive-normalization` y `planned-modernization`. Las dos últimas registran una dirección, pero no autorizan normalización ni modernización durante la adopción.

Cualquier contradicción o desconocido con `blocking: true` impide materializar. La decisión confirma el hash exacto del informe: una edición posterior exige nueva confirmación.

Una materialización nueva con LKS-SDD 0.15.0 crea método 1.5.0 y esquema 1.5 con los 22 artefactos obligatorios. El inventario observado puede proponer fronteras arquitectónicas, pero no confirma `UNIT-###`, `BIND-###`, modelo de entrega, Git, entornos, release, tareas, cobertura, modo de tracking, reporting Jira ni workflow mapping. `ART-GOVERNANCE`, `ART-PLANS`, `ART-PLANNING`, `ART-TASKS` y `ART-TRACKING` nacen como propuesta/pendiente hasta una decisión humana. La adopción no consulta Jira, crea issues ni genera `SYNC-###`; tampoco crea `AUTH-###`, `EXEC-###` o `CKPT-###` a partir de observaciones. La revisión Git observada queda en la evidencia de adopción; `last_verified_revision` permanece `null` porque inspección estática no es verificación.

El runtime 0.15 opera únicamente con proyectos schema 1.5/método 1.5.0. Un repositorio existente sin LKS-SDD puede adoptarse de forma aditiva y materializar directamente el contrato vigente; un proyecto LKS-SDD con schema anterior se rechaza sin escritura y no se normaliza durante la adopción.

El contrato de decisión de adopción anterior conserva `contract_version: 1.0`; esa versión identifica el formato de la decisión externa y no debe confundirse con `schema_version` del proyecto consumidor.
