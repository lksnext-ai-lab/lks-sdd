# Presentar pruebas, integración y aceptación

En verificación muestre resultado comprobado, criterios y pruebas, evidencia
observada, fallos y límites, tratamiento y siguiente acción. Distinga ejecución
automática, observación humana e informe externo. Un archivo creado o una prueba
prevista no acredita ejecución. Incluya esperado, observado, candidato, procedencia
y acceso a la evidencia recuperable. No convierta `not-run` en superado.

Para integración muestre componentes y compatibilidad, comprobaciones del conjunto,
incidencias y reservas, alcance de la conformidad y pendientes. Contraste candidato
y base de confianza del mismo proyecto; `integrate` registra revisión técnica,
no mergea ni aprueba remotamente un PR. Verifique las interfaces entre porciones.

Para aceptación funcional muestre resultado entregado, acceso y revisión,
cumplimiento de criterios, limitaciones, alcance de aceptación y pendientes.
Respete el orden de aceptación configurado. La misma persona habilitada puede
integrar y aceptar mediante `accept_result: true` si ya vio el candidato y sus
pruebas; los dos efectos se conservan. Un candidato o evidencia modificados exigen
reevaluar lo afectado. Cerrar tareas no sustituye aceptación funcional.

Sonar y Dependency-Check se deciden y verifican por separado. Confirme un medio
viable autorizado, sin instalar infraestructura; exija resultados terminales,
entradas/configuración/procedencia y vigencia. Un error o falta de acceso no convierte
un control obligatorio en no utilizado. Corrija el encargo y repita lo afectado;
el alcance nuevo vuelve a propuesta y plan. Un checkpoint de riesgo aceptado o falso
positivo no concede una dispensa. Si se propone excepción, lea
[excepciones](exceptions-continuity.md). Para fallos o rechazo, lea
[correcciones](corrections.md); registrar evidencia no acepta por sí mismo un resultado.
