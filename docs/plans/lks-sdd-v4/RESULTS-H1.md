# LKS-SDD 4.0 — Resultados de V4-01 y V4-02

Fecha inicial: 2026-10-15. Actualización crítica: **2026-10-16**.
Plan [0.2](PLAN.md), validado por el usuario en esta conversación.
Decisión posterior vigente: **[valoración humana diferida a uso real sostenido](DECISION-TECHNICAL-SCOPE.md)**.
La repetición cronometrada se preparó y retiró sin iniciar casos. No se solicitan
fichas, tiempos ni cuestionarios. **V4-02/AC-33 cerrados en alcance técnico Codex**
con [protocolo de comparación 1.0](MEASUREMENT-PROTOCOL.md); no hay candidata ejecutada.
La autorización recibida cubre V4-01/V4-02 y exige presentar resultados/pendientes
antes de implementar cambios del plugin. No autoriza V4-03 ni fases posteriores.

## 1. Decisión de sesión y procedencia

Se registra la instrucción exacta: «Valido el plan 0.2. Empieza por V4-01 y V4-02 y
presenta los resultados y decisiones pendientes antes de implementar cambios en el
plugin». La aprobación procede del usuario de este chat; no se infiere una identidad
de Git/Windows ni se crea un miembro ficticio de un consumidor real.

Actualización de 2026-10-16. Continuación autorizada: «Continúa con Codex y deja Copilot pendiente al final.
Acepto los límites de presupuesto propuestos. Avanza en V4-02 y dime qué necesitas
de mí para medir el esfuerzo humano. No implementes todavía». El usuario responde
«Yo» al elegir participante del piloto. Se registran Codex inicial, Copilot aplazado,
los límites aceptados y P01 como etiqueta del participante. No se amplía a V4-03.

HEAD sigue siendo `bf4d059c98826039097d606121ab6406d762fcc7`. Al empezar solo estaban
los tres documentos del plan como archivos locales no versionados. La copia exacta
del plan validado y sus hashes se conservan en el área de evidencia externa descrita
en [BASELINE.md](BASELINE.md). Las actualizaciones de estados no cambian su alcance.

## 2. Entregables

| Tarea | Resultado | Estado y límite |
|---|---|---|
| V4-01 | [Contrato operativo](CONTRACT.md): interfaces, efectos, vigencia, fallos, recuperación, formatos y mapa G1–G10. | Entrega documental verificada; no implementación ni aceptación de una candidata. |
| V4-02 | Referencia 3.4.3, viabilidad, siete escenarios, revisión S1/S2 y protocolo 1.0 con ventanas/umbrales/ruido/recursos. | Cerrado en alcance técnico Codex. Percepción humana diferida, Copilot al final, tokens históricos mixtos no comparables y factura no medida. |
| V4-03 y posteriores | Sin ejecución. | No autorizadas en este encargo. |

## 3. Decisiones técnicas concretadas dentro del plan

1. Conservar método **3.1.0** y esquema **3.1**: las nuevas operaciones adaptan
   consultas y transiciones existentes. La compatibilidad de implementación/actualización
   se demostrará posteriormente, no se presume superada por este contrato.
2. Mantener comandos existentes; proponer `work-prepare`, `work-continue` y
   `work-record-results` en el CLI común con sobres operativos versionados. Los nombres
   son diseño documentado y todavía no son comandos disponibles.
3. Componer inicialmente por etapas con los guards y recibos actuales; no prometer
   atomicidad de pruebas, ediciones ni servicios. No recoger decisiones humanas nuevas
   mediante flags implícitos de una operación agrupada.
4. Captura diagnóstica externa y explícita; sin configuración no hay escritura oculta.
   Mantener límites y grado de confianza de importaciones. No agregar autoridad al
   proyecto mediante un índice diagnóstico ni silenciar corrupción canónica anterior.
5. M3 mantiene exclusiones acreditadas y ampliación conservadora; no cambia la
   invalidación del gobierno para ahorrar. M5 debe demostrar una mejora sobre los
   recorridos existentes, normalmente mediante M2/M4. M6 puede terminar sin cambios.

Estas decisiones concretan el diseño compatible. Si las pruebas futuras revelan
que la correlación de etapas o la compatibilidad exigen cambiar significado/formato
canónico, se presentará la diferencia antes de implementar el escritor afectado.

