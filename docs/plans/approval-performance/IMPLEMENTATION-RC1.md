# Implementación de la corrección de rendimiento

Fecha: 2026-10-14. Candidata: **3.4.3-rc.1**.
Rama: `codex/approval-evaluation-performance`.
Base: `a657bf7b07461c8b03516f9adbb00bb7a6b9ed7c`, contrastada con `origin/main`
mediante `git ls-remote` durante esta ejecución. El árbol contiene cambios locales;
no existe un commit ni un paquete de release acreditado de esta corrección.

## Cambios y decisiones

El [plan autorizado](PLAN.md) se implementa en la fuente del plugin. No se modifican
consumidores, instalaciones, caches oficiales ni `specs/canonical/`.

- `v3_contract.Model`: índices multivalor de identidad y tipo. Observación de cambios
  de mapas/metadatos mediante referencias débiles; resolución cualificada y errores
  originales conservados. Sin memoización negativa.
- `v3_evaluation`: ámbito anidable por objeto de modelo, hilo y tarea asíncrona;
  comprobación del contenido completo antes de devolver resultados, admisión acotada
  y liberación incluso por excepción. No cruza comandos.
- `v3_scope` y `v3_approval`: clasificación, cierre global y descriptores compartidos;
  copias defensivas de resultados públicos. La clave de admisión cuenta también los
  identificadores de consulta. No se cachea la autoridad de una persona entre comandos.
- `v3_migration`: originales leídos/analizados por ruta y hash esperado, con cada
  soporte físico conservado. Las decisiones y correspondencias se comprueban por
  unidad, también cuando dos rutas contienen los mismos bytes.
- `v3_workflow`: ámbito compartido de hechos y evaluación de petición. Se conserva
  `all(technology-approved(key) or proposal-approved(key) for key in technologies)`.
- Metadatos y documentación: candidata correctiva sincronizada, sin inventar una
  aprobación de release estable, etiqueta remota ni instalación.

Las entradas, presupuestos, invalidación, concurrencia y materialización se detallan
en [APPROVAL-PERFORMANCE.md](../../APPROVAL-PERFORMANCE.md). Se reutilizan los guards y
la recuperación existentes. La reutilización no reduce el contexto ni obligaciones.

## Corrección y procedencia

La referencia 3.4.2 conserva cinco módulos en un ZIP exclusivo de pruebas, con
inventario y SHA-256. Se ha contrastado cada archivo contra `git show` del commit
base: **5/5 coinciden**. Los workers no mezclan imports de ambas versiones.

La comparación controla UUID, reloj de generación, semilla de conjuntos Python y
rutas de los fixtures. No elimina campos, errores, hashes, fuentes ni decisiones.
El orden de conjuntos se fija mediante `PYTHONHASHSEED=0`, también para los paquetes
de integración. Una modificación de un original conserva el resultado negativo
de aprobación del runtime original; su detección no se convierte en un nuevo error.

Las [nueve pruebas focales](evidence/equivalence.json) incluyen comparación diferencial,
ambigüedades/colisiones, mutadores de identidad, revisiones, revocación, permisos,
originales modificados/ausentes/inconsistentes, obligaciones inciertas, dependencias,
lecturas físicas distintas, mezcla de aprobaciones tecnológicas, aislamiento entre
modelos/proyectos/revisiones/hilos/tareas asíncronas, liberación de memoria temporal
e importación aislada del módulo desde el conjunto de distribución de desarrollo.
Modificar un original tras una lectura compartida bloquea la preparación posterior.

Las regresiones existentes ejecutadas se conservan en:

- [Workflow y migración](evidence/workflow-migration.json): 13/13.
- [Pruebas restantes del núcleo](evidence/core-remaining.json): 10/10; junto con cuatro
  casos del grupo anterior cubren las catorce pruebas declaradas por la puerta técnica.
  El [núcleo completo](evidence/core-final.json) también se ejecutó en una sola pasada: 14/14.
- [Rutas largas de Windows](evidence/windows.json): 1/1, tras sincronizar marcadores de
  versión y ejemplo de piloto.
- [Operaciones agrupadas y aceptación previa](evidence/grouped.json): 2/2.
- [Obligaciones globales, inventarios y reservas](evidence/guarantees.json): 3/3.

Estos resultados son comprobaciones de desarrollo sobre un árbol local. No son un
gate de release vinculado al commit final. Los casos que utilizan transacciones,
configuración, permisos, calidad, originales, estados con reservas y aceptación
separada no se han sustituido por mocks para obtener mejores tiempos.

## Mediciones

La [matriz completa](evidence/measurement.json) contiene **18 pares equivalentes y
378 mediciones**: tres repeticiones de 100/5, 500/15 y 1.500/35, en cálculos y ciclo
público de biblioteca. La consolidación exige las seis huellas del código final y
compara íntegros los resultados de cada pareja. Las iteraciones anteriores quedan
fuera de la entrega. Se conservan muestras, rango/mediana, CPU, memoria y contadores.

El fixture de cálculos usa un archivo por elemento; el del ciclo público agrupa el
volumen adicional en un Markdown canónico multibloque. Se mantienen todos los
elementos y su contexto literal. Cada pareja usa el mismo fixture físico y las
mismas rutas absolutas. El volumen solicitado 1.500/35 corresponde a 1.502 elementos
en la evaluación actual y 1.501 en la heredada, tras añadir sus decisiones/recibo.

