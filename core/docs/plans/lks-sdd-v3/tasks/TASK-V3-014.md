# TASK-V3-014 · CLI y seis skills con carga progresiva

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de hosts y skills**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-013](TASK-V3-013.md).

Requisitos de responsabilidad principal: REQ-EQT-036, REQ-EQT-039, REQ-EQT-066.
Casos de aceptación principales: AC-EQT-036, AC-EQT-039, AC-EQT-089.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Integración continua de las seis capacidades
Conectar porciones funcionales desde R1: lectura/estado, configuración/autoría y propuesta;
después ejecución/calidad y migración. Conservar ausentes los comandos que aún no tengan
implementación. Registrar las limitaciones del candidato, sin declararlo utilizable
de extremo a extremo antes de disponer de sus guardas.

Cada operación mantiene un único flujo de reglas, compartido por CLI, skills y hosts.
Comprobar ejemplos de intención para las seis skills y casos ambiguos, además de revisar
la descripción; que un fichero SKILL.md exista no demuestra enrutamiento correcto.
Los manuales de rutas v2 siguen accesibles para su runtime, sin inyectarlos en v3.

## Encargo y límites
Integrar el núcleo en la CLI y las seis skills existentes con carga progresiva por versión
y operación. Mantener invocación implícita y descripciones sin solapamiento. Contrato
funcional equivalente en Codex y Copilot, declarando capacidades reales de cada host.

## Entregables e interfaces
- Añadir `scripts/v3_cli.py` y conectarlo al dispatcher `scripts/lks_sdd.py`, con
  comandos reales de consulta/preview/aplicación, no entrypoints vacíos.
- Reorganizar `skills/lks-sdd-{help,define,adopt-existing,assess-readiness,implement,verify}/`:
  entradas pequeñas y referencias por versión/operación. Mantener accesible legado.
- help consulta/explica; define configura/propuesta/plan; adopt-existing diagnostica y
  conduce adopción/migración autorizada; assess-readiness comprueba; implement ejecuta
  y corrige; verify acredita el alcance. El núcleo comparte reglas entre todas.
- Instrucciones mínimas: versión, límites, carga necesaria, fuentes de verdad, decisiones
  y continuidad. Sonar/migración se cargan cuando corresponden, no por estar instalados.
- Plantillas/instrucciones de consumidor y ayuda CLI alineadas; respuestas JSON y humanas
  usan el mismo resultado. No incorporar documentación de diseño completa al contexto diario.

## Aceptación y evidencia
Recorrer las seis entradas en v3 y las rutas legadas admitidas. Propuesta pendiente no
genera plan ejecutable; aprobación de plan no se supone al iniciar otra skill.
Una limitación del host no rebaja calidad/identidad. Un análisis existente se incorpora
sin crear pipelines. Medir metadatos propios ≤800 tokens e instrucciones ordinarias
totales ≤2.000 incluyendo referencias cargadas; justificar excesos necesarios sin recortar
garantías. Usar tokenizador identificado o etiquetar estimaciones. Evidencia focal de
routing, paridad y carga; observación de hosts reales corresponde a 017.

## Riesgos y revisión
Modificar skill descriptions puede degradar descubrimiento: revisar seis objetivos e
invocación implícita. Coordinar archivos compartidos con 015; un solo integrador del
dispatcher. Lectura adicional: técnica §§6.1–6.6 y 8; las seis skills actuales solo al
trabajar sobre su ruta correspondiente.
