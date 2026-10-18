# V4-07A — Actividad e interrupción cooperativa

Estado: **implementación local y comprobaciones técnicas superadas; aceptación de
AC-40 pendiente por sobrecoste sin acreditar**. V4-07A no se declara cerrada.
Sin instalación ni publicación.
La incidencia de aislamiento de Windows y H2 siguen pendientes, sin cargas ni accesos.

## Cambio

`--activity` añade señales breves por stderr, también durante la admisión del
lanzador público. No altera el JSON final ni presenta porcentajes o ETA. La cadencia
es 1,5 s y el límite 16 KiB por invocación; se desactiva al cerrar el canal. El hilo
principal no espera a que se vacíe un pipe de actividad sin lector.

En las tres operaciones V4, Ctrl+C solicita una parada cooperativa. Los checkpoints
de lectura, carga, parseo, evaluación y etapas interrumpen el cálculo en fronteras
declaradas. La aplicación material termina su etapa y retiene su recibo antes de
parar. No ejecuta cancelación de negocio. Conserva efectos, journal, objetos y
trabajo posterior; el reintento exacto y la recuperación mantienen sus guardas.
La salida usa 130 sin efectos y 3 con efectos/journal pendiente. Una captura externa
interrumpida puede requerir inspección aunque ya haya publicado una entrada.

No cambia contratos canónicos, esquemas, journal ni autoridad. La descripción de
superficies y límites está en [WORK-ACTIVITY.md](../../WORK-ACTIVITY.md).

## Evidencia y pendientes de aceptación

**81 comprobaciones distintas superadas**, sin contar repeticiones como pruebas nuevas:

| Grupo | Casos | Evidencia vigente |
|---|---:|---|
| Humo estable y regresión Windows larga | 15 | `technical-result.json` |
| Presentación compatible/operativa, exportación y errores | 17 | `presentation-result.json` |
| Captura, conservación, corrupción y recuperación | 28 | `diagnostic-result.json` |
| Autoridad, calidad, relevo, recibos y lanzador fijado | 5 | `guards-result.json` |
| Actividad, Ctrl+C, etapas, journal, rutas largas y pipe sin lector | 16 | 14 de `activity-corrected-result.json`, caso corregido en `long-case-final-result.json`, pipe en `pipe-final.stdout` |

`consolidated-result.json` selecciona los 81 resultados vigentes. Los hashes prueban
que producción no cambió desde la puerta técnica; la reconstrucción de la expresión
corregida y la comparación AST justifican reutilizar los otros casos del arnés.
Los **143 archivos** de contratos canónicos, esquemas y skills permanecen iguales
al inicio del lote. `git diff --check` y las validaciones estáticas no presentan errores.

Evidencia recuperable en
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-07a`.
`source-freeze.json` conserva el candidato de la batería; `verification-result.json`
conserva los fallos iniciales, sin convertirlos en aprobados. La corrección posterior
del arnés se contrasta contra los mismos hashes de producción antes de reutilizar
la evidencia no afectada.

La puerta técnica, presentación, diagnóstico y guardas han pasado. La primera
ejecución focal detectó una expectativa incorrecta: un efecto ya aplicado conserva
estado parcial si posteriormente cambia el código. El arnés también creó componentes
de directorio con espacios finales, accesibles mediante el prefijo NT extendido pero
incompatibles con su limpieza ordinaria. La primera observación no demuestra una
regresión de MAX_PATH del plugin. Se corrige únicamente el nombre del arnés,
conservando >260 caracteres, espacios interiores, Unicode y el helper existente.
La repetición focal de recuperación y limpieza pasó en **163,96 s** con espacios
interiores, Unicode y ruta >260. No se afirma soporte de nombres Win32 con espacios
finales. También pasó una prueba nativa que llena stderr sin lector: el proceso
termina con un único JSON válido, sin esperar a vaciar el pipe.
El residual de ese arnés fallido se retiró únicamente por su ruta propia exacta,
previamente verificada; el recibo `cleanup.json` conserva el alcance y resultado.

El ensayo local de señales breve pasó. Una comparación adicional de trabajo CPU fijo
de dos millones de checkpoints, ejecutada con otros tests/procesos concurrentes,
superó el límite: delta de medianas de **0,688 s de pared y 0,313 s de CPU**, frente
al mínimo permitido de 0,100 s. Se conserva en `fixed-work-overhead.json`.
La concurrencia impide atribuir la causa; no se descarta por su resultado ni se
acredita AC-40 con la muestra breve. El sobrecoste queda pendiente de una ventana
comparable y, si procede, de corrección dentro de la tarea. No se ejecutó ningún
recorrido S8 nuevo ni se acredita ahorro integral o de tokens.

Los límites de reacción se comprueban en checkpoints CPU y fronteras declaradas;
las E/S, Git y la sección de escritura pueden diferir la parada. Ni estas pruebas
ni la puerta técnica son aceptación de Codex/Copilot o ejecución de H2.

## Disposición

- **AC-41:** verificado en las superficies locales declaradas. Se conservan límites
  de E/S y aplicación material; no se promete reacción instantánea en ellas.
- **AC-40:** canal, cadencia, volumen y compatibilidad verificados; sobrecoste
  pendiente. Una única comprobación adicional sobre parseo real, preregistrada
  ABBAAB, tampoco proporciona una ventana estable: dispersión de pared de 57 %
  desactivado y 23 % activado, superior al 5 % fijado antes de medir.
  Las medianas favorables de esta muestra **no se consideran ahorro**.
  Se conserva `parse-overhead-result.json`; no se repite la medición indefinidamente
  ni se cambia producción sin una causa demostrada. Queda por acreditar el límite
  de coste en una ventana comparable y corregirlo si se reproduce el exceso.
- La consolidación V4-15/17 debe recoger también stderr en el coste total cuando
  active señales; el tamaño de stdout no representa ese canal. No se añade un
  recorrido ni una tarea al DAG por esta integración ya prevista.
- Cota actual: aproximadamente **40 de 60 min**; se conserva el saldo y no se amplían
  presupuestos, variantes M6 ni intentos completos. **Cero intentos S8 nuevos**.
  V4-06 mantiene pendiente la aceptación de rendimiento integral anterior.
- Windows/H2 pendientes; sin cambios de configuración del host, instalación,
  publicación, commit o push. Las seis mejoras y la cobertura se mantienen.
