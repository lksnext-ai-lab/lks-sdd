# LKS-SDD — extensión contractual de definición y diseño visual v0.1

**Fecha:** 2026-08-20

**Estado:** confirmada para la implementación técnica compatible del plugin 0.6.0

**Ámbito:** definición de aplicaciones nuevas o incrementos posteriores a una adopción válida

**Entorno soportado:** Codex

**Carácter:** extensión aditiva; no sustituye ni modifica las tres fuentes canónicas anteriores

## 1. Motivación y decisión

La primera experiencia de definición ha demostrado tres carencias relevantes:

1. una petición breve puede conducir a una interpretación demasiado concreta del producto antes de conocer su dominio, usuarios y propósito;
2. durante una definición larga, la persona usuaria puede perder visibilidad sobre qué bloques están suficientemente cubiertos y cuáles necesitan profundización;
3. cuando existe frontend, el contrato actual de UX y accesibilidad no desarrolla con suficiente precisión pantallas, flujos, interacción, dirección visual ni prototipos de referencia.

La decisión de producto para la versión 0.6.0 es reforzar esos tres comportamientos dentro de `lks-sdd-define`. No se crea una skill adicional, no se selecciona tecnología automáticamente y no se amplía el runtime soportado más allá de Codex.

Esta decisión autoriza la implementación técnica de la extensión. No convierte la baseline normativa candidata en política corporativa, no acredita autoridad organizativa, no ejecuta el piloto M5 y no completa M6.

## 2. Relación con el contrato anterior

La extensión concreta reglas ya presentes sobre entrevista adaptativa, suficiencia, estados explícitos, resúmenes, preguntas de alto impacto y UX. Para cualquier materia no regulada aquí siguen gobernando, por este orden:

1. `LKS-SDD_definicion_plugin_v1.md` para propósito, límites y comportamiento general;
2. `LKS-SDD_paquete_preimplementacion_v0.1.md` para contratos, validación y calidad;
3. `LKS-SDD_baseline_normativa_candidata_v0.1.md` para reglas candidatas aplicables.

Ante una contradicción material que esta jerarquía no resuelva, LKS-SDD registra el punto abierto y solicita una decisión; no adapta silenciosamente el contrato a la implementación.

La extensión es compatible con `method_version: 1.0.0` y `schema_version: 1.0` mientras:

- el diseño visual siga siendo un anexo condicional;
- no se introduzcan campos obligatorios nuevos en documentos ya materializados;
- los activos binarios se referencien desde Markdown canónico y no sustituyan su contenido;
- los proyectos existentes no necesiten una reescritura para seguir siendo válidos.

Si una implementación rompe alguna de estas condiciones, debe versionar por separado método o esquema y aportar análisis de compatibilidad, migración y rollback.

## 3. Encuadre inicial sin presuposiciones

### 3.1 Regla de orientación

Ante una idea breve o ambigua, LKS-SDD no elige silenciosamente la interpretación más genérica ni la más habitual. Antes de detallar funcionalidades o tecnología debe comprender, con profundidad proporcional al proyecto, al menos:

- problema o necesidad y resultado esperado;
- dominio o contexto de uso;
- usuarios principales y quién recibe el valor;
- situación, frecuencia y criticidad de uso;
- alcance inicial, exclusiones o límites ya conocidos;
- señal de éxito y riesgos que puedan cambiar el enfoque.

Cada aportación se conserva como hecho, objetivo, requisito, restricción, propuesta, decisión, supuesto, punto abierto, riesgo o evidencia. Una interpretación plausible se registra como supuesto o propuesta, nunca como hecho.

### 3.2 Forma de preguntar

La conversación continúa usando tandas de una a tres preguntas de mayor impacto. El refuerzo de curiosidad no autoriza un formulario largo.

Cuando ayude a decidir, cada pregunta puede ofrecer entre dos y cuatro opciones breves y mutuamente comprensibles, además de permitir una respuesta libre. Las opciones:

- ilustran diferencias relevantes sin imponer una preferencia;
- explican el impacto de la elección cuando no sea evidente;
- incluyen únicamente alternativas compatibles con lo ya confirmado;
- no presentan una opción como aprobada o seleccionada de antemano.

Ejemplo: ante «quiero una calculadora», LKS-SDD debe aclarar primero si resuelve cálculos generales, reglas de un oficio o sector, simulaciones comerciales, cálculo científico u otro contexto. No debe documentar una calculadora genérica como intención confirmada.

### 3.3 Suficiencia del encuadre

El encuadre inicial se clasifica como `unknown`, `partial`, `sufficient` o `not-applicable: motivo`, igual que el resto de dimensiones. `sufficient` significa suficiente para avanzar al bloque siguiente, no definición completa del producto ni readiness para implementar.

Si la persona decide cerrar o diferir detalle, se conserva el alcance de ese cierre, las preguntas aplazadas y el riesgo residual. No se bloquea trabajo independiente.

