# Arquitectura y alcance de LKS-SDD 2.1.3

LKS-SDD es un plugin `skills-only` para Codex desktop y GitHub Copilot en VS Code
Agent. La versión 2.1.3 usa contrato consumidor 2.0 y método 2.0.0. Los Markdown
del proyecto consumidor son la fuente de verdad; `.lks-sdd/project.json` es un
índice operativo y no sustituye decisiones, tareas ni evidencia.

El enfoque es **Spec-anchored**: los acuerdos siguen gobernando el trabajo mientras
evoluciona el código. No es **Spec-as-source**; el código y una síntesis del agente
no deciden por sí solos la intención, aceptación o autorización humana.

## Núcleo y capacidades

El runtime agrupa:

| Área | Responsabilidad |
|---|---|
| `v2_contract`, `v2_schema` y `v2_storage` | Modelo documental, identidades, relaciones, snapshots, journal y recuperación. |
| `v2_authoring` y `v2_features` | Definiciones por funcionalidad, historia y navegación. |
| `v2_lifecycle`, `v2_controls` y `v2_verification` | Autoridad, diff real, continuidad, evidencia y cierre por alcance. |
| `v2_query` | Consulta de solo lectura sobre documentos, con código únicamente ante una carencia concreta o petición explícita. |
| `v2_migration` | Conversión explícita 1.5→2.0 con inventario, preview autorizado, recibo de conservación y rollback. |
| `v2_cli` | Entrada pública que enruta por schema y no interpreta una carpeta como permiso o host. |

Las seis skills comparten esta política: consultar, definir, adoptar, evaluar
readiness, implementar y verificar son operaciones diferentes. Una consulta no
escribe; readiness no autoriza código; una autorización acotada no permite
publicar, instalar ni hacer push.

## Distribución

`dual_distribution.py` genera adaptadores para ambos hosts desde el mismo núcleo.
El plugin Copilot contiene `core/` para ayuda sin proyecto y `setup/` para preparar
explícitamente un consumidor. El runtime fijado por un lock del consumidor prevalece
frente al plugin instalado; `runtime-doctor` comprueba esa integridad.

La distribución no instala dependencias personales, no añade MCP, hooks, apps ni
agentes ejecutables. ImageGen es una capacidad condicional de Codex; Copilot usa un
relevo visual explícito cuando es necesario. La generación de imágenes, las cuentas
de host y los servicios externos no forman parte del runtime.

## Compatibilidad y tecnología

Los lectores y writers 1.5 permanecen separados de 2.0 para permitir una migración
autorizada. El historial de un consumidor migrado se conserva como antecedente no
normativo; un `ART-TRACKING` o `SYNC-###` histórico no autoriza trabajo v2.

La tecnología se declara y confirma localmente en el proyecto. Las observaciones no conceden autorización y no existe catálogo, lock, receta ni certificación global.

## Límites de confianza

Los hashes detectan deriva, pero no son firmas de editor. Los roles declarados no
autentican personas. No hay locks distribuidos ni garantía de edición simultánea.
Las pruebas automatizadas no acreditan comprensión humana, piloto, navegación real
en host ni interoperabilidad externa: esos canales continúan `not-run` hasta contar
con evidencia observada.

Las guías operativas están en [V2-WORKFLOWS.md](V2-WORKFLOWS.md),
[V2-AUTHORING.md](V2-AUTHORING.md), [V2-MIGRATION.md](V2-MIGRATION.md),
[VALIDATION.md](VALIDATION.md) y [RELEASING.md](RELEASING.md).
