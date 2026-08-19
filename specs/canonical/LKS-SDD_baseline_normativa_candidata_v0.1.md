# LKS-SDD

## Baseline normativa candidata para el desarrollo profesional de aplicaciones web

**Versión de la propuesta:** 0.1  
**Estado:** candidata para revisión interna; no aprobada como política corporativa  
**Fecha:** 19 de agosto de 2026  
**Ámbito:** proyectos de aplicaciones web desarrollados o mantenidos por LKS  
**Propietario normativo:** pendiente de designación  
**Relación con LKS-SDD:** referencia transversal que deberá consumir el plugin  

> Esta propuesta no constituye todavía una norma oficial de LKS, una certificación, una garantía contractual ni asesoramiento legal. Define una baseline profesional inicial que debe pilotarse, ajustarse y aprobarse mediante el gobierno corporativo correspondiente.

---

## 1. Propósito

Esta baseline propone un marco común, verificable y evolutivo para que los equipos de LKS puedan desarrollar, adoptar, mantener y entregar aplicaciones web con un nivel profesional homogéneo, sin imponer una única tecnología.

Su objetivo es:

- convertir expectativas de calidad difusas en reglas comprobables;
- crear un lenguaje común entre negocio, desarrollo, arquitectura, seguridad, QA, operación y cliente;
- permitir que LKS-SDD formule preguntas, proponga soluciones y compruebe evidencias sin inventar políticas;
- separar normas transversales de perfiles tecnológicos;
- adaptar la profundidad al riesgo sin degradar los mínimos esenciales;
- producir documentación técnica canónica y entregables de cliente coherentes;
- permitir excepciones justificadas y trazables;
- evolucionar el estándar sin reescribir silenciosamente proyectos existentes.

## 2. Naturaleza y límites

La baseline es:

- **transversal:** se aplica con independencia de que el proyecto utilice React, Angular, Vue, FastAPI u otra pila;
- **basada en riesgo:** incrementa rigor y evidencia cuando aumentan sensibilidad, exposición o impacto;
- **verificable:** toda regla exige una evidencia mínima;
- **consultiva y gobernable:** LKS-SDD propone y registra; la decisión y la aprobación formal permanecen fuera del modelo;
- **compatible con proyectos nuevos y existentes:** documentar una aplicación heredada no implica homologarla ni modernizarla;
- **evolutiva:** las reglas, perfiles y referencias se versionan.

La baseline no:

- sustituye legislación, contrato, política del cliente ni criterio especializado;
- convierte automáticamente una recomendación en aprobación;
- garantiza seguridad, accesibilidad o cumplimiento por el mero hecho de generar documentación;
- obliga a migrar una tecnología existente que todavía resulte adecuada;
- autoriza despliegues, accesos productivos, tratamiento de datos reales ni acciones irreversibles;
- define todavía las versiones concretas del perfil FastAPI, React, PostgreSQL y Keycloak.

## 3. Modelo normativo

### 3.1 Niveles

Las palabras normativas se interpretan de forma coherente con BCP 14:

- **MUST:** requisito esperado de la baseline. Solo puede omitirse mediante una desviación explícita, justificada, acotada y revisable.
- **SHOULD:** práctica recomendada. Si no se aplica, debe quedar una razón proporcionada al riesgo.
- **MAY:** capacidad opcional que puede aportar valor según contexto.

Mientras la baseline mantenga estado candidato, un MUST significa «obligatorio dentro de esta propuesta», no «política corporativa ya aprobada».

### 3.2 Estados de una regla

- **candidate:** propuesta pendiente de piloto y aprobación.
- **approved:** aprobada por el gobierno de LKS.
- **deprecated:** todavía legible, pero con fecha de retirada.
- **superseded:** reemplazada por otra regla identificada.
- **retired:** fuera de vigencia; su identificador no se reutiliza.

### 3.3 Tipos de aplicabilidad

- **CORE:** aplica a todos los proyectos dentro del alcance.
- **PRODUCTION:** aplica cuando el sistema puede llegar a producción.
- **ENHANCED:** aplica cuando existen datos sensibles, exposición elevada, criticidad, regulación o exigencia contractual.
- **CONDITIONAL:** se activa por una capacidad concreta, por ejemplo API pública, pagos, ficheros, multi-tenant o tratamiento de datos personales.

### 3.4 Perfiles de rigor

| Perfil | Uso previsto | Condiciones | Resultado mínimo |
|---|---|---|---|
| P0 — Exploración | Prueba de concepto o validación temporal | Sin datos reales, sin usuarios productivos, sin dependencia operativa y con fecha de cierre | Alcance, límites, riesgos, seguridad básica, pruebas mínimas y prohibición de promoción directa |
| P1 — Producción estándar | Aplicación empresarial ordinaria | Usuarios o datos reales, operación controlada y criticidad baja o media | Baseline CORE y PRODUCTION, calidad medible, seguridad ASVS orientada a nivel 2, WCAG 2.2 AA y operación definida |
| P2 — Reforzado | Sistema sensible, expuesto, crítico, regulado o contractualmente exigente | Datos de categorías especiales, alto impacto, fraude, pagos, disponibilidad crítica, multi-tenant relevante o alta exposición | Controles ENHANCED, análisis especializado, seguridad ASVS orientada por riesgo hasta nivel 3 y evidencias reforzadas |

