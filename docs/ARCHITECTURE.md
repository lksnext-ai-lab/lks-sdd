# Arquitectura y alcance de la versión 0.6.0

## Entorno de ejecución

LKS-SDD se implementa como plugin de desarrollo SDD para Codex. Codex es el único entorno soportado contractualmente; la posible reutilización de Markdown, esquemas o scripts en ChatGPT Work, GitHub Copilot, Claude u otros asistentes no implica compatibilidad del plugin. La matriz y los criterios de portabilidad se mantienen en `docs/COMPATIBILITY.md`.

## Implementado en M0–M5 y evolución compatible v0.6

- Plugin único `lks-sdd`, basado exclusivamente en skills y recursos locales.
- Ayuda didáctica y contextual de solo lectura.
- Definición de aplicaciones nuevas mediante Markdown estructurado, inicialización aditiva y encuadre inicial que evita convertir ideas ambiguas en productos genéricos.
- Snapshots compactos de cobertura tras bloques relevantes, con estados comprensibles y sin porcentaje global de madurez.
- Para frontends aplicables, especificación condicional de detalle y estados por pantalla, flujos enlazados, interacción, dirección visual y activos trazables.
- Ciclo visual obligatorio cuando existe frontend nuevo o cambio visual material: brief suficiente, una a tres propuestas ImageGen si la capacidad está disponible, validación humana y fallback explícito; una baseline ya confirmada puede reutilizarse con motivo documentado.
- Evaluación explicable de preparación por incremento, sin autorización implícita.
- Esquemas para `.lks-sdd/project.json`, front matter, catálogos, perfil y lock.
- Núcleo de catorce artefactos y plantillas de anexos que solo se materializan cuando son aplicables.
- Perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, con versiones y contenedores fijados, scaffold de referencia, CI y gate reproducible.
- Preparación aditiva y autorizada del scaffold solo para un incremento listo y un perfil H0 validado.
- Verificación planificada y ejecutable que diferencia `passed`, `failed`, `not-run` y limitaciones; la evidencia visual 1.1 se liga a implementación, UX/VIS, viewports y capturas por hash.
- Adopción de repositorios existentes mediante inventario estático externo, reconciliación confirmada, detección de deriva y materialización exclusivamente documental.
- Validación integral, comprobación de trazabilidad y migración soportada `0.9` → `1.0` con preview, backup externo y rollback.
- Borradores para cliente derivados solo de fuentes `confirmed` y `client`/`public`, con bloqueo de indicadores sensibles y aprobación siempre pendiente.
- Validadores locales; solo el gate técnico explícito ejecuta herramientas externas y tráfico de descarga o health checks.
- Fixtures y evals de proyecto nuevo, información insuficiente, alternativa tecnológica, bloqueo independiente y ayuda.
- Harness M4 con catálogo base FX-01–FX-19, extensión v0.6 FX-20–FX-21, corpus de activación y conversación etiquetados, integridad de fixtures, umbrales, reportes y comparación con baselines versionadas. Los nuevos escenarios semánticos y humanos permanecen `not-run` hasta una ejecución controlada.
- Puertas diferenciadas para candidate y stable que conservan como `not-run` cualquier evidencia semántica, humana o de piloto aún no aportada.
- Bundle reproducible de plugin y marketplace de desarrollo, con manifiesto, checksums y exclusión de enlaces, cachés, generados y patrones de secretos.
- Piloto M5 con configuración externa, aliases, observaciones sin texto libre, almacén externo, agregación sin códigos y decisión go/no-go vinculada al harness M4.
- Soporte no sensible mediante Issues, canal de seguridad obligatorio en la configuración y rollback que no modifica automáticamente proyectos consumidores.

## Límite de capacidad

La implementación no inventa comportamiento de negocio: prepara la frontera técnica H0 y solo continúa cuando las decisiones y el incremento están confirmados. Una propuesta visual generada no sustituye requisitos, responsive, accesibilidad ni aprobación humana. La adopción no modifica comportamiento ni convierte el estado observado en intención. La verificación no convierte una comprobación no ejecutada en superada y una vista cliente generada no equivale a aprobación.

## Evolución posterior

La versión SemVer `0.6.0` no equivale al hito M6. M6 continúa cubriendo la ejecución completa del piloto, resolución de condiciones y publicación interna estable. MCP, conectores, hooks, apps, agentes y adaptaciones a otros asistentes solo se estudiarán si aparece una necesidad demostrada y mediante una decisión posterior.
