# H2 — Operación concreta preparada, sin aplicar

**Estado operativo vigente (2026-10-16):** [carga A/B resuelta; aislamiento sin acreditar; recuperación de perfiles comprobada](RESULTS-H2-CONTINUATION.md). Ningún caso H2 iniciado, AC-34 pendiente. Se conserva estado nativo de Windows sin acreditar su reversión; no hay candidata activa. Los estados preparatorios e informes anteriores que siguen se conservan como antecedentes.

**Resultado posterior vigente:** [H2 inconcluso y perfiles recuperados](RESULTS-H2.md).
El usuario autorizó la ejecución del plan 0.3; la carga falló antes de abrir casos.
La secuencia siguiente conserva el plan aprobado como antecedente. No hay ahorro
acreditado ni instalación candidata activa.

Fecha: 2026-10-16. Revisión 0.3 de la preparación H2; no modifica el plan funcional
0.4 ni el protocolo 1.0. Codex CLI interactivo y prioridad H2 **validados por P01**.
Estado al aprobar el plan: tiempo conciliado; ejecución aún no autorizada entonces.
No se ha instalado, registrado una versión, activado el catálogo ni iniciado H2.

## Operaciones revisables

Área existente:
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\h2-plan`.
Se han extraído los paquetes en `r/a/s/lks-sdd` y `r/b/s/lks-sdd`, preparado los
catálogos `r/a/m` y `r/b/m`, y creado dos CODEX_HOME vacíos `r/a/h` y `r/b/h`.
Son materiales de preparación, sin instrucciones cargadas por un agente medido.
Máxima ruta de los materiales extraídos: **175 caracteres** en ambos brazos.
La caché futura, temporales y consumidores aún requieren su comprobación separada.

| Brazo | Plan del gestor, solo preparación/catálogo | Huella del plan |
|---|---|---|
| A | `C:\AI-Workspace\extensions\_management\operations\41ab623cdc094b81b880be4632da5474\plan.json` | `db0c5069039368dc1dd588c81d2d98bae572f8087ff221b8c0d87eaac076b34b` |
| B | `C:\AI-Workspace\extensions\_management\operations\198400ac39fd47629782f58748e0371a\plan.json` | `da61d80d728a25d68d1a5c2a572da5a71659b8b5de2c399c3d496a4e697dd34d` |

Ambos planes tienen autorización `review-only` y **no se han aplicado**.
Las dos únicas acciones de cada uno son copiar un paquete exacto a su destino
inmutable y añadir el catálogo en su perfil aislado; no incluyen instalar el plugin.

| Brazo | Destino inmutable futuro, todavía inexistente | Hash completo del árbol |
|---|---|---|
| A | `C:\AI-Workspace\extensions\lks-sdd\packages\3.4.3\e12b37f54685bd74` | `e12b37f54685bd7499fee78da2a29e96f74e0b470ab771da9b7dae5789a75944` |
| B | `C:\AI-Workspace\extensions\lks-sdd\packages\3.4.3\ed237c8c25b29ece` | `ed237c8c25b29eceb9ff30cf207a6abb898635b160a97b48fe7ca69260308a07` |

Las huellas del árbol del gestor incluyen nombres/directorios y son distintas de
las huellas ZIP y del digest de runtime. Estas últimas siguen en H2-LOAD-PLAN.md;
no sustituirlas por el número de versión compartido 3.4.3. No son publicaciones.

`concrete-load-operations.json` enlaza cada plan, catálogo, perfil y solicitud.
`r/a/register-request.json` y `r/b/register-request.json` contienen los registros
privados **todavía no aplicados**. `load-stage2-request.json` en cada brazo contiene
la solicitud exacta de instalación futura, también sin aplicar.

## Secuencia futura, condicionada a admisión y autorización separada

1. Usar el presupuesto conciliado y revalidar su saldo antes de cargar. Confirmar hashes
   ZIP, árbol, plan, cliente y contenido del destino; si cambian, regenerar el plan.
   Capturar solo configuración habitual relevante, excluyendo autenticación.
2. Crear cada proceso hijo con su CODEX_HOME exacto y
   `EXTENSION_MAINTENANCE_CODEX` apuntando al cliente de `h2-load-plan.json`.
   No modificar el entorno del proceso padre. Comprobar estos valores antes de
   invocar el gestor; los planes no incorporan por sí solos el destino CODEX_HOME.
   Nunca aplicar estos planes desde el perfil por defecto ni invocarlos a mano
   prescindiendo de esas comprobaciones.
3. Usar exclusivamente `C:\AI-Workspace\extensions\bin\extensions.ps1 -Recovery`.
   La huella del archivo de recuperación fue verificada antes de preparar los
   planes. La copia activa presenta drift; no se ha reparado ni se utilizará para
   ejecutar acciones. Revalidar la recuperación antes de cualquier aplicación.
4. Tras autorización, aplicar el plan de etapa 1 de A con el entorno A y el de B
   con el entorno B. Comprobar paquete y catálogo resueltos, y registrar únicamente
   los nuevos registros exactos de estudio. No redirigir el recurso marketplace
   personal existente ni registrar B como actualización publicada de 3.4.3.
5. Generar entonces, en el mismo entorno, el plan de instalación a partir de cada
   `load-stage2-request.json`, y revisar sus precondiciones antes de aplicarlo.
   **No se ha generado aún**: el gestor necesita observar el catálogo ya enlazado
   y el paquete registrado. Fabricar ahora sus precondiciones produciría un plan
   ficticio. No usar instalación directa para evitar esta dependencia.
6. Instalar mediante la operación oficial del gestor dentro del alcance autorizado.
   Comprobar listado, origen real, seis skills, bytes instalados y runtime exactos;
   no tocar manualmente las cachés. Comprobar aislamiento de herencia y lecturas,
   permisos del brazo propio y denegación del otro, sin llamadas al modelo.
7. Preparar consumidores equivalentes desde el estado inicial preservado. Mantener
   todos los contratos/adjuntos/controles y la autoridad ya vigente, con código
   inicial Adios. Verificar longitudes previstas de caché/temporales/Git y ausencia
   de contaminación. Si no se prueba aislamiento, recuperar sin empezar W1.
8. Abrir dos sesiones interactivas nuevas con `--no-daemon`, A y B, modelo
   gpt-6.1-sol/xhigh. Registrar W1 íntegra desde el primer mensaje; ninguna lectura
   previa de instrucciones por los agentes medidos. Mantener todos los criterios
   y ventanas del protocolo: no repetir hasta obtener éxito ni eliminar fallos.
9. Recuperar los perfiles y comparar. Emitir AC-34 con garantías y métricas reales;
   cobertura final, S8, Copilot y aceptación funcional siguen separados.

La revisión preparatoria rechazó por identidad el catálogo `.github/plugin` del
ZIP: corresponde a Copilot. Se conservó el fallo y se usó como plantilla el catálogo
Codex verificado existente. Ningún catálogo erróneo fue registrado o aplicado.
No se ha ejecutado el caso ni gastado una plaza completa por esta preparación.

## Recuperación concreta

- Guardar los IDs de operación y sus journals antes de cualquier acción. Ante fallo
  de una etapa aplicada, comprobar journal y efectos antes de repetir. No deducir
  ausencia de efectos de la falta de una respuesta final.
- Cerrar solo los procesos propios de H2. Si se aplicó etapa 2, revertir primero
  esa operación con el mismo CODEX_HOME y cliente; verificar retirada del plugin
  aislado por la vía oficial. Después revertir etapa 1 y comprobar retirada del
  catálogo aislado. No retirar nada del perfil habitual.
- Los paquetes inmutables y la evidencia quedan conservados/referenciados hasta el
  cierre del estudio; no borrar directorios, cachés, credenciales ni registros para
  simular recuperación. La eventual retirada de referencias requiere cierre real.
- No restaurar un archivo global completo sobre cambios concurrentes. Si aparece
  un cambio inesperado en el perfil habitual, parar y presentar una recuperación
  limitada a efectos propios demostrados; conservar el material si no es posible.
- Inicio de sesión, si hace falta, en el perfil aislado; no copiar auth.json ni
  exportar secretos con la evidencia. Cerrar una sesión compartida no forma parte
  de la recuperación.

## Presupuesto y disposición vigentes (0.3)

La [conciliación temporal](TIME-RECONCILIATION.md) sustituye el bloqueo de la
revisión 0.2: Windows confirma tres periodos de espera moderna. Se descuenta
exclusivamente reposo profundo acreditado, conservando actividad, esperas técnicas,
fallos y calendario bruto. El informe original de 13,34 h se conserva como histórico;
no es la cuenta vigente del entorno ajustada.

Tras deduplicar 32 turnos y corregir solo 10.903,592044 s de indisponibilidad, el
cargo conocido es **10,411149 h**. Se reservan otros **10 min** para esta auditoría:
quedan **85,331034 min observados** frente a 12 h. H2 mantiene cota **45 min**:
10 preparación/carga, 10 A, 10 B, 10 recuperación protegida, 5 análisis. Después
quedan **40,331034 min comunes** para los demás bloques; no son reservas adicionales
por fase. La auditoría sustituirá su reserva por cargo real cuando cierre.

No se amplía el máximo, se reduce cobertura o se eliminan tareas. Mantener las seis
mejoras, S8 temprano/final, garantías, ambos hosts y Copilot al final, más contingencia.
La cuenta conocida/reservada sigue **45/48**, con las dos H2 ya incluidas. El saldo
corresponde al registro observado; no certifica históricos externos desconocidos.

**H2 cabe en esta cuenta; la viabilidad integral del resto de 4.0 no está acreditada.**
Conservar pendientes si no caben, sin declarar una release completa. Antes de cada
bloque, actualizar el ledger y reservarlo completo. No usar el ajuste de suspensión
para mejorar las métricas W1/W2/S8: los intentos afectados conservarán tiempo bruto
y clasificación según el protocolo congelado.

CLI interactivo y prioridad H2 siguen validados. No hace falta repetir esas decisiones
ni cronometrar esfuerzo humano. Los dos planes de primera etapa siguen sin aplicar;
las solicitudes de segunda etapa requieren el estado real posterior. Carga,
instalación, recuperación operativa y ejecución de los casos siguen pendientes de
la autorización separada y de comprobar todas las precondiciones técnicas.