En las tres repeticiones de 1.500/35 los contadores son iguales:

| Trabajo | Referencia 3.4.2 | Candidata |
|---|---:|---:|
| Entradas recorridas para resolver 3.004 UID/alias, con modelo cargado | 4.512.008 | 0; consultas directas |
| Reconstrucciones de descriptores/pertenencias, aprobación actual | 52 | 1 |
| Reconstrucciones de descriptores/pertenencias, aprobación heredada | 910 | 1 |
| Lecturas y análisis de originales, aprobación heredada | 70 / 70 | 2 / 2 |

Las dos rutas originales contienen los mismos bytes y ambas se verifican. La
construcción de índices se mide dentro de la carga y cuando se necesita por primera
vez; la resolución aislada de identidades utiliza el modelo ya cargado.

Se ejecutaron nueve runners independientes de ciclos públicos y tres de cálculos en
paralelo. **Sus tiempos de pared son observaciones bajo carga compartida**, con orden
referencia → candidata. El descenso de carga entre fases y el calentamiento del
sistema impiden atribuir todo el cociente de tiempos al parche. Los contadores y
la CPU permiten separar la reducción de cálculo del comportamiento de I/O.

Medianas de CPU por operación completa, sumando preparación y aplicación de cada
muestra, para 1.500/35:

| Operación pública de biblioteca | Referencia (s CPU) | Candidata (s CPU) |
|---|---:|---:|
| Inicio | 29,969 | 10,719 |
| Implementación | 20,641 | 11,359 |
| Evidencia | 9,781 | 10,641 |
| Verificación | 17,328 | 12,281 |
| Cierre | 17,328 | 11,875 |
| Integración | 30,328 | 22,266 |
| Aceptación | 22,625 | 15,781 |

La ruta de evidencia registra más CPU en esta muestra; no todas las rutas mejoran.
Las fases dominadas por carga, comprobaciones y escritura no acreditan un ahorro
general de I/O. Las medianas/rangos de pared de todas las fases están en el JSON.

El pico máximo de proceso registrado en la matriz es **72,93 MiB → 77,80 MiB**.
Es un máximo acumulado del proceso, no un pico de asignación aislado de cada función.
Los working sets antes/después también se conservan. La candidata intercambia
memoria derivada y comprobaciones de inmutabilidad por menos recorridos repetidos.
No se afirma que liberar referencias obligue a Python a devolver sus arenas al SO.

La comprobación [aislada de 1.500/35](evidence/isolated-calculations-1500.json)
terminó con **3/3 pares equivalentes**, secuenciales, sin los otros runners activos,
en orden referencia/candidata, candidata/referencia, referencia/candidata.

| Cálculo aislado | Referencia, mediana (s) | Candidata, mediana (s) |
|---|---:|---:|
| Carga | 33,843 | 28,369 |
| Contexto completo | 1,063 | 0,157 |
| Resolución de 3.004 UID/alias | 1,481 | 0,00759 |
| Clasificación | 0,0562 | 0,00137 |
| Dependencias | 0,0857 | 0,0335 |
| 35 aprobaciones actuales, con mecanismos mixtos | 4,828 | 0,0898 |
| 35 aprobaciones heredadas | 59,427 | 0,1784 |

El rango de aprobación actual es 3,097–7,392 s → 0,0776–0,1488 s; el de heredada,
36,003–65,600 s → 0,1702–0,1804 s. La CPU mediana también baja: 4,078 → 0,0781 s y
52,297 → 0,1719 s respectivamente. Sus rangos separados, la CPU y los contadores
acreditan la reducción del cálculo repetido en este contrato sintético. La carga
mantiene rangos solapados (25,720–40,235 s / 26,803–28,841 s); no acredita una mejora
estable de I/O. El reloj de CPU de Windows no distingue con precisión algunas
operaciones ya muy breves, por lo que un valor cero no significa coste nulo.

```powershell
python -B -X utf8 tests/measure_approval_performance.py `
  --sizes 1500:35 --repetitions 3 --phases calculations --order alternating `
  --output output/approval-performance/isolated.json
```

La reproducción predeterminada del script es secuencial y alterna el orden. No se
extrapolan los 155 segundos/78 minutos comunicados ni se atribuye ahorro de tokens.

## Entrega y pendientes

AP-01–AP-06 completadas técnicamente en local: referencia conservada, índices,
reutilización, equivalencia, benchmark y candidata. **38 pruebas distintas pasan**;
contrato estático y 13 fixtures válidos. La [verificación resumida](evidence/verification.json)
conserva comandos y estados. El diff se revisa y el parche se comprueba antes de entregar.

Los riesgos y límites restantes son el coste de construir/observar índices, serializar
la huella de inmutabilidad y mantener estructuras derivadas, la variación de I/O y la
ausencia de medición del proceso CLI completo y de la conversación del asistente.
No se reutilizan cálculos en modelos que cambian durante la evaluación. Otras
topologías, textos/inventarios mayores y cargas reales requieren medición propia.

Commit, integración real, push, preflight
de árbol limpio, build acreditado, publicación, instalación y aceptación real de host
permanecen pendientes y separados; no están autorizados por esta petición.