## 4. Hallazgos de referencia

Los resultados cuantitativos están en [BASELINE.md](BASELINE.md) y el
[manifiesto de evidencia](h1-reference.json). Son mediciones de la base, no ahorro de 4.0.

- El CLI agrega diagnóstico que puede repetir contenido; se mide stdout completo,
  no solo el contador interno que excluye el sobre: 20.136 B en contexto pequeño y
  62.961 B con prosa desconocida, con incrementos diagnósticos del 34,99 % y 45,29 %.
- La corrección sintética se comprobó realmente y terminó cerrada técnicamente;
  las consultas no mutaron el consumidor y la raíz inválida quedó bloqueada.
- La conservación diagnóstica produjo diez objetos/10.152 B; dos reproducciones en
  frío y un caso temprano inspeccionable. La confianza importada se mantuvo limitada.
- Las instrucciones de la base ya son progresivas: doce rutas, 3–6 archivos y
  10.065–18.990 caracteres. M4 se compara con ese uso correcto.
- Codex expone contadores reales en el registro de esta conversación; su disponibilidad
  y atribución por turno quedan comprobadas: 48 respuestas únicas de un turno cerrado
  suman exactamente su contador final. No se atribuye ese turno preparatorio a S1/S2.
- Copilot no tiene observación real en esta fase. No encontrar su CLI en PATH no
  prueba que no exista en otros clientes; tampoco acredita su métrica de consumo.
- P01 participó en S1/S2 y confirma «No los cronometré». No hay minutos activos
  medidos; feedback retrospectivo todavía pendiente. Menos llamadas no acredita
  menor tedio; la duración del chat no sustituye esa comprobación.
- S1 conserva resultado real conforme; S2 conserva 22 comprobaciones conformes
  (20 automáticas y dos revisiones del asistente), código/evidencia concordantes y
  668 archivos del runtime S2 sin cambios. No hay revisión independiente ni aceptación.
- S1 confirma un defecto del renderer de `usage-report`; S2 rectifica una atribución
  anterior: el auxiliar usó `ids` en vez de `units`, sin defecto demostrado del plugin.
- S2: ocho candidatos UF-01 corresponden a tres conjuntos de observaciones
  parcialmente solapados; no son ocho defectos. Los dos huecos `prepared` de `author`
  tienen observaciones `applied` de la misma invocación ya vinculadas. Se conserva
  su limitación provisional; no prueba pérdida de obligaciones.

## 5. Criterios de esta fase

| Criterio | Dictamen | Evidencia y límite |
|---|---|---|
| AC-01 | Verificado documentalmente. | CONTRACT.md define las operaciones, ejemplos válidos/negativos, efectos, paradas y recuperación. No acredita que existan implementadas. |
| AC-02 | Decisión de diseño documentada. | Se conservan método/schema; formatos operativos externos separados y restricciones de runtime. AC-24/25/26 siguen pendientes de implementación. |
| AC-03 | Verificado estáticamente. | Contrato 3.4.3 válido, seis skills y diff sin servicios/conectores/hooks/agentes/entrypoints nuevos. El auxiliar de observación vive bajo este plan, fuera del runtime. |
| AC-33 | Verificado; cierre técnico Codex. | Fuente/paquetes y capturas contrastados; alcance explícito; MEASUREMENT-PROTOCOL.md/JSON 1.0 fija ventanas, métricas, responsables, umbrales, presupuesto y paradas antes de candidata. No acredita ahorro ni uso humano. |
| Resto de AC de 4.0 | `not-run`. | Las capturas de 3.4.3 y los controles documentales no acreditan la candidata. |

H0 registra aprobación del plan y autorización limitada. **H1 preparatorio completo
en alcance técnico Codex**: V4-01 entregada y V4-02/AC-33 cerrados técnicamente;
no se cambia el estado de las tareas del runtime del plugin. El piloto usa únicamente
un consumidor sintético externo, con historial de fixture declarado como tal.

## 6. Decisiones y evidencia pendientes antes de V4-03

