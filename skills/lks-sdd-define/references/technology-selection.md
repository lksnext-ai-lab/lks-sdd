# Selección tecnológica

Comparar opciones después de comprender objetivo, alcance, restricciones y requisitos funcionales y no funcionales. Para cada propuesta registrar:

- adecuación a requisitos;
- compatibilidad;
- costes y restricciones;
- riesgos y medidas;
- impacto operativo;
- nivel de soporte LKS-SDD;
- alternativa razonable.

FastAPI, React, PostgreSQL y Keycloak forman el perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, con scaffold y lock técnico validados. Sigue siendo un perfil candidato, no una selección automática ni una homologación corporativa. Presentarlo como propuesta cuando encaje, conservar al menos una alternativa y esperar una decisión explícita. Una tecnología distinta puede documentarse, pero no se debe prometer implementación o verificación automatizada H0 para ella.

La decisión y suficiencia funcional pertenecen a `specification_readiness`; la disponibilidad del registro, scaffold, lock y gates pertenece a `automation_support`. Una alternativa confirmada puede quedar bien especificada y a la vez mostrar `automation_support: unsupported`. Esa combinación bloquea la automatización del plugin, no autoriza a cambiar de pila ni convierte la alternativa en una especificación deficiente.
