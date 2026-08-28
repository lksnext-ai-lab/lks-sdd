# Gobierno de LKS-SDD

## Estado de este incremento

La versión `0.15.0` es una release candidate técnica para Codex que conserva M0–M5 y el contrato 1.5. Añade dos perfiles OIDC simulados exactos, active y certificados exclusivamente para entornos no productivos. Los perfiles Microsoft Entra permanecen `candidate`, `unsupported` y con interoperabilidad real `not-run`; la identidad simulada no los sustituye ni satisface producción. El piloto real no ha comenzado: no existen en el repositorio participantes, proyectos, responsables, canal confidencial ni resultados. La versión SemVer no completa M6. Una publicación técnica en GitHub no implica distribución corporativa estable, soporte oficial ni aprobación como política corporativa. La baseline normativa y las extensiones de `specs/proposed/` conservan su estado no canónico.

## Autoridad y decisiones

El plugin puede formular propuestas y registrar confirmaciones, pero no evalúa la autoridad de quien responde ni convierte una frase ambigua en aprobación. Las decisiones de producto, arquitectura, tecnología, riesgo, excepción, publicación y despliegue requieren confirmación explícita y, cuando proceda, aprobación por los órganos externos competentes.

La decisión de producto vigente define LKS-SDD como plugin de desarrollo SDD para Codex. No se declara soporte para GitHub Copilot, Claude u otros asistentes sin una decisión de ampliación, implementación específica y evidencia de validación.

La extensión visual permite usar ImageGen de forma condicional cuando esa capacidad esté disponible en la superficie autorizada. La herramienta propone activos; la confirmación de la línea visual y de su alcance continúa siendo humana. ChatGPT Work puede apoyar análisis o revisión de documentos transferidos, pero no se convierte por ello en runtime soportado del plugin.

## Evolución

Todo cambio del método debe documentar motivación, alcance, compatibilidad, impacto, decisión explícita, validaciones y migración o incompatibilidad. Una extensión se incorpora como fuente aditiva versionada y preserva las fuentes anteriores; una diferencia de implementación se corrige sin reescribir el contrato. Las versiones del plugin, método, esquema, perfiles y hitos evolucionan por separado. Las migraciones nunca reescriben silenciosamente contenido adaptado por los equipos.

Los proyectos de esta release usan método 1.5.0 y esquema 1.5 como único contrato operativo. Los proyectos 1.0–1.4 se rechazan sin escritura y 0.15 no distribuye migradores. Actualizar el plugin no reescribe `plugin_version`, Markdown ni evidencias; cualquier evolución futura de contrato debe decidir explícitamente compatibilidad o incompatibilidad antes de implementarse.

La autoridad para considerar suficiente una especificación se separa de la capacidad técnica del plugin para automatizar una pila. `specification_readiness` puede ser favorable mientras `automation_support` bloquea la implementación; ninguna de las dos selecciona tecnología ni autoriza escribir código. `automation_coverage` solo explica qué partes están preparadas o pendientes: no crea soporte parcial, no compone capabilities y no permite sustituir Entra por Keycloak.

Las releases técnicas siguen `docs/RELEASING.md`: cada versión cerrada recibe una etiqueta inmutable y sus notas; los commits intermedios no reescriben una release publicada.

Un resultado `candidate` solo acredita los canales que `quality/catalog.json` exige para candidate. Los canales opcionales pueden permanecer `not-run`, pero deben seguir visibles y nunca se cuentan como superados. `stable` exige además definición conversacional, activación, revisión documental y piloto; cualquier canal requerido `not-run`, `skipped`, incompleto o fallido bloquea la promoción.

GitHub Issues es el canal candidate para soporte no sensible. La configuración externa debe aportar un canal confidencial de seguridad antes de iniciar el piloto. Los aliases no acreditan autoridad; las asignaciones reales y la decisión go/no-go siguen siendo externas.

## Responsabilidades pendientes

Antes del piloto deben designarse el propietario del método, mantenedores, responsables de perfiles, revisión de seguridad y privacidad, administración de publicación y canal de soporte. Mantener esos nombres como pendientes es deliberado; este incremento no los inventa.
