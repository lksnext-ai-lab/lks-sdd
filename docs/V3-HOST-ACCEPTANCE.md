# Aceptación observada de uso v3

Estado inicial: **not-run**. La aceptación de publicación solicitada por el usuario
en [DEC-V3-002](plans/lks-sdd-v3/AUTHORIZATION.md) no es una transcripción de uso
con personas. TASK-V3-017 permanece abierta hasta obtener estas observaciones.

Se ha solicitado disponibilidad de un proyecto de prueba y un participante en
Copilot. No se presume esa disponibilidad ni se atribuye a fixtures la observación
de Sonar, Dependency-Check o identidad corporativa reales.

Antes de cada recorrido, registrar candidato y checksums, host/versión/modelo,
capacidades disponibles, configuración, alcance funcional, participante y funciones
consentidas, criterios y límite de tiempo administrativo acordado. Separar tiempos
de herramientas y espera humana. No inventar una referencia temporal anterior.

| Recorrido | Resultado que debe observar la persona |
|---|---|
| Individual breve | Entiende el cambio concreto. Dos decisiones previas: propuesta y plan/autorización. Ningún registro interno editado manualmente ni confirmación por comando. |
| Especialistas | Identifica responsables, interfaces, porciones, relevo recibido y tarea que puede continuar durante un análisis pendiente. Distingue cierre de componentes de integración. |
| Mantenimiento | Reanuda con autorización vigente, entiende el efecto localizado de un cambio de proceso y conserva decisiones independientes. |
| Migración | Revisa una conversión/configuración concreta, conserva la historia y el plan; identifica confirmaciones reutilizadas y permiso operativo pendiente. |
| Verificación | Entiende qué se ha probado, lo que falla o queda pendiente y quién debe actuar. Una omisión excepcional sigue visible. |
| Petición directa de implementación | Ante «implementa estos cambios», identifica y comunica cobertura documental vigente; si falta, registra y valida propuesta y plan antes de la primera edición de código. No requiere invocar el nombre del plugin. |
| Decisiones aplazadas | Ante «el resto ya lo decidiré», registra los pendientes, comprueba su impacto y continúa solo una porción independiente cubierta. Una decisión crítica pendiente impide editar el código afectado. |

En estos dos últimos casos observe el orden real de lecturas, registros, decisiones
y ediciones, además de la explicación al usuario. Incluya un caso con cobertura
válida para comprobar que se reutiliza sin pedir aprobaciones repetidas. Comprobar
el texto de una skill o superar la CLI no acredita esta selección conversacional.

Ejecutar las rutas disponibles en Codex y Copilot sobre copias autorizadas. Registrar
observaciones minimizadas, intervenciones, defectos y fuentes, sin diálogos simulados.
Una capacidad ausente queda declarada como tal; no se rebaja la política del proyecto.

Para eficiencia, comparar primero operaciones comunes de v2/v3 sobre el mismo
problema y después contexto v3 conservador/candidato sobre el mismo contrato.
La versión v2 de referencia está conservada por el tag v2.3.1; todavía no hay una
medición conversacional de referencia. Acordar métricas y variación antes de medir.
Contar instrucciones, lecturas, ampliaciones, herramientas, reintentos, correcciones
y verificación completa. Distinguir texto único, texto acumulado, latencia/I/O y
uso facturado cuando el host lo exponga. Caracteres/4 es una estimación identificada.

El selector candidato se consulta con comparison: true en una copia controlada.
Comparar cobertura literal, calidad del trabajo y coste completo antes de activarlo.
No retirar obligaciones para alcanzar un presupuesto. Si no mejora o pierde una
obligación, mantener la ruta conservadora y corregir solo la causa observada.

El informe final separará verificación técnica, comprensión funcional,
agilidad/eficiencia y migración/continuidad. Una casilla vacía o not-run nunca
significa aprobado. Este protocolo no crea telemetría ni campañas recurrentes.
