# TASK-V3-015 · Compatibilidad y distribución local v3

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de distribución**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-014](TASK-V3-014.md).

Requisitos de responsabilidad principal: Contribución transversal; ver matriz.
Casos de aceptación principales: Comprobación conjunta; ver matriz.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Comprobación de paquete temprana
Desde la primera porción real de 014, construir/inspeccionar paquetes de prueba y resolver
referencias, recursos omitidos, runtime fijado y rutas largas. El cierre espera el conjunto;
la comprobación inicial no cambia la versión activa ni simula una release estable.

El cambio de metadatos a 3.0.0 se prepara al final de esta tarea, una vez coherentes todas
las rutas; el desarrollo anterior usa identificación explícita de candidato de prueba.
Concretar con 001 la lista de archivos reutilizados/adaptados y excluir duplicaciones
innecesarias. Un runtime v2 conservado por compatibilidad no se carga por defecto en v3.

## Encargo y límites
Preparar compatibilidad y distribución local para v3 sin cambiar el runtime operativo
de consumidores v2 ni publicar/instalar nada. Contribuye a REQ-EQT-039/054/055/058/066
y casos 039/062/063/067/089; la propiedad principal permanece en la matriz.

## Entregables e interfaces
- Actualizar metadatos locales de versión al destino 3.0.0 cuando el núcleo sea coherente:
  `.codex-plugin/plugin.json`, `distribution/dual.json`, documentación de versión y
  sus referencias necesarias. Método 3.0.0 y schema 3.0 declarados por separado.
- Adaptar `scripts/dual_distribution.py`, builders/validadores de paquete y rutas
  gestionadas para incluir runtime, schemas, referencias y plantillas realmente utilizadas.
- Ajustar el validador del contrato y sus fixtures a los tres ejes de versión de v3,
  conservando la comprobación de compatibilidad v2. Excluir del payload operativo los
  expedientes de planificación y snapshots de diseño que no necesite el consumidor.
- Preservar lectura/diagnóstico de orígenes soportados y dispatch al runtime v2 fijado
  disponible para su operación; si falta, diagnosticar, no sustituirlo por writers v3.
- Añadir guías `docs/V3-WORKFLOWS.md`, `V3-MIGRATION.md` y matriz de compatibilidad;
  README/CHANGELOG distinguen candidato, evidencia, aceptación y publicación.
- Generar paquetes de prueba en rutas temporales con las funciones de distribución y
  fixtures. No esquivar el builder oficial que exige commit limpio y evidencia de release.

## Aceptación y evidencia
Validar manifiestos, integridad, referencias y contenido de las variantes Codex/Copilot.
No falta un módulo/recurso por reducir contexto. Pruebas de instalación simulada en
fixture conservan identidad/runtime del consumidor v2 y no migran al consultar.
Lectores antiguos no escriben schema v3. El paquete no incorpora credenciales, informes
de clientes o datos de identidad reales. Entregar inventarios/checksums de paquetes de
prueba y resultados de regresión de distribución/rutas largas.

## Riesgos y revisión
La release oficial sigue requiriendo autorización y commit limpio: los ZIP de prueba
no son artefactos certificados de publicación. No modificar workflows CI/CD ni ampliar
su gate. Revisión de distribución y compatibilidad. Lectura adicional:
`docs/VALIDATION.md`, `distribution/dual.json` y builders vigentes.
