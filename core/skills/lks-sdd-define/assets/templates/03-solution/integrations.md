---
artifact_id: ART-INTEGRATIONS
artifact_type: integrations
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.15.0"
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

# Integraciones

## Interfaces entre unidades desplegables

| Interface | State | Consumer unit | Producer unit | Bindings | Protocol | Contract | Operations | Required evidence | Primary owner | Verification task | Requirements | Exact composition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

Cada interfaz material usa un `INT-###` confirmado, un consumidor y productor distintos, todos sus `BIND-###`, operaciones `read`, `write` o `read,write`, scopes cerrados y una composición exacta `local technology declaration@version`. Una escritura exige `contract,composition,user-flow,persistence`. La TASK de verificación conjunta debe declarar el mismo alcance y depender de las tareas de ambos extremos.

## Sistemas externos

| ID | State | System | Purpose | Contract | Authentication | Failure handling | Requirements |
|---|---|---|---|---|---|---|---|

No registre credenciales. Diferencie contratos confirmados de inferencias sobre sistemas externos.
