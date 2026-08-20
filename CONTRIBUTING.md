# Contribución a LKS-SDD

## Alcance

La versión `0.6.0` conserva M0–M5 y añade una evolución compatible de definición y UX como release candidate técnica para Codex. Una contribución puede mejorar las seis skills, contratos, perfil H0, harness, distribución candidate o infraestructura de piloto. M5 queda preparado pero no ejecutado; la numeración SemVer `0.6.0` no significa que M6, la publicación estable o el soporte corporativo estén completados o aprobados.

## Contrato de cambio

1. Describir el problema y separar hechos, inferencias, propuesta y decisión requerida.
2. No editar `specs/canonical/` para acomodar una implementación.
3. Mantener los Markdown consumidores como fuente canónica y el índice como navegación operativa.
4. Preservar ediciones humanas, invocación implícita y límites de autorización.
5. Añadir o ajustar una prueba que observe el comportamiento relevante.
6. Ejecutar `docs/VALIDATION.md` y revisar el diff completo.
7. Documentar compatibilidad, migración o incompatibilidad cuando cambie un contrato.
8. Seguir `docs/RELEASING.md` cuando el cambio cierre una versión publicable.
9. Actualizar el catálogo, el manifiesto de fixtures o la baseline de comparación cuando el cambio altere la evidencia M4 correspondiente.
10. Mantener cualquier configuración y evidencia real del piloto fuera del repositorio; solo se versionan contratos, ejemplos vacíos y resultados agregados expresamente saneados.
11. Cuando una evolución funcional amplíe el contrato, añadir una fuente versionada y su hash sin reescribir fuentes canónicas anteriores; cuando exista solo deriva, corregir implementación y evidencia.
12. Mantener los activos visuales del proyecto consumidor ligados a Markdown canónico, con estado y procedencia; no tratar una generación de ImageGen como aprobación humana ni como prueba de accesibilidad.

## Revisión

Todo cambio necesita revisión humana antes de integrarse. Cambios de método, esquema, seguridad, privacidad, licencia, distribución o perfil tecnológico requieren además la decisión correspondiente indicada en `GOVERNANCE.md`. Un resultado de test no constituye esa aprobación.

No se deben incluir secretos, datos reales de clientes ni contenido sustantivo de proyectos consumidores. Los fixtures deben ser sintéticos.
