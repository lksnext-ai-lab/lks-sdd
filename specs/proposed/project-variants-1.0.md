# Variantes tecnológicas de proyecto — contrato aditivo 1.0

Alcance solicitado: diagnóstico, aprobación durable, observers del consumidor,
verificación proporcional y cierre local de TASK. No modifica las fuentes de
`specs/canonical`, los perfiles, sus locks ni las EVID históricas.

El perfil del binding sigue siendo la **referencia**, no una afirmación de que
el consumidor reproduce su composición. La variante describe las diferencias
reales, incluidos versiones, dependencias, disposición y observer. Su aprobación
no cambia el catálogo ni concede G4, release o producción.

Estados tecnológicos: `exact-certified`, `compatible-certified` (reservado a
reglas certificadas explícitas), `unassessed-variant`,
`approved-project-variant`, `incompatible`, `not-assessed`. Una diferencia con
el catálogo es desconocimiento; una contradicción manifest/lock es incompatibilidad.

La política optativa y las variantes se declaran en un único Markdown canónico:
`docs/lks-sdd/02-design/technology-variants.md`. La ausencia de este documento
mantiene la ruta estricta. Aprobaciones inmutables en `technology-approvals/`
enlazan proyecto, release, incremento, tareas, entorno, etapa, AUTH, perfil base,
diferencias, riesgos, gates, hashes y vigencia. Preview/hash/apply liga una sola
decisión a todos esos elementos; ninguna aprobación implícita o `--force`.

El observer oficial se ejecuta en Docker Linux sin red exterior, root, privilegios,
socket Docker ni acceso al contrato canónico. Recibe una instantánea explícita de
entradas de solo lectura. Solo su directorio temporal de salida es escribible.
El runtime valida schema, código de salida, scopes, interfaces, artefactos y hashes;
el observer no escribe la evidencia ni el estado de la tarea. Un observer aprobado
es código revisado de confianza para ese alcance; un schema no demuestra por sí
solo la veracidad semántica de un test.

Diagnóstico no ejecuta procesos técnicos. Desarrollo selecciona gates de esa
etapa; integración añade los suyos; release exige todos los gates del perfil base
y de la política. Los gates de aceptación de la TASK y los de integración aplicables
son obligatorios para cerrarla, aunque no se ejecuten en cada iteración de desarrollo.
Omisión, reutilización y ejecución son hechos distintos. Solo evidencia íntegra,
determinista y vigente con iguales entradas puede reutilizarse.

La evidencia 1.3 se amplía con procedencia de variante; permanece separada de la
certificación global. Cerrar exige política explícita, aprobación vigente, AUTH y
EXEC actuales, gates críticos passed, reservas documentadas e integridad completa.
El cierre usa la transacción TASK/EXEC/CKPT existente y no acredita una entrega.
