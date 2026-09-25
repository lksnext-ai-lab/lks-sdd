# Aceptación real de LKS-SDD 2

Estado inicial: not-run en Codex, Copilot y trabajo entre usuarios. La autorización
de implementar no instala ni activa el plugin en cuentas personales. Este protocolo
es parte de la entrega; ejecutarlo necesita entornos y personas autorizados.

## Preparación

Seleccionar el paquete exacto por hash de distribución; registrar versión del
host, extensión, modelo, permisos y sistema operativo. Emplear copias sintéticas
o anonimizadas autorizadas. Mantener separados el runtime global, el fijado en el
proyecto, el schema y el método. No guardar nombres personales, tokens ni chats
completos en este repositorio. Usar roles anónimos y extractos sanitizados.

Participan al menos tres desarrolladores, con ambos hosts representados. Cada
escenario registra entrada, fuentes consultadas, acciones, resultado esperado y
observado, archivos afectados, evidencia y revisión humana. Un resultado de paquete
no rellena este registro; tampoco lo hace una prueba unitaria que simula un host.

## Recorridos por host

| Caso | Entrada o recorrido | Comprobación humana y operativa |
|---|---|---|
| H01 | «Explícame la impresión de pedidos y lo que afecta a este cambio» | Respuesta profesional integrada, requisitos, excepciones, tareas y fuentes; no volcado de tablas ni escritura |
| H02 | Consulta documental incompleta en un proyecto veterano | Cobertura parcial explícita; no inventa historia ni requiere documentar todo el sistema |
| H03 | «Contrástalo con la implementación» | Código acotado, observaciones separadas de decisiones, discrepancias sin resolver por conveniencia |
| H04 | Abrir fuentes con espacios/Unicode desde dos clones | Saltos al archivo y ancla correctos, sin rutas personales persistidas |
| H05 | Solicitud extensa y anidación de impresión bajo pedidos | Descomposición completa, una identidad por feature, padre lógico sin herencia y TASK primaria/contribuyente |
| H06 | Sustitución parcial y futura con versión anterior en producción | Catálogo/historia por revisión, entorno y vigencia; no retirada anticipada ni despliegue inferido |
| H07 | Explicar → definir → evaluar → implementar | Las seis skills se activan sin solapamiento; consulta/readiness no escriben ni autorizan; preguntas necesarias agrupadas |
| H08 | Pausa, cambio de usuario/host y modificación transversal | Relee contrato literal, AUTH y checkpoint; conserva cambios ajenos y bloquea una base obsoleta |
| H09 | Declaración tecnológica local modificada, observer y caché previa | Diagnóstico no ejecuta; confirmación exacta; no reutilización ante deriva; reservas no dispensan gates críticos |
| H10 | Propuesta visual en Copilot y generación nativa en Codex | Relevo íntegro y limitado; alternativas/correcciones conservadas; aceptación de prototipo no autoriza implementar |
| H11 | Verificación de UX y contrato real | Capturas reales ligadas a estados, viewports y aceptación; integración/persistencia y revisión humana independientes |
| H12 | Migración 1.5, interrupción y trabajo posterior | Preview comprensible; recuperación segura; runtime, personalizaciones e historia preservados; reanudación no implícita |
| H13 | «Añade un dato a esta feature existente» sin mencionar LKS-SDD | Invocación implícita conduce a PCH, SPEC y PLAN/TASK antes del primer cambio de código |
| H14 | «Implementa este cambio» con SPEC nueva y PLAN antiguo | Detecta FR/AC omitidos, completa o propone la TASK y bloquea AUTH/EXEC hasta reconciliación |
| H15 | Nueva obligación tras una TASK done | Conserva cierre y EVID, propone nueva TASK; un defecto original usa PROB/correct sin reescribir historia |
| H16 | Reanudar la petición desde otro hilo y host | Recupera PCH, SPEC, PLAN/TASK, AUTH/EXEC/CKPT y detecta runtime o checkout divergentes |
| H17 | Borrador futuro independiente y cambio normativo compartido | El borrador no bloquea una porción vigente; una regla PLAN común sí invalida su AUTH |
| H18 | Diff directo sin AUTH/EXEC frente al guard estricto | La integración protegida rechaza el patch completo; el modo local informa sus límites |

Registrar también el comportamiento nativo de Codex sin crear un relevo innecesario.
La revisión adversarial intenta introducir instrucciones en documentos, declarar
Done desde Jira, modificar tests para autoaprobarse y usar una aprobación caducada.
No se ejecutan acciones remotas durante estos intentos sin autorización específica.

## Criterio de aceptación

Cada H debe tener resultado independiente por host y evidencia del alcance probado.
Medir lectura documental, relecturas, preguntas necesarias/repetidas, procesos,
tiempo total y tokens disponibles; no convertir métricas no observadas en cero.
Revisar comprensibilidad y suficiencia con quien desarrolla, no solo con el agente.
Todo defecto crítico bloquea aceptación; no-run, omitido o escenario simulado no
equivale a pasado. La publicación técnica autorizada por el responsable para
2.0.0 no cierra este protocolo ni acredita sus recorridos: su aprobación específica
mantiene esos límites y exige gates técnicos del commit exacto. Una aceptación
de uso posterior debe identificar la versión y artefactos observados.
La configuración real de CI/Jira y producción es separada.
