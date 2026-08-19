# Contribución a LKS-SDD

## Alcance

La versión `0.1.0` es un incremento local M0–M1 para revisión. Una contribución puede mejorar ayuda, definición, readiness, contratos documentales, validadores o evals dentro de ese alcance. No debe aparentar que una capacidad de M2 o M3 ya está implementada.

## Contrato de cambio

1. Describir el problema y separar hechos, inferencias, propuesta y decisión requerida.
2. No editar `specs/canonical/` para acomodar una implementación.
3. Mantener los Markdown consumidores como fuente canónica y el índice como navegación operativa.
4. Preservar ediciones humanas, invocación implícita y límites de autorización.
5. Añadir o ajustar una prueba que observe el comportamiento relevante.
6. Ejecutar `docs/VALIDATION.md` y revisar el diff completo.
7. Documentar compatibilidad, migración o incompatibilidad cuando cambie un contrato.

## Revisión

Todo cambio necesita revisión humana antes de integrarse. Cambios de método, esquema, seguridad, privacidad, licencia, distribución o perfil tecnológico requieren además la decisión correspondiente indicada en `GOVERNANCE.md`. Un resultado de test no constituye esa aprobación.

No se deben incluir secretos, datos reales de clientes ni contenido sustantivo de proyectos consumidores. Los fixtures deben ser sintéticos.
