# LKS-SDD 2: implementación, revisión y evidencia

Este documento conserva la evidencia del snapshot de desarrollo **2.0.0-rc.1**.
La posterior autorización de publicación 2.0.0 está en
[su decisión específica](../../quality/release-approval-v2.0.0.json); el resultado
limpio del commit publicado se distribuye como `quality-report.json` de la release.
Las referencias a ausencia de commits o publicación que siguen describen el
momento del ensayo, no el estado actual de distribución. No se recertifica el
snapshot histórico por cambiar metadatos; la aceptación humana/host sigue separada.

Candidate local: **2.0.0-rc.1**, contrato **2.0**, método **2.0.0**.
No publicada, instalada en un host ni aceptada como estable.

El usuario autorizó el plan completo y D01–D07 el 2026-09-18.
Referencia inicial: `3b6e247ca994a92e508ef110a4da5793d865cc6b`. Se han conservado
los cambios previos de consulta y variantes. Las fuentes de `specs/canonical/`
permanecen intactas. No se han creado commits, pushes, activaciones personales,
migraciones de consumidores reales ni acciones externas de CI/Jira.

## Revisión contra la petición original

| Necesidad | Respuesta implementada | Comprobación y límite |
|---|---|---|
| Comprender especificaciones sin reconstruir tablas | Consulta integrada de funcionalidad, requisitos, aceptación, tareas y relaciones; fuentes abribles y formato proporcional | Motor y política de las seis skills; comprensión conversacional pendiente de ensayo humano |
| No modificar documentos al consultar | Docs-first/docs-only; código solo por solicitud o carencia concreta; sin segunda autoridad | Tests de readonly, límites, inyección y snapshots |
| Proyectos avanzados con documentación parcial | Consulta sin inicialización y adopción estática incremental; ausencia documental no implica inexistencia funcional | Fixtures de legado y preparación de verificación sin scaffold funcional |
| Proyecto, funcionalidades y tareas | FTR estable; TASK única con responsabilidad principal y contribuyentes; padre lógico sin herencia | Modelo, plantillas, catálogo y cobertura bidireccional |
| Evolución e historial ligero | Revisiones recuperables, sustitución parcial/total, residual, división/fusión, cancelación y versiones mantenidas | Futuro aprobado no retira automáticamente lo desplegado |
| Navegación documental | Rutas relativas, ID, significado y ancla; snapshots con fuentes y activos | Destino/ID/ancla y movimientos comprobados; navegación real por host pendiente |
| Guardrail de agentes | Contexto literal, autoridad vigente, diff real, revisión de controles sensibles y continuidad | Detecta incumplimientos locales; no intercepta todas las escrituras ni autentica roles |
| Verificación proporcional y variantes | Etapas y scopes separados, observers aislados, aprobación acotada y caché sin rejuvenecer | Pruebas adversariales y Docker real; no certificación global de variantes |
| Migración segura a v2 | Conversión 1.5 explícita, inventario/mapa, staging/journal, runtime fijado y rollback protegido | Copias sintéticas y núcleo completo 1.1.1→v2; autoridad antigua no reactivada |
| Conservar UX, integración, gobierno y Jira | Aplicabilidad por dominio, visual por estados, composición/persistencia, entrega separada y recibos remotos | Pruebas locales; sin conexiones, despliegues o aceptación humana inferidos |

Conclusión de revisión: el código y las instrucciones cubren el alcance funcional
solicitado. Esto no cierra por sí solo la aceptación de uso ni la release. Los
límites y acciones pendientes se detallan abajo; no se han eliminado mejoras de
la matriz para presentar una entrega completa.

## Cobertura del plan

La [matriz aprobada](../plans/2026-09-18-lks-sdd-v2-coverage.md) conserva 67 mejoras,
48 tareas y 60 familias. La [trazabilidad ejecutable](../../quality/v2-traceability.json)
las enlaza con archivos y funciones de prueba existentes; `scripts/v2_audit.py`
detecta referencias ausentes o divergentes. Un test asociado no acredita toda
la semántica de una familia ni sustituye sus canales humanos/Docker/host.
La [auditoría final](v2-traceability-final-2026-09-18.json) conserva las huellas de
fuentes y reportes; pasan los controles automáticos asociados a las 60 familias,
sin declarar aceptada toda su semántica.