## 4. Resumen visual del estado de definición

### 4.1 Momentos de presentación

LKS-SDD presenta un snapshot compacto de cobertura:

- al completar el encuadre inicial;
- tras cubrir un bloque funcional relevante;
- al consolidar solución, UX o decisiones técnicas;
- antes de recomendar una evaluación de readiness;
- cuando la persona usuaria lo solicite;
- cuando un cambio reabra una dimensión antes considerada suficiente.

No repite el snapshot después de cada edición menor si no aporta orientación.

### 4.2 Contenido mínimo

El snapshot debe poder entenderse sin conocer la estructura documental interna. Incluye:

1. fase e incremento o alcance al que se refiere;
2. bloques con información suficiente para continuar;
3. bloques parciales o desconocidos que necesitan profundización;
4. decisiones o evidencias que bloquean solo el alcance afectado;
5. siguiente paso recomendado;
6. una opción explícita para solicitar el detalle y las evidencias de cualquier bloque.

La representación usa etiquetas textuales estables —`sufficient`, `partial`, `unknown`, `not-applicable` y `blocked` cuando proceda— y puede acompañarlas de símbolos visuales accesibles. El significado nunca depende solo del color o del icono.

No se calcula un porcentaje global de madurez. El snapshot orienta la conversación; no sustituye la rúbrica de readiness ni autoriza implementación.

### 4.3 Persistencia

La información sustantiva permanece en los Markdown canónicos afectados. `project-status.md` puede registrar fase, puerta, alcance y siguiente paso. Los vacíos y bloqueos se mantienen en `open-points.md`. `.lks-sdd/project.json` continúa siendo un índice y no duplica la evaluación narrativa.

## 5. Aplicabilidad del diseño de interfaz

Al conocer la superficie del producto, LKS-SDD determina explícitamente si existe frontend o interacción visual relevante:

- si no existe, registra `not-applicable` con motivo y no crea documentación o imágenes vacías;
- si existe, materializa o actualiza el anexo condicional de UX y accesibilidad;
- si la aplicabilidad todavía es incierta, la mantiene como punto abierto y evita anticipar una línea visual.

La profundidad depende del riesgo, número de perfiles, variedad de dispositivos, criticidad de los flujos, accesibilidad exigida y existencia de un sistema de diseño o marca previa.

## 6. Contrato de definición de interfaz

Antes de generar una propuesta visual deben quedar suficientemente reflexionados los bloques aplicables siguientes.

### 6.1 Inventario de pantallas y superficies

Cada pantalla, vista, diálogo u otra superficie relevante registra:

- identificador estable y nombre;
- propósito y usuarios autorizados;
- punto de entrada y salida;
- información principal y jerarquía;
- acciones primarias y secundarias;
- requisitos, reglas y criterios relacionados;
- permisos y variantes por rol;
- estados de carga, vacío, error, sin permisos, confirmación y recuperación;
- necesidades responsive y dispositivos prioritarios;
- criterios de accesibilidad y contenido pendiente.

### 6.2 Flujos e interacción

Los flujos prioritarios describen navegación, pasos, bifurcaciones, validación, retorno y recuperación. Cuando apliquen, se definen además:

- confirmaciones para acciones irreversibles o de impacto;
- validación en línea y resumen de errores;
- avisos, ayudas, feedback de éxito y estados de proceso;
- comportamiento de diálogos, menús, tablas, filtros y formularios;
- foco, teclado, orden de lectura y alternativas no gestuales;
- prevención de pérdida de cambios y recuperación tras interrupciones;
- visibilidad de estado, permisos y consecuencias de una acción.

### 6.3 Dirección visual

La dirección visual separa hechos de marca, restricciones, propuestas y decisiones. Puede cubrir:

- tono y personalidad;
- sistema de diseño o componentes existentes;
- color, tipografía, densidad, espaciado e iconografía;
- uso de ilustración, fotografía o datos;
- patrones de navegación y composición;
- contraste, legibilidad, ampliación y movimiento reducido;
- referencias aceptadas y referencias que deben evitarse.

Una preferencia estética no se convierte en decisión hasta que la persona la confirme.

## 7. Ciclo de prototipado con ImageGen

### 7.1 Puerta de generación

ImageGen se utiliza únicamente cuando el brief visual aplicable sea `sufficient` para la propuesta que se pretende evaluar. Como mínimo deben conocerse pantalla o flujo objetivo, usuario, contenido principal, acciones, estados críticos, restricciones de marca y dispositivo de referencia.

Si falta información que cambiaría materialmente la composición o interacción, LKS-SDD pregunta antes de generar. No usa una imagen atractiva para ocultar una decisión abierta.

### 7.2 Generación y comparación

Cuando exista un frontend nuevo o un cambio visual material, el brief sea suficiente e ImageGen esté disponible en la superficie autorizada, LKS-SDD debe generar entre una y tres propuestas PNG o JPG para explorar y validar la línea de diseño. Cada variante parte del mismo brief confirmado y explicita las diferencias que se desean comparar.