P0 no es una vía rápida hacia producción. Promover un prototipo obliga a reclasificarlo y superar las puertas del perfil de destino.

### 3.5 Registro profesional de cada regla

La implementación definitiva de la baseline almacenará, como mínimo:

- identificador inmutable;
- título y enunciado;
- nivel MUST, SHOULD o MAY;
- aplicabilidad;
- razón y riesgo mitigado;
- evidencia mínima;
- fuente externa o decisión LKS que la sustenta;
- versión y estado;
- propietario normativo;
- reglas relacionadas;
- condiciones de desviación;
- fecha de última revisión.

## 4. Modelo documental profesional

### 4.1 Fuente canónica interna

La documentación canónica reside versionada junto al proyecto y está dirigida al equipo que define, implementa, verifica, opera y mantiene la aplicación. Debe ser precisa, accionable y trazable.

### 4.2 Entregables para cliente

Los documentos de cliente son vistas derivadas y revisadas, no una segunda fuente de verdad. Según el servicio podrán incluir:

- resumen ejecutivo;
- contexto, objetivos, alcance y exclusiones;
- requisitos y criterios de aceptación;
- arquitectura y decisiones;
- plan, hitos, dependencias y riesgos;
- dossier de calidad y evidencias;
- seguridad y privacidad en el nivel acordado;
- operación, despliegue, soporte y continuidad;
- limitaciones, desviaciones y asuntos pendientes.

No se trasladan automáticamente al cliente:

- secretos o datos personales;
- vulnerabilidades no gestionadas en detalle explotable;
- credenciales, rutas sensibles o configuración interna;
- comentarios informales o hipótesis no validadas;
- deuda interna que no afecte al alcance contratado;
- contenido perteneciente a otro cliente o proyecto.

## 5. Catálogo de normas candidatas

Las tablas siguientes constituyen la versión 0.1 del catálogo transversal. Los umbrales concretos de rendimiento, cobertura, disponibilidad, retención o recuperación deben definirse por proyecto; esta baseline evita cifras universales sin contexto.

### 5.1 Gobierno y clasificación

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| GOV-001 | MUST | CORE | Cada proyecto declarará objetivo, cliente o contexto seudonimizado, modo nuevo o existente, perfil de rigor, sensibilidad de datos y alcance técnico. | Evita aplicar controles sin contexto. Evidencia: estado inicial versionado. |
| GOV-002 | MUST | CORE | Toda información se clasificará como hecho, requisito, restricción, propuesta, decisión, supuesto, riesgo, evidencia o punto abierto. | Evita convertir sugerencias en acuerdos. Evidencia: metadatos y registros con estado. |
| GOV-003 | MUST | CORE | Las decisiones relevantes exigirán confirmación explícita y conservarán alternativas, motivos, consecuencias y fecha. | Aporta auditabilidad. Evidencia: ADR o registro equivalente. |
| GOV-004 | MUST | CORE | Las puertas se evaluarán por incremento y dependencia; un bloqueo no paralizará trabajo independiente. | Reduce burocracia y riesgo de alcance. Evidencia: informe de readiness. |
| GOV-005 | MUST | CORE | Todo MUST incumplido requerirá una desviación con alcance, riesgo, medidas compensatorias, revisión y plan de salida. | Permite flexibilidad gobernada. Evidencia: registro de desviaciones. |
| GOV-006 | SHOULD | CORE | Cada proyecto identificará responsables funcionales, técnicos, de seguridad, de calidad y de operación cuando resulten aplicables. | Clarifica interlocución sin que LKS-SDD juzgue autoridad. Evidencia: matriz de responsabilidades. |
| GOV-007 | MUST | CORE | Las versiones del plugin, método, esquema documental y perfiles se registrarán por separado. | Evita migraciones implícitas. Evidencia: manifiesto del proyecto. |

### 5.2 Requisitos, alcance y aceptación

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| REQ-001 | MUST | CORE | El proyecto documentará problema, usuarios, valor esperado, alcance incluido, exclusiones, restricciones y medida de éxito. | Evita soluciones sin objetivo verificable. Evidencia: contexto y alcance. |
| REQ-002 | MUST | CORE | Cada requisito será atómico, inequívoco, necesario, priorizado, comprobable y tendrá identificador estable. | Habilita trazabilidad y prueba. Evidencia: catálogo de requisitos validado. |
| REQ-003 | MUST | PRODUCTION | Los requisitos de calidad usarán condiciones observables y umbrales acordados, alineados con un modelo como ISO/IEC 25010. | Sustituye adjetivos por expectativas medibles. Evidencia: RNF y criterios. |
| REQ-004 | MUST | CORE | Cada requisito incluido en un incremento tendrá al menos un criterio de aceptación observable. | Define terminado de forma compartida. Evidencia: relación requisito–criterio. |
| REQ-005 | MUST | CORE | Se mantendrá trazabilidad entre requisito, criterio, decisión relevante, incremento, prueba y evidencia. | Permite demostrar cobertura. Evidencia: matriz de trazabilidad sin elementos huérfanos. |
| REQ-006 | MUST | CORE | Los puntos desconocidos indicarán impacto, dependencia y si bloquean el incremento actual. | Evita falsa completitud. Evidencia: registro de puntos abiertos. |
| REQ-007 | SHOULD | PRODUCTION | Los cambios de alcance incluirán impacto en plazo, coste, arquitectura, seguridad, pruebas, operación y entregables. | Facilita gestión profesional del cambio. Evidencia: análisis de impacto. |

