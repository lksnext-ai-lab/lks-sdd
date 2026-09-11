# Migración a LKS-SDD 0.17.0

## Compatibilidad

No cambia `method_version: 1.5.0` ni `schema_version: 1.5`. La extensión de interfaces es aditiva y no requiere reescribir proyectos sin integración multiunidad confirmada. `plugin_version` conserva la procedencia original.

## Proyectos sin interfaz material

No añada filas ni documentos vacíos. Backend-only y frontend standalone conservan sus gates y reciben `GATE-BROWSER-FULLSTACK-E2E: not-applicable` con razón TASK-aware.

## Proyectos con interfaz multiunidad

1. Añada `ART-INTEGRATIONS` solo si existe una interfaz material confirmada.
2. Declare `INT-###`, extremos `UNIT-###`, todos los `BIND-###`, contrato, operaciones, scopes, propietario, TASK de verificación y composición exacta.
3. En el detalle de la TASK conjunta, declare la misma selección estructurada y dependencias de consumidor y productor.
4. Use una composición de sistema exacta certificada. Si no existe, mantenga `automation_support=unsupported`.
5. Registre nueva evidencia como EVID 1.3. No edite EVID anterior.

## Reconciliación histórica

Los perfiles que consumen el backend compartido cambian de identidad exacta: `WEB-FASTAPI-REACT-KEYCLOAK-PG` 2.1.0, `API-FASTAPI-KEYCLOAK-PG-OCI` 1.1.0 y `SYS-WEB-ANGULAR-FASTAPI-KEYCLOAK-PG` 1.0.0-candidate.2. Actualizar el plugin no sustituye automáticamente locks consumidores ni autoriza preparar código. Revise el binding y su decisión, reconcilie el lock mediante el flujo gobernado y repita los gates afectados. El perfil Angular sigue candidate y no soportado.

`reconciliation-required` no invalida los checks de componente ni cambia estados. Identifique los criterios de integración, TASK y EVID afectados; abra el mecanismo PROB/PCH gobernado, implemente lo pendiente si existe y produzca una nueva ejecución autorizada que superseda únicamente la afirmación conjunta insuficiente.

## Rollback

El rollback de bundle no transforma datos. Restaure el artefacto anterior verificado y sus checksums. Un runtime anterior no debe registrar nueva evidencia para una interfaz que ya requiere scopes 0.17.
