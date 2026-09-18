# Revisión crítica de investigación sobre contexto

Fecha de corte: 2026-09-11. Fuentes primarias abiertas: 12 principales y 9 de apoyo, con fechas, versiones, resultados y limitaciones en [sources.json](sources.json). Esta investigación no constituye un benchmark local ni una decisión de implementación.

## Cambios que debería provocar en la propuesta

1. **Calidad antes que presupuesto.** El compilador debe preservar requisitos conocidos y ser capaz de ampliar contexto. No basta con recibir una restricción: también importan sus relaciones y su presentación. Menos contexto puede reducir ruido; demasiado poco elimina ingredientes de solución. Ninguno de los estudios demuestra un tamaño mínimo universal.
2. **Tres problemas distintos.** Separar contrato normativo, adquisición de evidencia de código e historial de ejecución. Las técnicas eficaces sobre observaciones antiguas no autorizan a resumir una especificación. Las mejoras en QA documental no prueban mejores parches.
3. **Núcleo literal y procedencia fuera del prompt.** Conservar redacción, condiciones, excepciones, unidades, ámbitos y vigencia. Una reformulación debe ser una representación candidata revisada, no un contrato aprobado por el compilador. Huellas extensas e informes completos pueden permanecer fuera, pero la obligación real debe ser legible.
4. **Selección reversible y dinámica.** Conservar originales accesibles y recalcular selección si cambian archivos afectados, hipótesis, interfaces, perfil o contrato. El paquete inicial no puede anticipar todos los descubrimientos del debugging. La línea de investigación más reciente está atendiendo precisamente al cambio de foco.
5. **La suficiencia documental no es suficiencia de implementación.** Un grafo completo de IDs puede omitir una regla en prosa; un índice de archivos completo puede omitir la función pertinente. Identificar explícitamente texto no clasificado y operaciones que no soporta el selector.
6. **Recuperación heterogénea.** Símbolos, grafo de dependencias, referencias contractuales, búsqueda literal y semántica deben aportar candidatos. No hay una familia ganadora en todos los casos. Las consultas deben depender de la operación: encontrar pruebas, localizar un error o anticipar efectos sobre consumidores no son lo mismo.
7. **No adoptar una notación por ahorro de tokens.** La equivalencia de un parser no demuestra comprensión por el modelo. Los formatos compactos pueden fallar al generar y al mantener conversaciones, incluso con ahorro medido. Mantener Markdown compacto y texto claro como controles.
8. **Ahorro de contexto, tokens facturados y dinero son métricas diferentes.** Registrar input nuevo, relecturas, cache, salida, razonamiento si está disponible, llamadas auxiliares y latencia. El prefijo estable ayuda al cache, pero el plugin no controla necesariamente el historial del host ni puede prometer eliminarlo.

## Lecturas que cambian al abrir tablas y limitaciones

