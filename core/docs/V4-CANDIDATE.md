# Desarrollo y promoción de 4.0

Este árbol incorpora las seis líneas de mejora: presentación y transporte,
operaciones compuestas, contexto por alcance, instrucciones por operación,
recorridos de mantenimiento y cálculo medido. La sexta conserva la reutilización
acotada existente; V4-13 descarta incorporar otra variante sin validación suficiente.

Las candidatas técnicas se construyeron como `development-unreleased`, con versión
base 3.4.3 e identidad por fuente y `runtime_digest`. Se conservan como evidencia;
no son los assets estables. El responsable valida el desarrollo y autoriza su cierre,
la release **4.0.0** y su distribución en Codex el 2026-10-18. La aprobación no
sustituye el gate estable ni la comprobación de los paquetes del commit integrado.
Véase [actualización, resultados y reservas](UPGRADE-4.0.0.md).

## Uso y compatibilidad

Las seis skills mantienen sus nombres e invocación implícita. El núcleo de ambos
adaptadores es idéntico; una extracción y ejecución técnica no acreditan selección
ni aceptación conversacional de Codex o Copilot.

El método actual sigue siendo 3.1.0 y el formato de proyecto 3.1. Los lectores
declarados para 1.5/2.0/3.0 se conservan: no significa que todos esos orígenes hayan
ejecutado una actualización a esta candidata. La ruta focal de V4-14 es un consumidor
sintético fijado en 3.4.3, formato 3.1, hacia la candidata y su recuperación.

- [Presentación y transporte](CLI-PRESENTATION.md): salida compatible por defecto;
  vista operativa explícita y acceso al detalle íntegro.
- [Preparación](WORK-PREPARE.md): `work-prepare` consulta y no autoriza ni escribe.
- [Operaciones](WORK-OPERATIONS.md): continuar y registrar resultados, conservando
  actor, alcance, bases frescas, evidencia y efectos parciales; no ejecutan código
  proporcionado dentro del JSON.
- [Actividad](WORK-ACTIVITY.md): canal optativo separado de stdout; interrupción
  cooperativa, sin promesa de aborto inmediato ni cancelación de negocio.
- [Captura](DIAGNOSTIC-CAPTURE.md): conservación externa, capacidad y recuperación;
  su contenido no concede autoridad sobre el consumidor.
- [Contexto](DOCUMENT-CONTEXT.md): conserva obligaciones literales, prosa incierta,
  fuentes globales/entrantes y adjuntos aplicables.

## Actualización explícita y recuperación

Construir o cargar un plugin no actualiza el runtime fijado de un proyecto. Antes
de actuar, comprobar el lock, `runtime-doctor` y `migration-diagnose`. La actualización
de formato/método o runtime requiere `migration-preview` con actor, configuración,
declaración y `runtime_bundle` compatibles. Revisar la decisión completa, obtener
su recibo y aplicar únicamente el hash exacto del preview; no reutilizar una decisión
para otro contenido. Conservar el paquete anterior y la evidencia del corte.

Una actualización no renueva aprobaciones, permisos, evidencia ni revisión de las
tareas existentes. El trabajo abierto mantiene sus guardas y puede requerir una
decisión nueva si cambió su base. Ante interrupción, inspeccionar journal, efectos y
hash; usar `recover` o `rollback` explícitos antes de otro intento. Un rollback debe
rechazarse si sobrescribe trabajo posterior o el runtime no soporta el contrato.
No borrar manualmente el journal ni reemplazar archivos para forzar el cambio.

Con objetos ZIP, las herramientas actuales rechazan fijar un lector anterior que
no los admita. El pin y los datos deben ser compatibles: restaurar un respaldo
completo comprobado, conservando el trabajo posterior. V4-22 compacta originales
sueltos y restaura sus bytes en un destino independiente; no cambia automáticamente
el lector ni retira ZIP para volver a una versión anterior. Antes del primer ZIP,
la actualización conserva respaldos
sueltos que permiten volver al lector anterior. V4-14 ampliada prueba ambas
fronteras y la restauración de un respaldo en consumidores sintéticos;
[resultado y límites](plans/lks-sdd-v4/RESULTS-V4-19-20.md#v4-14-ampliada--compatibilidad-y-recuperación).

Los helpers de rutas largas y las restricciones de enlaces/contención se incluyen
en ambos paquetes. La evidencia de rutas largas del plugin se distingue de la
incidencia nativa del aislamiento de Windows: esta última y H2 siguen pendientes.

## Límites de aceptación

La comparación histórica S8 no alcanzó la reducción temporal del 20 %; el usuario
aceptó ese compromiso de producto y el criterio conserva su resultado no alcanzado.
AC-40 sigue inconcluso. La integración del escritor agrupado comprueba comportamiento,
sin convertir esa ejecución en otra comparación de rendimiento. Ningún ahorro integral
de tokens facturados se deduce de las mejoras estáticas. H2, observación real de hosts
y percepción humana prolongada siguen pendientes. La aceptación del responsable
permite publicar con estas reservas; no convierte esas observaciones en superadas.
AC-52 conserva los costes comparativos medidos sobre el componente histórico;
el coste comparativo del runtime final no se ha vuelto a medir. La puerta estable
requiere fuente integrada limpia y la aprobación de 4.0.0 conforme a
[VALIDATION.md](VALIDATION.md).
