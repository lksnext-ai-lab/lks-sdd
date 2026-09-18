# Plan de implementación de LKS-SDD 2

Fecha: 2026-09-18. Revisión: plan aprobado para implementación.
Estado: implementación autorizada por el usuario el 2026-09-18; en curso.
Decisión confirmada del usuario: todas las mejoras se agrupan en la versión 2 del plugin.
Decisiones D01–D07 aprobadas: contrato documental 2.0 y método 2.0.0.
La implementación se ensayó como candidate 2.0.0-rc.1. La autorización posterior
de publicación 2.0.0 se registra por separado en
`quality/release-approval-v2.0.0.json`, sin convertir aceptación humana/host en pasada.

Este es un plan de mantenimiento del propio plugin, no una inicialización ni adopción
de un proyecto consumidor. Los IDs P00–P15, T001–T048, R001–R067 y C001–C060 son
referencias de este plan, no TASK/AUTH/EVID canónicas ni aprobaciones materiales.
Los roles indicados son responsabilidades propuestas: no se inventan personas,
estimaciones, capacidad, fechas de entrega ni autorizaciones.

Documento complementario obligatorio: [cobertura y aceptación](2026-09-18-lks-sdd-v2-coverage.md).
Ambos archivos constituyen una sola planificación. La matriz conserva el origen de
cada mejora y su relación con una tarea principal, contribuyentes y casos de prueba.

## 1. Objetivo y resultado esperado

Crear una versión mayor Spec-anchored que permita comprender, definir, mantener,
implementar y verificar un proyecto desde un contrato vivo, legible y trazable.
Una persona debe entender el producto sin reconstruirlo recorriendo tablas; el
agente debe recuperar obligaciones completas, actuar dentro del alcance autorizado
y justificar el resultado mediante evidencia del sujeto técnico correcto.

Resultados exigidos:

- Especificaciones humanas y estructuradas, con navegación por funcionalidades.
- Una sola fuente canónica por obligación; índices, tableros y catálogos derivados.
- Identidad funcional estable, evolución parcial/total e historia recuperable.
- Consulta documental integrada y de solo lectura, con código cuando corresponda.
- Contexto de ejecución completo, no un resumen pensado para una consulta.
- Planificación, autorización, ejecución, continuidad y verificación coherentes.
- Variantes tecnológicas aprobables y observers seguros, con comprobación proporcional.
- Adopción progresiva, migración oficial y compatibilidad sin conversión automática.
- Colaboración controlada y comprobación de conflictos semánticos entre aportaciones.
- Seis skills claras, instrucciones compartidas y documentación del plugin mantenible.
- Guardrails verificables con límites explícitos y protección externa opcional.
- Validación adversarial y aceptación real por host, además del empaquetado.

## 2. Referencia actual y fuentes

HEAD observado al iniciar la planificación: 3b6e247ca994a92e508ef110a4da5793d865cc6b.
El árbol de trabajo tiene cambios previos y archivos no versionados de consultas y
variantes. Este plan no los modifica, incorpora, descarta ni considera una release.
P00 deberá fijar la referencia exacta aprobada antes de implementar; el HEAD por sí
solo no reproduce esos cambios locales.

Fuentes contrastadas:

- [Instrucciones de mantenimiento](../../AGENTS.md).
- [Definición original del plugin](../../specs/canonical/LKS-SDD_definicion_plugin_v1.md).
- [Arquitectura actual](../ARCHITECTURE.md).
- [Contrato documental actual](../../skills/lks-sdd-define/references/document-contract.md).
- [Método de definición](../../skills/lks-sdd-define/references/method.md).
- [Cobertura de definición](../../skills/lks-sdd-define/references/definition-coverage.md).
- [Plan de consulta previo](2026-09-17-consulta-proyecto.md) y [guía de consulta](../PROJECT-QUERY.md).
- [Guía de variantes](../PROJECT-VARIANTS.md) y [contrato propuesto](../../specs/proposed/project-variants-1.0.md).
- [Aceptación dual](../DUAL-HOST-ACCEPTANCE.md).
- [Validaciones](../VALIDATION.md) y [política de rendimiento](../../quality/performance-policy.json).
- Brief aportado por el usuario: «Evolutivo prioritario de LKS-SDD: variantes
  tecnológicas aprobables con verificación ágil», y las decisiones de esta conversación.

Hechos de partida, no promesas de v2:

1. Existen seis skills y un contrato consumidor 1.5 con 22 Markdown de núcleo.
2. La lectura estructurada actual se apoya en tablas; las referencias canónicas
   esperan IDs/listas/rangos. Enlaces Markdown requieren adaptación explícita.
3. Consultas y variantes tienen implementación local aditiva; su integración,
   distribución y aceptación v2 se deben comprobar de nuevo.
4. La consulta actual lee el checkout y no recupera automáticamente otras revisiones.
5. La autorización actual depende de huellas de especificación y planificación.
   El aislamiento de invalidaciones por ámbito no puede darse por supuesto.
6. No existe migrador público del contrato consumidor actual.
7. Skills e instrucciones no interceptan toda escritura directa del agente.
8. Pruebas automatizadas, aceptación humana, publicación e instalación son estados
   distintos. Ningún resultado anterior acredita automáticamente la versión 2.

## 3. Alcance, exclusiones y principios no negociables

### Incluido en la versión 2

Todas las mejoras R001–R067 de la matriz, sin sustitución por un MVP menor ni
aplazamiento silencioso. La secuencia de construcción divide la entrega, no elimina
obligaciones. Las capacidades actuales de perfiles, UX, gobierno, tracking,
evidencia y distribución se conservan o migran explícitamente con regresión.

