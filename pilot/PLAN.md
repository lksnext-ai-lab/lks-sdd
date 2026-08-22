# Plan operativo del piloto M5

## Objetivo y muestra

El piloto valida utilidad, coherencia y carga documental con tres a cinco proyectos y cinco a ocho participantes. Debe incluir una ruta greenfield con perfil active certificado, una adopción de repositorio existente y una arquitectura/perfil alternativo; un caso de riesgo reforzado es opcional. La muestra debe representar al menos dos modelos de entrega entre `bounded-release`, `continuous-evolution` y `maintenance-stream`. Solo se admiten proyectos sintéticos, copias sanitizadas o entornos no productivos con autorización confirmada.

## Duración

- Semana 0: preparación, responsables, canales, paquete, rollback y onboarding.
- Semanas 1–2: definición, gobierno de entrega, planificación y readiness.
- Semanas 2–5: implementación o adopción con seguimiento `TASK-###`.
- Semanas 5–6: verificación G3/G4 y entregables.
- Semanas 6–8: correcciones, evaluación y decisión.

El calendario se adapta al incremento; no se fuerza un proyecto a finalizar para cerrar la observación.

## Puerta de inicio

Antes de cambiar el estado externo a `running`, `scripts/manage_pilot.py validate-config` debe devolver `ready`. Esto exige muestra, aliases, responsables, soporte, canal confidencial de seguridad, paquete 0.9.0 candidate con checksum, rollback a 0.8.0 confirmado y restricciones de privacidad. El archivo de ejemplo permanece deliberadamente `blocked`.

## Evidencia

Las observaciones usan exclusivamente códigos `PRJ-*`, `USR-*` y métricas cerradas. Se almacenan fuera del repositorio con retención definida. El resumen agregado no contiene códigos de proyecto o participante y alimenta una decisión `go`, `go-conditioned`, `no-go` o `withdrawal`.