### 5.3 Arquitectura y decisiones técnicas

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| ARC-001 | MUST | CORE | La arquitectura se derivará de requisitos y restricciones; la pila preferente nunca se seleccionará de forma silenciosa. | Evita tecnología dirigida por costumbre. Evidencia: propuesta comparada y decisión. |
| ARC-002 | MUST | PRODUCTION | Se documentarán límites de sistema, componentes, responsabilidades, dependencias, integraciones, datos, identidad y despliegue. | Hace la solución comprensible y operable. Evidencia: vistas de arquitectura vigentes. |
| ARC-003 | MUST | CORE | Toda decisión con impacto estructural, contractual, de seguridad, datos u operación tendrá ADR. | Conserva contexto y consecuencias. Evidencia: ADR enlazada. |
| ARC-004 | MUST | PRODUCTION | Las cualidades relevantes —seguridad, rendimiento, fiabilidad, mantenibilidad, compatibilidad y accesibilidad— se vincularán a decisiones y pruebas. | Evita arquitecturas solo funcionales. Evidencia: escenarios de calidad. |
| ARC-005 | SHOULD | PRODUCTION | Los componentes se diseñarán con alta cohesión, bajo acoplamiento y contratos explícitos, evitando distribución innecesaria. | Reduce complejidad accidental. Evidencia: revisión arquitectónica. |
| ARC-006 | MUST | ENHANCED | Se realizará modelado de amenazas y abuso antes de cerrar la baseline técnica. | Prioriza controles por riesgo. Evidencia: amenazas, mitigaciones y riesgos residuales. |

### 5.4 Ingeniería y código

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| ENG-001 | MUST | CORE | El repositorio seguirá la estructura, convenciones y herramientas del perfil tecnológico confirmado. | Evita variantes locales incompatibles. Evidencia: validación del perfil. |
| ENG-002 | MUST | CORE | Formato, lint y análisis estático se automatizarán y no dejarán errores bloqueantes en el incremento. | Hace reproducible la calidad básica. Evidencia: pipeline o informe local. |
| ENG-003 | MUST | CORE | El código será legible, cohesivo, sin duplicación relevante, ramas muertas ni complejidad injustificada. | Favorece mantenibilidad. Evidencia: revisión de código y análisis. |
| ENG-004 | MUST | PRODUCTION | Configuración y comportamiento dependiente de entorno estarán externalizados y validados al inicio; ningún secreto residirá en el código. | Reduce errores y exposición. Evidencia: esquema de configuración y escaneo. |
| ENG-005 | MUST | PRODUCTION | Los errores se gestionarán de forma consistente, sin filtrar detalles internos ni información sensible. | Protege al usuario y facilita soporte. Evidencia: manejo de errores y pruebas negativas. |
| ENG-006 | SHOULD | CORE | Las APIs públicas, módulos compartidos y decisiones no obvias tendrán documentación cercana al código y ejemplos mantenidos. | Reduce conocimiento tribal. Evidencia: documentación revisada con el cambio. |

