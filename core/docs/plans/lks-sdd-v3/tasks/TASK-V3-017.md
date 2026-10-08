# TASK-V3-017 · Aceptación de uso, migración y eficiencia

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Revisión funcional y técnica con usuarios**; persona/agente por asignar.
Inicio del trabajo independiente: autorización del plan; sin tarea previa.
Dependencias para cerrar: [TASK-V3-016](TASK-V3-016.md).

Requisitos de responsabilidad principal: REQ-EQT-049, REQ-EQT-059, REQ-EQT-069.
Casos de aceptación principales: AC-EQT-068, AC-EQT-069, AC-EQT-070, AC-EQT-071, AC-EQT-098, AC-EQT-099.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Preparación temprana y comparación válida
Iniciar protocolo, escenarios, muestras y disponibilidad antes de modificar las rutas
que se compararán. Guardar referencia de v2 por commit/runtime, configuración y datos;
observarla en un entorno autorizado. No reconstruir después sus resultados de memoria.

Separar dos comparaciones: v2/v3 para operaciones comunes, y v3 suficiente/v3 seleccionada
para obligaciones nuevas. En la primera conservar el mismo problema funcional y declarar
diferencias de formato; en la segunda mantener exactamente el mismo contrato v3.
No atribuir ahorro a retirar requisitos o comparar una función nueva con su ausencia.

Acordar antes de medir tokenizador/métricas disponibles, límites temporales y tratamiento
de variación entre ejecuciones; mantener condiciones observables comparables. No aceptar
una mejora general por un único ejemplo favorable ni exigir un número universal de runs.
Repetir solo cuando variación o resultados inconclusos lo justifiquen.

Observar las fichas de validación temprano y reservar la aceptación final para el candidato
verificado. La ruta seleccionada puede probarse en copias controladas después del contraste
de cobertura, sin activarla por defecto. Un medio/host no disponible se comunica al
prepararlo, no se descubre como único bloqueo al final. No crear telemetría o pruebas
humanas recurrentes para futuras releases.

## Encargo y límites
Comprobar con personas la agilidad, comprensión, migración y eficiencia de la tarea
completa en Codex y Copilot. Esta tarea decide la aceptación observada de v3; no la
sustituyen validadores ni demostraciones con diálogos inventados.

## Preparación antes de medir
- Acordar participantes/funciones, hosts, escenarios y límites de tiempo administrativo;
  separar tiempo de herramientas externas y espera humana. Datos reales solo donde
  estén autorizados, sin copiar identidades a fixtures compartidos.
- Fijar mismos alcances, fuentes, decisiones y criterios para base actual y candidata.
  Registrar versión/modelo/configuración observables y limitaciones para comparar.
- Preparar candidato local 015 y evidencia 016; observación real requiere entorno de
  pruebas autorizado. Instalación activa necesita permiso específico; no se presume.
- Elegir un medio real de análisis ya disponible/autorizado para los formatos soportados.
  Si falta, marcar esa observación pendiente, sin presentar fixtures como servicio probado.

## Recorridos y medidas
1. Cambio pequeño configurado: dos decisiones antes de ejecutar, aceptación final solo
   si se exige, cero edición manual y ninguna confirmación redundante.
2. Especialistas: responsables entienden propuesta/contratos, aceptación por porción,
   relevo recibido, tarea compatible durante Sonar pendiente y verificación conjunta.
3. Mantenimiento/reanudación: cero nuevas aprobaciones sin cambio; política o contrato
   nuevo afectan solo su ámbito. Estado y siguiente acción comprensibles.
4. Migración individual y equipo: una decisión agrupada cuando procede, historia cerrada
   conservada, plan activo reutilizado, autorización operativa localizada y mapa común.
5. Contexto: medir instrucciones, lecturas, ampliaciones, herramientas, reintentos,
   correcciones y verificación; separar texto único, volumen acumulado y uso facturado
   observable. Registrar latencia/I/O y revisar el código producido.

## Aceptación y evidencia
Registrar observaciones/transcripciones minimizadas, tiempos, intervenciones y defectos
con su revisión de candidato, host y escenario. Cada exceso debe tener causa concreta;
no basta etiquetarlo “por precaución”. Si falta observación o límites previos, la agilidad
queda pendiente. Si el resumen oculta un cambio material, comprensión no está aceptada.
Si solo baja el primer prompt o crecen omisiones, errores o consumo total, eficiencia
no está aceptada. Sin datos de host no afirmar ahorro facturado o persistencia de memoria.

El selector permanece en comparación hasta que cobertura, calidad y medición justifiquen
su activación. Tras activarlo, reconstruir el candidato local afectado y repetir la
verificación focal sobre sus bytes finales; no reutilizar hashes del candidato anterior.
Una limitación devuelve corrección a su tarea propietaria y después se repite solo el
escenario afectado, sin rebajar el requisito aprobado.

## Cierre y revisión
Entregar informe con cuatro resultados separados: verificación técnica, aceptación
funcional, agilidad/eficiencia y migración/continuidad. Identificar pendientes por host,
origen o herramienta. Esta evidencia prepara una decisión posterior de publicación,
pero no la autoriza. Revisión por responsables funcional/técnico y personas de uso.
Lectura adicional: funcional §§5.10–5.11, 11.1 y 13; técnica §§6 y 9.5.
