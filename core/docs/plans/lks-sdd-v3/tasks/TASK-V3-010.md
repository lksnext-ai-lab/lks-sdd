# TASK-V3-010 · Contexto suficiente, selección y caché

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento del contexto**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-002](TASK-V3-002.md).
Dependencias para cerrar: [TASK-V3-005](TASK-V3-005.md).

Requisitos de responsabilidad principal: REQ-EQT-067, REQ-EQT-068.
Casos de aceptación principales: AC-EQT-090, AC-EQT-091, AC-EQT-092, AC-EQT-093, AC-EQT-094, AC-EQT-095, AC-EQT-096, AC-EQT-100.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Comparación útil y activación sin circularidad
Preparar con 017 una referencia reproducible antes de optimizar. Primero comparar
selección/cobertura localmente, conservando la ruta suficiente para la operación normal.
Tras superar esa comprobación, probar ambas rutas en copias y escenarios de aceptación
controlados, con las mismas obligaciones. Esa prueba experimental no activa la selección
por defecto para consumidores; la activación normal exige los resultados de 016/017.

Medir aparte el coste del experimento, las lecturas frías/calientes, CPU/I/O y volumen
acumulado. El contraste doble es propio de la evaluación y no debe quedarse ejecutándose
en cada operación ordinaria aceptada. Si la optimización empeora, conservar la ruta
suficiente y corregir: el plan no considera v3 aceptada por renunciar silenciosamente
a la mejora comprometida. No añadir un framework de compresión o caché distribuida.

## Encargo y límites
Producir contexto por operación con obligaciones literales completas y una sola copia
de cada bloque. Mejorar el selector existente, empezando en **comparación**: no retirar
al ejecutor su ruta suficiente hasta la verificación de 016 y aceptación de 017.
No resumir reglas normativas para ajustarlas a un número de tokens.

## Entregables e interfaces
- Añadir `scripts/v3_context.py`; partir de `v2_contract.execution_context`,
  separando representación para el modelo de las entradas completas del guard.
- Raíz válida por UID/operación; recorrer obligaciones, contribuyentes, interfaces,
  dependencias inversas y restricciones globales, incluida prosa y adjuntos.
- Aplicabilidad confirmada, exclusión justificada o incertidumbre; ampliar lectura
  ante lo desconocido, bloquear solo la actuación afectada si persiste duda crítica.
- Cache derivada por contenido, inventario/altas/bajas, runtime/selector, política,
  autoridad, base, evidencia, operación y porción. Nunca usar solo fechas de archivos.
- Distinguir caché del runtime de texto disponible en el chat. Tras compactación,
  sesión nueva o incapacidad de comprobar disponibilidad, rehidratar núcleo literal.
- Diagnóstico de fuentes incluidas/excluidas/inciertas, totales y localizadores,
  sin copiar inventarios extensos ni alterar fingerprints de autorización.

## Aceptación y evidencia
Raíz inexistente/ambigua no produce suficiencia vacía. Una restricción global nueva
invalida contexto aunque la TASK no cambie. Contribuciones e interfaces sin enlaces
completos no desaparecen. Reglas parecidas con ámbitos distintos no se deduplican.
Diez veces más historia ajena no aumenta el núcleo normativo enviado; medir I/O aparte.
Obligaciones que superan el aviso de 8.000 tokens se conservan; si no caben conjuntamente,
se explica y propone dividir alcance/replanificar. Nueva sesión recupera texto y
mantiene decisiones vigentes. Entregar comparación de cobertura con ruta de referencia,
casos adversos y resultados de caché; no declarar ahorro real todavía.

## Riesgos y revisión
Las APIs de 007–009 están fijadas por 001; usar sus contratos para trabajo paralelo,
y exigir implementación integrada en 016 antes de activar selección. Revisión de
cobertura y calidad del código, no solo tamaño. Lectura adicional: funcional §5.11
y técnica §§6.1–6.6 completos.
