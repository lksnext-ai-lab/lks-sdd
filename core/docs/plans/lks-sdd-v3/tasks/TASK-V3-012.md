# TASK-V3-012 · Migración: aplicación, recuperación y continuidad

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de migración**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-011](TASK-V3-011.md).
Dependencias para cerrar: [TASK-V3-009](TASK-V3-009.md), [TASK-V3-011](TASK-V3-011.md).

Requisitos de responsabilidad principal: REQ-EQT-056, REQ-EQT-057, REQ-EQT-058.
Casos de aceptación principales: AC-EQT-064, AC-EQT-065, AC-EQT-066, AC-EQT-067, AC-EQT-085, AC-EQT-086, AC-EQT-087.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Continuidad que debe verificarse expresamente
Al convertir una dependencia v2 sin tipo, conservar su exigencia anterior hasta una
decisión explícita; no transformarla por defecto en “contrato validado” para habilitar
trabajo antes. Conservar también extensiones, declaración tecnológica, evidencia y
restricciones relevantes del plan.

Comprobar que el runtime fijado y los writers activos son coherentes después del corte;
conservar bytes del runtime/documentos necesarios para recuperación, sin usar un lector
antiguo como writer sobre v3. Probar una segunda interrupción durante recuperación y
cambios posteriores, además del camino satisfactorio. 013 participa en la comprobación
de estado aplicado/pendiente, no solo en la vista previa.

## Encargo y límites
Aplicar una migración concreta autorizada y recuperable, conservar originales e historia,
y reconciliar trabajo abierto y ramas antiguas. Trabajar sobre copias de prueba; ninguna
aprobación de este plan autoriza migrar proyectos reales del usuario.

## Entregables e interfaces
- Completar `scripts/v3_migration.py` sobre 011 y almacenamiento 002; journal, recibo,
  mapa de correspondencias y validación final de formatos, referencias e inventario.
- Congelar el ámbito de escritura durante el corte acordado. Base distinta invalida
  la vista; reintento usa los mismos UID y decisiones.
- Continuidad mediante 009: propuesta/plan exactos conservados, decisiones originales
  reutilizadas solo con correspondencia acreditada y AUTH nueva si cambia su contrato.
- Mapa único desde rama/base acordada; incorporar ramas v2 tardías sin segunda
  asignación independiente de identidades. Writers incompatibles rechazan el checkout v3.
- Recuperación específica si hay trabajo posterior; rollback no sobrescribe ni convierte
  nuevas TASKs v3 en tareas válidas v2 por restaurar archivos.

## Aceptación y evidencia
Aplicar/interrumpir/recuperar en cada frontera material conserva originales byte a byte,
código de negocio, evidencia y trabajo posterior. Todas las fuentes quedan contabilizadas.
Reaplicar no crea entidades duplicadas. Método 2.0 con aprobación activa ausente pide solo
revisión necesaria; 2.1 con aprobación recuperable conserva negocio y renueva solo permiso
operativo aplicable. Una tarea cerrada no se reabre. Una rama antigua se reconcilia con
el mapa común y su historia permanece. Entregar comparación antes/después, fault injection,
mapa, recibos y demostración de reanudación sin regenerar el plan.

## Riesgos y revisión
No afirmar corte completo ante mezcla parcial ni bloqueo de clones desconectados.
Revisión de almacenamiento, gobierno e integración Git. Lectura adicional: 011 y sus
muestras, técnica §§9.2–9.5; resultados de 007/009.
