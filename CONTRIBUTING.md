# Contribución a LKS-SDD

## Alcance

La versión `0.3.0` es la release técnica M0–M3 para revisión y piloto con Codex. Una contribución puede mejorar las seis skills, contratos documentales, perfil H0, validadores, migración, vistas cliente o evals dentro de ese alcance. No debe presentar capacidades de M4–M6, distribución o soporte corporativo como ya aprobadas.

## Contrato de cambio

1. Describir el problema y separar hechos, inferencias, propuesta y decisión requerida.
2. No editar `specs/canonical/` para acomodar una implementación.
3. Mantener los Markdown consumidores como fuente canónica y el índice como navegación operativa.
4. Preservar ediciones humanas, invocación implícita y límites de autorización.
5. Añadir o ajustar una prueba que observe el comportamiento relevante.
6. Ejecutar `docs/VALIDATION.md` y revisar el diff completo.
7. Documentar compatibilidad, migración o incompatibilidad cuando cambie un contrato.
8. Seguir `docs/RELEASING.md` cuando el cambio cierre una versión publicable.

## Revisión

Todo cambio necesita revisión humana antes de integrarse. Cambios de método, esquema, seguridad, privacidad, licencia, distribución o perfil tecnológico requieren además la decisión correspondiente indicada en `GOVERNANCE.md`. Un resultado de test no constituye esa aprobación.

No se deben incluir secretos, datos reales de clientes ni contenido sustantivo de proyectos consumidores. Los fixtures deben ser sintéticos.