### 5.5 Seguridad y privacidad

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| SEC-001 | MUST | CORE | Cada proyecto clasificará activos, datos, usuarios, exposición, amenazas y requisitos de seguridad antes de implementar. | Permite seleccionar controles proporcionados. Evidencia: contexto de seguridad. |
| SEC-002 | MUST | PRODUCTION | La verificación se basará en OWASP ASVS 5.0.0: nivel 1 como mínimo de entrada, nivel 2 como objetivo estándar y nivel 3 según riesgo reforzado. | Usa un estándar verificable y graduado. Evidencia: perfil ASVS versionado y resultados. |
| SEC-003 | MUST | PRODUCTION | Autenticación y autorización se aplicarán en componentes de confianza, con mínimo privilegio y denegación por defecto. | Evita confiar en el cliente. Evidencia: matriz de permisos y pruebas. |
| SEC-004 | MUST | CONDITIONAL | Cuando exista identidad, se preferirán protocolos y proveedores corporativos consolidados; una autenticación propia requerirá ADR y revisión reforzada. | Reduce soluciones de credenciales ad hoc. Evidencia: arquitectura de identidad. |
| SEC-005 | MUST | CORE | Secretos, tokens, claves y certificados no se almacenarán en repositorios, documentación, prompts, logs ni fixtures. | Previene exposición directa. Evidencia: gestión de secretos y escaneos saneados. |
| SEC-006 | MUST | PRODUCTION | Datos sensibles se protegerán en tránsito y reposo con mecanismos vigentes y gestión documentada de claves. | Preserva confidencialidad e integridad. Evidencia: configuración y revisión. |
| SEC-007 | MUST | PRODUCTION | Entradas, salidas, ficheros, serialización, consultas y contenido dinámico se validarán o codificarán en el contexto correcto. | Mitiga inyección y manipulación. Evidencia: controles y pruebas negativas. |
| SEC-008 | MUST | PRODUCTION | Dependencias y artefactos se analizarán frente a vulnerabilidades conocidas; los hallazgos tendrán severidad, decisión y plazo. | Gestiona riesgo de terceros. Evidencia: informe y backlog trazable. |
| SEC-009 | MUST | CONDITIONAL | Todo tratamiento de datos personales documentará finalidad, minimización, acceso, retención, eliminación y responsables confirmados; LKS-SDD no determinará por sí solo la base jurídica. | Aplica privacidad desde el diseño sin simular criterio legal. Evidencia: ficha de tratamiento revisada. |
| SEC-010 | MUST | ENHANCED | Los sistemas reforzados tendrán revisión especializada de amenazas, privacidad, registros de auditoría, respuesta a incidentes y controles compensatorios. | Aumenta garantía cuando el impacto lo exige. Evidencia: dictamen y riesgos residuales. |

### 5.6 APIs e integraciones

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| API-001 | MUST | CONDITIONAL | Toda API HTTP mantenida por LKS tendrá contrato OpenAPI versionado en una versión soportada por el perfil y el ecosistema del proyecto. | Hace explícito el contrato. Evidencia: especificación validada. |
| API-002 | MUST | CONDITIONAL | Rutas, métodos, códigos de estado, formatos, paginación, filtros y validaciones seguirán semántica consistente. | Reduce ambigüedad para consumidores. Evidencia: revisión contractual. |
| API-003 | MUST | CONDITIONAL | Los errores HTTP usarán un formato coherente, preferentemente Problem Details conforme a RFC 9457 cuando encaje. | Evita formatos propietarios inconsistentes. Evidencia: esquema y pruebas. |
| API-004 | MUST | CONDITIONAL | Se definirán autenticación, autorización, cuotas, límites, timeouts, idempotencia y protección frente a abuso según el riesgo de cada operación. | Protege integridad y disponibilidad. Evidencia: contrato y pruebas. |
| API-005 | MUST | CONDITIONAL | Los cambios incompatibles requerirán versión, estrategia de transición, deprecación y comunicación. | Protege a consumidores. Evidencia: política y changelog. |
| API-006 | SHOULD | CONDITIONAL | Se aplicarán pruebas de contrato entre productor y consumidores críticos. | Detecta roturas antes de desplegar. Evidencia: ejecución en CI. |
| API-007 | MUST | CONDITIONAL | La API no expondrá campos internos, secretos ni datos que el consumidor no necesite. | Aplica minimización y desacoplamiento. Evidencia: revisión de esquemas. |

### 5.7 Datos y persistencia

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| DAT-001 | MUST | CONDITIONAL | El modelo de datos documentará entidades, relaciones, invariantes, propiedad, clasificación y ciclo de vida. | Hace visibles reglas y responsabilidades. Evidencia: modelo vigente. |
| DAT-002 | MUST | PRODUCTION | Integridad, unicidad, referencias y reglas críticas se protegerán en la capa de confianza apropiada, incluida la base de datos cuando corresponda. | Evita depender solo de la interfaz. Evidencia: esquema y pruebas. |
| DAT-003 | MUST | PRODUCTION | Toda evolución de esquema será versionada, revisable, probada y compatible con despliegue y reversión acordados. | Reduce riesgo de pérdida o indisponibilidad. Evidencia: migraciones y ensayo. |
| DAT-004 | MUST | PRODUCTION | Se definirán backup, restauración, RPO, RTO, retención y eliminación conforme al riesgo y contrato. | Asegura recuperabilidad. Evidencia: plan y prueba de restauración. |
| DAT-005 | MUST | CORE | No se copiarán datos productivos a desarrollo o pruebas salvo autorización, minimización y protección explícitas; por defecto se usarán datos sintéticos. | Protege privacidad y confidencialidad. Evidencia: estrategia de datos de prueba. |
| DAT-006 | SHOULD | PRODUCTION | Consultas, índices y volúmenes críticos tendrán evidencia de rendimiento representativa, evitando optimización prematura sin medición. | Equilibra rendimiento y mantenibilidad. Evidencia: análisis y pruebas. |