Puede omitirse una nueva generación cuando el incremento no modifica la experiencia visual o aplica una baseline visual ya confirmada. La excepción se registra con su motivo y las referencias reutilizadas; no se usa para evitar una validación todavía pendiente.

Las imágenes son referencias visuales, no código, contrato de píxeles, copia textual exacta ni evidencia de accesibilidad. El Markdown conserva comportamientos, contenido, reglas, responsive y criterios verificables que una imagen estática no puede demostrar.

No se incluirán secretos, datos personales, contenido real de cliente no autorizado, credenciales ni información restringida en prompts o imágenes. Se usarán datos sintéticos o neutros y se respetarán marca, licencias y derechos de terceros.

### 7.3 Validación humana e iteración

Cada propuesta permanece en estado `proposal` hasta una confirmación explícita. La revisión solicita feedback útil sobre jerarquía, claridad, flujo, densidad, tono, accesibilidad aparente y adecuación al trabajo real, no solo una valoración estética genérica.

La persona puede:

- confirmar la línea completa o una parte delimitada;
- solicitar una nueva iteración con cambios concretos;
- rechazar una variante;
- diferir la decisión;
- confirmar principios de diseño sin aprobar todavía una pantalla final.

Una respuesta ambigua no se interpreta como aprobación.

### 7.4 Persistencia y trazabilidad

Las imágenes seleccionadas se guardan en el repositorio consumidor, preferentemente bajo `docs/lks-sdd/03-solution/ui-prototypes/`, con nombre estable y sin sobrescribir una versión previa.

El Markdown canónico de UX registra para cada activo:

- ID y ruta relativa;
- pantallas, flujos y requisitos relacionados;
- brief o decisión de origen;
- herramienta de generación declarada como `ImageGen` y fecha;
- estado `proposal`, `confirmed`, `rejected` o `superseded`;
- alcance exacto de la confirmación;
- SHA-256 del archivo confirmado;
- limitaciones y criterios todavía no visibles en la imagen.

Los PNG/JPG son activos controlados de apoyo a la especificación. `.lks-sdd/project.json` no duplica su contenido ni transforma su mera existencia en aprobación.

### 7.5 Fallback

Si ImageGen no está disponible, falla o no permite conservar el resultado como archivo local:

- se declara la limitación;
- se mantiene el brief y la especificación textual;
- se registra el prototipo visual como pendiente;
- no se crea un archivo ficticio ni se afirma que la validación visual se ha realizado;
- solo se bloquea el alcance cuya implementación dependa realmente de esa validación.

ChatGPT Work puede apoyar el análisis o revisión de documentos transferidos, pero esta extensión no promete que ejecute el plugin ni ImageGen con el mismo contrato que Codex.

## 8. Handoff a implementación y verificación

Codex implementa únicamente decisiones visuales y activos cuyo estado y alcance estén confirmados. Una imagen en `proposal`, un enlace remoto temporal o una preferencia conversacional sin registrar no forman parte de la baseline implementable.

Antes de readiness, la especificación relaciona, cuando apliquen:

- pantallas y flujos con requisitos y criterios de aceptación;
- estados de interacción con pruebas previstas;
- componentes o patrones con decisiones de diseño;
- activos confirmados con sus hashes;
- accesibilidad, responsive y contenido con evidencia esperada.

Si una imagen contradice un requisito, criterio, decisión o regla de accesibilidad, prevalece el Markdown confirmado y se reabre la propuesta visual. Verificación distingue fidelidad razonable a la dirección aprobada de coincidencia píxel a píxel, salvo que exista un criterio explícito que exija esta última.

## 9. Calidad y evidencia

La versión 0.6.0 añade escenarios de calidad para:

- idea inicial ambigua sin presuposiciones de dominio;
- snapshot de cobertura comprensible y sin porcentaje engañoso;
- ciclo visual desde brief suficiente hasta activo confirmado o limitación explícita.

Las comprobaciones estructurales pueden automatizar presencia, rutas, estados, referencias y hashes. La pertinencia de preguntas, claridad del resumen, utilidad del prototipo y adecuación visual requieren evaluación semántica o humana.

Mientras esas sesiones no se hayan ejecutado, su canal permanece `not-run`. Una release candidate puede declarar ese pendiente; una release stable no puede presentarlo como superado sin evidencia.

## 10. Límites

Esta extensión no autoriza:

- generar código antes de decisiones críticas;
- seleccionar automáticamente la pila o el sistema de diseño;
- crear una skill, MCP, conector, hook, app o agente adicional;
- instalar o publicar el plugin;
- tratar ImageGen como diseñador autónomo o autoridad de aprobación;
- declarar compatibilidad equivalente con ChatGPT Work u otros asistentes;
- usar contenido sensible para mejorar una propuesta visual;
- presentar el piloto M5, M6 o la promoción a stable como completados.
