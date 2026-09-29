# LKS-SDD v3: propuesta funcional y técnica para revisar

Fecha: 2026-09-29. Revisión: **v3-propuesta-03**.
Estado: **pendiente de validación funcional y técnica por el usuario**.

Esta revisión sustituye al borrador v3-propuesta-02, que no fue aprobado. Conserva
los siete puntos de la revisión crítica y añade eficiencia de contexto. Estamos revisando
qué se propone construir y cómo; aceptar el alcance permitirá preparar su plan. La
implementación y la migración se autorizarán después sobre sus objetos concretos.

## Qué cambia para quien utiliza el plugin

El objetivo es trabajar con un proceso acordado sin convertir al usuario en gestor de
registros. El plugin prepara propuestas, mantiene la trazabilidad, comprueba condiciones
y explica el siguiente paso; las personas deciden sobre contenido y responsabilidades.

| Punto revisado | Comportamiento concreto que se propone validar |
|---|---|
| 1. Agilidad | Un cambio pequeño con configuración vigente tiene dos decisiones antes de ejecutar: validar su propuesta y aprobar el plan con autorización. La aceptación final se añade si el proyecto la exige. Cero edición manual de registros internos y cero nuevas decisiones al reanudar sin cambios. |
| 2. Comprensión de la validación | Una ficha explica situación actual, resultado propuesto, ejemplos, solución, consecuencias y exclusiones. Cada función revisa lo que le corresponde. El resumen debe conservar las restricciones materiales del detalle. |
| 3. Aprobaciones reutilizables | Cada porción funcional/técnica tiene contenido y revisión identificados. Un paquete puede conservar una parte aprobada y presentar otra modificada; cambiar un contrato obliga a revisar sus dependencias aunque su texto no haya cambiado. |
| 4. Configuración manejable | Tres recorridos editables: individual breve, equipo coordinado y equipo con revisión separada. El proyecto confirma el elegido. Se distinguen garantías del método, autoridad vigente, proceso de petición y excepciones. |
| 5. Coordinación entre ramas | Se diferencia preparado localmente, compartido y recibido. Al iniciar/reanudar y al cerrar/integrar se contrastan las referencias acordadas; se explican los límites del trabajo sin conexión y la actualidad real del estado mostrado. |
| 6. Calidad sin esperas innecesarias | Se comprueba primero que existe un medio viable de análisis. Varias tareas pueden reutilizar un informe aplicable. Se distingue necesitar un contrato validado, un resultado disponible o uno verificado para continuar. |
| 7. Migración sencilla | La vista previa muestra conversión automática, historia conservada, decisiones pendientes y tareas que podrán continuar. Una migración sencilla agrupa la decisión; no pide revisar cada archivo ni volver a aceptar tareas cerradas. |
| 8. Eficiencia de contexto | Cargar solo instrucciones y fuentes pertinentes a la operación y versión, sin duplicar bloques ni volcar la historia completa. Preservar el contrato literal necesario, ampliar ante dudas y medir consumo y calidad de la tarea completa. |

Se conserva el alcance anterior: trabajo individual/equipo, especialistas y relevos,
evolución de identidades y política, excepciones validadas, ramas por petición,
identificadores permanentes y orientación al consultar o completar un paso.
Sonar y Dependency-Check se usan según decisión del proyecto durante la implementación;
su no utilización explícita queda registrada y se reutiliza.

## Dos ejemplos para entender la decisión