### 5.8 Experiencia de usuario y accesibilidad

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| UXA-001 | MUST | PRODUCTION | Las interfaces web tendrán WCAG 2.2 nivel AA como objetivo candidato, salvo obligación contractual superior o desviación justificada. | Establece un estándar verificable y actual. Evidencia: matriz WCAG. |
| UXA-002 | MUST | CONDITIONAL | Flujos críticos serán operables con teclado, foco visible y orden lógico; la semántica se apoyará primero en HTML nativo. | Favorece accesibilidad robusta. Evidencia: pruebas manuales. |
| UXA-003 | MUST | CONDITIONAL | Contraste, tamaño de objetivos, etiquetas, mensajes de error y ayudas cumplirán los criterios aplicables. | Mejora percepción y comprensión. Evidencia: revisión automática y manual. |
| UXA-004 | MUST | PRODUCTION | La interfaz definirá estados de carga, vacío, error, sin permisos, confirmación y recuperación. | Evita experiencias incompletas. Evidencia: diseño y pruebas de flujo. |
| UXA-005 | SHOULD | PRODUCTION | Se reutilizará un sistema de diseño o componentes compartidos antes de crear variantes locales. | Aumenta coherencia y mantenibilidad. Evidencia: inventario de componentes. |
| UXA-006 | MUST | PRODUCTION | La verificación de accesibilidad combinará automatización y revisión humana de los flujos prioritarios. | Las herramientas automáticas no cubren todo WCAG. Evidencia: informe mixto. |

### 5.9 Pruebas y aseguramiento de calidad

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| TST-001 | MUST | CORE | Cada incremento tendrá estrategia de pruebas proporcional a sus riesgos y criterios de aceptación. | Evita pruebas genéricas sin propósito. Evidencia: plan del incremento. |
| TST-002 | MUST | CORE | Se combinarán pruebas unitarias, integración, contrato, sistema o end-to-end cuando cada nivel aporte cobertura relevante. | Evita depender de una sola capa. Evidencia: pirámide justificada. |
| TST-003 | MUST | CORE | Toda prueba se ejecutará de forma determinista, aislada y repetible; la inestabilidad se registrará y corregirá. | Mantiene confianza en CI. Evidencia: historial y gestión de flaky tests. |
| TST-004 | MUST | CORE | Los criterios de aceptación se vincularán con pruebas y resultados, incluyendo limitaciones conocidas. | Permite demostrar terminado. Evidencia: índice de evidencias. |
| TST-005 | MUST | CORE | Los datos de prueba serán sintéticos, anonimizados o seudonimizados según el contexto. | Evita exposición innecesaria. Evidencia: fixtures revisados. |
| TST-006 | SHOULD | CORE | La cobertura de código se usará como señal, no como objetivo aislado; los umbrales se justificarán por perfil y componente. | Evita métricas engañosas. Evidencia: criterio documentado. |
| TST-007 | MUST | ENHANCED | Rendimiento, seguridad, accesibilidad, resiliencia y recuperación tendrán pruebas específicas cuando sean riesgos materiales. | Cubre cualidades no funcionales. Evidencia: resultados y riesgos residuales. |

### 5.10 Repositorio y control del cambio

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| SCM-001 | MUST | CORE | Código, configuración no secreta, documentación, migraciones y pruebas se versionarán en Git con una raíz y alcance claros. | Crea trazabilidad común. Evidencia: repositorio estructurado. |
| SCM-002 | MUST | PRODUCTION | La rama principal estará protegida y los cambios pasarán por pull request o merge request y revisión proporcional al riesgo. | Reduce cambios no revisados. Evidencia: configuración y revisión. |
| SCM-003 | MUST | CORE | Cada cambio será acotado, comprensible y vinculado a un requisito, incidencia, decisión o incremento. | Facilita revisión y auditoría. Evidencia: metadatos del cambio. |
| SCM-004 | SHOULD | CORE | Los mensajes de commit y títulos de cambio seguirán una convención estable y orientada al propósito. | Mejora historial y automatización. Evidencia: validación de convención. |
| SCM-005 | MUST | CORE | No se sobrescribirán ni descartarán cambios ajenos; cualquier modificación mecánica preservará ediciones humanas. | Protege trabajo concurrente. Evidencia: diff revisado. |
| SCM-006 | SHOULD | ENHANCED | Componentes sensibles tendrán propietarios de revisión y reglas reforzadas de aprobación. | Aumenta control donde el impacto es mayor. Evidencia: configuración de ownership. |

