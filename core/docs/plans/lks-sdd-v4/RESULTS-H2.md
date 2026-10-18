# H2 — Carga intentada, recuperación verificada, comparación inconclusa

**Estado operativo vigente (2026-10-16):** [carga A/B resuelta; aislamiento sin acreditar; recuperación de perfiles comprobada](RESULTS-H2-CONTINUATION.md). Ningún caso H2 iniciado, AC-34 pendiente. Se conserva estado nativo de Windows sin acreditar su reversión; no hay candidata activa. Los estados preparatorios e informes anteriores que siguen se conservan como antecedentes.

Fecha: 2026-10-16. Plan H2 0.3 y conciliación aceptados; autorización explícita de
carga aislada, pareja AB y recuperación dentro de los **45 minutos existentes**.
Resultado: **preparación interrumpida antes de los casos; AC-34 pendiente**.
No se modifica código del plugin ni se inicia V4-06.

## Resultado y efectos reales

P01 completó los accesos de A y B. Se verificaron sin exportar credenciales.
Se conservaron los ZIP exactos aprobados y el perfil habitual. Para A se copió el
paquete inmutable, se registró su referencia privada de estudio y se dio de alta
el catálogo local en su CODEX_HOME. No se completó la instalación del plugin.
B no llegó a copiarse al destino inmutable, registrar catálogo o instalarse.

La instalación A falló en el gestor de recuperación con
`Marketplace unavailable or ambiguous`. El listado oficial del cliente mostraba
el catálogo aislado y su ruta correcta. El journal de instalación terminó como
fallido, sin una etapa de instalación completada ni una copia nativa acreditada.
Se comprobaron efectos antes de cualquier reintento; no se repitió la instalación
ni se usó una vía directa para sortear el fallo del gestor.

Los casos A/B **no se abrieron**. Por tanto no hay lecturas de instrucciones por un
agente medido, cambio de greeting(), prueba funcional, cierre técnico o métricas
comparables. La evidencia técnica anterior de V4-05A no se usa para sustituir H2.
No se acredita ahorro ni se afirma una regresión funcional del plugin por este fallo.

## Hallazgos y tratamiento dentro del bloque

| Hallazgo | Tratamiento / límite |
|---|---|
| La solicitud preparada de registro omitía el enlace resource/version de su referencia. | El gestor la rechazó antes de escribir. Se conservó el error y se creó una solicitud corregida; el registro A se completó. |
| El plan original mezclaba copia inmutable y catálogo en una operación reversible. | Se generaron planes autorizados separados: conservar el paquete referenciado y poder revertir solo el catálogo. Los planes originales de revisión no se alteraron. |
| El gestor no resolvió el catálogo aislado al instalar mediante su protocolo, aunque el CLI sí lo enumeró. | Fallo de integración de carga reproducido en A. Causa interna exacta pendiente; no se atribuye al runtime LKS-SDD ni se corrige el gestor instalado en esta tarea. |
| El límite externo de 30 s venció durante esa operación. | Se consultó el journal antes de continuar: el mismo intento acabó fallido tras 39,6545 s. El timeout no se contó como una segunda instalación ni se interpretó como ausencia de efectos. |
| El listado de plugins devuelve también entradas remotas de la cuenta. | Ese listado no acredita exclusividad de instrucciones del perfil. No se abrió ningún caso con aislamiento sin demostrar. No se modificaron plugins de cuenta. |
| Un listado previo a recuperar B superó 12 s. | Se conservó el timeout. B no había recibido ninguna operación de carga; se comprobó su configuración/caché local intacta, sin repetir el caso ni una instalación. |

## Recuperación y garantías comprobadas

- **A:** rollback oficial del catálogo verificado; ausencia de instalación LKS
  observada en el listado y coherente con journal fallido sin efectos nativos.
  El paquete inmutable y su referencia de estudio se conservan, no se borran.
- **B:** no hubo alta de catálogo, copia canónica o instalación. Se comprobó que
  no existe caché local LKS del estudio ni configuración de carga equivalente.
- **Credenciales:** retirada oficial de los archivos de autenticación temporales
  en ambos CODEX_HOME; no se copió autenticación previa ni se usó logout compartido.
- **Entorno habitual:** huella de configuración igual a la inicial. No se redirigió
  su marketplace, retiró su plugin ni se borraron cachés manualmente.
- **Integridad:** ZIP A/B y fuentes del protocolo congelado conservan sus huellas.
  Los fallos, solicitudes, planes y journals quedan disponibles para diagnóstico.

| Garantía / criterio | Estado de esta ejecución |
|---|---|
| Integridad de paquetes y protocolo | Comprobada. |
| Contención de cambios y recuperación del perfil habitual | Comprobada en los efectos y huellas indicados. |
| Carga efectiva de seis skills y runtime de cada versión | No acreditada; la instalación no se completó. |
| Aislamiento de instrucciones y lecturas en un caso real | No ejecutado. |
| Resultado Hola, sin parámetros, código solo app.py y prueba real | No ejecutado en H2. |
| Contratos, autoridad, guardas y cierre técnico durante H2 | No ejecutado; no se declaran superados por haber recuperado el perfil. |
| B_out, B_in, B_flow, N_admin y tokens W1 comparables | No medidos; no usar la carga administrativa como denominador. |
| AC-34 / ahorro / aceptación de host | Pendientes; H2 inconcluso. |

## Presupuesto y continuación

La preparación y recuperación terminaron antes de abrir los casos. Se cargan todos
los costes de estudio, fallos, esperas y reporte. La reserva local sigue siendo
**45 minutos acumulados**, sin empezar otra bolsa al corregir o reanudar.
El consumo y saldo al registrar el cierre están en `execution/resource-ledger.json`;
se reconciliarán con la duración final del turno, evitando doble cómputo.

**Cero casos completos nuevos; las dos plazas H2 siguen sin consumir.** Se mantiene
la cuenta de 45/48 cargos conocidos y reservas, las seis mejoras, toda la cobertura,
los máximos globales y Copilot al final. No se promete la viabilidad integral de
la release por disponer de tiempo de reserva no consumido en esta pareja.

Antes de volver a los casos hace falta resolver la ruta gestor/Codex para este
catálogo aislado y comprobar su recuperación y exclusividad con el cliente real,
sin modificar el plugin LKS-SDD. El diagnóstico debe usar los efectos conservados;
no repetir una instalación ciega. Después se puede preparar una continuación
acotada con los mismos paquetes y el saldo existente, sin relajar el protocolo,
inventar métricas o reiniciar los 45 minutos. Este bloque se detiene para presentar
resultados; no inicia ese trabajo posterior automáticamente.

Evidencia privada:
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\h2-plan\execution`.
Resultados y comprobaciones: `results.json` y `recovery-result.json`; por brazo,
solicitudes, salidas y recibos. El journal del fallo A se conserva en
`C:\AI-Workspace\extensions\_management\operations\f3ce60d09b5a4b6cb04448847cd36643\journal.json`.