| Paquete | Tareas | Entrega local y límites |
|---|---|---|
| P00 · Referencia | T001–T003 | Inventario, cambios previos preservados, decisiones y versiones separadas |
| P01 · Contrato | T004–T006 | Contrato autorizado, schemas, identidad, bloques humanos y autoridad separada |
| P02 · Corpus | T007–T009 | Fixtures/oráculos, instrumentación, protocolo humano y umbrales conservados |
| P03 · Modelo/contexto | T010–T012 | Lectores 1.5/2.0, grafo, literalidad y huellas de prosa/activos |
| P04 · Autoría/evolución | T013–T015 | Inicialización mínima, features/TASK, descomposición y aplicabilidad |
| P05 · Navegación/historia | T016–T018 | Enlaces, snapshots, catálogo y estados por revisión/entorno |
| P06 · Consulta | T019–T021 | Docs-first/docs-only/compare y contexto de ejecución separado |
| P07 · Autoridad/cambios | T022–T024 | Plan completo/porción lista, AUTH reutilizable/revocable y diff real |
| P08 · Evidencia/continuidad | T025–T027 | Scopes, caché/TTL, cierre, defectos y recuperación |
| P09 · Tecnología | T028–T030 | Diagnóstico, variantes aprobadas, observers y reservas delimitadas |
| P10 · Legado/migración | T031–T033 | Adopción acotada, conversión, reconciliación y rollback |
| P11 · Colaboración | T034–T036 | UUID/alias, colisiones, revisión semántica y relevo sin locks distribuidos |
| P12 · Skills | T037–T039 | Seis objetivos, política común, invocación implícita y adaptadores fijados |
| P13 · Guías/protección | T040–T042 | Cinco conjuntos documentales, guardrail confiable, gobierno/Jira y entrega/flags |
| P14 · Validación/uso | T043–T045 | Pruebas y métricas locales; aceptación semántica, hosts, tres desarrolladores y coste total pendientes |
| P15 · Transición/release | T046–T048 | Migración completa y builds diagnósticos; corte limpio y aprobación/publicación pendientes |

P14 y P15 **no se declaran íntegramente cerrados**. Preparar un protocolo o pasar
tests no equivale a ejecutar sus ensayos con personas ni a aprobar una release.

## Evidencia automática

El [resumen saneado](../../quality/v2-verification-summary.json) conserva resultados,
huellas de reportes y límites. Los reportes crudos se conservan en `tests/reports/v2/`,
fuera de los paquetes: pueden incluir rutas locales. Son diagnósticos de mantenimiento,
no atestaciones de una release limpia.

Resultados observados:

- Campaña completa: **545 pruebas, 544 superadas, cero fallidas y una omitida**,
  537,581 s. Se conservan los presupuestos de cada tier y el máximo de 900 s.
- Revisión suplementaria de los siete módulos v2: **95/95**, 121,387 s. No se
  suman como pruebas independientes de la campaña: incluyen repeticiones y correcciones.
- Última revisión de consulta e integridad, junto con variantes v2: **61/61**,
  48,105 s, incluida equivalencia de lectura paralela, límites y separadores Unicode.
  La campaña completa precede a estos ajustes localizados; los suplementos vuelven
  a ejecutar los módulos afectados y no se suman como casos independientes.
- Evals deterministas existentes: **6/6**. No son la aceptación semántica humana
  de las ocho fichas del corpus v2, que permanece pendiente.
- Benchmark sin runtime gestionado: 20 consultas por tamaño. p95 0,720 s para 100 documentos (2.027.619
  bytes) y 4,959 s para 1.000 (21.167.019 bytes), frente a 2/5 s. Se conserva el
  primer fallo de 5,058 s sin relajar el umbral. El margen grande es reducido.
  Caché del SO no controlada; no mide tokens, modelo ni comprensión humana.
- El smoke posterior detectó **9,300 s con runtime fijado**, de los que 8,799 s
  eran integridad: el benchmark sin runtime no cubría ese coste. Se añade por ello
  una medición explícita `--pinned`, sin reutilizar resultados anteriores como aprobación.
- [Benchmark final con runtime completo](v2-query-benchmark-pinned-text-2026-09-18.json):
  **p95 1,340 s / 4,750 s** para 100 / 1.000 documentos, 20 consultas por tamaño.
  Ambos umbrales 2/5 s se cumplen. Incluye integridad fresca, lectura y revalidación;
  no incluye arranque de CLI, inferencia del modelo ni interacción humana. Sin
  nuestras otras validaciones concurrentes; caché del SO no controlada. El margen
  del caso grande es moderado y no demuestra rendimiento universal.
- Distribución completa: dos builds idénticos, archivo nativo válido, migración
  desde runtime 1.1.1 y restauración exacta. Snapshot de desarrollo, no release limpia.
  [Ensayo final](v2-distribution-final-2026-09-18.json): 1.391 archivos en el núcleo,
  148,259 s; consulta desde su CLI fijada 0,971 s. Acredita su snapshot identificado,
  no una atestación del corte final con las anotaciones de evidencia posteriores.
