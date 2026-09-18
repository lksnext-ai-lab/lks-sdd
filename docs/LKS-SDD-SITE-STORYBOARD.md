# Storyboard del site «Desarrollo SDD con CODEX»

**Fecha:** 2026-08-26\
**Estado:** propuesta de diseño; no constituye implementación ni publicación\
**Audiencia principal:** responsables funcionales, responsables de proyecto, responsables técnicos y equipos de desarrollo de LKS Next\
**Entorno explicado:** Codex con el plugin LKS-SDD

## 1. Objetivo de la experiencia

El site debe permitir comprender, en pocos minutos y sin conocer previamente SDD:

1. qué reto plantea el desarrollo agéntico;
2. qué aporta el plugin LKS-SDD dentro de Codex;
3. por qué su diseño es Spec-anchored;
4. cómo sirve tanto para proyectos nuevos como para aplicaciones existentes;
5. cómo se trabaja realmente con Codex durante definición, diseño, planificación, implementación y verificación;
6. cómo evoluciona la especificación junto con el producto;
7. cómo puede proyectarse el trabajo en Jira sin trasladarle la autoridad del repositorio;
8. cómo está construido técnicamente el plugin.

La experiencia no debe presentarse como una landing comercial genérica ni como una infografía continua. Será una narración vertical compuesta por escenas diferenciadas, conectadas mediante un mismo lenguaje de movimiento.

## 2. Marco de decisiones

### 2.1 Decisiones confirmadas

- Título principal: **Desarrollo SDD con CODEX**.
- La apertura debe indicar expresamente que se ha creado un plugin de LKS Next para Codex.
- El site alternará escenas claras y oscuras; no tendrá una apariencia predominantemente negra.
- El enfoque Spec-anchored se presentará como decisión de diseño del plugin por considerarse adecuada, no como metodología corporativa aprobada para toda LKS Next.
- La especificación se explicará como contrato vivo que evoluciona con el producto.
- En proyectos existentes, el código aporta evidencia del estado `as-is`; la intención, corrección y evolución requieren confirmación humana.
- El ejemplo práctico usará una empresa y datos completamente ficticios.
- El caso mostrará la creación de una aplicación web de escritorio adaptada a la identidad visual del cliente ficticio.
- Jira tendrá una escena propia con tablero Kanban y detalle de ticket.
- Jira será una proyección operativa opcional mediante un peer Atlassian Rovo independiente; no será la fuente de verdad ni un componente interno del plugin.
- Existirá una ruta técnica independiente para explicar el interior del plugin.

### 2.2 Propuestas de diseño pendientes de validación final

- Nombre del cliente ficticio: **Mendiara Mobility**.
- Caso funcional: gestión de flota, rutas e incidencias de vehículos comerciales eléctricos.
- Distribución aproximada de color: 60–65 % de escenas claras, 25–30 % oscuras y 10 % de transiciones o superficies dominadas por naranja/coral.
- Uso de una escena Three.js persistente para el hilo de energía, reservando HTML, SVG y componentes reales para contenido y producto.
- Intensidad cinematográfica mayor en escritorio y simplificada en móvil.

## 3. Tesis de diseño

### 3.1 Tesis visual

Una experiencia editorial luminosa y técnica, con grandes campos blancos y azul mineral, planos color petróleo y una corriente naranja que atraviesa el site transformando intención, conversación y especificaciones en software verificable.

### 3.2 Plan de contenido

- **Apertura:** qué es LKS-SDD y qué promete.
- **Contexto:** reto del desarrollo agéntico y elevación del trabajo humano.
- **Método:** SDD, enfoque Spec-anchored, contrato vivo y dos puertas de entrada.
- **Demostración:** trabajo real con Codex sobre un proyecto ficticio.
- **Control:** trazabilidad, evidencia e integración opcional con Jira.
- **Profundidad:** ruta técnica sobre el interior del plugin.
- **Cierre:** acelerar sin perder el control.

### 3.3 Tesis de interacción

1. Un hilo luminoso naranja recorre toda la experiencia y cambia de forma según el significado de cada escena.
2. El scroll no desplaza únicamente contenido: controla convergencias, capas, versiones, puertas de autorización y ciclos de reconciliación.
3. Las interfaces de Codex, la aplicación ficticia y Jira se construyen como superficies HTML interactivas; se revelan, seleccionan, ejecutan y anotan durante el recorrido.

