# LKS-SDD para Codex y GitHub Copilot

La versión `2.3.1-oracle.1` de LKS-SDD organiza el desarrollo con agentes alrededor de
especificaciones comprensibles, decisiones explícitas y resultados verificables.
La documentación del proyecto sigue siendo la fuente de verdad; el código aporta
evidencia de lo implementado, no decide por sí solo qué comportamiento es correcto.

El enfoque es **Spec-anchored**: los acuerdos siguen vigentes durante todo el ciclo
de desarrollo. No es **Spec-as-source** ni promete generar una aplicación correcta
solo a partir de documentos. Definir, planificar, autorizar, implementar, verificar,
aceptar y entregar son estados distintos.

## Empezar con la versión 2

| Necesidad | Guía |
|---|---|
| Entender el producto y sus límites | [Índice v2](docs/V2-INDEX.md) y [compatibilidad](docs/COMPATIBILITY.md) |
| Instalar el paquete del host | [Instalación](docs/INSTALLATION.md) |
| Definir o evolucionar funcionalidades | [Ciclo de trabajo](docs/V2-WORKFLOWS.md) y [estructura documental](docs/V2-AUTHORING.md) |
| Modificar una funcionalidad existente | [Continuidad SPEC → PLAN/TASK → implementación](docs/V2-SPEC-PLAN-TASK.md) |
| Consultar requisitos, especificaciones y tareas | [Consultas para personas](docs/PROJECT-QUERY.md) |
| Adoptar un sistema con documentación parcial | [Adopción acotada](docs/V2-WORKFLOWS.md#adopt-existing-ámbito-legado-suficiente) |
| Pasar un proyecto 1.5 a v2 | [Migración explícita y rollback](docs/V2-MIGRATION.md) |
| Entender controles y tecnología aprobable | [Guardrails](docs/V2-GUARDRAILS.md) y la declaración tecnológica local |
| Comprobar la entrega | [Historial de versiones](CHANGELOG.md), [estado actual](docs/STATUS.md), [validación](docs/VALIDATION.md) y [aceptación por host](docs/V2-HOST-ACCEPTANCE.md) |

## Qué cambia

- **Documentación humana y navegable.** Cada funcionalidad explica propósito,
  comportamiento, requisitos, excepciones y aceptación, con enlaces a tareas y
  decisiones. Usa prosa, tablas, listas o diagramas según lo que ayude a entenderla.
- **Funcionalidades con identidad e historia.** Un proyecto contiene funcionalidades
  y trabajo trazado. Las relaciones padre/hija son lógicas; no duplican documentos
  ni heredan aprobaciones. El catálogo diferencia definiciones vigentes, propuestas,
  sustituciones parciales o totales y entregas observadas.
- **Consulta centrada en lo documentado.** Las respuestas reúnen información
  relacionada y enlazan sus fuentes sin modificarla. El código se consulta ante
  una carencia concreta o petición expresa. Ausencia documental no significa que
  una función no exista, especialmente en sistemas con años de evolución.
- **Desarrollo delimitado.** El agente necesita obligaciones completas, plan,
  tecnología aplicable y autorización vigente para las tareas y el entorno.
  Revisa el diff real, conserva checkpoints y reconcilia cambios antes de reanudar.
- **Cada cambio vuelve a la SPEC.** La petición material se registra por puntos,
  se compara con requisitos y aceptación vigentes y completa PLAN/TASK antes de
  autorizar código, también cuando la feature ya tenía tareas anteriores.
- **Evidencia por alcance.** Una prueba de componente no acredita integración,
  persistencia, aceptación humana ni producción. La evidencia conserva su sujeto
  técnico, procedencia y limitaciones; una incidencia posterior no reescribe la historia.
- **Declaración tecnológica local.** Las observaciones y decisiones técnicas permanecen en el proyecto; ninguna selección global habilita trabajo ni verificación.
- **Migración controlada.** La ruta 1.5 → 2.0 ofrece diagnóstico, preview, aplicación
  autorizada, originales conservados y recuperación. Actualizar el plugin no migra
  automáticamente ningún proyecto.

## Uso cotidiano

No es necesario memorizar IDs ni comandos. Puedes pedir:

- «Explícame cómo funciona la impresión de pedidos, sus requisitos y tareas».
- «Esta función ya existe; analiza qué parte cambia y qué debe seguir funcionando».
- «Descompón esta petición en funcionalidades y tareas, sin implementar todavía».
- «Evalúa si podemos implementar las tareas seleccionadas y qué decisión falta».
- «Implementa la porción autorizada y conserva el estado necesario para retomarla».
- «Verifica el resultado y separa lo probado, lo pendiente y la entrega».

Las seis skills siguen siendo ayuda, definición, adopción, readiness, implementación
y verificación. La invocación implícita permanece activa; pedir una explicación
nunca autoriza una escritura.

## Documentos, equipo y versiones

Los Markdown del consumidor son canónicos y `.lks-sdd/project.json` es un índice.
La [estructura v2](docs/V2-AUTHORING.md) reúne contexto, especificación por
funcionalidad, solución, trabajo e historia. Una tarea puede contribuir a varias
funcionalidades sin duplicarse; un incremento y una release no son funcionalidades.

Cada desarrollador usa su clon y el runtime fijado en el proyecto. Las decisiones,
fuentes y evidencias se comparten mediante Git, no mediante el chat de una persona.
Los conflictos requieren reconciliación semántica; no hay garantía de escritores
simultáneos sobre el mismo alcance.

Plugin 2.3.1-oracle.1, schema 2.0 y método 2.1.0 son versiones distintas. Los consumidores
con método 2.0.0 siguen legibles y se actualizan explícitamente.
Los consumidores 1.5/1.5.0 siguen su workflow y runtime fijado hasta autorizar
una migración.
La compatibilidad 1.5 se limita al runtime fijado y a su migración explícita; no
sustituye las reglas v2.

## Distribución y límites

Hay paquetes para Codex desktop y GitHub Copilot en VS Code Agent con un núcleo
común. La alternativa de skills de proyecto sigue disponible, sin activarla a la vez
que el plugin nativo. Publicación, instalación personal, runtime del proyecto y
aceptación conversacional son hechos independientes.

ImageGen es una capacidad condicional del host Codex. Copilot puede preparar un
relevo visual explícito; Codex nativo trabaja normalmente sin ese relevo.
Atlassian Rovo es un peer opcional para `jira-hybrid`; no se incluye cliente Jira, MCP,
conector, hook, aplicación ni agente ejecutable adicional. `repository-only` no
requiere servicios externos. Claude, ChatGPT Work y la extensión Codex de VS Code
quedan fuera del alcance de esta distribución.

Los roles son declarados, no autenticados; los hashes no son una firma de editor.
Los controles locales detectan incumplimientos, pero no interceptan toda escritura
del host. La [guía de guardrails](docs/V2-GUARDRAILS.md) explica cómo comprobar un
cambio desde una base confiable sin permitir que se autoapruebe.

Esta versión es un candidato local con la corrección del observador Oracle; no está
publicada y su referencia Copilot no se ha creado en remoto. La release técnica
estable exige gates y una aprobación propia; la [aprobación de 2.3.0](quality/release-approval-v2.3.0.json)
es histórica y no acredita este candidato.
No equivale a aceptación humana, política corporativa, despliegue ni soporte
universal. Los ensayos reales de host, piloto, comprensión humana e interoperabilidad
Rovo/Jira o Entra sin evidencia siguen `not-run`. La tecnología se documenta y
confirma localmente.

## Mantenimiento

`skills/` contiene los seis workflows; `scripts/`, los motores y validadores;
`schemas/`, los contratos versionados; las declaraciones tecnológicas viven en cada proyecto;
`tests/` y `quality/`, pruebas y evidencia. `specs/canonical/` permanece congelado.
El [contrato de proyecto v2](specs/proposed/project-contract-2.0.md) es la
propuesta vigente para declaraciones tecnológicas locales; no es política
corporativa.

Consulte [arquitectura](docs/ARCHITECTURE.md), [validación](docs/VALIDATION.md),
[distribución](docs/DISTRIBUTION.md) y [releases](docs/RELEASING.md).
Las salidas regenerables no se versionan; se conservan fuentes, fixtures,
planes y contraejemplos relevantes. [Licencia](LICENSE.md),
[contribución](CONTRIBUTING.md), [soporte](SUPPORT.md) y [gobierno](GOVERNANCE.md)
mantienen sus condiciones, sin añadir SLA ni responsables no confirmados.
