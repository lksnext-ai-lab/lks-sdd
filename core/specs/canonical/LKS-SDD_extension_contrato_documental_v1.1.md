# Extensión LKS-SDD: contrato documental y handoff 1.1

**Fecha de decisión:** 2026-08-20

**Estado:** confirmed

**Ámbito:** proyectos creados o migrados con `method_version: 1.1.0` y `schema_version: 1.1`
**Compatibilidad:** los proyectos 1.0 siguen siendo legibles mediante un modo explícito de compatibilidad; no se reinterpretan silenciosamente como 1.1.

## Motivo

La experiencia con un proyecto consumidor real mostró que un documento estructuralmente válido podía producir resultados incoherentes entre validación, ayuda, trazabilidad y readiness. Las causas confirmadas fueron una ontología de estados compartida por naturalezas distintas, referencias extraídas de cualquier texto, rangos tratados como extremos aislados, dependencias implícitas mediante `ART-*`, mezcla de material activo e histórico, aplicabilidad de dominios agregada, readiness persistido y una puerta técnica confundida con la suficiencia de la especificación.

Esta extensión fija un contrato único para que todos los workflows consuman la misma representación normalizada. No cambia la regla de autoridad: los Markdown versionados del proyecto consumidor son canónicos y `.lks-sdd/project.json` es solo un índice.

## Naturaleza y estado

La naturaleza de un elemento se deriva del artefacto, la tabla y el prefijo propietario. `State` expresa únicamente su ciclo de vida dentro de una política declarada por tabla.

- Contenido contractual (`FR`, `NFR`, `TR`, `AC`, `ADR`, `INC`, `DATA`, `SEC`, `PRIV`, `INT`, `UX`, `VIS`): `draft`, `proposed`, `confirmed`, `rejected`, `superseded` o `retired`.
- Puntos abiertos (`OPEN`): `open`, `blocked`, `resolved`, `superseded` o `retired`.
- Planes de prueba (`TEST`): `draft`, `proposed`, `planned`, `confirmed`, `superseded` o `retired`.
- Riesgos, dependencias y desviaciones: la política específica distingue estados activos, mitigados y cerrados.
- Artefactos de adopción `as-is`: conservan estados epistemológicos para hechos, observaciones, inferencias, supuestos, incógnitas y contradicciones. No se convierten en intención `to-be`.

Los estados de ejecución de una prueba o evidencia (`passed`, `failed`, `blocked`, `not-run`) pertenecen al registro de ejecución y no sustituyen el ciclo de vida del `TEST-###`.

## Identificadores propietarios

Cada tabla contractual declara si define un ID, qué prefijos puede poseer y qué columnas contienen relaciones. Entre otros:

- `CON-###` pertenece a restricciones; `DEP-###` sigue significando dependencia y `DEV-###`, desviación.
- `TEST-###` se define una sola vez en `ART-QUALITY`; `ART-TEST-STRATEGY` lo referencia mediante la columna `Test`.
- Las columnas descriptivas de arquitectura, despliegue, observabilidad y operación usan `Label`; no se interpretan como identificadores por llamarse `Reference`.
- Solo se extraen referencias de columnas declaradas como relación. Un ID mencionado en una explicación, fuente, observación o prompt no crea una arista contractual.

## Gramática de referencias

Una relación admite:

- un ID: `FR-001`;
- una lista separada por coma o punto y coma: `FR-001, FR-004; FR-010`;
- un rango inclusivo canónico: `FR-001..FR-079`.

Un rango exige el mismo prefijo, orden ascendente, tamaño acotado y existencia de todos los IDs incluidos. Si falta un elemento o la sintaxis es inválida, la celda completa falla: nunca se conservan solo los extremos ni una expansión parcial.

El modo de compatibilidad 1.0 acepta `FR-001 a FR-079` y emite una advertencia de migración. El modo 1.1 lo rechaza. Las relaciones activas 1.1 no aceptan `ART-*` como expansión implícita; deben enumerar IDs o usar un rango canónico resoluble.

## Contrato activo e histórico

El modelo documental conserva todos los elementos para auditoría, pero el contrato de un incremento se obtiene desde su `INC-###` siguiendo únicamente relaciones declaradas `active_input`.