## 4. Sistema visual global

### 4.1 Paleta

| Función | Color orientativo | Uso |
|---|---|---|
| Naranja LKS Next | `#F85900` / `#FF5A00` | hilo narrativo, llamadas a la acción, estados activos y puntos de control |
| Petróleo profundo | `#17222A` | escenas de profundidad, texto sobre fondos claros y arquitectura técnica |
| Petróleo corporativo | `#253E46` | planos, navegación y transiciones |
| Azul mineral claro | `#E0EBF0` | fondos luminosos, capas técnicas y separación editorial |
| Blanco cálido | `#F7F8F5` | escenas de producto, conversación, Jira y respiración |
| Coral | `#CC4C45` | transiciones puntuales y alertas no críticas |

El color naranja conserva siempre el significado de continuidad, actividad o decisión. Los estados de calidad, riesgo o confirmación no dependerán exclusivamente del color.

### 4.2 Tipografía

- Familia principal: **Inter Variable**, siguiendo la presencia observada en la web corporativa.
- Titulares: peso alto, caja alta selectiva y escala editorial.
- Cuerpo: 16–20 px en escritorio, líneas cortas y lectura inmediata.
- Etiquetas técnicas: 12–14 px, peso medio y espaciado moderado.
- Máximo de dos familias tipográficas; inicialmente no se propone una segunda.

### 4.3 Ritmo claro y oscuro

El site no utilizará un fondo oscuro permanente. La secuencia alternará:

- escenas claras para explicación, conversación, producto y Jira;
- escenas oscuras para tensión, profundidad conceptual y arquitectura interna;
- transiciones naranja o coral para separar actos;
- cierre luminoso, evitando regresar a una gran superficie negra.

### 4.4 Elemento persistente

El hilo naranja será el único recurso visual que atraviese todas las escenas. Podrá comportarse como:

- ramificación desordenada;
- eje de control;
- secuencia de skills;
- ciclo alrededor de la especificación;
- flujo de trabajo;
- traza requisito–evidencia;
- recibo controlado hacia Jira;
- haz vertical entre las capas internas del plugin.

No debe convertirse en un adorno repetitivo. Su geometría cambia porque cambia su significado.

## 5. Arquitectura de información

### 5.1 Ruta principal — `/`

Narración vertical completa para comprender la propuesta, el método y la experiencia de trabajo.

### 5.2 Ruta técnica — `/por-dentro`

Explicación interactiva de la arquitectura del plugin, sus seis skills, contratos, perfiles, gates, repositorio consumidor y capacidades externas opcionales.

### 5.3 Navegación

Cabecera mínima y superpuesta:

- Visión
- Cómo se trabaja
- Jira
- Por dentro

En escritorio se añadirá un indicador lateral de capítulos. En móvil se sustituirá por una barra de progreso discreta y un menú desplegable.

## 6. Storyboard de la ruta principal

### Escena 01 — Apertura

**Trabajo de la escena:** presentar el producto y su promesa.\
**Tratamiento:** claro.\
**Altura narrativa:** 120–140 vh.

**Titular**

> DESARROLLO SDD\
> CON CODEX

**Texto de apoyo**

> Un plugin de LKS Next para CODEX que convierte las especificaciones en un contrato vivo para dirigir, implementar y verificar el desarrollo.

**Visual dominante**

Una especificación versionada ocupa el centro. Una mano activa un nodo y el hilo naranja recorre tres hitos: dirigir, implementar y verificar, antes de materializar una aplicación web.

**Coreografía**

1. El fondo mineral aparece mediante una apertura suave.
2. Entran logo, antetítulo y titular con desplazamiento corto.
3. Varias versiones documentales se alinean detrás del documento activo.
4. La interacción humana enciende el hilo.
5. Los tres hitos se activan en secuencia.
6. La aplicación emerge parcialmente en el extremo derecho.

**Referencia visual**

`exec-db6e74b2-9bf6-4648-a17e-1cd284096283.png`

### Escena 02 — El reto

**Trabajo de la escena:** explicar la dificultad sin formularla como un problema insoluble.\
**Tratamiento:** oscuro.\
**Altura narrativa:** 140–160 vh.

**Titular**

> CUANDO LA EJECUCIÓN\
> AVANZA MÁS RÁPIDO

**Texto de apoyo**

> El reto es mantener conectadas intención, decisiones, código, pruebas y evidencias mientras aumenta la capacidad de ejecución.

