# Relevo visual Copilot → Codex → continuación opcional

Referencia del contrato 1.5. Para contrato 2.0 use los comandos `v2 visual-request`,
`visual-inspect`, `visual-observe`, `visual-accept` y `visual-cancel` documentados en
[workflows v2](V2-WORKFLOWS.md); no mezcle formatos de solicitudes entre contratos.

El relevo coordina archivos; no genera imágenes, llama APIs, crea sesiones ni abre apps.
El schema consumidor sigue siendo 1.5. La solicitud auxiliar 1.0 no es una autorización
de implementación ni un registro de aceptación. UX/VIS/ADR canónicos conservan autoridad.

## Codex nativo

Siga el proceso visual habitual sin avisos ni fichas de relevo. Pida la aprobación visual
normal y explique fallos reales. No invite al usuario a volver a Codex si ya está allí.
`prepare --host codex` es defensivamente una operación sin escrituras ni invitación.

## Preparar en Copilot

Solo para brief suficiente, interfaz aplicable y modo `new` o `material-change`.
Materialice ART-UX y documente el pendiente en ART-INCREMENTS/ART-OPEN. Mantenga un
brief delimitado separado en `docs/lks-sdd/03-solution/visual-briefs/`, con requisitos,
pantallas, flujos/estados, restricciones, estilo, referencias, alcance y exclusiones.
No use la tabla UX de salida como archivo inmutable de brief. No prepare relevo para
backend, reutilización confirmada o decisiones que todavía impiden escribir el brief.

```powershell
python "<runtime>/scripts/lks_sdd.py" visual-handoff prepare "<proyecto>" --host copilot --increment INC-001 --brief docs/lks-sdd/03-solution/visual-briefs/BRIEF-001.md --scope "Propuestas de las pantallas UX-001 y UX-002" --owner-role design-owner --json
```

Repita los mismos argumentos con `--apply --authorize HASH_DEVUELTO` tras confirmar esa
escritura local. `--input ruta/relativa` añade referencias binarias u otros archivos al
snapshot. `--task` y `--execution` solo se usan si existen y corresponden al alcance;
no se crean TASK/AUTH/EXEC/CKPT para simular un relevo durante definición.

La CLI devuelve el ID real y `request.md`. Muestre una invitación breve y el mensaje de
esa ficha. Antes de repetir preparación, lea `status`: una solicitud vigente se reutiliza;
no reinvite en cada turno. Una revisión material usa `--revision` y fuentes actuales,
sin borrar ni reescribir la historia anterior.

## Continuar en Codex

Abra el mismo proyecto o transfiera el repositorio completo al clon del compañero mediante
el procedimiento Git autorizado. Pegue el mensaje de `request.md`; no hace falta el chat.

```powershell
python "<runtime>/scripts/lks_sdd.py" visual-handoff inspect "<proyecto>" --id VH_ID_REAL --json
```

Si hay deriva, identidad/versión distinta o archivos ausentes, reconcilie antes de generar.
Use generación integrada y conserve las nuevas revisiones PNG/JPEG bajo la ubicación
actual de `ui-prototypes/`. No edite una referencia de entrada en su mismo archivo.
Registre VIS reales con firma, dimensiones, hash y procedencia ImageGen. En `Prompt or brief`
incluya la ruta relativa exacta del brief de esta solicitud. Presente alternativas y solicite
selección/correcciones explícitas; no invente confirmaciones para completar la ficha.

Actualice VIS/UX y la tabla de interfaz; use una ADR nueva para la decisión visual cuando
las decisiones anteriores formaban parte del snapshot. Si cambia sustancialmente una decisión
previa o el brief, es una nueva revisión, no una devolución compatible.

```powershell
python "<runtime>/scripts/lks_sdd.py" visual-handoff complete "<proyecto>" --id VH_ID_REAL --visual VIS-001 --json
```

Puede repetir `--visual` para varios resultados aprobados. Aplique con el hash exacto.
La operación exige validación canónica, aprobación explícita, ADR válida, pertenencia al
incremento y vínculo al brief. El resultado es inmutable y su estado se deriva al releerlo.
Una marca manual «completado» no evita los checks. Si el proyecto tiene errores canónicos,
se deben reconciliar antes de cerrar el resultado; no se interpreta como aprobación parcial.

## Volver o permanecer

Al terminar, indique una sola vez que los resultados están guardados y que puede continuar
en Codex o volver a Copilot. Si aún no se ha aprobado, diga que sigue pendiente.
En Copilot, «continúa» debe leer las solicitudes, seleccionar el alcance e inspeccionar
el resultado. Recalcule readiness normal; no regenere lo aprobado ni salte autorizaciones.
Las capturas y pruebas de la aplicación siguen siendo obligaciones separadas.

## Integridad y recuperación

`request.json` y su Markdown se publican juntos mediante renombrado local exclusivo.
`result.json` y `cancelled.json` no se sobrescriben. El lock local no es un lock distribuido
entre clones. Si se interrumpe una operación, inspeccione archivos y proceso antes de
retirar manualmente un lock huérfano; no marque completado por el último mensaje del chat.

Las huellas incluyen las fuentes canónicas sustantivas y referencias previas. Solo se
normalizan las filas VIS de salida, las celdas de aprobación de dirección visual y los
campos Visual mode/Visual prototype; una ADR nueva puede añadirse sin cambiar las anteriores.
ART-STATUS/ART-OPEN no son el brief. Un cambio de UX, requisito, archivo referenciado o
decisión previa exige reconciliación. No se excluye globalmente la carpeta de handoffs
de las huellas técnicas existentes: un relevo puede invalidar autorización/verificación y
se recalculan los gates normales. Nunca reutilice una autorización obsoleta por comodidad.

`status` e `inspect` son de solo lectura. `cancel --id ... --reason ...` usa preview/hash/apply,
no borra archivos y no convierte la cancelación en aceptación. Una solicitud cancelada
requiere revisión nueva. Con varios IDs no se selecciona «el último» automáticamente.