### Fuera de la autorización de este plan

- Modificar proyectos consumidores reales o migrarlos sin su autorización específica.
- Cambiar specs/canonical/ para resolver diferencias de implementación.
- Crear una séptima skill, MCP, conectores, hooks, aplicaciones o agentes ejecutables.
- Crear un portal web, servicio central de coordinación o nuevo gestor de tareas.
- Configurar permisos/ramas protegidas/CI remoto, acceder a Jira o producción.
- Crear commits, tags, pushes, publicaciones, instalaciones o activaciones.
- Inventar soporte para todos los schemas históricos o locks distribuidos.

P13 incluye el contrato, verificador offline y ejemplos de protección de integración.
Habilitarlos en un repositorio real es una acción externa separada. El prototipo
de contexto de estudios previos no se integra por sus resultados sintéticos:
debe superar el corpus y los controles de esta versión.

### Invariantes

- Markdown y evidencia son fuentes primarias; project.json es índice, no otra verdad.
- Consulta/análisis/readiness no escriben ni aprueban.
- Una modificación autorizada evoluciona el contrato sin borrar su historia.
- Código observado no equivale a intención, aceptación o ejecución en producción.
- Naturaleza, estado, autoridad, vigencia y ámbito se distinguen por elemento.
- Ni catálogo completo ni toda la aplicación documentada son requisitos de consulta.
- Implementar exige suficiencia del ámbito y sus dependencias; la parcialidad global
  no justifica ocultar incertidumbre crítica.
- Aprobación de plan, autorización de ejecución, aprobación tecnológica, verificación
  y entrega no se sustituyen mutuamente.
- Solo se reutiliza evidencia realmente aplicable, íntegra y vigente.
- Datos del repositorio y adjuntos no otorgan permisos ni alteran instrucciones.
- Cada claim de guardrail identifica si orienta, detecta, rechaza una transición o
  depende de controles externos. No se promete seguridad absoluta del host.

## 4. Diseño objetivo que deberá cerrar P01

### 4.1 Documentación del consumidor

Estructura propuesta para proyectos nuevos o migrados, no un conjunto de carpetas
vacías obligatorias:

    docs/lks-sdd/
    ├── README.md
    ├── 00-control/
    ├── 01-context/
    ├── 02-specification/
    │   ├── catalog.md
    │   ├── features/
    │   │   └── FTR-###-nombre/
    │   │       ├── specification.md
    │   │       ├── details/               Solo cuando aporte contenido
    │   │       └── assets/                Solo materiales propios
    │   ├── shared/
    │   │   ├── business-rules.md
    │   │   ├── non-functional-requirements.md
    │   │   └── technical-constraints.md
    │   └── flows/                        Flujos transversales aplicables
    ├── 03-solution/
    ├── 04-delivery/
    │   ├── increments.md
    │   ├── plans.md
    │   ├── planning-coverage.md
    │   ├── tasks/
    │   └── checkpoints/
    ├── 05-quality/
    └── 06-operation/

Los bloques principales tienen número; las subcarpetas tienen nombres semánticos
o IDs. Las carpetas FTR son hermanas: la jerarquía funcional es una relación, no
una obligación de anidar rutas. Los IDs no indican prioridad ni orden de desarrollo.

Cada especificación reúne finalidad, alcance, comportamiento, reglas/excepciones,
requisitos propios, aceptación, relaciones y evolución. Las reglas compartidas
se referencian sin copiar. Una división del documento traslada contenido y mantiene
su identidad; no crea dos definiciones canónicas. La ficha TASK es la autoridad de
su trabajo; los estados de AUTH/EXEC/EVID conservan sus propios registros.

README, catálogo, tablero y relaciones inversas son vistas derivadas. Pueden
mostrarse sin persistir; exportarlas/materializarlas requiere acción explícita,
procedencia y política de sobrescritura que preserve ediciones humanas.

Los anexos de UX/accesibilidad, datos, identidad, seguridad, privacidad,
integraciones, arquitectura y operación dependen de aplicabilidad y riesgo.
Prototipos, capturas y aprobación humana mantienen su semántica, sin cuotas que
sustituyan cobertura ni imágenes generadas presentadas como aceptación.

### 4.2 Modelo funcional, documental y temporal

La navegación humana es proyecto → funcionalidades → tareas. El modelo admite
una funcionalidad en varios incrementos y tareas que contribuyen a varias.
Distingue identidad, definición, intervención y trabajo. Se reutilizan INC/PCH,
PLAN/REL/TASK y CHG; no se crea un segundo sistema de gestión.

Relaciones: agrupación/pertenencia, uso, dependencia, modifica, sustituye parcial
o totalmente, divide/fusiona, verifica y contribuye. Un padre no transmite
automáticamente requisitos, autorización, aceptación ni estado.

Una definición identifica fuentes recuperables y revisiones exactas; no basta
conservar hashes. Sustituciones declaran alcance residual y efectividad. Se
admiten versiones mantenidas, ramas, entornos y flags sin un único estado global.
Aprobado para el futuro no significa implantado hoy. La salud actual no reescribe
el hecho histórico de una ejecución.

Un nuevo enlace contiene ID y texto útil, ruta relativa y ancla estable.
El parser valida ID, destino y tipo; no interpreta el enlace como permiso.
Las referencias históricas no se redirigen silenciosamente a texto vigente.

### 4.3 Contexto y cambio

Modelo normalizado compartido, derivado de fuentes versionadas. Lectores específicos
por contrato; nada de reinterpretar v1 como v2 cambiando solo el encabezado.