- Un elemento `rejected`, `superseded` o `retired` es histórico y no se atraviesa como entrada de implementación.
- Una relación activa hacia un elemento histórico o pendiente genera un diagnóstico localizado.
- `document_fingerprint` representa la instantánea completa leída.
- `active_contract_fingerprint` representa solo nodos, relaciones, selección y lock de perfil y assets visuales activos del incremento.

Modificar un asset visual histórico no invalida el preview de un incremento que no lo consume. Un `VIS-###` activo continúa exigiendo archivo íntegro, formato, dimensiones, SHA-256, validación humana y decisión enlazada según el contrato visual vigente.

## Aplicabilidad por dominio

La tabla principal de `ART-INCREMENTS` contiene alcance, requisitos, aceptación, decisiones y pruebas. La aplicabilidad se declara aparte mediante:

`Increment | Domain | Applicability | References | Reason`

Cada incremento incluye exactamente una fila para `data`, `identity`, `security`, `privacy` e `integrations`.

- `applicable` exige referencias del prefijo correspondiente.
- `not-applicable` exige motivo y no admite referencias activas.
- `pending` exige motivo y bloquea readiness para ese incremento.

Identidad, seguridad y privacidad se evalúan por separado. Una decisión sobre un dominio no satisface automáticamente los demás.

## Readiness y soporte de automatización

La evaluación devuelve dos resultados independientes:

1. `specification_readiness`: suficiencia del contrato del incremento, sus confirmaciones, aplicabilidades y trazabilidad previa a implementación.
2. `automation_support`: capacidad real del perfil seleccionado para analizar, implementar o verificar con un lock validado y recursos empaquetados.

El resultado combinado permanece conservador: no se inicia implementación si cualquiera de las dos dimensiones bloquea. Una pila alternativa puede estar bien especificada y ser documentable aunque el plugin no garantice su implementación.

Readiness se deriva bajo demanda y no se persiste como autorización en `.lks-sdd/project.json`. La ayuda puede ejecutar un preflight de solo lectura, pero lo etiqueta como tal y no lo presenta como una evaluación completa.

## Trazabilidad por fase

La trazabilidad nunca es válida con un alcance aplicable vacío.

- En `preimplementation`, cada requisito confirmado del alcance debe enlazar aceptación, incremento, prueba y decisión o una no aplicabilidad razonada. `Evidence` puede quedar vacío.
- En `verification`, la misma cadena debe alcanzar una evidencia realmente ejecutada y correspondiente al incremento.

Validación, ayuda, trazabilidad, readiness, implementación y verificación consumen la misma gramática y el mismo grafo; no mantienen interpretaciones privadas de IDs o rangos.

## Diagnósticos

Los validadores emiten diagnósticos estructurados y deduplicables con código estable, severidad, etapa, ubicación (ruta, artefacto, tabla, fila, columna e ID origen), valor observado, expectativa, corrección y causa cuando proceda. Las listas textuales anteriores se mantienen como vista de compatibilidad, no como fuente primaria.

Un error sintáctico raíz impide ejecutar validaciones derivadas de esa relación para evitar cascadas engañosas.

## Migración y compatibilidad

La migración 1.0 a 1.1 siempre ofrece preview, hash reproducible, backup externo y rollback. Puede normalizar estructuras y estados cuya equivalencia sea expresa, pero no inventa confirmaciones:

- `proposal` pasa a `proposed`;
- `decision` pasa a `confirmed` solo porque el contrato 1.0 ya expresaba una decisión;
- `fact`, `requirement` y `assumption` pasan a `draft` y quedan señalados para revisión humana;
- una aplicabilidad agregada o ambigua pasa a `pending` con motivo.

El proyecto 1.0 original continúa validable en compatibilidad hasta que una persona revise y aplique la migración. El plugin no modifica automáticamente un repositorio consumidor al actualizarse.

## Calidad y publicación

La release que implementa esta extensión debe:

- ejecutar un recorrido coherente desde definición hasta readiness sobre un fixture realista y saneado;
- resolver cada evidencia `test:` o `eval:` del catálogo contra una prueba existente y ejecutada;
- separar tests superados, omitidos y fallidos; un omitido crítico deja la automatización incompleta;
- empaquetar los bytes de un commit Git real, coincidente con `HEAD` y con árbol limpio;
- mantener actualizadas las seis skills, referencias, documentación, changelog, nota de release y guía de migración.

Los canales semánticos, humanos o de piloto no ejecutados permanecen `not-run`. Una candidate puede publicarse con esa limitación explícita; una release `stable` no.
