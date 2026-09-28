# TASK-V3-016 · Verificación conjunta y regresión

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Revisión técnica e integración**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-015](TASK-V3-015.md).

Requisitos de responsabilidad principal: Contribución transversal; ver matriz.
Casos de aceptación principales: Comprobación conjunta; ver matriz.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Verificación por recorridos y cobertura semántica
Preparar casos desde 001 y ejecutarlos con cada porción disponible de R1–R3. El cierre
consolida el candidato R4, sin volver a ejecutar todo por cada edición ni aplazar la
integración hasta que terminen 15 módulos.

Cada caso compuesto de la matriz debe conservar todas sus condiciones observables:
preparación, actuación, resultado esperado, restricciones que no deben alterarse,
contribuyentes y evidencia. La relación numérica requisito→caso no demuestra cumplimiento;
un test de la primera cláusula no acredita todo el caso. Usar el mismo registro de
resultados por caso y campos, sin un documento adicional por cada comprobación.

Probar las tres entradas (nuevo, existente sin SDD, consumidor 2.x), revisión incremental
del plan, resultados concurrentes de calidad y continuidad entre hosts. Revisar también
coste e impacto de extensiones sobre v2 y el uso de tecnología/evidencia existentes.
Las observaciones tempranas no sustituyen los resultados sobre el candidato final.

## Encargo y límites
Verificar la integración real entre todas las porciones y las regresiones materiales.
Tiene responsabilidad explícita sobre la comprobación conjunta de las 17 tareas.
Los propietarios de cada requisito/caso conservan la corrección de su componente.

## Entregables e interfaces
- Ejecutar los casos automáticos de la matriz agrupados en fixtures y pruebas de
  comportamientos materiales, sin crear un test mecánico por cada fila.
- Recorridos integrados: individual sin controles; equipo frontend/backend/BBDD con
  relevo; controles activos y fallo/corrección; excepción; cambios concurrentes;
  revisión parcial; mantenimiento con historia; migración 2.0/2.1 con trabajo abierto.
- Pruebas Git en dos clones/ramas y destino no-main; aprobación/autoridad desde fuentes
  independientes de la propuesta candidata; interrupciones de escritura y migración.
- Comparar selector de contexto con ruta suficiente: obligaciones globales, contribuyentes,
  prosa, adjuntos, cambio de inventario y compactación. No activarlo solo por medir tamaño.
- Regresión focal v2, distribución y Windows; contrato del plugin. Usar
  `tests/run_unit_tests.py` conforme a sus opciones verificadas y
  `python -B -X utf8 scripts/validate_plugin_contract.py .`.
- Guardar mapa caso → revisión exacta/fixture/resultado/evidencia en
  `docs/plans/lks-sdd-v3/evidence/` al ejecutar, y actualizar cobertura. Ese mapa
  todavía no existe como evidencia; la matriz actual es planificación.

## Aceptación y evidencia
No hay requisitos sin dueño, ciclos, enlaces inválidos ni integración declarada por
sumar “done”. Todos los casos automáticos aplicables tienen evidencia sobre el candidato
exacto; fallos se corrigen y repiten solo pruebas afectadas. Los casos humanos pendientes
quedan identificados para 017. Preservar resultados negativos y separar mocks/informes
fixture de observación real. Revisor comprueba el diff completo, fuentes canónicas
inalteradas y ausencia de ampliación a CI/CD.

## Riesgos y revisión
No cambiar el contrato para hacer pasar una implementación. No convertir esta campaña
en una segunda puerta permanente de publicación: integrar solo regresiones materiales
en pruebas mantenidas y registrar el resto como aceptación de esta evolución.
Revisión técnica conjunta distinta de la aceptación humana de uso en 017.