- **AttnCompress, 08-09-2026:** la comparación favorable del titular es contra otro compresor. La tabla muestra menor tasa de éxito que conservar el historial completo. Aporta una idea útil de recuperación dinámica, pero no cumple por sí sola un criterio estricto de calidad primero. [R06](https://arxiv.org/html/2609.08318v1)
- **SWE-Pruner Pro, 20-07-2026:** el ahorro máximo procede de consultas; en reparación los resultados son asimétricos entre modelos y no hay mejora simultánea universal. Además requiere estados internos del modelo, inaccesibles como simple codificación de archivos sobre una API cerrada. [R05](https://arxiv.org/html/2607.18213v1)
- **SWEzze, 30-03-2026:** ofrece evidencia favorable a optimizar por ingredientes necesarios para la reparación. Su evaluación se limita a un pipeline y repositorios Python; el entrenamiento con oráculo tampoco convierte la inferencia en una prueba de suficiencia. [R04](https://arxiv.org/html/2603.28119v1)
- **AGENTS.md, revisión 23-06-2026:** no justifica suprimir requisitos nuevos ni reglas de seguridad. Sí cuestiona mantener resúmenes genéricos que el agente puede deducir del código. El estudio no evalúa todos los atributos de calidad. [R01](https://arxiv.org/html/2602.11988v2)
- **Observaciones y resúmenes:** la sencillez merece un brazo de control. Un resumidor puede añadir turnos y ocultar señales de fallo; no tiene por qué superar una política básica de ocultación con acceso al original. [R02](https://arxiv.org/html/2508.21433v3)
- **Benchmarks comerciales de ahorro:** los ensayos de JetBrains muestran por qué deben medirse tareas enteras y no extrapolar diferencias entre una salida bruta y su versión filtrada. La ausencia de diferencia significativa de calidad no demuestra equivalencia. [S06](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/)

## Diseño de evaluación recomendado

Mantener cuatro capas y no presentar sus resultados como intercambiables:

| Capa | Qué demuestra | Qué no demuestra |
|---|---|---|
| Integridad determinista | Resolución de referencias, cobertura conocida, vigencia y procedencia | Comprensión ni completitud de prosa ambigua |
| Simulación de selección | Qué desaparece al recortar; coste de las representaciones | Calidad de una implementación por un modelo |
| Implementación ciega con pruebas independientes | Cumplimiento de comportamientos observables en las tareas ensayadas | Seguridad general, mantenibilidad ni todos los dominios |
| Piloto repetido y revisión humana | Efecto dentro del flujo real y fallos por contexto | Garantía para modelos o proyectos no ensayados |

Usar tareas heterogéneas: excepciones remotas, negaciones, reglas globales sin enlace, términos homónimos entre módulos, unidades y redondeo, Unicode e idiomas, fechas y zonas, aislamiento de tenants, transacciones, autorización frente a implementación, contratos visuales, interfaces de terceros, migraciones, consumidores indirectos, pruebas alejadas, cambios durante la ejecución y evidencia antigua que vuelve a ser relevante.

Añadir negativos reales: no existe archivo relevante, no hay evidencia suficiente para decidir, una regla quedó sustituida, la tarea pertenece a otro perfil o un dato solicitado no aparece. Los negativos sintéticos fáciles no calibran por sí solos una abstención fiable. [R03](https://arxiv.org/html/2607.24882v1)

Comparar por lo menos: flujo actual, lectura selectiva competente, selector determinista conservador y propuesta optimizada. Para historial, añadir ocultación simple y resumen como brazos separados. Para formato, usar la misma selección y cambiar únicamente la representación. Así no se atribuye al formato un ahorro producido por eliminar obligaciones.

Preparar pruebas desde fuentes completas y ocultas al generador; separar ajuste y evaluación por repositorio o clase de problema. Registrar cada regresión por severidad, incluyendo los casos que el baseline resuelve y el candidato pierde. Contar compilaciones bloqueadas y recuperaciones como resultados operativos, nunca como implementaciones correctas. Repetir tareas y presentar intervalos, diferencias pareadas y resultados por familia; un promedio puede ocultar un fallo crítico.

## Propuesta mejorada derivada

Construir primero un **proveedor de evidencia por tarea con núcleo normativo protegido**, política explícita de ampliación y conservación de fuentes. La optimización debe buscar representaciones más baratas entre candidatos comprobados, sin imponer un ratio fijo. Si no se puede demostrar aplicabilidad o cerrar contexto, ampliar o declarar la incertidumbre; nunca rellenarla por inferencia silenciosa.

Orden de incorporación: inventario y medición real; extracción literal con cobertura; selección de código y salidas exactas; reanudación con estado estructurado; comparación de representaciones; solamente después, selección aprendida de material auxiliar. La ejecución determinista fuera del modelo puede aplicar el principio de RLM y procesamiento previo sin añadir MCP, hooks ni agentes ejecutables al plugin. La poda neural, los slots latentes y la edición del historial del host son líneas separadas que requieren capacidades y evaluación propias.
