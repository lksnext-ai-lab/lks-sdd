# Diagnóstico del uso del plugin

El objetivo es identificar problemas y oportunidades de reducir trabajo o tiempo,
y conservar un caso que pueda investigarse en el repositorio de LKS-SDD. La calidad,
el contrato literal y la autoridad tienen prioridad sobre reducir contexto.

## Recogida y continuidad

Las operaciones de `v3` entregan sobres `usage.observations` del runtime común.
Conserve esos sobres en la conversación mientras consulta o prepara. En cada
operación del mismo trabajo pase `usage_context` con `run_id`, `phase`, y las
referencias `request`/`tasks` que haya observado. No atribuya personas, tareas,
lecturas o historial que no conozca. Una ventana sin referencias es provisional.
Reutilice el run conservado tras compactación o chat nuevo; anote huecos en `gaps`.
`window_state` describe provisional/linked/in-progress/finished/blocked/interrupted;
es independiente de los estados de calidad y aceptación del proyecto.

Antes de un hito útil ya autorizado, incluya los sobres pendientes en
`usage_context.observations`. El mismo preview y diario del hito conservan un lote
mediante receipt y objetos inmutables. No cree un checkpoint por cada consulta.
También existe `v3 usage-record`, para conservar un lote sin otro hito disponible.
No requiere otra aprobación dentro del alcance de trabajo autorizado, aunque
exige el runtime actual, la configuración y el operador ya observado. El
reenvío idéntico no genera otra escritura; una colisión de ID/datos se rechaza.
Dos invocaciones iguales siguen siendo dos invocaciones. Preparación y aplicación
se distinguen y se relacionan por preview_hash; un preview no demuestra aplicación.

Los sobres importados no adquieren origen medido por escribir `origin=runtime`.
Las importaciones conservadas se identifican como declaraciones; los hashes
acreditan integridad interna, no autenticidad ni lectura del host. Las medidas
indican método, unidad, cobertura y datos medidos/estimados/declarados/ausentes.
No hay registro de razonamiento privado, tokens facturados ni ahorro inventado.

Si el runtime/proyecto falla antes de iniciar, el CLI devuelve observaciones
transitorias, resumen y prompt sin escribir en el consumidor. Conserve ese JSON
para el exportador independiente. Un fallo de render deja diagnóstico incompleto;
un objeto o lote corrupto impide aplicar el journal, sin eliminar guards.

## Reporte y mantenimiento

Al implementar, verificar o preparar entrega, presente el resumen `usage.summary`
y mantenga accesible su prompt. En éxito, bloqueo o corrección relevante, agrupe
el diagnóstico del intento: cobertura; problema/candidato; evidencia; causa
pendiente; siguiente acción; material disponible. No repita el reporte por cada
reintento ni confunda diagnóstico con verificación o aceptación del producto.

Consulte `v3 usage-report` con `run_id`, `request` o `task`. Es de solo lectura y
regenerable. Incluye `summary`, `markdown`, `prompt`, hallazgos y métricas. Use
`offset`/`limit` (máximo 100), y `finding_id` para un caso focal. El total cuenta
operaciones compartidas una sola vez; los caracteres únicos se calculan por unión
de intervalos de cada fuente/revisión. El acumulado mantiene las repeticiones.

| Regla | Disparador | Límite de interpretación |
|---|---|---|
| UF-01 | Mismo fragmento/revisión en invocaciones distintas | Puede ser una relectura necesaria. |
| UF-02 | Selector amplía por alcance incierto/conflictivo | No demuestra fuentes irrelevantes. |
| UF-03 | Entradas/fallos equivalentes repetidos | Un reintento acordado puede ser correcto. |
| UF-04 | Guard rechaza preview con base intervenida | No permite saltarse el guard. |
| UF-05 | Contrato recuperado tarde y corrección vinculada | Declaración; causa y aplicabilidad previa pendientes. |
| UF-06 | Pregunta/paso repetido ante decisión vigente | Exige decisión, alcance e intervención; decisiones nuevas son legítimas. |
| UF-07 | Evidencia focal de coste, crecimiento o contaminación | No usa un umbral universal de rapidez. |

Los hallazgos conservan firma por regla/versión/alcance, ocurrencias, hecho,
hipótesis, impacto, destinatario, prioridad razonada, componente y siguiente
acción comprobable. Las declaraciones se añaden al sobre `stage=declared` y se
conservan mediante `usage-record`. Los tipos son `late-context`,
`repeated-question`, `diagnostic-overhead` y `finding-disposition`. Para UF-05
refiera `before`, `after`, `contract`, `defect`, `check` a adjuntos exactos; para
UF-06, `question`, `decision`, `scope`, `intervention`; para UF-07, `evidence`.
La disposición exige `finding_id`, `state` y `reason`; una resolución exige además
`plugin_version`, `change`, `evidence`. Una recomendación no resuelve un hallazgo.