**Visual dominante**

El hilo procedente de la apertura entra ordenado y comienza a dividirse entre requisitos, código, pruebas, decisiones y Jira. Las ramas periféricas pierden conexión; las cercanas al eje conservan trazabilidad.

**Coreografía**

- La superficie clara se pliega y deja paso al petróleo profundo.
- Los elementos se dispersan con velocidades distintas.
- El cursor del usuario detiene el movimiento y revela las conexiones ausentes.
- El scroll vuelve a atraer las piezas hacia un eje central.

### Escena 03 — Elevar el desarrollo

**Trabajo de la escena:** mostrar el nuevo reparto del trabajo.\
**Tratamiento:** claro con transición coral.\
**Altura narrativa:** 160 vh.

**Titular**

> ELEVAR EL DESARROLLO

**Texto de apoyo**

> Más capacidad de ejecución permite dedicar más atención a comprender, decidir, priorizar y supervisar.

**Visual dominante**

Tres planos amplios, no tarjetas:

1. Ejecución: código, pruebas y entregables.
2. Dirección funcional: alcance, decisiones y prioridades.
3. Supervisión y evidencia: trazabilidad, calidad y cumplimiento.

**Coreografía**

La cámara asciende atravesando los planos. El plano de ejecución permanece activo, pero el foco y la escala visual se desplazan hacia dirección funcional y supervisión.

### Escena 04 — La respuesta dentro de Codex

**Trabajo de la escena:** presentar LKS-SDD como sistema de trabajo integrado en Codex.\
**Tratamiento:** claro.\
**Altura narrativa:** 180 vh.

**Titular**

> LKS-SDD PARA CODEX

**Texto de apoyo**

> Seis capacidades conectadas para comprender, definir, adoptar, evaluar, implementar y verificar.

**Visual dominante**

Las seis skills aparecen como estaciones diferentes sobre el hilo, con verbos comprensibles antes que nombres técnicos:

- Ayudar y orientar.
- Definir.
- Adoptar un proyecto existente.
- Evaluar readiness.
- Implementar una tarea autorizada.
- Verificar con evidencia.

**Coreografía**

Cada estación se activa con el scroll y transforma el mismo objeto: idea, contrato, baseline, plan, software y evidencia. No se mostrará una colección de seis tarjetas iguales.

### Escena 05 — Qué significa Spec-anchored

**Trabajo de la escena:** situar el enfoque sin convertirlo en doctrina corporativa.\
**Tratamiento:** oscuro.\
**Altura narrativa:** 170 vh.

**Titular**

> UNA SPEC QUE NO SE ABANDONA\
> CUANDO EMPIEZA EL CÓDIGO

**Texto de apoyo**

> El plugin se ha diseñado con un enfoque Spec-anchored porque mantiene una referencia comprensible y contrastable durante toda la evolución.

**Visual dominante**

Tres trayectorias se muestran en profundidad:

- Spec-first: el documento queda atrás.
- Spec-anchored: documento, código y evidencia continúan conectados.
- Spec-as-source: la especificación intenta convertirse en el origen ejecutable de todo.

La trayectoria central será la única iluminada completamente.

**Nota visible**

> Es el enfoque elegido para diseñar este plugin; no representa por sí solo una decisión metodológica corporativa de LKS Next.

### Escena 06 — La especificación evoluciona

**Trabajo de la escena:** explicar la reconciliación supervisada.\
**Tratamiento:** oscuro con núcleo naranja.\
**Altura narrativa:** 220 vh.

**Titular**

> LA SPEC EVOLUCIONA\
> CON EL PRODUCTO

**Texto de apoyo**

> No se termina antes de desarrollar. Se amplía y reconcilia según cambian la intención, el producto y la evidencia.

**Visual dominante**

Un ciclo orbital alrededor de una especificación viva:

`Especificación → cambio funcional → código y pruebas → evidencia → reconciliación → especificación`

Una puerta de confirmación humana interrumpe de forma visible cualquier atajo automático.

**Coreografía**

1. La versión 1.0 ocupa el centro.
2. Un cambio funcional deforma la órbita.
3. Código y pruebas producen evidencia.
4. La evidencia no modifica directamente el documento.
5. La confirmación humana abre la reconciliación.
6. La versión 1.1 sustituye a la anterior conservando su rastro.

**Referencia visual**

