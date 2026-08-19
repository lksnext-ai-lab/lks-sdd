# Gobierno de LKS-SDD

## Estado de este incremento

La versión `0.5.0` es la release candidate técnica M0–M5 para Codex. Incluye el harness M4 y la infraestructura de distribución y piloto M5, pero el piloto real no ha comenzado: no existen en el repositorio participantes, proyectos, responsables, canal confidencial ni resultados. Su publicación en GitHub no implica instalación global, distribución corporativa estable, soporte oficial ni aprobación como política corporativa. La baseline normativa y el perfil H0 conservan estado `candidate`.

## Autoridad y decisiones

El plugin puede formular propuestas y registrar confirmaciones, pero no evalúa la autoridad de quien responde ni convierte una frase ambigua en aprobación. Las decisiones de producto, arquitectura, tecnología, riesgo, excepción, publicación y despliegue requieren confirmación explícita y, cuando proceda, aprobación por los órganos externos competentes.

La decisión de producto vigente define LKS-SDD como plugin de desarrollo SDD para Codex. No se declara soporte para GitHub Copilot, Claude u otros asistentes sin una decisión de ampliación, implementación específica y evidencia de validación.

## Evolución

Todo cambio del método debe documentar motivación, alcance, compatibilidad, impacto, decisión explícita, validaciones y migración o incompatibilidad. Las versiones del plugin, método, esquema y perfiles evolucionan por separado. Las migraciones nunca reescriben silenciosamente contenido adaptado por los equipos.

Las releases técnicas siguen `docs/RELEASING.md`: cada versión cerrada recibe una etiqueta inmutable y sus notas; los commits intermedios no reescriben una release publicada.

Un resultado `candidate` solo puede promocionarse con los canales exigidos por `quality/catalog.json`. `stable` queda bloqueado si falta evidencia semántica, documental o de piloto.

GitHub Issues es el canal candidate para soporte no sensible. La configuración externa debe aportar un canal confidencial de seguridad antes de iniciar el piloto. Los aliases no acreditan autoridad; las asignaciones reales y la decisión go/no-go siguen siendo externas.

## Responsabilidades pendientes

Antes del piloto deben designarse el propietario del método, mantenedores, responsables de perfiles, revisión de seguridad y privacidad, administración de publicación y canal de soporte. Mantener esos nombres como pendientes es deliberado; este incremento no los inventa.
