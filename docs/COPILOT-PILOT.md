# Piloto guiado: plugin LKS-SDD en Copilot

Este recorrido conserva el workflow 1.5. Para aceptar la versión 2 use el
[protocolo v2 por host](V2-HOST-ACCEPTANCE.md) y sus [workflows](V2-WORKFLOWS.md).
Instalación, aceptación conversacional y publicación tienen evidencias distintas.

Objetivo: comprobar tanto instalación como comportamiento, sin usar un proyecto real.
No basta con que aparezca el plugin: hay que observar que lee las instrucciones,
conserva decisiones y respeta límites. Requiere VS Code/Copilot autorizados y Python 3.11+.

## Preparación

Utiliza una carpeta corta para el plugin, como `C:\LksPilot\lks-sdd`, y otra para
el consumidor, como `C:\Dev\reservas-piloto`. No las confundas. Sigue el registro
local de [instalación](INSTALLATION.md). No cambies políticas corporativas.
Anota versión de VS Code, Copilot, modelo elegido, versión/digest del paquete y fecha;
no registres datos personales ni credenciales. El piloto puede consumir cuota normal
de Copilot/Codex y de sus herramientas; el plugin no añade una API de imágenes.

## Recorrido y resultado esperado

1. **Descubrimiento.** Abre el consumidor y un chat nuevo. Comprueba las seis skills
   en la interfaz. Pide «Explícame LKS-SDD sin modificar archivos». Esperado: explicación
   comprensible, ninguna inicialización. Prueba también `/lks-sdd:lks-sdd-help`.
2. **Preparación del proyecto.** Pide inicializar LKS-SDD. Revisa la vista previa antes
   de autorizar. Esperado: runtime y lock, sin aplicación inventada ni commit/push.
   El lock tiene `entrypoints: plugin`; no aparecen seis duplicados en `.github/skills/`.
3. **Definición.** Pide definir reservas de salas, sin programar. Contesta algunas
   preguntas y deja otra pendiente. Esperado: hechos y propuestas separados, sin
   convertir lo desconocido en una decisión. No se elige una pila automáticamente.
4. **Imagen.** Pide explorar la interfaz. Esperado: ficha de relevo e invitación a Codex,
   sin API key ni generación nativa desde Copilot. No repetir la invitación cada turno.
5. **Relevo.** Abre el mismo proyecto secuencialmente en Codex con el acceso necesario.
   Pide continuar la ficha. Genera una imagen, solicita una corrección y elige una
   alternativa. Esperado: assets reales, procedencia y aprobación documentadas.
6. **Retorno.** Vuelve a un chat nuevo de Copilot. Pide estado y continuación. Esperado:
   valida lo recibido, reconoce la selección y no interpreta esa aprobación como
   permiso para implementar. Repite el caso permaneciendo en Codex en lugar de volver.
7. **Cambio posterior.** Modifica expresamente un requisito relacionado con el prototipo.
   Esperado: detectar la necesidad de reconciliar; no reutilizar ciegamente la imagen.
8. **Trabajo autorizado.** Completa decisiones y planificación. Autoriza una TASK
   pequeña. Esperado: implementación acotada, verificación separada de aceptación,
   sin despliegue ni escritura remota implícitos.
9. **Otro compañero.** Transfiere mediante Git autorizado a otro clon con el plugin.
   Esperado: misma versión del runtime y estado reconstruido sin compartir chats.
10. **Actualización personal.** En una prueba aislada usa un plugin más reciente sobre
    un proyecto fijado. Esperado: mantiene el núcleo fijado, no migra automáticamente.

Para verificación técnica desde la raíz del consumidor:

```powershell
$runtime = (Get-Content .lks-sdd/distribution-lock.json -Raw | ConvertFrom-Json).runtime
python "$runtime/scripts/lks_sdd.py" runtime-doctor . --json
python "$runtime/scripts/lks_sdd.py" visual-handoff status . --json
```

`runtime-doctor` debe devolver `valid`; esto no acredita los puntos conversacionales.
Después de materializar la especificación, añade `validate-project . --json`.

## Registro de resultados

Por cada paso registra: solicitud, respuesta observada, archivos cambiados, comando
y salida relevante, resultado (`passed`, `failed`, `not-run`) y decisión pendiente.
Conserva imágenes y referencias en el proyecto; sanea capturas antes de compartirlas.
Un fallo en descubrimiento, permisos o integridad detiene el paso afectado, no se
compensa diciendo que los tests unitarios pasaron. No se inventan aprobaciones.

La aceptación de equipo exige al menos tres desarrolladores con ambas herramientas
representadas. Navegador real y Jira/Rovo se prueban por separado cuando estén
autorizados y disponibles. Usa la matriz completa del
[plan](plans/2026-09-10-codex-copilot-implementation.md) para la aceptación final;
este recorrido es la entrada didáctica, no sustituye esos escenarios.
