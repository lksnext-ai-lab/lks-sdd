# Preguntas frecuentes

## ¿SDD significa escribir mucha documentación?

No. El detalle se ajusta al riesgo y al siguiente incremento. El objetivo es no perder decisiones, criterios y trazabilidad necesarios, no maximizar páginas.

## ¿El plugin decide la arquitectura?

No. Puede comparar y proponer. La persona confirma las decisiones y su autoridad formal, si existe, se registra por separado.

## ¿FastAPI, React, PostgreSQL y Keycloak son obligatorios?

No. Integran el perfil H0 implementable y verificable `WEB-FASTAPI-REACT-KEYCLOAK-PG`, pero el perfil sigue siendo candidato y debe seleccionarse mediante una decisión confirmada. Una alternativa puede documentarse con su justificación.

## ¿`ready` significa que Codex puede empezar?

No. `specification_readiness` indica si no se conocen bloqueos funcionales para el alcance, mientras `automation_support` comprueba si la pila confirmada tiene soporte implementable. El estado combinado puede seguir bloqueado aunque la especificación esté lista. La autorización humana es independiente; `lks-sdd-implement` exige además un preview y un hash coincidente antes de escribir.

## ¿Actualizar a 0.7.0 cambia mis documentos 1.0?

No. Los proyectos 1.0 siguen validándose en modo de compatibilidad. Pasar a método 1.1.0 y esquema 1.1 requiere una migración explícita con dry-run. Si `human_review_required` contiene entradas, la aplicación se rechaza siempre antes de crear el backup o escribir: hay que resolver cada entrada listada en los Markdown canónicos 1.0, validar el origen y repetir el dry-run hasta obtener una lista vacía. Solo entonces se aplica con backup externo, hash coincidente, autorización y validación posterior. La `Identity` agregada 1.0 se convierte aparte en identidad, seguridad y privacidad `pending`, sin referencias inferidas: no impide el apply si la lista está vacía, pero bloquea readiness hasta resolverse en 1.1. Si el origen es 0.9, primero se solicita 1.0 y se revisa ese salto por separado.

## ¿Cuándo se exige evidencia en la trazabilidad?

`preimplementation` exige relaciones desde cada requisito aplicable hasta aceptación, decisión o no aplicabilidad motivada, incremento y prueba. `verification` exige además evidencia ejecutada del mismo incremento. Una comprobación sin requisitos aplicables falla como alcance vacío en vez de producir un falso positivo.

## ¿Puedo usar LKS-SDD con un repositorio existente?

Sí. `lks-sdd-adopt-existing` realiza primero un inventario estático de solo lectura y externo al repositorio. La materialización solo continúa tras reconciliación, confirmación, baseline vigente, preview y autorización, y únicamente añade documentación LKS-SDD.

## ¿Funciona igual en GitHub Copilot o Claude?

No se garantiza. LKS-SDD se implementa y soporta como plugin para Codex. Los documentos y algunos validadores pueden ser reutilizables, pero Copilot, Claude u otros asistentes necesitarían su propia integración y pruebas antes de declarar compatibilidad o resultados equivalentes.

## ¿Qué archivo manda si el índice y un Markdown discrepan?

El Markdown canónico. `.lks-sdd/project.json` es un índice que debe corregirse de forma explícita, sin reescribir el contenido humano silenciosamente. En esquema 1.1, readiness se deriva al consultar y no se persiste en el índice como aprobación.
