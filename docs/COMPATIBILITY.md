# Compatibilidad de LKS-SDD 0.17.0

## Contrato de proyecto soportado

LKS-SDD 0.17.0 opera exclusivamente sobre proyectos con:

- `schema_version: "1.5"`;
- `method_version: "1.5.0"`.

No se distribuyen schemas de proyecto 1.0–1.4 ni el comando `migrate`. Un proyecto con otro contrato se rechaza de forma legible y sin modificar ningún archivo. Este corte es deliberado: durante el desarrollo previo a 1.0 existe una sola aplicación consumidora y ya usa schema 1.5/método 1.5.0.

`plugin_version` en `.lks-sdd/project.json` no expresa el runtime activo. Es la procedencia de la materialización del proyecto y puede conservar, por ejemplo, `0.12.0` mientras el runtime es 0.15.0. `status --view audit` y `doctor --quick` muestran ambos valores por separado; actualizar el plugin no reescribe esa procedencia.

Las vistas `help`, `status` y `doctor` son de solo lectura respecto al contrato canónico. La caché derivada vive, cuando se usa, bajo `.lks-sdd/cache/`, puede desactivarse o eliminarse y nunca es autoridad.

## Compatibilidad histórica de evidencia

Eliminar schemas legacy de proyecto no elimina evidencia inmutable. Los quality reports 1.1 y la evidencia técnica o de entrega anterior que el contrato vigente declara legible continúan validándose como historial. No pueden acreditar una release nueva si esta exige un contrato más reciente.

La evidencia técnica nueva usa schema 1.3 y registra bindings, scopes tipados e interfaces aplicables. Para un único binding, la identidad superior de perfil debe coincidir; para varios bindings no se inventa una identidad superior común. EVID 1.2 y la evidencia G4 anterior conservan sus bytes. Si una EVID histórica pretendía cerrar integración sin prueba cross-binding, se conserva como evidencia de componente y se informa `reconciliation-required`; nunca se migra ni reabre automáticamente.

## Perfiles y superficies

La compatibilidad tecnológica se declara por composición exacta de perfil, lock, scaffold, gates y certificación vigente. Una semejanza de nombres o capabilities no acredita soporte. Los perfiles candidate, la interoperabilidad real Microsoft Entra y Rovo/Jira y los canales humanos o de piloto permanecen `not-run` o `unsupported` hasta disponer de evidencia real.

Codex es el único entorno objetivo soportado para el plugin. ChatGPT Work, GitHub Copilot y Claude no tienen integración ni equivalencia verificadas. ImageGen puede ser una ayuda visual cuando Codex lo expone, pero no forma parte del contrato del plugin ni sustituye revisión humana. Atlassian Rovo es el peer externo previsto para Jira y sigue sujeto a política, autorización, relectura e interoperabilidad real demostrada.

Jira es una proyección outbound-only opcional. Un proyecto `repository-only` mantiene la experiencia completa. Un backend sin frontend no recibe revisión visual por inferencia, y una tarea local no queda bloqueada por decisiones exclusivamente productivas.

## Puente de actualización desde 0.14.2

0.15.0 conserva un rollback de distribución limitado al periodo de adopción desde la única instalación 0.14.2: sustituir el bundle por el artefacto inmutable anterior y verificar sus checksums. Ese rollback no transforma ni reescribe el proyecto consumidor.

Este puente es temporal. La versión 1.0 debe partir de un contrato único ya estabilizado y no distribuir migradores, schemas de proyecto legacy ni una promesa de rollback a releases pre-1.0. Los rollbacks transaccionales de una operación fallida siguen siendo obligatorios porque protegen la atomicidad; no son compatibilidad legacy.

## Diagnóstico

```powershell
python "<plugin-root>/scripts/lks_sdd.py" doctor "<project-root>" --quick
python "<plugin-root>/scripts/lks_sdd.py" validate-project "<project-root>"
python "<plugin-root>/scripts/lks_sdd.py" status "<project-root>" --view audit --json
```

Los comandos deben confirmar schema 1.5/método 1.5.0, mostrar por separado el runtime y la procedencia de materialización, y no alterar Markdown ni el índice.

0.17 mantiene lectura de proyectos y EVID 1.2 sin migración destructiva. Las revisiones visuales 1.1 siguen legibles; una revisión nueva se materializa como 1.2. El nuevo `ART-INTEGRATIONS` es aditivo: proyectos sin interfaces confirmadas conservan comportamiento y obtienen no aplicabilidad determinista. Un runtime anterior no interpreta los nuevos scopes ni EVID 1.3 y no debe usarse para registrar nueva evidencia conjunta.