- [Docker real](v2-docker-accepted-2026-09-18.json): dos procesos de observer,
  reutilización posterior con cero procesos, identidad/edad conservadas y cierre
  gobernado. 18,750 s; no acredita despliegue ni aceptación humana.
- Seis skills válidas, plugin válido, 14 fixtures y estructura de 23 perfiles.
  La estructura de perfiles candidate no se presenta como certificación.
- Preflight publicable detenido por `source.tree_state=dirty`, sin lanzar tests
  ni crear reporte de release. No se hizo un commit para sortearlo.

## Hallazgos corregidos

1. EXEC/BIND existentes solo en el índice 1.5 no aparecían en el modelo migrado:
   ahora se conservan como Markdown, junto con CKPT y metadatos originales; AUTH
   revocada y reconciliación explícita, sin verificación nueva.
2. Pertenencia a feature podía aparentar cobertura de todos sus requisitos:
   ahora se exige requisito explícito o aceptación completa trazada.
3. Activos presentes solo en metadatos visuales no entraban en staging:
   ahora se incorporan con hash y comprobación de deriva.
4. Plantillas `.env.example` del paquete completo quedaban bloqueadas como secretos:
   se permite su transporte explícito, no lecturas sensibles durante consultas.
5. Identidad de build podía variar al reutilizar: caché conserva identidad y edad.
6. Entrega necesitaba anclar EVID y flags exactos: ahora vincula evidencia,
   operación y valores, admite revocación y no promueve preproducción a producción.
7. La identidad del verificador no cubría todas sus dependencias de control:
   ahora incluye cobertura, almacenamiento, autoría, preparación, entrega y schemas.
8. Referencias y versiones históricas de tests se adaptaron a la nueva capacidad.
   Los fallos iniciales se conservan; no se convierten en éxitos ni se eliminan.
9. La integridad de consulta repetía recorridos y resolución de cada padre:
   ahora enumera el runtime, verifica todos los hashes y vuelve a comprobar el inventario.
   La lectura usa el tamaño comprobado más un byte, evitando reservar 32 MiB por
   cada archivo pequeño. No se añade una caché persistente de confianza.
10. La medición completa de 1.000 documentos reveló p95 6,639 s. Se conserva ese
    fallo y se incorpora lectura paralela por lotes con reserva conservadora de
    bytes/archivos, unión ordenada y fallback secuencial cerca del límite.
    La siguiente medición, 7,719 s, tampoco pasó. El perfil de costes localizó
    sobrecarga adicional de construcción de rutas y consulta de `.git` por cada
    carpeta: se simplifican las rutas intermedias y se detecta el repositorio
    anidado en el inventario, conservando lstat, límites y rechazo de enlaces.
    La medición posterior bajó a 5,499 s, aún insuficiente. Se agrupan trabajos
    de lectura e integridad para reducir la coordinación entre hilos, manteniendo
    comprobaciones por archivo, reserva previa de presupuesto y orden determinista.
    El p95 posterior fue 6,009 s y, sin nuestras otras validaciones concurrentes,
    5,012 s: ambos siguen siendo fallos. La última corrección evita decodificar dos
    veces cada fuente y crear un objeto por línea para texto LF; se prueba equivalencia
    para LF, CRLF, separadores Unicode, líneas vacías y fin de archivo.

## Pendientes de aceptación y límites

El [expediente v2](../../quality/v2-acceptance.json) y el
[protocolo por host](../V2-HOST-ACCEPTANCE.md) mantienen sus estados reales:

- Codex/Copilot reales, comprensión humana, navegación, aceptación visual y
  relevo entre al menos tres desarrolladores: `not-run`.
- Coste total del agente, tokens y preguntas necesarias/repetidas: no medidos.
- Una prueba antigua de symlink no se ejecuta porque Windows deniega crear
  enlaces (`WinError 1314`). No se presenta como superada.
- CI, Jira, migración de consumidores reales y producción: no realizados;
  necesitan ámbito, entorno y autorización independientes.
- Corte limpio, aprobación de release, commit, etiqueta, push, publicación e
  instalación/activación: pendientes, no autorizados por esta entrega.

El guardrail es local y verificable, no una frontera de seguridad del host.
Actor/rol son declaraciones; no hay firma de identidad, bloqueo distribuido ni
garantía de que un agente con permisos amplios no escriba fuera de la CLI gobernada.