El contexto de consulta responde con suficiencia y límites. El de ejecución
conserva obligaciones completas, entradas/salidas, tipos, restricciones, excepciones,
precedencias, seguridad, mutabilidad, contratos visuales, contribuciones y dependencias.
La incertidumbre crítica amplía la búsqueda o bloquea el ámbito, no desaparece.

Las huellas incluyen bloques normativos completos, relaciones, activos y versión
del lector/política pertinentes. Lo puramente derivado se excluye mediante reglas
deterministas; no se ignora un cambio porque el agente lo llame cosmético.

Cada cambio material explicará qué cambia, qué permanece, qué consumidores
afecta, qué pruebas lo acreditarán y qué queda desconocido. El control contrasta
el diff real con la referencia aprobada, incluidos tests, gates y configuración.

### 4.4 Variantes y verificación proporcional

Conservar modo estricto por defecto. Diferenciar compatibilidad exacta/reglas
certificadas, variante sin evaluar, aprobación local, incompatibilidad demostrada
e información insuficiente. compatible-certified solo se concede con reglas
certificadas comprobables; si no existen, se conserva como estado reservado.

Aprobación durable: proyecto/release/incremento/TASK, referencia, stack/versiones,
diferencias, hashes manifests/locks, razones/riesgos, gates, entorno/etapa,
rol/identidad declarada, fecha/caducidad y referencias AUTH/EXEC/CKPT aplicables.
No es un flag force ni una autenticación organizativa por escribir un nombre.

Observer aprobado: hash, código revisado, comando/imagen exactos, schemas, scopes
e interfaces, nonce y artefactos verificables. Aislamiento con mínimos privilegios,
sin secretos ni montaje escribible del contrato, y límites de red/recursos/salida.
No sustituir silenciosamente el empaquetado ni confiar en stdout passed.
Requisitos externos no observables quedan pendientes, no simulados como superados.

Diagnóstico ligero; desarrollo sobre impacto; integración sobre contratos,
composición y persistencia; release con campaña exigida por política.
Reportar executed/reused/omitted y motivo, sin omisión crítica como passed.
No rejuvenecer observed_at ni reutilizar fallos/bloqueos. Cierre con reservas
solo si política, aprobación y todos los gates críticos aplicables lo permiten;
nunca concede por sí mismo entrega o despliegue.

### 4.5 Migración, convivencia y colaboración

Migrador oficial 1.5→nuevo contrato, con ruta dedicada que valida runtime origen
y destino sin eludir el lock ordinario. Instalación del plugin y migración del
proyecto son acciones distintas. Orígenes desconocidos reciben diagnóstico,
no una transformación aproximada.

Diagnóstico → preview/mapa → staging → validación → aprobación de propuesta exacta
→ aplicación recuperable → informe. Las decisiones semánticas se revisan antes
del apply; toda edición posterior relevante del origen invalida el preview.
Incluye journal, idempotencia, detección de colisiones, rollback y ensayo de
interrupciones. No prometer atomicidad multiarquivo que el sistema no proporcione.

Preservar IDs, contenido personalizado, activos, decisiones, historia y bytes EVID.
Conservar desconocidos como tales. Ejecutar pausa segura y reconciliar AUTH/EXEC/CKPT
antes de continuar. No fabricar nueva verificación ni dos contratos activos.
Rollback detecta trabajo posterior y no lo destruye. Código/dependencias/despliegue
quedan fuera de la conversión.

Colaboración: identidad estable, base de revisión, ámbito de escritura y contratos
compartidos explícitos; handoff durable y revisión semántica al integrar.
Continuar trabajo independiente cuando sea seguro. No crear un coordinador
central ni afirmar exclusión distribuida por disponer de locks locales.

### 4.6 Skills, instrucciones y documentación interna

| Skill | Responsabilidad de v2 | Límite |
|---|---|---|
| help | Consultas, catálogo, historia, estado y explicación de migración | Solo lectura; no arranca otro workflow por preguntar |
| define | Definición/evolución, descomposición y planificación; conducir conversión solicitada | No código, migración automática ni aprobación inferida |
| adopt-existing | Inspección y baseline acotadas, reconciliación y materialización autorizada | No normalización de código ni intención inferida |
| assess-readiness | Suficiencia/plan/porción/automatización/AUTH por separado | No arreglos ni autorizaciones silenciosas |
| implement | Contexto íntegro, ejecución autorizada, diff y continuidad | No alcance añadido ni autoconformidad |
| verify | Gates, regresión, integración y evidencia exacta | No aceptación humana, certificación global o entrega inventadas |

Política común breve de intención, fuentes, autoridad, incertidumbre y acción segura.
Referencias condicionales; scripts para invariantes deterministas. Mantener
invocación implícita. AGENTS de consumidor conserva instrucciones ajenas, no copia
todo el método ni se instala durante una consulta. Los archivos agents/openai.yaml
son metadatos, no agentes autónomos.

Documentación del plugin: contrato normativo versionado; guías de uso; referencia
técnica; mantenimiento/migraciones/distribución; evidencia de versión. Una fuente
por regla, con correspondencia a control y prueba. Guías históricas inequívocas.
Conservar tracking local/Jira opcional y núcleo común Codex/Copilot, sin ampliar
las capacidades reales del host ni introducir herramientas no autorizadas.

## 5. Decisiones de implementación aprobadas

El usuario aprobó las recomendaciones D01–D07 el 2026-09-18 y autorizó implementar
el plan completo. La aprobación del diseño no identifica responsables humanos de
piloto ni autoriza publicación, instalaciones activas o cambios remotos. El contrato
de implementación concreta estas decisiones en specs/proposed/project-contract-2.0.md.