## Paquete portable

`v3 usage-export` consulta la ventana y prepara un paquete. Las variantes
independientes funcionan incluso sin consumidor o runtime anterior:

```powershell
python -B <plugin-root>/scripts/lks_sdd.py usage-export --input case.json --output preview.json
python -B <plugin-root>/scripts/lks_sdd.py usage-export --input preview.json --destination <directorio-nuevo> --authorize <export_hash>
python -B <plugin-root>/scripts/lks_sdd.py usage-inspect <paquete>
python -B <plugin-root>/scripts/lks_sdd.py usage-inspect <paquete> --reproduce
```

`case.json` contiene `observations`, `materials` (ruta relativa → texto/JSON o
descriptor binario `{"encoding":"base64","data":"..."}`),
`selector` y dependencias explícitas. Los materiales solo se permiten bajo
`sources/`, `evidence/` y `reproduction/`. El paquete contiene REPORT.md,
MAINTENANCE-PROMPT.md, observations.json, manifest.json y esos adjuntos.
El prompt autónomo contiene el caso pequeño; si referencia adjuntos son necesarios.
Tras importarlo aquí, investigue hechos y causas antes de proponer cambios.
`dependencies` enumera requisitos externos imprescindibles aún sin incluir;
mientras existan, el paquete mantiene `needs-material`.

Para un caso de contexto, prepare explícitamente el fixture documental mediante
`usage_bundle.fixture(root, roots)`, y adjúntelo como `reproduction/fixture.json`.
Preserva bytes del grafo documental y selecciones esperadas; no es un respaldo
del código. `usage-inspect --reproduce` solo ejecuta el selector conocido sobre
ese fixture aislado. Nunca ejecuta scripts/órdenes recibidos. Su evidencia distingue
reproducción de selección de contexto, causa del defecto y aceptación del host.
El inspector ordinario comprueba campos, contenido, dependencias e integridad;
solo los datos imprescindibles completos permiten `ready-for-investigation`.
Los patrones de credenciales se redactan y sus transformaciones se declaran;
no garantizan anonimización completa. El caso transformado exige nuevo contraste.

Preview y exportación tienen `export_hash` propio sobre bytes exactos. El paquete
se publica completo en un destino nuevo y externo; una interrupción no produce
una entrega completa ni reemplaza otra. No use `v3 apply`/`--apply` sobre ese
preview informativo: no es una operación canónica del consumidor.

## Límites y compatibilidad

Lote: 1 MiB / 1000 observaciones. Ventana: 20000 observaciones / 64 MiB.
Página: 100 hallazgos. Paquete total: 64 MiB, manifiesto 1 MiB / 10000 entradas.
El exceso requiere acotar caso/ventana o consultar otras páginas. No se entregan
volúmenes incompletos como preparados. Al conservar el lote se recuperan fuentes
grandes y adjuntos binarios cuya revisión y bytes todavía coinciden. Se guardan
una sola vez en objetos inmutables; siguen exportables tras retirar la fuente.
Los sobres transitorios limitan texto inline a 64 KiB por fragmento y 512 KiB
por sobre. `transient_gap` conserva el hueco previo cuando el lote recupera sus
bytes. Si ya no están disponibles, queda material pendiente; un hash solo no los
hace recuperables. Los adjuntos usan intervalos de bytes, separados del recuento
de caracteres de las fuentes de texto.

`lks-sdd-usage/1` es un formato técnico nuevo, compatible con método/schema 3.1.
Los consumidores anteriores mantienen sus consultas; recoger de forma persistente
requiere corte explícito al runtime con esa capacidad. Actualizar el plugin del host
no actualiza el runtime fijado. Los receipts diagnósticos quedan fuera de la selección
normativa y bases semánticas de decisión; guards de documentos/preview siguen frescos.
Las acciones usage-* no se observan a sí mismas. Recogida, conservación, reporte y
exportación se miden por separado; no se afirma ahorro total a partir de este coste.

## Protocolo de aceptación en chat nuevo

En un consumidor de prueba, realice una funcionalidad, conserve su diagnóstico y
exporte un caso. Abra manualmente un chat en el repositorio del plugin y traiga el
prompt y todos sus adjuntos. Compruebe si permite localizar el componente, entender
esperado/observado, identificar pendientes, reproducir y proponer una regresión sin
consultar el chat original. Repita con Codex y Copilot registrando versión, fecha,
material y resultado. Este protocolo y la comprensión humana permanecen **not-run**
hasta observación real; las pruebas técnicas de paquetes no los sustituyen.
