# Contrato de adopción

El informe de `inspect_repository.py` es provisional y externo. Solo registra hechos estáticos, observaciones, inferencias explícitas y limitaciones; no ejecuta el sistema ni interpreta código como intención.

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

Una materialización nueva con LKS-SDD 0.7.0 crea método 1.1.0 y esquema 1.1. Un proyecto ya materializado con esquema 1.0 sigue validándose en compatibilidad y no se reescribe por volver a ejecutar una ayuda o actualizar el plugin; su migración pertenece al flujo explícito 1.0 → 1.1. Toda entrada de `human_review_required` bloquea siempre antes de crear backup o escribir hasta resolverse en el origen 1.0 y repetir el preview; solo una lista vacía permite continuar con backup externo, hash y autorización propios. La `Identity` agregada se traslada a tres dominios `pending`, sin referencias inferidas: valida tras la migración, pero bloquea readiness hasta resolverse en 1.1.

El contrato de decisión de adopción anterior conserva `contract_version: 1.0`; esa versión identifica el formato de la decisión externa y no debe confundirse con `schema_version` del proyecto consumidor.
