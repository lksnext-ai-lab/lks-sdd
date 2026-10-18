# V4-14 a V4-16 — Compatibilidad, garantías y paquetes

Fecha: 2026-10-17. Sin instalación activa, publicación, commit ni push.

| Tarea | Resultado y alcance |
|---|---|
| V4-14 / AC-24, AC-25 | Verificadas técnicamente sobre consumidores sintéticos: actualización explícita desde 3.4.3, conservación del trabajo abierto/decisiones, rollback y recuperación. |
| V4-15 / AC-26 | Comprobaciones técnicas consolidadas; aceptación global pendiente por los hallazgos conocidos de rendimiento y AC-40. No se declara ausencia de defectos materiales pendientes. |
| V4-16 / AC-29 | Cinco archivos ZIP reproducibles del mismo núcleo; integridad, recursos, extracciones y capacidades técnicas comprobados. Desarrollo, sin aceptación de host. |

## Qué se ha incorporado

La [guía de candidata](../../V4-CANDIDATE.md) explica capacidades, actualización,
compatibilidad, recuperación y límites. README y validación la enlazan. Se añade
`tests/test_v4_compatibility.py` y se incluyen sus recursos en la distribución.
El motor, las seis skills, los esquemas y `specs/canonical/` no cambian en este
bloque; las huellas permiten reutilizar las garantías vigentes sin una batería global.

La matriz ejecutada comprende formato 3.1/método 3.1.0 con pin 3.4.3 → candidata.
Los lectores declarados de formatos anteriores se conservan y su evidencia previa
se reutiliza: no se afirma una nueva actualización ejecutada desde cada origen.
La corrección histórica 3.4.2 → 3.4.3 se mantiene separada de este corte.

## Comprobaciones nuevas y evidencia reutilizada

Tres pruebas focales de compatibilidad pasan: preview de solo lectura, actualización
y validación desde CLI fijada, identidad de tareas/planes/propuestas/decisiones
anteriores, estado abierto y código conservados; rollback exacto de archivos previos;
recuperación tras una escritura interrumpida; rechazo de rollback sobre cambio
posterior; rechazo de bundle ausente y de pin modificado entre preview y aplicación.

Cuatro pruebas adversas pasan: mutación durante preparación (dos subcasos), permiso
revocado, calidad obligatoria sin resultado válido y captura corrupta. Se reutiliza
la evidencia vigente de negativos, continuidad, instrucciones, adjuntos, recuperación,
interrupción y rutas largas del plugin: scripts, formatos y reglas implicados son
idénticos. `guarantee-map.json` vincula G1–G10, fuentes y límites a la candidata.
La incidencia del aislamiento nativo de Windows no se ha vuelto a probar.

Desde cada proyección empaquetada se ejecutaron preparación, inicio y registro hasta
cierre: **seis operaciones públicas**, con prueba Python real del saludo/firma,
stdout JSON operativo, actividad limitada por stderr y captura externa `stored`.
Las consultas no mutaron sus consumidores; cada cierre conserva cuatro ejecuciones
y una evidencia. Esto acredita capacidades técnicas, no una sesión del host ni H2.

El descubrimiento inicial incluyó once pruebas de la clase de fixture importada,
además de las tres previstas. Sus resultados se conservan, sin contarlas como nuevas
garantías necesarias. Se corrigió el import a un alias de módulo: futuros runs solo
descubren las tres propias. El intento inicial también encontró dos expectativas
incorrectas del arnés: el journal debe conservar la transacción revertida y la
interrupción inyectada es `InterruptedError`. Se corrigieron y se repitieron solo
esos dos casos; el tercero y las once pruebas importadas ya superadas se conservan.
El código funcional no cambió.

Se conservan otros tres resultados del arnés: rechazo correcto de CLI externa al pin;
una expectativa incorrecta de cinco ejecuciones en vez de cuatro más evidencia;
y detección del cambio de import al comprobar la huella final. No se relajó ninguna
guarda: se utilizó la CLI fijada, se corrigió la expectativa y se conservaron los dos
recorridos ya completados, sin repetirlos. Los paquetes finales se reconstruyeron
con identidad nueva y se validaron otra vez desde el pin de cada adaptador.

## Paquetes finales de aceptación técnica

- Fuente: `working-tree:5f489951930534a51097c7d83e36c455aa91c7074d5edf2b68c96871ae291db2`.
- Runtime: `26334075bc388308823bd63350a098b1a3a5ff722c14ce02bcead6d32d4b4c53`.
- Canal: `development-unreleased`; versión base de manifest `3.4.3`.
- Dos construcciones finales producen bytes idénticos; cinco ZIP, manifiesto y
  `SHA256SUMS` conservados en `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-14-16\final-corrected`.

El número 3.4.3 del manifest no convierte estos archivos en la versión publicada:
se distinguen por canal, fuente y digest. La promoción de versión estable queda
pendiente; estos paquetes no deben sustituir silenciosamente assets publicados.

Los cinco ZIP preliminares se extrajeron completamente y se verificó cada archivo.
Tras corregir el descubrimiento y las dos expectativas de pruebas se revisaron todos los nombres/CRC,
manifiestos y checksums finales; se reutilizan los archivos idénticos por sus bytes.
Los núcleos finales Codex/Copilot se extrajeron completamente en consumidores propios,
se verificó cada byte, pin y estado cerrado y ambas CLI finales validaron el proyecto.
La procedencia y la diferencia exacta entre revisiones están en `final-package-result.json`.
No se repiten seis operaciones cuyo código e instrucciones son idénticos.

Contrato estático, 13 fixtures y revisión de diff pasan. Se ha revisado la diferencia
de producción: solo documentación, inventario de distribución y pruebas. No se ha
ejecutado ni declarado aprobado un nuevo gate stable; exige otra fuente limpia y
aprobación de versión conforme a la política del repositorio.

## Pendientes preservados

AC-40 (sobrecoste), regresión temporal/memoria S8, Windows y H2 siguen pendientes.
V4-15 no convierte esos resultados en aceptación de AC-26. La cobertura de interrupción
del motor se reutiliza y ambos adaptadores conservan exactamente esos bytes; no se
afirma una nueva señal nativa por host ni aborto instantáneo. Copilot real, observación
de host, comparación final S8 y percepción humana prolongada no se acreditan aquí.

Se mantienen seis mejoras, 23 tareas, 44 criterios y las reservas. Cero variantes
M6 y ninguna muestra nueva para acreditar ahorro. Por prudencia se imputan tres
intentos de recorrido al presupuesto global: el inicial rechazado antes de preparar
y los dos recorridos empaquetados completados. Las correcciones del arnés continuaron
esas mismas ejecuciones, sin reiniciar trabajo aplicado. El registro conocido y
reservado pasa de 45 a **48/48**; conserva cuatro slots S8 finales y dos H2 ya incluidos
en la reserva previa. No queda capacidad no asignada para otro recorrido completo.
No se amplía presupuesto ni se certifica un nuevo saldo global de horas. Las pruebas
unitarias/estáticas se registran aparte. Tokens del host y facturados siguen `null`.

Siguiente bloque: V4-17/V4-17A, sin reactivar Windows/H2 por esta entrega.
Registro: [v4-14-16-progress.json](v4-14-16-progress.json).
Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-14-16`.