### 5.11 Integración, entrega y cadena de suministro

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| DEL-001 | MUST | PRODUCTION | Todo cambio integrable ejecutará en CI las validaciones aplicables de formato, análisis, pruebas, build, seguridad y contrato. | Hace reproducible la puerta técnica. Evidencia: pipeline satisfactorio. |
| DEL-002 | MUST | PRODUCTION | Los artefactos de entrega serán inmutables y trazables a revisión, pipeline, dependencias y configuración de build. | Permite reproducir y auditar entregas. Evidencia: metadatos del artefacto. |
| DEL-003 | MUST | CORE | Dependencias directas estarán declaradas, bloqueadas cuando el ecosistema lo permita y sujetas a política de actualización y fin de soporte. | Reduce deriva y riesgo de versiones. Evidencia: manifiesto y lockfile. |
| DEL-004 | MUST | PRODUCTION | Se comprobarán vulnerabilidades y licencias de dependencias; las excepciones tendrán responsable, plazo y mitigación. | Gestiona riesgo legal y de suministro. Evidencia: informes y decisiones. |
| DEL-005 | SHOULD | PRODUCTION | Cada entrega generará un SBOM en formato estándar cuando el producto, contrato o riesgo lo justifique; será MUST en P2 salvo desviación. | Aporta transparencia de componentes. Evidencia: SBOM vinculada al artefacto. |
| DEL-006 | MUST | PRODUCTION | Los entornos estarán separados y la promoción reutilizará el mismo artefacto; secretos y parámetros se inyectarán por mecanismos autorizados. | Reduce diferencias entre entornos. Evidencia: pipeline y configuración. |
| DEL-007 | MUST | PRODUCTION | El despliegue tendrá verificación, estrategia de reversión y autorización explícita para producción; LKS-SDD no desplegará de forma autónoma. | Limita impacto operativo. Evidencia: plan y registro de despliegue. |

### 5.12 Observabilidad, resiliencia y operación

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| OPS-001 | MUST | PRODUCTION | Se definirán indicadores, objetivos de servicio y umbrales operativos para las capacidades críticas. | Conecta calidad con operación. Evidencia: SLI, SLO y criterios de alerta. |
| OPS-002 | MUST | PRODUCTION | Logs, métricas y trazas usarán contexto y correlación coherentes; se preferirán estándares abiertos como OpenTelemetry cuando encajen. | Facilita diagnóstico y evita dependencia innecesaria. Evidencia: diseño de telemetría. |
| OPS-003 | MUST | PRODUCTION | La telemetría no contendrá secretos ni datos personales innecesarios y tendrá acceso y retención definidos. | Evita convertir observabilidad en fuga de datos. Evidencia: revisión de campos. |
| OPS-004 | MUST | PRODUCTION | Se implementarán comprobaciones de salud y readiness que representen el estado útil sin exponer detalles sensibles. | Mejora operación y despliegue. Evidencia: endpoints y pruebas. |
| OPS-005 | MUST | PRODUCTION | Alertas accionables tendrán responsable, severidad, canal y runbook; se evitará alertar sin acción posible. | Reduce ruido y tiempos de recuperación. Evidencia: catálogo de alertas. |
| OPS-006 | MUST | ENHANCED | Se probarán degradación, timeouts, reintentos, aislamiento de fallos, recuperación y continuidad según el modelo de amenazas y dependencia. | Aumenta resiliencia. Evidencia: pruebas y riesgos residuales. |

### 5.13 Documentación y entrega profesional

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| DOC-001 | MUST | CORE | Los artefactos canónicos serán Markdown versionado con identificador, tipo, estado, versión, audiencia, propietario y fecha. | Permite lectura humana y validación. Evidencia: metadatos completos. |
| DOC-002 | MUST | CORE | La documentación se actualizará con el cambio que invalida su contenido y no dependerá del historial del chat. | Evita deriva y pérdida de contexto. Evidencia: diff conjunto. |
| DOC-003 | MUST | PRODUCTION | El proyecto mantendrá contexto, requisitos, arquitectura, decisiones, pruebas, despliegue, operación y trazabilidad en la profundidad aplicable. | Cubre el ciclo completo. Evidencia: índice documental. |
| DOC-004 | MUST | CORE | Los entregables de cliente se derivarán de la fuente interna y pasarán una revisión específica de exactitud, audiencia y confidencialidad. | Evita duplicidad y fugas. Evidencia: revisión de publicación. |
| DOC-005 | MUST | CORE | Todo entregable profesional declarará alcance, exclusiones, supuestos, decisiones, riesgos, evidencias, limitaciones y estado de aprobación. | Evita conclusiones ambiguas. Evidencia: checklist editorial. |
| DOC-006 | MUST | CORE | No se presentarán propuestas como decisiones, inferencias como hechos ni documentos generados como aprobación formal. | Mantiene integridad profesional. Evidencia: revisión semántica. |
| DOC-007 | SHOULD | CORE | El lenguaje será claro, neutral, consistente y adaptado a la audiencia, evitando jerga innecesaria y contenido de plantilla sin completar. | Mejora utilidad y credibilidad. Evidencia: revisión editorial. |

