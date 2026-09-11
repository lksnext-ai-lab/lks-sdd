# Selección tecnológica

Comparar opciones después de comprender objetivo, alcance, restricciones y requisitos funcionales y no funcionales. Para cada propuesta registrar:

- adecuación a requisitos;
- compatibilidad;
- costes y restricciones;
- riesgos y medidas;
- impacto operativo;
- nivel de soporte LKS-SDD;
- alternativa razonable.

El catálogo 0.8 usa tres niveles. Una **familia** agrupa opciones y no se selecciona. Una **capacidad** reutiliza constraints, scaffold parcial y gates, pero tampoco se homologa de forma aislada. Un **perfil de referencia** es una composición cerrada, acotada y seleccionable por ADR para una `UNIT-###`; solo puede anunciar `supported` si descriptor, driver, scaffold, lock, gates de capacidad, gate de composición y evidencia de certificación coinciden por hash.

Los perfiles empaquetados cubren React/Vite estático, Angular estático, API FastAPI stateless, API FastAPI con OIDC/PostgreSQL, la web completa React/FastAPI/Keycloak/PostgreSQL y Next.js SSR. Angular SSR, sistema Angular/FastAPI, worker RabbitMQ y procesador Kafka se incluyen como candidatos hasta superar su certificación exacta. RabbitMQ y Kafka permanecen separados porque acknowledgements/reintentos/DLQ no son equivalentes a particiones/offsets/replay/lag.

Un sistema puede usar varios `BIND-###`, uno por unidad desplegable. Los gates de capacidad se componen, pero la unidad mínima de soporte sigue siendo el perfil exacto y su gate de integración; un lock aporta identidad y reproducibilidad, no demuestra compatibilidad por sí solo. Ningún perfil es una selección automática ni una homologación corporativa.

La decisión y suficiencia funcional pertenecen a `specification_readiness`; el plan, release y tareas a `delivery_readiness`; la certificación de cada binding a `automation_support`. `automation_coverage` solo explica por separado encaje de catálogo, preparación, implementación, verificación local, interoperabilidad externa y evidencia de entrega. Una alternativa confirmada puede quedar bien especificada y a la vez mostrar `automation_support: unsupported`, aunque algunas dimensiones de cobertura existan. Esa combinación bloquea la automatización, no autoriza cambiar de pila ni convierte la alternativa en una especificación deficiente.

Las capabilities son piezas reutilizables del catálogo, no perfiles seleccionables. En 0.12, `CAP-OIDC-DISCOVERY-JWKS`, `CAP-OIDC-API-BEARER`, `CAP-OIDC-SPA-PKCE` y `CAP-ENTRA-CLAIMS` permiten explicar cobertura sin abrir una combinatoria dinámica. `API-FASTAPI-ENTRA-PG-OCI` y `WEB-REACT-VITE-ENTRA-STATIC` son composiciones exactas candidate; frontend y backend mantienen bindings separados y Keycloak no es un sustituto de Entra.
