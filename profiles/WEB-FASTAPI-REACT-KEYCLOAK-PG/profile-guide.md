# Perfil WEB-FASTAPI-REACT-KEYCLOAK-PG

Este perfil candidato proporciona la primera combinación H0 de LKS-SDD para Codex: SPA React, API FastAPI, PostgreSQL, identidad Keycloak mediante OpenID Connect y entrega con contenedores OCI.

## Condiciones de uso

- Codex solo puede proponerlo después de evaluar requisitos y restricciones.
- Su selección requiere una decisión ADR confirmada en los Markdown del proyecto.
- El lock exacto se copia al proyecto y no se actualiza silenciosamente.
- El scaffold es un punto de partida, no una aplicación terminada ni una arquitectura obligatoria para todos los proyectos.
- Los secretos se suministran mediante el entorno; `.env.example` contiene únicamente nombres y marcadores.
- La implementación se limita al incremento confirmado y conserva la trazabilidad requisito–aceptación–decisión–incremento–prueba–evidencia.

## Puerta técnica

`scripts/run_reference_profile_gate.py` copia el scaffold a una carpeta temporal y comprueba locks, lint, tipado, tests, build, OpenAPI y configuración de Compose. La integración con PostgreSQL y Keycloak se activa mediante `--containers`; no se considera superada si una comprobación requerida no se ejecuta.

El estado `candidate` se mantiene hasta que el perfil supere la puerta técnica y la revisión humana. H0 expresa la capacidad implementada y probada del perfil, no una aprobación corporativa formal.