### 5.14 Adopción de aplicaciones existentes

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| ADP-001 | MUST | CONDITIONAL | La adopción comenzará con un preflight que confirme raíz, alcance, revisión Git, estado productivo, exclusiones y permisos. | Evita inspecciones ambiguas. Evidencia: acta de preflight. |
| ADP-002 | MUST | CONDITIONAL | El descubrimiento inicial será estático y de solo lectura: no modificará archivos ni ejecutará aplicación, builds, tests, hooks, contenedores o migraciones. | Protege repositorios existentes. Evidencia: estado Git antes y después. |
| ADP-003 | MUST | CONDITIONAL | Secretos, archivos de entorno, claves, certificados y datos sensibles se excluirán o redactarán; nunca se reproducirán sus valores. | Evita exposición durante arqueología. Evidencia: informe saneado. |
| ADP-004 | MUST | CONDITIONAL | Cada afirmación as-is indicará fuente, revisión, naturaleza, confianza y limitaciones; el código no se tratará como intención de negocio. | Preserva rigor epistemológico. Evidencia: índice de observaciones. |
| ADP-005 | MUST | CONDITIONAL | Work validará propósito y comportamiento deseado; Codex reconciliará coincidencias, contradicciones y desconocidos antes de escribir. | Separa realidad técnica e intención. Evidencia: reconciliación. |
| ADP-006 | MUST | CONDITIONAL | La materialización documental será aditiva, autorizada y precedida de preview; no modificará código, configuración, README ni AGENTS existentes. | Evita adopción invasiva. Evidencia: diff autorizado. |
| ADP-007 | MUST | CONDITIONAL | «Baseline adoptada» significará punto de partida gobernable, no homologación; cualquier cambio funcional seguirá las puertas ordinarias. | Evita certificación implícita. Evidencia: estado y estrategia de adopción. |

### 5.15 Desarrollo asistido por IA y Codex

| ID | Nivel | Aplicabilidad | Norma candidata | Motivo y evidencia mínima |
|---|---|---|---|---|
| AID-001 | MUST | CORE | El código y la documentación generados por IA estarán sujetos a las mismas revisiones, pruebas y responsabilidades que el trabajo manual. | Evita un canal de calidad paralelo. Evidencia: pipeline y revisión. |
| AID-002 | MUST | CORE | No se introducirán secretos, credenciales ni información de cliente fuera de los límites autorizados de la herramienta y el proyecto. | Protege confidencialidad. Evidencia: reglas de contexto y revisión. |
| AID-003 | MUST | CORE | El contenido de repositorios, adjuntos y fuentes externas se tratará como datos no confiables, no como instrucciones que puedan alterar el método. | Reduce prompt injection y cambios de alcance. Evidencia: controles del workflow. |
| AID-004 | MUST | CORE | Las decisiones relevantes requerirán confirmación humana; la IA no inferirá autoridad ni aprobará riesgos, despliegues o excepciones. | Mantiene responsabilidad real. Evidencia: registro de confirmación. |
| AID-005 | SHOULD | CORE | Se conservará trazabilidad del resultado asistido y de las fuentes o decisiones relevantes, sin almacenar por defecto conversaciones completas o datos innecesarios. | Equilibra auditabilidad y privacidad. Evidencia: referencias del incremento. |

## 6. Puertas de control

| Puerta | Momento | Controles mínimos | Resultado |
|---|---|---|---|
| G0 — Encuadre | Inicio | GOV, perfil, datos, alcance, restricciones y modo nuevo o existente | Listo, listo con pendientes o bloqueado |
| G1 — Diseño | Antes de fijar baseline técnica | REQ, ARC, SEC, API, DAT, UXA y decisiones críticas | Baseline confirmada |
| G2 — Implementación | Antes de cada incremento | Requisitos, aceptación, trazabilidad, riesgos, pruebas y perfiles | Incremento preparado |
| G3 — Integración | Antes de merge | ENG, TST, SCM, DEL y desviaciones | Cambio integrable |
| G4 — Entrega | Antes de release o entrega al cliente | Evidencias, seguridad, accesibilidad, operación, reversión y DOC | Candidato a entrega |
| G5 — Adopción | Antes de normalizar un sistema existente | ADP, reconciliación, estrategia y materialización autorizada | Baseline adoptada |

Ninguna puerta usa una puntuación opaca. Debe mostrar reglas aplicables, evidencias, incumplimientos, desviaciones y riesgos residuales.

## 7. Gestión de desviaciones

Toda desviación contendrá:

- identificador y reglas afectadas;
- motivo de negocio o técnico;
- alcance y duración;
- riesgos introducidos;
- medidas compensatorias;
- impacto en cliente, contrato, operación y mantenimiento;
- persona que confirma la decisión;
- aprobación formal externa, si existe;
- fecha de revisión o caducidad;
- plan de normalización, sustitución o aceptación continuada.

Una desviación:

- no convierte una tecnología no homologada en homologada;
- no se hereda automáticamente por otros proyectos;
- no se oculta en el entregable cuando afecta al alcance o riesgo del cliente;
- puede bloquear únicamente el trabajo que depende de ella.

## 8. Evidencias mínimas del proyecto

El proyecto mantendrá:

- índice de reglas aplicables;
- matriz de cumplimiento y desviaciones;
- trazabilidad requisito–criterio–incremento–prueba–evidencia;
- ADR y análisis de impacto;
- informes de CI y verificación;
- inventario y decisiones de dependencias;
- resultados de seguridad y accesibilidad saneados;
- evidencia de despliegue y reversión cuando proceda;
- riesgos residuales y limitaciones;
- revisión de entregables para cliente.

La evidencia debe ser reproducible en proporción al riesgo, pero no debe copiar logs, datos o secretos innecesarios.

