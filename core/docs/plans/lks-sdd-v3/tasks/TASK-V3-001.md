# TASK-V3-001 · Contrato v3 y frontera con v2

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento del contrato**; persona/agente por asignar.
Inicio del trabajo independiente: autorización del plan; sin tarea previa.
Dependencias para cerrar: autorización del plan; sin tarea previa.

Requisitos de responsabilidad principal: REQ-EQT-054.
Casos de aceptación principales: AC-EQT-062.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Primera entrega y compatibilidad
Entregar primero el núcleo que necesitan las demás tareas: identidad, revisión, procedencia,
referencias, propuesta/decisión y diagnóstico. Ampliar schemas por dominio al integrar
sus propietarios; no bloquear el arranque por diseñar todas las extensiones a la vez.

Inventariar las operaciones actuales que afectan a v3: creación, autoría, adopción,
readiness, declaración tecnológica, ejecución/verificación, retención y rutas por host.
Para cada una indicar reutilización, adaptación o limitación, con propietario y prueba.
Consultar `v2_authoring.py`, `v2_adoption.py` y `v2_preparation.py`, además de los
lectores. Mantener v2 operativo no acredita que esas operaciones existan en v3.
Una incompatibilidad material no se convierte silenciosamente en exclusión de alcance.

Fijar qué bytes/revisión identifican fuentes y unidades, incluidos textos Unicode y
finales de línea entre hosts; no normalizar contenido normativo para conservar una
aprobación indebidamente. Validadores/fixtures aceptarán desarrollo aditivo v3 sin
cambiar el contrato activo v2 antes del momento previsto en 015.

## Encargo y límites
Formalizar el contrato documental v3 y sus fronteras con los lectores/runtime fijados v2.
Especificar metadatos de política, miembro, petición, unidades de aprobación, decisiones,
asignación, excepción y análisis, reutilizando SPEC/PLAN/TASK y AUTH/EXEC/CKPT/EVID cuando
su significado coincida. Fijar qué es normativo, histórico, derivado y local de sesión.
No activar v3 ni transformar consumidores.

## Entregables e interfaces
- Añadir `docs/V3-CONTRACT.md`, schemas `*-3.0.schema.json` necesarios y lectores
  `scripts/v3_schema.py` / `v3_contract.py`, con fixtures válidos e inválidos.
- Fijar tipos Python y salidas de lectura, evaluación, preview/apply, análisis,
  contexto y migración descritas en PLAN. Registrar dependencias tipadas y causas legibles.
- Especificar detección separada de plugin/método/schema y rechazo de combinaciones
  desconocidas; lectura admitida no concede permiso de escritura.
- Inventariar revisiones 2.x documentadas y formatos observados para que 011 prepare
  muestras. No declarar cobertura de toda la línea por una sola muestra.
- Referencias de partida: `scripts/v2_contract.py`, `v2_schema.py`, schemas 2.0 y
  `docs/V2-MIGRATION.md`. Añadir pruebas focales en `tests/`.

## Aceptación y evidencia
Una muestra v3 válida se lee; referencias ambiguas, tipos incorrectos y versiones
desconocidas producen diagnóstico, sin writes. Instalar/seleccionar el código v3 no
reescribe una muestra v2 ni cambia su runtime operativo fijado. La gramática declara
autoridad/identidad observada sin simular autenticación. Los demás agentes reciben
firmas, ejemplos y causas concretas, no solo nombres de módulos.
Entregar schemas, muestras, resultados de lectura/rechazo y mapa de compatibilidad inicial.

## Riesgos y revisión
Revisar con mantenimiento de runtime y migración. Un requisito incompatible con una
garantía canónica vuelve a decisión; no se corrige reescribiendo `specs/canonical/`.
Lectura adicional: propuesta técnica §§2–5 y 9; funciones actuales de lectura y formatos.
