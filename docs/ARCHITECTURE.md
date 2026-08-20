# Arquitectura y alcance de la versión 0.7.0

## Entorno de ejecución

LKS-SDD se implementa como plugin de desarrollo SDD para Codex. Codex es el único entorno soportado contractualmente; la posible reutilización de Markdown, esquemas o scripts en ChatGPT Work, GitHub Copilot, Claude u otros asistentes no implica compatibilidad del plugin. La matriz y los criterios de portabilidad se mantienen en `docs/COMPATIBILITY.md`.

## Implementado en M0–M5 y evoluciones compatibles v0.6–v0.7

- Plugin único `lks-sdd`, basado exclusivamente en skills y recursos locales.
- Ayuda didáctica y contextual de solo lectura.
- Definición de aplicaciones nuevas mediante Markdown estructurado, inicialización aditiva y encuadre inicial que evita convertir ideas ambiguas en productos genéricos.
- Snapshots compactos de cobertura tras bloques relevantes, con estados comprensibles y sin porcentaje global de madurez.
- Para frontends aplicables, especificación condicional de detalle y estados por pantalla, flujos enlazados, interacción, dirección visual y activos trazables.
- Ciclo visual obligatorio cuando existe frontend nuevo o cambio visual material: brief suficiente, una a tres propuestas ImageGen si la capacidad está disponible, validación humana y fallback explícito; una baseline ya confirmada puede reutilizarse con motivo documentado.
- Evaluación explicable por incremento que separa `specification_readiness` de `automation_support`, sin seleccionar una pila ni conceder autorización implícita. El estado combinado de implementación permanece bloqueado si falta cualquiera de las dos condiciones.
- Contrato documental 1.1 para proyectos nuevos (`method_version: 1.1.0`, `schema_version: 1.1`) y validación compatible de proyectos 1.0, sin actualización automática.
- Catálogo declarativo por artefacto y tabla para cabeceras, propietario de identificadores, estados, relaciones, cardinalidad, aplicabilidad y assets. La naturaleza del elemento procede del artefacto o prefijo y el estado expresa su ciclo de vida.
- Parser común de referencias individuales, listas y rangos inclusivos `FR-001..FR-079`. El rango `a` y las listas separadas solo por espacios se aceptan con aviso exclusivamente en compatibilidad 1.0; una expansión parcial o un ID inexistente no se silencian.
- Matriz de dominios separada para datos, identidad, seguridad, privacidad e integraciones, con aplicabilidad y referencias explícitas por incremento.
- Diagnósticos estructurados con código, severidad, fase, localización, observado, esperado y corrección mínima, además de una vista textual compatible para consumidores anteriores.
- Esquemas para `.lks-sdd/project.json`, front matter, catálogos, perfil y lock.
- Núcleo de catorce artefactos y plantillas de anexos que solo se materializan cuando son aplicables.
- Perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, con versiones y contenedores fijados, scaffold de referencia, CI y gate reproducible.
- Preparación aditiva y autorizada del scaffold solo para un incremento listo y un perfil H0 validado.
- Handoff por fases: `preimplementation` exige trazabilidad desde requisitos aplicables hasta pruebas planificadas, mientras `verification` exige además evidencia ejecutada y correspondiente al incremento. Un alcance vacío nunca supera la comprobación.
- Grafo activo por incremento que excluye de los inputs operativos filas rechazadas, sustituidas o retiradas, aunque las conserva en el modelo documental para auditoría. La huella documental completa y la huella del contrato activo tienen propósitos distintos.
- Verificación planificada y ejecutable que diferencia `passed`, `failed`, `blocked`, `not-run` y `not-applicable`; la evidencia visual 1.1 se liga a implementación, UX/VIS, viewports y capturas por hash.
- Adopción de repositorios existentes mediante inventario estático externo, reconciliación confirmada, detección de deriva y materialización exclusivamente documental.
- Validación integral y migraciones explícitas, reversibles y de un solo salto: se conserva `0.9` → `1.0` al solicitar ese destino y se añade `1.0` → `1.1`. Esta última falla siempre antes de crear backup o escribir si el preview contiene entradas en `human_review_required`; cada entrada se resuelve en los Markdown 1.0 y se repite el preview antes de aplicar con backup, autorización, hash y rollback. Como `Identity` 1.0 agregaba tres dominios que el origen no puede separar, se materializan identidad, seguridad y privacidad como `pending` con motivo y sin referencias inferidas; no entran en esa lista, validan tras la migración y bloquean readiness hasta resolverse en 1.1.
- Borradores para cliente derivados solo de fuentes `confirmed` y `client`/`public`, con bloqueo de indicadores sensibles y aprobación siempre pendiente.
- Validadores locales; solo el gate técnico explícito ejecuta herramientas externas y tráfico de descarga o health checks.
- Fixtures y evals de proyecto nuevo, información insuficiente, alternativa tecnológica, bloqueo independiente y ayuda.
- Harness M4 con catálogo base FX-01–FX-19, extensión v0.6 FX-20–FX-21, corpus de activación y conversación etiquetados, integridad de fixtures, umbrales, reportes y comparación con baselines versionadas. Los nuevos escenarios semánticos y humanos permanecen `not-run` hasta una ejecución controlada.
- Puertas diferenciadas para candidate y stable que conservan como `not-run` cualquier evidencia semántica, humana o de piloto aún no aportada.
- Dispatcher portable `scripts/lks_sdd.py` que resuelve recursos desde la instalación del plugin y recibe por separado la raíz del proyecto consumidor.
- Bundle reproducible de plugin y marketplace de desarrollo construido desde un commit Git real igual a `HEAD`, con árbol limpio, manifiesto, checksums y exclusión de enlaces, cachés, generados y patrones de secretos.
- Piloto M5 con configuración externa, aliases, observaciones sin texto libre, almacén externo, agregación sin códigos y decisión go/no-go vinculada al harness M4.
- Soporte no sensible mediante Issues, canal de seguridad obligatorio en la configuración y rollback que no modifica automáticamente proyectos consumidores.

## Límite de capacidad

La implementación no inventa comportamiento de negocio: prepara la frontera técnica H0 y solo continúa cuando las decisiones y el incremento están confirmados. Una especificación puede estar preparada sin disponer de soporte automatizado para su perfil; eso no es permiso para seleccionar H0 ni para implementar manualmente sin una decisión aparte. Una propuesta visual generada no sustituye requisitos, responsive, accesibilidad ni aprobación humana. La adopción no modifica comportamiento ni convierte el estado observado en intención. La verificación no convierte una comprobación no ejecutada en superada y una vista cliente generada no equivale a aprobación.

## Evolución posterior

La versión SemVer `0.7.0` no equivale al hito M6. M6 continúa cubriendo la ejecución completa del piloto, resolución de condiciones y publicación interna estable. Los canales semánticos, humanos, de activación, revisión documental o piloto sin observaciones reales permanecen `not-run`; candidate puede declararlos opcionales, pero `stable` no. MCP, conectores, hooks, apps, agentes y adaptaciones a otros asistentes solo se estudiarán si aparece una necesidad demostrada y mediante una decisión posterior.