**Cambio pequeño:** añadir búsqueda por nombre a una lista ya cargada. El plugin
presenta comportamiento, solución, límites y pruebas en una ficha. La persona la valida;
después recibe el plan y autoriza su ejecución. El plugin implementa, comprueba y registra
sin más permisos administrativos. La sección 13.3 de la
[propuesta funcional](team-workflow-traceability.md#133-recorrido-completo-de-un-cambio-pequeño)
incluye el diálogo y explica cuándo sería necesario volver a preguntar.

**Trabajo de equipo:** añadir alta de proveedores con frontend, backend y BBDD.
El responsable funcional valida reglas y resultado; los técnicos, contrato, solución
y datos. Después se planifica el reparto. Frontend puede comenzar con el contrato
validado mientras backend avanza; la comprobación conjunta sigue pendiente hasta
disponer de resultados y controles aplicables. Véase la sección 13.4 de la
[misma propuesta](team-workflow-traceability.md#134-recorrido-de-una-petición-con-especialistas).

No son tareas reales ni un plan de implementación de v3. Son ejemplos del comportamiento
que se pide aceptar. Un cambio de reglas o un dato crítico ausente puede requerir otra
decisión; el plugin debe explicar la causa concreta y conservar lo que siga siendo válido.

## Cómo se evita que el plugin resulte pesado

Consultar el estado no debe cargar el contexto necesario para implementar todo el
proyecto. Implementar una tarea requiere sus reglas completas y dependencias pertinentes,
pero no los manuales de versiones inactivas o las actas de cambios ajenos. Los informes
grandes se procesan localmente y el modelo recibe resultados pertinentes con acceso al
detalle. Una referencia o un resumen no sustituyen un contrato que necesita interpretar.

Se proponen presupuestos iniciales de tamaño para instrucciones y diagnósticos, además
de un aviso de crecimiento del contexto de trabajo. Excederlos exige justificar el
volumen o eliminar duplicación; nunca permite recortar obligaciones. Tras cambiar de
chat se recupera lo necesario y se conservan las aprobaciones vigentes. El usuario no
tiene que gestionar tokens ni confirmar cada lectura.

La aceptación compara consumo total, ampliaciones, reintentos y calidad con el flujo
actual. Todavía no hay una medición de ahorro real. Los criterios se concretan en la
sección 5.11 funcional y en la [sección 6 técnica](lks-sdd-v3-technical-proposal.md#6-agilidad-y-costes-de-operación).

## Solución técnica y consecuencias

Se mantienen las seis skills y un núcleo local sobre la infraestructura Python actual.
Markdown sigue siendo canónico y el índice se puede reconstruir. El núcleo comprueba
contenido, referencias, autoridad admitida, dependencias y condiciones; el modelo propone
y explica impactos, y la persona competente decide sobre cambios normativos.

Las aprobaciones se vinculan a unidades de contenido exactas. El paquete reúne esas
unidades y sus dependencias, sin exigir el mismo número de revisión en todas. Un cambio
de palabras normativas o un impacto incierto no se aprueba por considerarlo editorial.
Los estados de progreso se separan del contenido aprobado para evitar invalidarlo.

La coordinación usa referencias Git compartidas, sus revisiones observadas y el flujo
de publicación ya autorizado. El análisis agrupa entradas compatibles y admite varias
dependencias de resultado; esperar Sonar no convierte automáticamente todo el trabajo
en bloqueado. El cierre ordinario mantiene las comprobaciones exigidas.

La migración utiliza lectores por formato/método, un único mapa de correspondencias y
escrituras recuperables. Se propone plugin **3.0.0**, método **3.0.0** y formato **3.0**,
como versiones distintas. El plugin actual continúa en **2.3.1**. La
[propuesta técnica](lks-sdd-v3-technical-proposal.md) concreta las reglas y la matriz
de orígenes; la sección 11.1 funcional muestra el coste de intervención esperado.

## Límites y aceptación pendientes

- CI/CD, pipelines, despliegues y publicación quedan fuera de esta evolución. Se usan
  medios de análisis existentes y autorizados, sin nuevos conectores, skills o agentes.
- La configuración usa condiciones conocidas y comprobables. Una regla arbitraria no
  interpretable requiere aclaración; no se ejecuta texto del repositorio como código.
- El plugin controla sus propias operaciones y detecta divergencias observables. No
  bloquea físicamente clones desconectados ni garantiza un estado global en vivo.
- Instalar v3 no migra un proyecto. La compatibilidad depende del formato/método real y
  de rutas probadas; un origen desconocido se diagnostica y conserva sin transformación.
- Los **69 requisitos y 100 casos de aceptación** son criterios futuros. La agilidad,
  eficiencia de contexto y migración necesitan pruebas; sus límites de tiempo se acuerdan antes de
  medirlos. No se presentan como capacidades demostradas ni amplían automáticamente
  la puerta de publicación actual.

## Qué decisión se necesita

Validar el comportamiento, el diseño técnico y el destino v3 de esta revisión completa,
pedir ajustes o aceptar una porción expresamente delimitada. En una aceptación parcial
se comprueban sus dependencias y se conservan los demás pendientes.

Una respuesta suficiente sería: «Valido la propuesta v3-propuesta-03 y prepara el plan».
No hace falta copiar huellas. Las decisiones todavía necesarias para un proyecto concreto
—personas, destino Git, controles y umbrales— se tomarán en su configuración, con las
reglas aquí descritas; no se inventan valores corporativos universales.

## Documentos exactos de esta revisión

Las huellas identifican los bytes de las dos propuestas. Cualquier cambio requiere
actualizar este paquete y mostrar la diferencia antes de validarlo. La futura decisión
referenciará también este documento tal como se presente; no existe aún aceptación.

| Documento | SHA-256 |
|---|---|
| [Propuesta funcional](team-workflow-traceability.md) | `15f09dde2faa8912bf979be630184a90d50bae15a4e87a3f67a56a5dd0f750a3` |
| [Propuesta técnica](lks-sdd-v3-technical-proposal.md) | `c76c2a5904638d749bbe79795ed0d569d76d6a9452512c299e0ad18d1b60e7d1` |

Recorrido de esta evolución: propuesta revisada → **validación pendiente** →
planificación pendiente → implementación pendiente → verificación y aceptación de uso
pendientes. Los ejemplos explican la propuesta; no registran aprobaciones reales.