`exec-e001f343-93ab-4af5-8b86-ba7b67f04403.png`

### Escena 07 — Dos puertas de entrada

**Trabajo de la escena:** hacer comprensibles proyecto nuevo y proyecto existente.\
**Tratamiento:** claro.\
**Altura narrativa:** 180–200 vh.

**Titular**

> DOS PUERTAS.\
> UN CONTRATO VIVO.

**Recorrido izquierdo: proyecto nuevo**

`Necesidad → conversación → decisiones confirmadas → primera especificación`

**Recorrido derecho: proyecto existente**

`Código observado → baseline as-is → intención confirmada → especificación progresiva`

**Mensaje central**

> El código muestra lo que existe. Las personas confirman qué debe conservarse, cambiar o incorporarse.

**Coreografía**

Los dos recorridos nacen en extremos opuestos y convergen en la especificación viva. Después de la convergencia, ambos continúan mediante el mismo ciclo evolutivo de la escena anterior.

### Escena 08 — Conversación funcional

**Trabajo de la escena:** iniciar una demostración reconocible del trabajo real.\
**Tratamiento:** claro.\
**Altura narrativa:** 160 vh.

**Caso ficticio**

Mendiara Mobility necesita una aplicación web de escritorio para gestionar vehículos, rutas e incidencias.

**Titular**

> TODO EMPIEZA\
> CON UNA CONVERSACIÓN

**Visual dominante**

Una conversación con Codex que clasifica las aportaciones como:

- hecho;
- propuesta;
- decisión;
- pendiente.

**Coreografía**

Los mensajes no aparecen como un chat interminable. Cada aportación relevante abandona la conversación y ocupa un lugar en una estructura funcional visible.

### Escena 09 — Propuesta técnica y visual

**Trabajo de la escena:** mostrar que Codex propone y la persona decide.\
**Tratamiento:** claro con fondo mineral.\
**Altura narrativa:** 220 vh.

**Titular**

> COMPARAR ANTES\
> DE CONSTRUIR

**Visual dominante**

1. Dos alternativas técnicas con implicaciones de tiempo, riesgo y evolución.
2. Selección humana de una alternativa.
3. Tres propuestas ImageGen para la aplicación Mendiara.
4. Una propuesta avanza y se afina.
5. La UI final adopta verde bosque, arena y dorado, además de fotografía corporativa ficticia de movilidad eléctrica.

**Coreografía**

Las propuestas visuales se desplazan lateralmente, pero el scroll —no un carrusel automático— controla la comparación. La selección produce una segunda iteración más detallada.

### Escena 10 — Planificar y autorizar

**Trabajo de la escena:** visibilizar la frontera entre propuesta y ejecución.\
**Tratamiento:** petróleo profundo con planos claros.\
**Altura narrativa:** 170 vh.

**Titular**

> PLANIFICAR ANTES\
> DE EJECUTAR

**Visual dominante**

Requisitos y aceptación convergen en tareas trazadas. Un análisis de readiness señala huecos concretos, sin porcentajes globales engañosos. Una puerta `AUTORIZAR` permanece cerrada hasta que el alcance aplicable está confirmado.

**Coreografía**

- El plan se completa por capas.
- Las dependencias se conectan.
- Los huecos permanecen visibles.
- La persona activa la autorización.
- El hilo atraviesa la puerta y cambia de comportamiento: de propuesta a ejecución.

### Escena 11 — Construir, ejecutar y señalar

**Trabajo de la escena:** demostrar la integración de Codex con la ejecución real.\
**Tratamiento:** claro.\
**Altura narrativa:** 260 vh en secuencia fijada.

**Titular**

> CREANDO UNA APLICACIÓN\
> CON CODEX

**Texto de apoyo**

> De la conversación funcional a una web UI alineada con la imagen corporativa del cliente.

**Visual dominante**

La aplicación web de escritorio Mendiara ocupa el centro y evoluciona en cuatro pasos:

1. implementación visible mediante cambios de código;
2. ejecución de pruebas;
3. apertura de la aplicación en el navegador;
4. selección de una zona concreta y anotación: «Dar más visibilidad a las incidencias críticas».

El feedback vuelve a la especificación como nuevo requisito o propuesta de cambio antes de una nueva ejecución.

**Coreografía**

