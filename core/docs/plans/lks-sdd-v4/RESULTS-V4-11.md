# V4-11 — Seis skills e instrucciones por operación

Fecha: 2026-10-17. Implementación y comprobación técnica completadas.
AC-20/21 verificados en alcance técnico local. La aceptación dependiente del
sobrecoste AC-40 de V4-07A y la observación del host AC-30 siguen pendientes;
no se cierra esa dependencia por adaptar las instrucciones.

## Entrega

- Las seis skills conservan nombres, descripciones, invocación implícita y rutas
  de legado. Comparten comandos, autorización, presentación y recarga en V3-COMMON;
  mantienen sus instrucciones específicas y enlaces condicionales.
- Autoría usa alcance explícito y lotes de legado revisables; consultas/preparación
  reutilizan hechos vigentes; implementación y verificación referencian las
  operaciones compuestas sin confundirlas con decisiones, pruebas o aceptación.
- Se incorporan versión efectiva, actividad sin resultado terminal, continuidad,
  interrupción cooperativa, recibos y recuperación. Las señales son optativas;
  no provocan relanzamientos ni se confunden con avance o éxito.
- Se corrigen dos rutas ausentes del catálogo: `work-continue` y
  `work-record-results`. El fallo se reproduce con el catálogo previo conservado.
  Las tres operaciones V4 reciben únicamente su guía operativa pertinente mediante
  `instruction_refs(..., event=...)`; la llamada anterior sigue siendo válida.
- La lista estática admite exactamente las tres guías compartidas recién enlazadas.
  Se conservan comprobaciones de existencia, límites de ruta y enlaces transitivos.
  No se añaden perfiles, comandos, agentes, hooks ni política distinta por host.

El destino de las obligaciones centralizadas consta en la
[matriz de reglas](RULE-MAP-V4-11.md). Las fuentes previas exactas quedan en `before/`
dentro de la evidencia; no se sustituyen por resúmenes. La revisión de destino no
equivale a comprensión humana ni a certificación semántica por el validador.

## Comprobación focal y reducción estática

**9 pruebas distintas superadas:** ocho de rutas, recursos, metadatos, composición,
rechazos y paquetes, más una regresión real de recibo obligatorio y cambio de
fuente. La prueba de paquetes extrae ambos adaptadores, comprueba las seis skills
y guías, y ejecuta presentación/captura desde sus bytes. Esto no es H2 ni aceptación
de Codex/Copilot. Las seis skills pasan además `quick_validate`.

La primera validación estática rechazó los nuevos enlaces compartidos. Se conserva
esa salida; la lista finita se corrigió y la validación final pasa, junto con los
13 fixtures y `git diff --check`. No hubo fallos de las pruebas focales. Las cuatro
comprobaciones rápidas preliminares pertenecen a las ocho finales y no se suman.

La comparación de las **mismas 12 rutas existentes** mide **5,04–11,97 % menos
caracteres**, manteniendo **3–6 archivos seleccionados** según la ruta. Las tres
rutas compuestas adicionales se miden por separado, sin inventar una referencia
anterior equivalente. No se usa la comparación con «todas las guías» como ahorro
frente a la versión anterior. Los datos exactos están en `paired-static-routes.json`.
La batería de rutas duró 124,064 s y la regresión de recibos 21,256 s, en paralelo.

Estos datos describen archivos de instrucciones seleccionados. No miden lectura,
búsqueda, ampliaciones condicionales, errores del host, tokens facturados ni ahorro
de tarea completa. `billed_tokens` y `observed_host_tokens` permanecen `null`.
La ausencia de mayor fricción en uso real pertenece a la observación pendiente.

## Evidencia reutilizada y límites

Las fuentes canónicas, esquemas, rutas de legado, metadatos de invocación, escritores
de negocio y guardas de frescura permanecen iguales. En runtime solo cambian el
catálogo, sus dos consumidores de referencias y la lista estática de recursos.
Se reutilizan las pruebas anteriores de autoridad, operaciones, recuperación y
puerta general; no se repiten Windows ni las suites no afectadas.
Después de la ejecución de paquetes se aclaró únicamente el formato de los nombres
de dos comandos en la guía común; se revisó el texto y se refrescaron hashes y
validaciones estáticas, sin repetir esa ejecución completa.

Se mantienen seis mejoras, 23 tareas, 44 criterios y los presupuestos. Cero intentos
de campaña de tarea completa o variantes M6 nuevos. No se deduce un nuevo saldo
global ni aceptación de AC-40. Windows/H2 permanecen pendientes; no hay instalación,
publicación, commit ni push. La siguiente tarea es V4-12.

Registro: [v4-11-progress.json](v4-11-progress.json).
Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-11`
(`consolidated-result.json`, comprobaciones, rutas, huellas y fuentes previas).