| ID | Decisión | Recomendación | Cierre necesario |
|---|---|---|---|
| D01 | Versiones de contrato/método y compatibilidad | Nuevo contrato mayor independiente de distribución; primer origen migrable 1.5; v1 conserva runtime fijado | T003 antes de P01 |
| D02 | Identidad y alias entre clones | Identidad técnica única con alias legible estable; preservar IDs antiguos y rechazar colisiones hasta reconciliar | T004 antes de T034 |
| D03 | Sintaxis de bloques, anclas e historia recuperable | Markdown con bloques normativos identificados y refs tipadas; snapshots/revisiones disponibles sin red; semántica de fuentes única | T006 antes de P03 |
| D04 | Autoridad, roles, riesgo y política de cierre | Roles declarados no autenticación; gates críticos no dispensables; reserva tecnológica separada de aceptación | T005 antes de P07/P09 |
| D05 | Alcance externo y responsables de aceptación | Verificador/ejemplos locales en v2; habilitación real CI/Jira/permisos/pilotos mediante autorización aparte y responsables reales | Antes de T041/T045 |
| D06 | Budgets y criterios de agilidad | Conservar presupuestos vigentes, objetivos locales de consulta 2 s/5 s y comparación por etapa; fijar antes de optimizar | T009 antes de T044 |
| D07 | Condiciones de release y hosts anunciados | Evidencia técnica y aceptación por escenario/host para los claims de v2; no heredar aprobación 1.x | Antes de P14/P15 |

## 6. Paquetes de trabajo y dependencias

Cada tarea entrega implementación/documentación y tests focalizados; no se deja
toda la prueba para P14. Dentro de cada paquete el orden inicial es primera tarea
→ segunda → tercera; solo se relaja con interfaces y condiciones de entrada
explícitamente revisadas. Las dependencias de paquetes son condiciones de entrada,
no autorización para lanzar agentes o escritores concurrentes.

| Paquete | Entrega | Depende de | Tareas |
|---|---|---|---|
| P00 | Referencia inicial y decisiones de contrato | — | T001, T002, T003 |
| P01 | Contrato documental y funcional v2 | P00 | T004, T005, T006 |
| P02 | Corpus y evaluación desde el inicio | P00 | T007, T008, T009 |
| P03 | Modelo común y contexto íntegro | P01, P02 | T010, T011, T012 |
| P04 | Autoría documental y evolución funcional | P03 | T013, T014, T015 |
| P05 | Enlaces, catálogo e historia | P03, P04 | T016, T017, T018 |
| P06 | Consulta humana y selección de contexto | P03, P05 | T019, T020, T021 |
| P07 | Planificación, autorización y control del cambio | P03, P04, P06 | T022, T023, T024 |
| P08 | Verificación, evidencia y continuidad | P07, P09 | T025, T026, T027 |
| P09 | Variantes tecnológicas y observers | P03, P07 | T028, T029, T030 |
| P10 | Adopción progresiva y migrador oficial | P04, P05, P07, P08 | T031, T032, T033 |
| P11 | Colaboración y reanudación entre personas | P07, P08 | T034, T035, T036 |
| P12 | Seis skills e instrucciones coherentes | P06, P08, P09, P10, P11 | T037, T038, T039 |
| P13 | Documentación del plugin y protección de entrega | P08, P09, P12 | T040, T041, T042 |
| P14 | Validación integrada y aceptación de uso | P10, P11, P12, P13 | T043, T044, T045 |
| P15 | Ensayo de transición y release 2 | P14 | T046, T047, T048 |

### P00 — Referencia inicial y decisiones de contrato

Dependencias: —. Rol propuesto: Producto, mantenimiento y QA.

- **T001:** Inventariar el alcance conversacional y el brief original; registrar HEAD, cambios locales y capacidades ya implementadas sin publicarlas.
- **T002:** Medir la referencia actual con fixtures, validaciones y limitaciones conocidas; separar defectos previos de regresiones.
- **T003:** Registrar la aprobación D01–D07 y concretar el contrato v2, compatibilidad, autoridad y límites. Cada detalle bloquea solo sus tareas dependientes; no se exige adelantar responsables de piloto al diseño del lector.

Criterio de salida: Inventario y decisiones revisados; ninguna funcionalidad actual se pierde por omisión; no se modifica specs/canonical/ para ajustar código.

### P01 — Contrato documental y funcional v2

Dependencias: P00. Rol propuesto: Diseño del método y mantenimiento.

- **T004:** Definir identidad funcional, revisiones recuperables, agrupación, relaciones tipadas, sustituciones y vigencia por versión/entorno.
- **T005:** Definir fuente canónica por dato, naturaleza/estado/autoridad por elemento, obligaciones por etapa y modelos de autorización.
- **T006:** Especificar formato híbrido, bloques normativos, referencias Markdown, metadatos, sintaxis y reglas de compatibilidad.

Criterio de salida: Contrato propuesto versionado con ejemplos positivos/negativos; semántica suficiente para construir lectores sin reinterpretaciones silenciosas.

### P02 — Corpus y evaluación desde el inicio

Dependencias: P00. Rol propuesto: QA y revisión funcional.

- **T007:** Crear fixtures nuevas/heredadas, multitecnología, multiusuario y con formatos personalizados; fijar oráculos de obligaciones y acciones prohibidas.
- **T008:** Preparar instrumentación de lecturas, escrituras, procesos, red, cambios de snapshot, recuperación y fallos inyectados.
- **T009:** Definir rúbrica humana, escenarios por host y protocolo de métricas; congelar umbrales antes de optimizar.