- El prototipo confirmado se transforma en interfaz ejecutable.
- El código aparece únicamente como evidencia secundaria.
- Los checks se activan en secuencia.
- La aplicación ocupa toda la superficie.
- Una anotación hace zoom sobre la prioridad de incidencias.
- Una curva naranja regresa hacia la especificación con la etiqueta `NUEVO REQUISITO → RECONCILIAR SPEC`.

**Referencia visual**

`exec-a6f03111-c8b2-40c6-96a5-3c9c7eea24e7.png`

### Escena 12 — Del requisito a la evidencia

**Trabajo de la escena:** resumir el control que conserva el método.\
**Tratamiento:** oscuro.\
**Altura narrativa:** 170 vh.

**Titular**

> DEL REQUISITO\
> A LA EVIDENCIA

**Visual dominante**

Una secuencia amplia y muy legible:

`FR-017 → AC-021 → TASK-008 → CÓDIGO + PRUEBAS → EVID-005`

Al recorrerla, cada elemento abre una breve explicación y muestra su relación con la escena Mendiara. El último estado distingue con claridad código escrito de código verificado.

### Escena 13 — Integración con Jira

**Trabajo de la escena:** mostrar Jira como experiencia real y explicar su frontera.\
**Tratamiento:** claro.\
**Altura narrativa:** 240 vh en secuencia fijada.

**Titular**

> INTEGRACIÓN\
> CON JIRA

**Texto de apoyo**

> Las tareas y los hitos pueden proyectarse en Jira sin sacar la fuente de verdad del repositorio.

**Visual dominante**

Un tablero Kanban realista de Mendiara Mobility con las columnas Por hacer, En curso, En revisión y Hecho. La tarea `MDM-41 · Priorizar incidencias críticas` abre su detalle y muestra:

- `INC-001`;
- `FR-017`;
- `AC-021`;
- `TASK-008`;
- `EVID-005`;
- actividad de implementación, pruebas y verificación.

**Secuencia de integración**

1. El Markdown canónico genera una proyección saneada.
2. Atlassian Rovo aparece como peer externo.
3. Los recibos `SYNC-014` y `RPT-008` atraviesan puntos de control.
4. La tarjeta se mueve de En curso a En revisión.
5. Se abre el ticket y aparecen sus relaciones.
6. La transición a Hecho requiere confirmación humana.
7. Una observación remota regresa mediante `RELEER Y RECONCILIAR`, sin modificar automáticamente el contrato.

**Mensaje de frontera**

> Jira es una proyección operativa. No autoriza, no verifica y no sustituye el contrato del repositorio.

**Referencia visual**

`exec-9d2e15b4-2823-41ef-99bb-9c655c62f5fb.png`

### Escena 14 — Cierre

**Trabajo de la escena:** condensar la propuesta y conducir a la exploración técnica.\
**Tratamiento:** naranja y blanco cálido.\
**Altura narrativa:** 110–130 vh.

**Titular**

> ACELERAR\
> SIN PERDER EL CONTROL

**Texto de apoyo**

> Especificaciones vivas, decisiones humanas y ejecución verificable dentro de Codex.

**Acciones**

- Primaria: `VER EL PLUGIN POR DENTRO`.
- Secundaria: `VOLVER AL PROCESO`.

**Coreografía**

Todos los hilos de las escenas anteriores convergen en una línea estable. La energía disminuye, el fondo se vuelve luminoso y el CTA técnico aparece como siguiente paso natural.

## 7. Storyboard de la ruta técnica `/por-dentro`

### Técnica 01 — Visión explotada

**Tratamiento:** oscuro.\
**Objetivo:** presentar el plugin como sistema skills-only aplicado sobre un repositorio consumidor.

Capas suspendidas:

1. Codex e intención.
2. Seis skills.
3. Método y plantillas.
4. Contratos, schemas y validadores.
5. Perfiles tecnológicos y gates.
6. Repositorio del proyecto.

El scroll separa y vuelve a unir las capas. El cursor puede fijar una capa para ampliar su explicación.

**Referencia visual**

`exec-56392256-a025-45be-90ba-630e0a8602b1.png`

### Técnica 02 — Las seis skills

**Tratamiento:** claro.\
**Objetivo:** explicar propósito, entrada, resultado y límite de cada skill.

Cada skill ocupa todo el escenario durante un tramo breve. El mismo ejemplo Mendiara permite conservar continuidad:

