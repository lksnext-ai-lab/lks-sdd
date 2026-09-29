# TASK-V3-008 · Sonar y Dependency-Check: evidencia y viabilidad

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de calidad**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-002](TASK-V3-002.md).
Dependencias para cerrar: [TASK-V3-005](TASK-V3-005.md).

Requisitos de responsabilidad principal: REQ-EQT-021, REQ-EQT-023, REQ-EQT-024, REQ-EQT-025, REQ-EQT-038, REQ-EQT-064.
Casos de aceptación principales: AC-EQT-022, AC-EQT-023, AC-EQT-024, AC-EQT-026, AC-EQT-028, AC-EQT-038, AC-EQT-081, AC-EQT-082, AC-EQT-083, AC-EQT-084, AC-EQT-097.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Ejecución y obtención de resultados
Concretar dos rutas soportadas antes de cerrar la tarea: solicitar un análisis con el
medio existente/autorizado y recoger su resultado, o importar un resultado ya producido
con procedencia comprobable. Se fija un contrato de invocación/recogida/resultado con
configuración aprobada; el núcleo no crea una integración de CI/CD ni descubre ejecutores
por texto del repositorio. Un lector de informes, por sí solo, no completa el ciclo.

Documentar los formatos/versiones admitidos y los campos necesarios para vincular
snapshot real → ejecución → resultado terminal. El gate “más reciente” del proyecto
sin correspondencia a esa ejecución no sirve. Probar corrección sin commit, informe
concurrente y actualización de datos de dependencias; mantener pendientes no observados.

Comprobar pronto la disponibilidad del medio real con 017. Las pruebas de componente
usan resultados controlados; R2 obtiene/corrige/repite mediante un medio real cuando
esté disponible y autorizado. Si no lo está, el recorrido real queda pendiente, sin
bloquear parsers o confundir la simulación con su aceptación.

## Encargo y límites
Consumir y normalizar resultados de Sonar y OWASP Dependency-Check mediante medios ya
disponibles/autorizados. Separar decisión de uso, aplicabilidad, obligatoriedad, ejecución
y resultado; comprobar viabilidad antes de comprometer un flujo que exija análisis.
No instalar herramientas, diseñar pipelines ni crear conectores/agentes.

## Entregables e interfaces
- Añadir `scripts/v3_quality.py` y lectores de los formatos de resultado concretos
  soportados, con fixtures de procedencia documentada. Configuración de ejecutor
  explícita, nunca ejecutar campos arbitrarios de documentos/informes.
- Sonar: análisis identificado y resultado terminal del Quality Gate aplicable.
  Dependency-Check: dependencias, versión/configuración, actualización de datos,
  umbrales y supresiones; no equiparar un análisis aislado de archivo a un gate completo.
- Comprobar acceso/ámbito/sujeto/resultados, timeout y reintentos configurados sin lanzar
  un análisis completo solo para configurar. Declarar limitación si depende de un PR ausente.
- Agrupar por entradas, base, configuración, herramienta, ámbito y vigencia externa.
  Reutilizar un análisis en varias tareas solo con cobertura demostrable.
- Espera/cancelación/reintento retomables por ID; informes amplios procesados localmente,
  totales y paginación explícitos con fallos críticos visibles. Conservar evidencia en 002.

## Aceptación y evidencia
No uso decidido permite avanzar sin declarar pasado; outage/error/acceso ausente siguen
siendo estados distintos. Mismos inputs cubiertos no generan ejecuciones nuevas al
consultar o reanudar. Cambios de código, reglas, supresiones, dependencias o datos externos
revisan vigencia. Un informe de otra rama/sujeto no autoriza cierre. Espera con límite
agotado no equivale a éxito. Lectura paginada mantiene pendientes no mostrados.
Entregar fixtures terminales/pendientes/fallidos/desactualizados y tests del contrato.
Prueba contra medio real, si está disponible y autorizada, con evidencia separada en 017.

## Riesgos y revisión
Versiones/ediciones de las herramientas pueden variar: documentar formatos probados y
rechazar resultados desconocidos; no certificarlos por el nombre del producto.
Revisión de calidad y ejecución. Lectura adicional: funcional §7 y técnica §7 completo.
