# Tratar observaciones y resultados rechazados

Presente el acuerdo o resultado esperado, la diferencia observada, su tratamiento,
los cambios y alcance, la comprobación y pendientes. Conserve el desacuerdo original
y muestre el antes y después. No sustituya un rechazo por aprobación porque falte
un documento, una prueba o un dato administrativo.

`review-comment` puede registrar una objeción sobre un borrador. `resolve-comment`
explica incorporación o descarte y su motivo; el autor de una objeción confirma su
tratamiento al revisar. Registrar el comentario no requiere otra firma.

`reject-result` conserva fase, esperado, observado y alcance; una evidencia ausente
se declara pendiente. `define-correction` distingue defecto, cambio de acuerdo,
petición nueva y asunto externo. Corregir un defecto dentro de un encargo vigente
no amplía el permiso. Si cambia lo acordado, lea [especificaciones](specifications.md)
y complete la planificación antes de ampliar código.

`resolve-defect` exige definición confirmada y evidencia vigente posterior al fallo.
No reutilice las pruebas anteriores como prueba de corrección ni declare aceptación
funcional por resolver el defecto. Lea [verificación](verification.md) para presentar
las pruebas nuevas y volver a integrar/aceptar cuando corresponda. Las decisiones
positivas se vinculan al contenido presentado; comentarios y rechazos siguen
disponibles aunque no sea posible una aprobación global.

## Elegir el recorrido proporcional

Para un incumplimiento dentro del acuerdo vigente, conserve petición, propuesta,
plan, tareas y decisiones que sigan cubriendo el cambio. Compruebe las condiciones
actuales con `work-prepare`; su respuesta ya contiene estado, intervenciones y
contrato literal. Reutilice esa respuesta mientras no cambie su base. No repita
`status`, `interventions`, `readiness` y `context` para obtener los mismos datos.
Un cambio de fuente, evidencia, operador o base exige preparar de nuevo.

Con tarea vigente, permiso actual y alcance cubierto, use `work-continue` para
iniciar/reanudar y `work-record-results` para conservar resultados de las pruebas
afectadas y las etapas técnicas siguientes. Los acuerdos vigentes se reutilizan;
las operaciones vuelven a comprobarlos. La guía de
[operaciones compuestas](../WORK-OPERATIONS.md) contiene sus entradas y límites.
Con un runtime anterior use los comandos individuales disponibles: no actualice
ni instale implícitamente para resolver una corrección.

Una tarea cerrada requiere `reopen`; un permiso revocado o una identidad vencida
requiere restablecer autoridad por su operación competente. Un resultado rechazado
conserva `reject-result`, clasificación con `define-correction`, pruebas posteriores
al fallo y `resolve-defect`. Después se repiten integración y aceptación cuando
correspondan. La reapertura o la resolución por sí solas no restauran aceptación.

Si cambia el comportamiento acordado, los permisos, los datos o una interfaz,
presente primero la propuesta revisada y registre su validación; prepare después
las tareas afectadas y su autorización. Use `author` para cada contenido y las
decisiones existentes de propuesta y plan. En recorrido integral, la propuesta
pasa por `close-proposal` y el plan por `authorize-plan`. No cree propuesta nueva
y tareas ejecutables juntas antes de esa validación, ni reinicie el proyecto.

Una capacidad nueva sigue ese recorrido en una petición propia y con cobertura
explícita. Clasificar como `new-request` no amplía el permiso de las tareas previas;
las nuevas tareas necesitan su acuerdo, plan y autorización. Conserve la petición
original y sus reservas. Una incertidumbre crítica impide continuar hasta decidirla.
El número de líneas cambiadas no determina ninguna de estas clasificaciones.
