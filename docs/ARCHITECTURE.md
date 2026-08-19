# Arquitectura y alcance de la versión 0.5.0

## Entorno de ejecución

LKS-SDD se implementa como plugin de desarrollo SDD para Codex. Codex es el único entorno soportado contractualmente; la posible reutilización de Markdown, esquemas o scripts en ChatGPT Work, GitHub Copilot, Claude u otros asistentes no implica compatibilidad del plugin. La matriz y los criterios de portabilidad se mantienen en `docs/COMPATIBILITY.md`.

## Implementado en M0–M5

- Plugin único `lks-sdd`, basado exclusivamente en skills y recursos locales.
- Ayuda didáctica y contextual de solo lectura.
- Definición de aplicaciones nuevas mediante Markdown estructurado e inicialización aditiva.
- Evaluación explicable de preparación por incremento, sin autorización implícita.
- Esquemas para `.lks-sdd/project.json`, front matter, catálogos, perfil y lock.
- Núcleo de catorce artefactos y plantillas de anexos que solo se materializan cuando son aplicables.
- Perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, con versiones y contenedores fijados, scaffold de referencia, CI y gate reproducible.
- Preparación aditiva y autorizada del scaffold solo para un incremento listo y un perfil H0 validado.
- Verificación planificada y ejecutable que diferencia `passed`, `failed`, `not-run` y limitaciones.
- Adopción de repositorios existentes mediante inventario estático externo, reconciliación confirmada, detección de deriva y materialización exclusivamente documental.
- Validación integral, comprobación de trazabilidad y migración soportada `0.9` → `1.0` con preview, backup externo y rollback.
- Borradores para cliente derivados solo de fuentes `confirmed` y `client`/`public`, con bloqueo de indicadores sensibles y aprobación siempre pendiente.
- Validadores locales; solo el gate técnico explícito ejecuta herramientas externas y tráfico de descarga o health checks.
- Fixtures y evals de proyecto nuevo, información insuficiente, alternativa tecnológica, bloqueo independiente y ayuda.
- Harness M4 con catálogo FX-01–FX-19, corpus de activación etiquetado, integridad de fixtures, umbrales, reportes y comparación con baselines versionadas.
- Puertas diferenciadas para candidate y stable que conservan como `not-run` cualquier evidencia semántica, humana o de piloto aún no aportada.
- Bundle reproducible de plugin y marketplace de desarrollo, con manifiesto, checksums y exclusión de enlaces, cachés, generados y patrones de secretos.
- Piloto M5 con configuración externa, aliases, observaciones sin texto libre, almacén externo, agregación sin códigos y decisión go/no-go vinculada al harness M4.
- Soporte no sensible mediante Issues, canal de seguridad obligatorio en la configuración y rollback que no modifica automáticamente proyectos consumidores.

## Límite de capacidad

La implementación no inventa comportamiento de negocio: prepara la frontera técnica H0 y solo continúa cuando las decisiones y el incremento están confirmados. La adopción no modifica comportamiento ni convierte el estado observado en intención. La verificación no convierte una comprobación no ejecutada en superada y una vista cliente generada no equivale a aprobación.

## Evolución posterior

M6 cubre la ejecución completa del piloto, resolución de condiciones y publicación interna estable. MCP, conectores, hooks, apps, agentes y adaptaciones a otros asistentes solo se estudiarán si aparece una necesidad demostrada y mediante una decisión posterior.