Criterio de salida: Corpus y protocolo revisados independientemente de las salidas del código; resultados inicialmente not-run, sin sesgar pruebas para conseguir verde.

### P03 — Modelo común y contexto íntegro

Dependencias: P01, P02. Rol propuesto: Mantenimiento del runtime.

- **T010:** Implementar lectores versionados 1.5/v2 y modelo normalizado derivado de Markdown, registros y evidencias, sin segunda base de datos autoritativa.
- **T011:** Resolver fuentes, IDs, relaciones, contribuciones, obligaciones compartidas, prosa, activos, ambigüedades y aplicabilidad conocida/desconocida.
- **T012:** Implementar snapshots y huellas versionadas que cubran texto normativo completo, relaciones y activos; distinguir vistas regenerables de entradas contractuales.

Criterio de salida: Sin IDs duplicados activos ni obligaciones perdidas; una edición relevante en prosa invalida el contexto y no se acepta un contexto vacío como listo.

### P04 — Autoría documental y evolución funcional

Dependencias: P03. Rol propuesto: Mantenimiento de definición y plantillas.

- **T013:** Crear plantillas legibles, inicialización v2 por obligaciones y ficha TASK fuente única; tablero y catálogo derivados bajo escritura explícita.
- **T014:** Implementar gestión de funcionalidades y cambios: misma identidad, división/fusión, sustitución parcial/total y descomposición de solicitudes extensas.
- **T015:** Integrar requisitos compartidos y anexos aplicables de UX, datos, seguridad, interfaces, arquitectura, decisiones y operación, sin documentos vacíos.

Criterio de salida: Proyecto nuevo legible y validable; solicitudes y plan cubiertos en ambos sentidos; no se crean tareas para historia desconocida ni decisiones por inferencia.

### P05 — Enlaces, catálogo e historia

Dependencias: P03, P04. Rol propuesto: Mantenimiento documental y consulta.

- **T016:** Ampliar parser y validadores para IDs enlazados, rutas relativas y anclas estables; validar correspondencia etiqueta/ID/destino y enlaces inversos derivados.
- **T017:** Implementar catálogo e historia con definiciones recuperables mediante snapshots o revisiones disponibles, sin checkout, fetch ni cambios de rama durante consulta.
- **T018:** Construir vistas de tareas, requisitos, impactos y estados separados por definición/revisión/entorno; materialización opcional con procedencia.

Criterio de salida: Navegación real al elemento correcto; catálogos no son segunda autoridad; fuentes ausentes, futuras o históricas no se presentan como vigentes.

### P06 — Consulta humana y selección de contexto

Dependencias: P03, P05. Rol propuesto: Mantenimiento de consulta y experiencia.

- **T019:** Integrar la consulta local existente: docs-first, docs-only y compare, legado sin índice y ampliación al código justificada y acotada.
- **T020:** Separar contexto de explicación y contexto obligatorio de ejecución; incluir tareas contribuyentes, consumidores y reglas transversales no enlazadas cuando sean pertinentes.
- **T021:** Implementar explicación profesional y neutra, tablas/listas/diagramas justificados, fuentes por afirmación, límites útiles y ampliación progresiva.

Criterio de salida: Consulta sin escrituras/ejecuciones; decisiones de negocio no inferidas del código; obligación crítica no desaparece por resumir o limitar búsqueda.

### P07 — Planificación, autorización y control del cambio

Dependencias: P03, P04, P06. Rol propuesto: Mantenimiento de planificación y ejecución.

- **T022:** Adaptar cobertura, propietarios/contribuyentes, dependencias y readiness por porción frente al plan completo; conservar planificación incremental explícita.
- **T023:** Vincular confirmaciones y AUTH a inputs vigentes, política, rol y alcance; reutilizar aprobaciones válidas y bloquear divergencias sin auto-renovación.
- **T024:** Contrastar diff real con alcance y referencia aprobada, incluyendo requisitos, tests, verificadores, dependencias y configuración; presentar desviaciones para decisión.

Criterio de salida: No basta un plan correcto para cerrar un diff fuera de alcance; tareas canceladas no satisfacen dependencias; campos de actor no equivalen a identidad autenticada.

### P08 — Verificación, evidencia y continuidad

Dependencias: P07, P09. Rol propuesto: Mantenimiento de verificación y continuidad.

- **T025:** Adaptar gates tipados y selección proporcional por etapa; usar aceptación acordada, negativos, regresión e integración real como oráculo del resultado.
- **T026:** Implementar reutilización segura de evidencia determinista por inputs/sujeto/motor/aprobación/TTL; reportar executed/reused/omitted y conservar observed_at.
- **T027:** Adaptar TASK/EXEC/CKPT, pausa, reanudación, bloqueos, reapertura, cancelación y salud actual, preservando EVID histórica y autorizaciones obsoletas.

Criterio de salida: No cerrar con evidencia ajena, caducada o de alcance inferior; la recuperación revalida el repositorio; aprobar desarrollo no acredita entrega.

### P09 — Variantes tecnológicas y observers

Dependencias: P03, P07. Rol propuesto: Mantenimiento de compatibilidad y revisión técnica.

- **T028:** Integrar diagnóstico de diferencias y estados exact-certified, compatible-certified, unassessed-variant, approved-project-variant, incompatible y not-assessed con semántica explícita.
- **T029:** Integrar aprobación durable acotada de variante mediante preview/hash/apply, diferencias, riesgos, gates, entorno, etapa, responsable y caducidad.
- **T030:** Integrar observers empaquetados, aprobados de consumidor y experimentales con aislamiento, contrato de salida, integridad de artefactos y política de cierre con reservas.

