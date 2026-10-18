# V4-08 y V4-09 — Resultado técnico

Fecha: 2026-10-17. Continuación autorizada con prioridad de rapidez y pruebas
focales. Ambas tareas y AC-15/16/17 quedan verificadas en el alcance técnico local.
La aceptación de uso real y del rendimiento integral sigue pendiente.

## Entrega

- Autoría determina la porción de la tarea con planes concordantes. Rechaza la
  herencia ambigua y la porción explícita contradictoria; ignora planes retirados.
- `catalog` con `kind: scope`, `roots` y un lote opcional `proposals` devuelve
  fuentes literales y un `proposed_project` separado. No escribe ni concede
  autoridad; continúa por la revisión de gobierno ya existente. Página por defecto
  de 20 fuentes, máximo 100; lote máximo de 100 declaraciones.
- Contexto explica unidades y prosa excluidas, e incertidumbres conservadas.
  `comparison: true` muestra diferencias con la referencia conservadora y verifica
  identidad literal de las fuentes comunes; no afirma equivalencia semántica.
- La clasificación de prosa conserva un manifiesto de adjuntos directos y
  transitivos en el evento de gobierno. Texto cambiado, adjunto cambiado, prueba
  revocada o manifiesto ausente amplían el contexto o bloquean una fuente ilegible.
  La caché comprueba también los adjuntos que fundamentaban exclusiones.
- Los descriptores conservan contratos entrantes, dependencias tipadas y conflictos.
  Las nuevas decisiones registran `approval_roots`: incluir una propuesta como
  dependencia no la aprueba de forma independiente. Se conserva la combinación de
  decisiones explícitas y la lectura de decisiones históricas compatibles.

Uso y formatos: [DOCUMENT-CONTEXT.md](../../DOCUMENT-CONTEXT.md).

## Comprobación y revisión

**39 casos distintos superados**, sin omisiones: 20 focales nuevos, 4 documentales
existentes, 14 del núcleo técnico y 1 regresión real de rutas largas. La incidencia
del aislamiento de Windows no se ha retomado.

La primera batería congelada pasó la puerta técnica y las cuatro integraciones
documentales. La revisión añadió un caso que reprodujo una ampliación indebida de
aprobación por una propuesta entrante. Se corrigió la causa y se comprobó que
aprobar A no aprueba B ni el conjunto A+B; dos decisiones independientes vigentes
sí pueden cubrir el conjunto y una dependencia cambiada invalida su vigencia.
También se corrigió la participación de planes retirados en la herencia de alcance.

Tras esas dos correcciones se repitieron los 20 casos rápidos y dos recorridos
afectados de ejecución completa/caducidad. Los dos recorridos pertenecen a los 14
del núcleo y no se cuentan dos veces. Se conserva el fallo inicial como evidencia.

La puerta inicial duró 515,100 s, en paralelo con las integraciones documentales.
La suite focal final duró 2,393 s y los dos recorridos repetidos, 103,961 s.
Son tiempos de validación del desarrollo, no latencias ni ahorros del producto.
Las esperas se hicieron en procesos nativos; no hubo campaña de rendimiento nueva.

Contrato estático y revisión de diff superados. Los cambios finales respecto al
lote congelado se limitan a `v3_scope.py` y `v3_approval.py`; su alcance y las pruebas
repetidas constan en el registro. Fuentes canónicas, esquemas y skills permanecen
intactos durante esta entrega. No se cambian las seis mejoras, las 23 tareas ni los
44 criterios.

## Legado, coste y límites

Ensayo acotado: cuatro documentos ajenos declarados, cinco campos por declaración,
previsualización sin autoridad y comparación con obligaciones globales, compartidas,
desconocidas, negaciones e imágenes. Se conserva el texto completo ante incertidumbre.
La prueba no demuestra amortización de una clasificación masiva: no se amplía el
lote ni se mide o estima esfuerzo humano. `billed_tokens` permanece `null`.

Se consumieron **cero intentos de tarea completa**. Se conservan los límites de
campaña y las reservas; no se deduce un nuevo presupuesto global de esta continuación.
V4-06 y AC-40 mantienen pendientes sus mediciones válidas. Windows y H2 siguen
apartados; Copilot y la percepción humana siguen pendientes de su cobertura real.
No se ha instalado, publicado, hecho push ni creado commits.

Registro único: [v4-08-09-progress.json](v4-08-09-progress.json).
Evidencia local: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-08-09`
(`consolidated-result.json`, resultados, huellas y ejecutores reproducibles).
La siguiente tarea funcional es V4-10; esta entrega no da por terminada la versión 4.0.