- `lks-sdd-help`: orientar sin modificar.
- `lks-sdd-define`: descubrir y definir.
- `lks-sdd-adopt-existing`: construir una baseline desde evidencia `as-is`.
- `lks-sdd-assess-readiness`: evaluar sin autorizar.
- `lks-sdd-implement`: ejecutar una tarea autorizada.
- `lks-sdd-verify`: producir evidencia sin confundir implementación con verificación.

### Técnica 03 — Contrato y motores

**Tratamiento:** oscuro con diagramas blancos.\
**Objetivo:** enseñar cómo se sostiene el método.

Se muestran, con profundidad progresiva:

- fuentes contractuales;
- plantillas Markdown;
- schemas;
- validadores y motores;
- planificación, trazabilidad, continuidad y evidencia;
- perfiles, locks, drivers y certificaciones.

No se reproducirá un árbol completo de archivos. Cada capa mostrará únicamente las piezas que explican su responsabilidad.

### Técnica 04 — El repositorio consumidor

**Tratamiento:** claro.\
**Objetivo:** aclarar dónde vive la autoridad y cómo se reanuda el trabajo.

El repositorio se abre como una estructura navegable:

- especificaciones Markdown canónicas;
- planes, releases, tareas y autorizaciones;
- código y pruebas;
- evidencias y checkpoints;
- `.lks-sdd/project.json` como índice operativo.

El usuario puede activar `PAUSAR` y `REANUDAR`; el escenario muestra cómo `AUTH`, `EXEC` y `CKPT` permiten continuar sin depender del historial del chat.

### Técnica 05 — Gates y límites

**Tratamiento:** petróleo y naranja.\
**Objetivo:** cerrar la visión técnica sin prometer capacidades inexistentes.

Secuencia principal:

`G2 · READY → G3 · VERIFICACIÓN TÉCNICA → G4 · EVIDENCIA DE ENTREGA`

Fuera del núcleo aparecen:

- ImageGen, opcional;
- Atlassian Rovo/Jira, peer externo opcional.

Límites visibles:

- plugin skills-only;
- sin MCP, hooks, app o cliente Jira propios;
- ninguna propuesta equivale a aprobación;
- ningún código escrito equivale a evidencia superada;
- ninguna integración externa sustituye la autoridad del repositorio.

El cierre enlaza de nuevo con la ruta principal y con la guía de uso del plugin.

## 8. Guion de transiciones

| Desde | Hacia | Transformación principal |
|---|---|---|
| Apertura | Reto | La aplicación se fragmenta y el fondo claro se pliega hacia petróleo |
| Reto | Elevar | Las piezas dispersas se ordenan en tres planos verticales |
| Elevar | Skills | Los planos se convierten en estaciones sobre el mismo hilo |
| Skills | Spec-anchored | Las estaciones generan tres trayectorias comparables |
| Spec-anchored | Spec evolutiva | La trayectoria central se curva hasta cerrar una órbita |
| Spec evolutiva | Dos puertas | La órbita se abre en dos recorridos simétricos |
| Dos puertas | Conversación | La especificación central se transforma en superficie de Codex |
| Conversación | Propuesta | Las decisiones abandonan el chat y forman alternativas |
| Propuesta | Autorización | La alternativa seleccionada se descompone en alcance y tareas |
| Autorización | Aplicación | El pulso atraviesa la puerta y materializa la web UI |
| Aplicación | Evidencia | La anotación se convierte en requisito y recorre la cadena trazada |
| Evidencia | Jira | La tarea se desprende como proyección y entra en el tablero |
| Jira | Cierre | Tablero, ticket y repositorio se reducen a un hilo estable |
| Cierre | Por dentro | El hilo gira 90 grados y se convierte en el eje vertical de las capas técnicas |

## 9. Estrategia técnica de representación

Esta sección describe una propuesta de implementación, no una selección tecnológica confirmada.

### 9.1 HTML y CSS

Se usarán para:

- titulares, texto, navegación y llamadas a la acción;
- conversación funcional;
- propuestas técnicas;
- aplicación Mendiara;
- tablero y ticket Jira;
- estados, labels y mensajes accesibles.

El contenido importante no se rasterizará dentro de imágenes generadas.

### 9.2 SVG

Se usará preferentemente para:

- recorridos y relaciones;
- ciclo de especificación;
- cadena de trazabilidad;
- arquitectura del plugin;
- flechas y recibos Jira;
- iconografía técnica.

### 9.3 Three.js

Se reservará para elementos que realmente se beneficien de profundidad:

- hilo luminoso y partículas;
- planos de elevación;
- versiones documentales en profundidad;
- órbita de reconciliación;
- capas explotadas del interior del plugin.

No se empleará Three.js para texto, tablas, formularios, tableros o navegación.

### 9.4 Imágenes

- La fotografía corporativa de Mendiara será sintética y se identificará como parte de un caso ficticio.
- Los keyframes ImageGen son referencias de dirección artística, no fondos finales ni contratos de píxel.
- Los logotipos y recursos de LKS Next deberán partir de activos corporativos autorizados.
- Si el site se publica fuera del entorno interno, se revisará el uso de marcas y apariencia de terceros como Jira y Atlassian.

## 10. Comportamiento responsive

### Escritorio

- Escenas fijadas de 140–260 vh según complejidad.
- Canvas persistente con profundidad completa.
- Aplicación y Jira pueden usar inspector lateral.
- Indicador vertical de capítulos.

### Tableta

- Reducción de profundidad y partículas.
- Aplicación y Jira mantienen estructura horizontal simplificada.
- Las escenas complejas se dividen en dos pasos.

### Móvil

- Se conserva toda la información, pero no toda la simultaneidad.
- La conversación, alternativas, aplicación, pruebas y anotación aparecen secuencialmente.
- El Kanban se convierte en columnas deslizables y el ticket se abre como panel completo.
- El hilo naranja pasa a ser principalmente SVG/CSS.
- No se utilizará scroll horizontal obligatorio para comprender el relato.

## 11. Movimiento reducido y accesibilidad

- `prefers-reduced-motion` elimina partículas continuas, parallax y cámara 3D.
- Las escenas se convierten en bloques normales con transiciones de opacidad breves.
- No habrá scroll secuestrado: la persona podrá desplazarse con rueda, trackpad, teclado y tecnologías de asistencia.
- El canvas será decorativo para accesibilidad y tendrá equivalencia completa en HTML.
- Estados y categorías incluirán texto o símbolos, no solo color.
- El foco será visible y seguirá el orden narrativo.
- Las anotaciones tendrán alternativa textual.
- Las interfaces ficticias deberán mantener contraste, tamaño de texto y objetivos de interacción adecuados.

## 12. Rendimiento

- Un único canvas persistente, reutilizando escena, geometrías y materiales.
- Carga diferida de imágenes y escenas técnicas.
- Pausa de render cuando el canvas no esté visible.
- `devicePixelRatio` limitado según dispositivo.
- Reducción dinámica de partículas en equipos de menor capacidad.
- Imágenes en AVIF/WebP con tamaños adaptados al viewport.
- Interfaces de producto construidas en HTML; no se cargarán grandes vídeos para simular interacción.
- La experiencia debe conservar sentido si Three.js no se inicializa.

## 13. Referencias visuales seleccionadas

| Ámbito | Archivo de trabajo |
|---|---|
| Apertura clara | `exec-db6e74b2-9bf6-4648-a17e-1cd284096283.png` |
| Especificación evolutiva | `exec-e001f343-93ab-4af5-8b86-ba7b67f04403.png` |
| Caso Mendiara | `exec-a6f03111-c8b2-40c6-96a5-3c9c7eea24e7.png` |
| Integración Jira | `exec-9d2e15b4-2823-41ef-99bb-9c655c62f5fb.png` |
| Interior técnico | `exec-56392256-a025-45be-90ba-630e0a8602b1.png` |

Los archivos permanecen actualmente en el directorio local de imágenes generadas de Codex. Antes de implementar se decidirá cuáles son meras referencias y cuáles deben convertirse en activos controlados del proyecto del site.

## 14. Criterios para autorizar la implementación del site

Antes de generar código deben quedar confirmados:

1. estructura de las dos rutas;
2. orden y mensaje principal de las escenas;
3. equilibrio de fondos claros, oscuros y naranjas;
4. caso ficticio Mendiara Mobility;
5. nivel de detalle visible de Codex y Jira;
6. intensidad de movimiento en escritorio;
7. destino del site y audiencia autorizada;
8. activos corporativos definitivos de LKS Next;
9. tratamiento legal y visual de marcas de terceros;
10. alcance de analítica, publicación y mantenimiento, si aplican.

La aprobación del storyboard no implica por sí misma autorización para publicar, desplegar o modificar el plugin LKS-SDD.