Criterio de salida: Variante válida puede verificarse bajo política sin certificación global; incompatibilidad demostrada bloquea; ruta estricta sigue predeterminada y sin nuevas preguntas.

### P10 — Adopción progresiva y migrador oficial

Dependencias: P04, P05, P07, P08. Rol propuesto: Mantenimiento de adopción/migración y QA.

- **T031:** Definir y materializar baseline acotada para legado, con fronteras, dependencias, incertidumbres y reconciliación, sin cambiar código ni inventar intención.
- **T032:** Implementar diagnóstico y preview de migración 1.5→v2, mapa elemento a elemento, conservación de contenido personalizado y propuestas semánticas separadas.
- **T033:** Implementar staging, autorización exacta, aplicación recuperable, validación, recibo, transición del runtime fijado y rollback que detecte trabajo posterior.

Criterio de salida: Ningún contenido sin destino conocido; cero EVID reescritas; migrar no verifica la aplicación ni autoriza reanudar; no hay dos fuentes activas tras el corte.

### P11 — Colaboración y reanudación entre personas

Dependencias: P07, P08. Rol propuesto: Mantenimiento de continuidad y QA.

- **T034:** Implementar la estrategia aprobada de identidad/alias y detección de colisiones entre clones, conservando IDs históricos y referencias.
- **T035:** Detectar cambios de base y contratos compartidos; definir propiedad de escritura por ámbito, reconciliación semántica e integración conjunta.
- **T036:** Adaptar relevos duraderos entre usuarios, sesiones y hosts con contexto, autoridad, cambios locales, límites y siguiente acción segura.

Criterio de salida: Dos cambios que Git fusiona sin conflicto no se consideran semánticamente compatibles sin comprobación; no se promete un lock distribuido.

### P12 — Seis skills e instrucciones coherentes

Dependencias: P06, P08, P09, P10, P11. Rol propuesto: Mantenimiento de skills y revisión de experiencia.

- **T037:** Consolidar política común de intención, autoridad, suficiencia, incertidumbre, preguntas, límites y escalado; eliminar reglas normativas contradictorias.
- **T038:** Actualizar help, define, adopt-existing, assess-readiness, implement y verify con responsabilidades diferenciadas, referencias condicionales y seis pruebas de routing propias.
- **T039:** Actualizar metadatos de invocación, ejemplos y adaptadores; mantener activación implícita y proponer bloques AGENTS gestionados solo con autorización.

Criterio de salida: No séptima skill ni nuevos agentes ejecutables; consulta no activa definición; ninguna skill declara capacidades o permisos ausentes en el host.

### P13 — Documentación del plugin y protección de entrega

Dependencias: P08, P09, P12. Rol propuesto: Mantenimiento, revisión de gobierno y documentación.

- **T040:** Reorganizar contrato propuesto, guías, referencia técnica, mantenimiento y evidencia de release; documentar modos, migración, límites y aprendizaje progresivo.
- **T041:** Preparar verificador offline/CI y ejemplos de política de integración confiable, revisión de cambios de gates y aprobación externa sin instalar hooks ni configurar repositorios remotos.
- **T042:** Conservar gobierno de entrega, Git/entornos/recuperación, tracking repository-only y Jira opcional, recibos y handoffs visuales, adaptándolos al contrato v2.

Criterio de salida: Guías no redefinen el contrato; estado remoto no autoriza trabajo local; protección externa se declara habilitada solo tras configuración y evidencia reales.

### P14 — Validación integrada y aceptación de uso

Dependencias: P10, P11, P12, P13. Rol propuesto: QA, responsable de producto y usuarios de piloto.

- **T043:** Ejecutar matriz completa positiva, negativa, adversarial y de regresión, incluidas mutaciones de contrato/pruebas, migración y fallos concurrentes.
- **T044:** Medir latencia fría/caliente, lectura total, preguntas, procesos y reutilización por etapa; comparar con referencia sin sacrificar suficiencia ni rebajar límites.
- **T045:** Ejecutar escenarios conversacionales reales en Codex y Copilot: comprensión, navegación, modos, autorización, relevo y pruebas con varios usuarios.

Criterio de salida: Cero fallos críticos en el corpus aplicable; evidencia por host; no equiparar tests de paquete con aceptación humana ni bytes con ahorro facturado.

### P15 — Ensayo de transición y release 2

Dependencias: P14. Rol propuesto: Mantenimiento de distribución y responsable de release.

- **T046:** Ensayar migración completa de copias sintéticas/anonimizadas autorizadas, restauración y convivencia de proyectos sin migrar; publicar matriz exacta de soporte.
- **T047:** Preparar versión 2, dos builds reproducibles, extracción/validación e instalación aislada de ambos paquetes; comprobar Windows y runtime fijado.
- **T048:** Preparar expediente de release, notas, límites, formación y aprobación nueva; publicar/instalar/activar únicamente tras autorizaciones separadas.

Criterio de salida: Release limpia y exacta, sin heredar aceptación 1.x; canales no ejecutados visibles; la función no se anuncia soportada en un host sin su evidencia exigida.

## 7. Secuencia de integración

Orden topológico propuesto, sin estimaciones de duración:

1. P00 fija referencia y decisiones; P01 especifica el contrato y P02 fija el corpus.
2. P03 construye el modelo; P04 materializa documentos; P05 incorpora navegación/historia.
3. P06 integra consulta y contexto; P07 adapta planificación/autoridad.
4. P09 integra variantes antes del cierre de P08, que prueba verificación y continuidad conjuntas.
5. P10 migración y P11 colaboración pueden desarrollarse en ámbitos separados tras P08.
6. P12 consolida seis skills con contratos ya definidos; P13 completa guías y protección de entrega.
7. P14 ejecuta campaña conjunta; P15 ensaya transición y prepara release.

Se pueden elaborar borradores de guías, fixtures y adaptadores antes de sus puertas
de integración. La conformidad final siempre depende del contrato y runtime
efectivos. El orden no es un camino crítico temporal: faltan capacidad y duraciones.

Hitos de revisión:

| Hito | Resultado | No significa |
|---|---|---|
| H1 | P00–P02: contrato propuesto, corpus y decisiones cerradas | Implementación ni aceptación del producto |
| H2 | P03–P06: definición, navegación y consulta demostradas | Autorización de implementación de consumidores |
| H3 | P07–P09: ejecución y verificación gobernadas | Despliegue ni certificación global de variantes |
| H4 | P10–P13: migración, colaboración, skills y protección preparadas | Migración o configuración remota ya ejecutadas |
| H5 | P14: aceptación técnica y humana de alcance anunciado | Publicación/instalación |
| H6 | P15: expediente y paquete de release exactos | Activación en todos los equipos |

## 8. Superficies de cambio previstas

Rutas actuales que se revisarán, no lista de archivos modificados en esta entrega:

| Área | Superficies |
|---|---|
| Contrato y fuente | specs/proposed/, schemas/, scripts/contract_engine.py, scripts/planning_engine.py |
| Documentación de consumidores | skills/lks-sdd-define/assets/templates/, lectores y materializadores de definición/adopción |
| Consulta y vínculos | scripts/query_sources.py, query_context.py, query_code.py, query_render.py, query_project.py |
| Ejecución y continuidad | scripts/manage_planning.py, manage_tasks.py, work_task.py, manage_continuity.py |
| Verificación y variantes | scripts/evidence_contract.py, delivery_engine.py, project_variants.py, manage_project_variants.py, consumer_observer.py, variant_preparation.py, variant_verification.py |
| Migración | Nuevo módulo y contrato dedicados por diseñar; runtime_doctor.py y dispatcher con ruta autorizada explícita |
| Skills y hosts | Las seis skills, referencias compartidas, agents/openai.yaml, scripts/dual_distribution.py y adaptadores |
| Calidad y distribución | tests/, quality/test-suites.json, quality/test-impact-map.json, manifests, distribution/ y builders |
| Guías | docs/ARCHITECTURE.md, VALIDATION.md, PROJECT-QUERY.md, PROJECT-VARIANTS.md, instalación, aprendizaje y aceptación dual |

No se reescriben en bloque los archivos anteriores. P00 determina solapamientos con
trabajo local y P01 fija contratos antes de cambios. Todo cambio en entradas de
certificación requiere recertificar perfiles afectados; no basta conservar su etiqueta.

## 9. Validación y aceptación

La [matriz](2026-09-18-lks-sdd-v2-coverage.md) define 67 mejoras, 48 tareas y 60
escenarios. Cubrirlos en el plan no significa que estén implementados o superados.

Canales separados:

1. Estructural: formatos, IDs, ownership, enlaces, DAG, schemas y manifiestos.
2. Determinista: autoridad, transiciones, snapshots, gates, evidencia y recuperación.
3. Semántico: suficiencia, ambigüedad, fidelidad, impacto y no autoconformidad.
4. Operativo: rendimiento, procesos, preguntas y reutilización por etapa.
5. Conversacional/humano: routing, comprensión y navegación en cada host.
6. Distribución: integridad, reproducibilidad, Windows e instalación aislada.
7. Organización/entrega: controles externos realmente habilitados y aprobación de release.

Todos los escenarios comienzan not-run. Cada resultado registra fixture, versión,
revisión, inputs, acción, esperado/observado, pruebas y límites; humanos añaden host,
modelo y evaluación. Las aserciones automáticas no sustituyen juicio humano.
No usar solo coincidencia literal de frases o cobertura de IDs como prueba semántica.

Criterios de salida de v2:

- Todas las mejoras incluidas tienen implementación y evidencia aplicable.
- Ninguna obligación crítica se pierde en el corpus; ningún caso negativo permite
  un cierre indebido dentro del flujo gestionado.
- No se pierden fuentes, historia ni personalizaciones en migración y recuperación.
- No hay regresiones críticas ni incumplimientos de autorización/seguridad abiertos.
- Runtime, contrato y documentación concuerdan; no hay reglas históricas activas contradictorias.
- Presupuestos congelados satisfechos o revisión explícita justificada antes de aceptación.
- Cada host anunciado tiene evidencia exigida; canales ausentes siguen not-run.
- No se ocultan reservas de variantes ni se hereda aceptación de la versión 1.

Métricas: cero escrituras/ejecuciones de consumidor en consultas; cero lecturas
de implementación con docs suficientes/docs-only; cero repreguntas por decisiones
vigentes sin cambios; cero gates pesados en diagnóstico sin necesidad.
Medir muestras pequeñas/medias/grandes, frío/repetición, lectura total del agente,
reintentos y ampliaciones. Objetivos locales existentes de consulta: p95 ≤2 s para
100 archivos/2 MiB y ≤5 s para 1.000 archivos/20 MiB, con runner identificado y
al menos 20 consultas por tamaño. No extrapolar esos tiempos a la latencia del modelo.
Otros presupuestos se fijan en D06 antes de medir; no se modifican para ocultar fallos.