## 9. Gobierno y evolución propuesta

### 9.1 Flujo de una regla

1. Propuesta y justificación.
2. Revisión técnica, seguridad, calidad y aplicabilidad.
3. Fixture y eval de comportamiento.
4. Piloto en proyectos representativos.
5. Ajuste por evidencia.
6. Aprobación o rechazo por el gobierno de LKS.
7. Publicación versionada.
8. Seguimiento, deprecación y retirada.

### 9.2 Versionado

- La baseline usará SemVer cuando se convierta en artefacto implementado.
- Un cambio incompatible en obligaciones o significado incrementará la versión mayor.
- Nuevas reglas compatibles incrementarán la versión menor.
- Correcciones editoriales sin cambio normativo incrementarán la versión de parche.
- Cada proyecto conservará la versión aplicada.
- El plugin nunca migrará o reinterpretará automáticamente proyectos existentes.

### 9.3 Propiedad

Antes del piloto deben designarse:

- propietario del método;
- responsables de cada dominio;
- responsables de perfiles tecnológicos;
- revisión de seguridad y privacidad;
- responsable de calidad documental;
- administración y publicación del plugin;
- canal de soporte y proceso de excepción.

## 10. Estrategia de piloto

El piloto debería incluir, al menos:

1. una aplicación nueva con el perfil tecnológico de referencia;
2. una aplicación existente documentada sin cambios funcionales;
3. una alternativa tecnológica reconocida pero no automatizada;
4. un proyecto P0;
5. un proyecto P1;
6. un escenario P2 simulado o con datos no sensibles;
7. un entregable interno y su vista para cliente;
8. una desviación justificada;
9. un cambio de baseline sin migración automática;
10. una ejecución consecutiva en dos proyectos sin contaminación de contexto.

Las métricas del piloto incluirán:

- utilidad percibida por equipo y cliente;
- tiempo y carga documental;
- reglas ambiguas o no verificables;
- falsos bloqueos;
- desviaciones recurrentes;
- calidad y completitud de evidencias;
- consistencia entre Work y Codex;
- ausencia de exposición de información sensible;
- mantenimiento de documentos tras cambios reales.

## 11. Decisiones todavía abiertas

Esta propuesta permite continuar la definición, pero antes de implementar la baseline completa deben cerrarse:

1. responsables y órgano de aprobación;
2. clasificación corporativa definitiva de perfiles P0, P1 y P2;
3. nivel ASVS por perfil y reglas excluidas por tecnología;
4. objetivos de accesibilidad contractuales y excepciones;
5. política de licencias y formatos de SBOM;
6. estructura y protección de ramas en GitHub y GitLab;
7. herramientas corporativas de CI, análisis, seguridad y evidencias;
8. umbrales por tipo de proyecto, nunca universales sin validación;
9. política de retención y clasificación de documentación de cliente;
10. contrato exacto del perfil FastAPI, React, PostgreSQL y Keycloak.

## 12. Referencias primarias

- [ISO/IEC 25010:2023 — Product quality model](https://www.iso.org/standard/78176.html): marco para especificar y evaluar calidad de producto.
- [NIST SP 800-218 — Secure Software Development Framework 1.1](https://csrc.nist.gov/pubs/sp/800/218/final): prácticas transversales de desarrollo seguro.
- [OWASP ASVS 5.0.0](https://owasp.org/www-project-application-security-verification-standard/): requisitos verificables de seguridad para aplicaciones web.
- [OWASP ASVS 5.0 — niveles de verificación](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x03-What-is-the-ASVS.md): graduación L1, L2 y L3 por riesgo.
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/): criterios comprobables de accesibilidad web.
- [EDPB Guidelines 4/2019](https://www.edpb.europa.eu/documents/guideline/guidelines-42019-on-article-25-data-protection-by-design-and-by-default_en): protección de datos desde el diseño y por defecto.
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html): descripción estándar y agnóstica de APIs HTTP.
- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html): formato interoperable para errores HTTP.
- [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/): telemetría y observabilidad con estándares abiertos.
- [CISA — Minimum Elements for an SBOM, 2025](https://www.cisa.gov/sites/default/files/2025-08/2025_CISA_SBOM_Minimum_Elements.pdf): elementos mínimos y trazabilidad de componentes.
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): semántica de versiones y compatibilidad.

## 13. Recomendación de adopción

Esta baseline debería incorporarse a LKS-SDD como un módulo versionado y separado de los perfiles tecnológicos. La versión 0.1 debe considerarse suficientemente completa para revisión profesional y piloto, pero no para presentarse como estándar aprobado.

El siguiente paso recomendado es revisar el catálogo por dominios, resolver las decisiones abiertas de mayor impacto y convertir cada regla aceptada en una referencia autocontenida del plugin con:

- texto normativo;
- aplicabilidad;
- evidencia;
- ejemplos conformes y no conformes;
- validador determinista cuando sea posible;
- eval conversacional cuando requiera juicio;
- trazabilidad a la fuente o decisión corporativa.