| ID | Decisión/evidencia necesaria | Recomendación | Consecuencia si falta |
|---|---|---|---|
| H1-D1 | Codex primero, Copilot al final. S1: 16 respuestas, 1.584.190 tokens. Cinco turnos S2: 54 respuestas, 11.487.304 tokens; 11.097.472 de entrada cacheada ya incluida. Todas las sumas por turno coinciden con sus contadores finales. | Cuenta técnica consolidada; ventanas mixtas, primera ventana S2 incluye contabilidad S1. Preparar referencia con contexto y ayudas comparables antes de candidata. | No hay coste funcional aislado ni facturado. No comparar S1 con S2 ni atribuir todo al plugin. Copilot sin observar. |
| H1-D2 | Resuelto el alcance: percepción/esfuerzo humano se evaluarán en uso real sostenido. Repetición preparada, retirada sin iniciar. Tiempos históricos no medidos; experiencia de P01 habitual. | No pedir fichas, cronómetros ni cuestionario experimental. Conservar material y costes; decisiones funcionales siguen vigentes. | `delta_admin`/E5/AC-36 diferidos, sin `passed`; ya no bloquean el cierre técnico AC-33. No se declara menor tedio. |
| H1-D3 | Resuelto el presupuesto: 48 ejecuciones, 8 h de persona, 12 h de entorno; M6 dos variantes/cuatro horas dentro de los globales. | Registrar consumo y aplicar primero el límite más restrictivo. Los techos no son una previsión de duración ni autorizan implementar. | Ampliar recursos requeriría decisión nueva; no se vuelve a pedir la aceptación ya recibida. |
| H1-D4 | Resuelto: W1 desde primer mensaje de chat nuevo hasta turno técnico cerrado, incluidas instrucciones; H2 10 %/8 KiB y una llamada menos, sin crecimiento B_flow; M6 ≥5 s/>2×MAD/5 de 6 positivos/medianas por orden positivas. | Protocolo 1.0 congelado antes de B. `delta_admin` diferido. | Comparaciones futuras obligadas a ese protocolo; cambio posterior no convierte fallos en éxito. |

E1/E2/E3 conservan los objetivos del plan ya validado; no se solicita aprobarlos
otra vez ni se presentan como promesas. La autorización para cargar una futura
candidata en un host se concretará antes de H2. Ninguna de estas propuestas amplía
por sí sola la autorización actual a modificar o instalar el plugin.

La prueba de extracción y el estado operativo se registran en
[v4-02-progress.json](v4-02-progress.json). No se necesita otra aprobación de host
inicial o presupuesto. Los ejercicios históricos se ejecutaron; los dos consumidores
de repetición solo se prepararon. La decisión del usuario resuelve el alcance humano:
queda diferido a uso real sostenido. No se requieren más datos de P01 para el cierre
técnico; ventanas/umbrales fijados antes de observar candidata, en protocolo 1.0.
El cambio de alcance no acredita ahorro ni autoriza implementar el plugin.

## 7. Verificación y continuidad

Se han revisado contrato estático, diff, enlaces, referencias de tareas/AC,
integridad de escenarios y doce hashes de evidencia más el archivo fuente. Se ha
comprobado que solo cambien documentos y
el auxiliar de medición del plan; scripts, schemas, skills y fuentes canónicas del
plugin permanecen intactos. El contrato estático devuelve `VALID` para 3.4.3 y seis
skills; las diez garantías conservan su texto literal. No se ejecuta gate de release,
build, commit o publicación.

Los intentos de instrumentación fallidos, sus salidas y causas se conservan en el
área externa y se contabilizan como preparación, no como tareas completadas baratas.
La evidencia final distingue errores del auxiliar/fixture de defectos demostrados
del plugin. No se cambia producto para conseguir una referencia favorable.

Se presentan estos resultados con V4-02 cerrado en alcance técnico Codex según la
sección siguiente; implementar V4-03 requiere autorización posterior.

## 8. Cierre técnico de V4-02

El encargo de concretar ventanas y umbrales cierra AC-33 en el alcance decidido.
Evidencia y congelación documental en el área H1 existente:
`C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/v4-02-closure-20261016/`.
Propietario: tarea actual de mantenimiento; retención heredada mientras esté referenciada.
Se conservan fuentes, hashes y estados anteriores. El cierre no acredita candidato,
ahorro, percepción humana, Copilot ni saldo presupuestario histórico exacto.

V4-03 y posteriores siguen sin autorización. No se ha cambiado el plugin, preparado
una release, instalado, activado, creado commit ni publicado nada en esta fase.