Aplicar [VALIDATION.md](../VALIDATION.md): tests focalizados durante desarrollo,
un tier por módulo, harness integral una vez por candidato exacto, recertificación
cuando cambien entradas, dos builds, extracción y pruebas aisladas de distribución.
Docker, navegador y canales externos no se ejecutan durante una consulta.
La release v2 tendrá expediente/aprobación propios, no el fichero de aprobación 1.1.1.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación / responsable |
|---|---|
| Reescritura grande que pierde reglas | Lectores versionados, corpus de conservación y P01/P03 antes de autoría nueva |
| Más legibilidad pero prosa fuera de huellas | Bloques normativos completos y C002/C026, no parser solo de tablas |
| Catálogo como segunda especificación | Fuente única y regeneración explícita, C012/C016 |
| Contexto reducido omite excepciones | Oráculo completo, contribuyentes y desconocidos; calidad antes que compresión |
| Aprobación local aparenta autoridad autenticada | Declarar frontera de confianza; control externo opcional y probado |
| Agent modifica código y pruebas para autoaprobarse | Referencia aprobada, revisión de diff y verificador independiente de inputs no confiables |
| Migración interrumpida o rollback destructivo | Staging/journal, snapshots, idempotencia y rechazo ante cambios posteriores |
| Colisión o contradicción entre usuarios | Identidad/alias, base comprobada, ownership y revisión semántica conjunta |
| Variantes debilitan modo estricto | Ruta optativa, políticas explícitas, pruebas negativas y recertificación afectada |
| Preguntas/gates duplicados ralentizan trabajo | Reutilización vigente, modos por etapa y métricas extremo a extremo |
| Instrucciones/versiones divergen entre hosts | Núcleo compartido, guías no duplicadas y aceptación por host |
| Defecto previo impide empaquetar | Registrar en P00, resolver con evidencia; no borrar estudios ni esconder fixtures |
| Crece el alcance sin autorización | Matriz bidireccional; ninguna tarea sin mejora o requisito de preservación asociado |

## 11. Revisión crítica del plan

La revisión incluye pasada de cobertura y pasada adversarial del diseño.

Correcciones incorporadas para evitar omisiones o promesas excesivas:

1. El brief original de variantes tiene tareas propias, incluidos observers, TTL,
   aprobación única, reservas, modo rápido y regresión de perfil exacto.
2. La estructura final usa 02-specification/ y carpeta por FTR; no queda features/
   sin numeración en la raíz ni anidación física obligatoria de funcionalidades.
3. Los enlaces son parte del contrato/parser/validación, no solo formato de salida.
4. Historia incluye recuperación de contenido, no únicamente hashes.
5. El contexto de tareas contribuyentes y la prosa normativa tienen trabajo y tests propios.
6. El migrador es entrega de v2, con interrupción, rollback y runtime fijado; no un futuro indefinido.
7. Colaboración incluye conflictos sin choque textual, pero no finge locks distribuidos.
8. Guardrails incluyen diff real y cambios a pruebas/gates; no prometen interceptar toda escritura.
9. Se preservan UX, interfaces, Jira opcional, gobierno, perfiles y ambos hosts.
10. La aceptación humana, la publicación y la instalación permanecen separadas.
11. No se utiliza el plan anterior de consultas como evidencia de que v2 ya está aceptada.
12. No se obliga al consumidor veterano a documentar todo el producto para un cambio acotado.

La revisión estructural comprueba: IDs únicos, 67 mejoras con tarea principal y
pruebas; 48 tareas y 60 escenarios relacionados; dependencias conocidas y sin ciclos;
enlaces locales existentes. Esto acredita integridad del plan, no completitud
semántica universal ni funcionamiento de capacidades aún no implementadas.

El usuario aprobó D01–D07 y la implementación completa. Siguen separados los
responsables reales de aceptación, las sesiones de piloto y la autorización de
publicación/instalación. Los resultados y límites actuales se registran en el
[expediente de implementación](../validation/v2-implementation.md).

## 12. Registro histórico de la entrega inicial del plan

Lo que sigue describe la entrega del plan, anterior a la autorización de implementar;
no describe el estado actual del código. Se conserva como procedencia.

Se crean únicamente este documento y su matriz. No se inicializa un consumidor,
modifican skills/código/contratos canónicos, registran AUTH, crean commits ni se
publica/instala el plugin. La ejecución funcional de v2 permanece not-run.

Validación documental de esta entrega:

- Cobertura bidireccional comprobada: 67 mejoras, 48 tareas y 60 escenarios, sin
  IDs duplicados, referencias desconocidas ni elementos huérfanos.
- Dependencias de los 16 paquetes comprobadas: grafo sin ciclos.
- Los 17 enlaces locales de los dos documentos resuelven; codificación UTF-8 y
  formato del diff revisados, incluidos los archivos nuevos no versionados.
- Puerta rápida de docs/VALIDATION.md superada: validación de las seis skills,
  manifiesto del plugin, contrato actual y manifiesto de 14 fixtures. Los 23
  perfiles pasan validación estructural con --allow-unvalidated; esto no certifica
  perfiles candidatos ni acredita verificación funcional.

No se han ejecutado pruebas funcionales de v2, Docker, benchmarks, pilotos,
aceptación humana, instalación ni publicación. Los 60 escenarios de la matriz
siguen not-run. Los cambios preexistentes del árbol de trabajo se conservan;
esta entrega solo añade los dos documentos de planificación.
