# Plan de implementación 4.0.1 — revisión 0.2

Fecha: 2026-10-18. Estado: **plan 0.2 y máximo de 7 h validados por el usuario**.
V401-01 y V401-02 validadas por el usuario. **V401-03–06 autorizadas y completadas
en el candidato técnico 4.0.1-rc.1**, con resultados en §9. El usuario ha validado
esos resultados y autorizado el cierre estable y la publicación de 4.0.1, incluida
su distribución en Codex. La ejecución y comprobación de esos pasos siguen separadas.

## Revisión crítica y conclusión

**Viable por arquitectura, con tiempo y memoria pendientes de comprobar.** El código
actual ya aporta ZIP determinista, publicación atómica, slot compartido y dos fases
de autorización. Reutilizarlos reduce el cambio; no basta cambiar `LIMIT`.

| Debilidad de 0.1 | Corrección en 0.2 |
|---|---|
| Manifiesto separado antes del diario: huérfanos y recuperación adicional. | Incluir el manifiesto autorizado en el diario oficial, publicado completo al adquirir el slot; copia externa en el respaldo. Sin nuevo fichero de autoridad dentro del consumidor. |
| Streaming de ZIP sin concretar implementación. | Reutilizar codificadores actuales con cuerpos de un solo lote. Mantener bytes/formato ZIP; no desarrollar un codificador incremental ni modificar el lector común para ahorrar memoria. |
| 512 MiB parecía garantizado por acotar buffers. | Medir el pico completo y probar JSON grande/denso en V401-01: `json.loads` asigna memoria antes de contar nodos. Si no cabe, detener ese diseño sin omitir validación. |
| Ceder a los 600 s podía exigir un coordinador nuevo con plazos difíciles de cumplir. | Una llamada local avanza hasta terminar o pausar en frontera durable; la continuación usa `store-recover`. Los 600 s son presupuesto de trabajo entre fronteras, no garantía de respuesta inmediata. |
| Recuperación y salida sin retirada demasiado genéricas. | Definir fases, efectos sin checkpoint, temporales propios, recibos terminales y condiciones para liberar el slot sin retirar. |
| Porcentaje de ahorro y ventana de 30 min poco justificados. | Denominador y máximo de 507 altas permanentes explícitos; una ventana de 45 min incluida en el mismo máximo propuesto de 7 h, con reserva de recuperación. |

La revisión 0.2 se validó antes de ejecutar. El prototipo de §7 acreditó la
viabilidad local de V401-01; §9 registra el parche y el recorrido completo de 800 MB,
sin convertir esa evidencia sintética en aceptación del consumidor real o del host.

## 1. Problema y alcance

La incidencia actualizada el 18 de octubre confirma que 4.0.0 corrige el inventario
de código, pero `store-preview` rechaza un almacén de 800.539.116 bytes por aplicar
64 MiB al conjunto. La reproducción sintética ya registrada, con 12 objetos y
75.497.507 bytes, falla del mismo modo sin modificar el consumidor. Se reutiliza
esa evidencia; no se repite para iniciar el trabajo.

4.0.1 permitirá mantenimiento explícito por lotes, con inventario completo,
respaldo independiente, restauración y recuperación durable. **Compactar no será
requisito para cerrar una tarea.** La recuperación administrativa del proyecto real
seguirá pendiente de comprobar allí; este plan no interviene en ese consumidor.

Se mantienen las seis mejoras de 4.0, las seis skills, Markdown canónico, método
3.1.0, esquema 3.1, referencias `lks-sdd-object/1` y contenedores ZIP/1. Quedan fuera
GC, eliminación de historia, compactación automática, servicios externos y nuevas
dependencias. Windows nativo/H2 y la valoración humana continúan pendientes. La
regresión exigible de rutas largas del plugin conserva su cobertura independiente.

## 2. Diseño que deberá implementar el parche

### Inventario, lotes y recursos

- Inventariar completamente objetos sueltos y empaquetados, incluidas copias,
  referencias y contenido válido sin referencias conocidas. Verificar bytes/hash,
  contradicciones y enlaces. Un resultado truncado o parcial no produce autorización.
- Conservar tamaños e identidades en metadatos acotados; leer cuerpos
  secuencialmente y liberar cada uno. Validar referencias contra el mapa completo,
  sin acumular sus cuerpos ni todas las referencias en RAM. El presupuesto de
  recorrido estructurado se aplica por objeto, con límite de trabajo por comando;
  el millón de nodos acumulados actual no debe convertirse en el siguiente bloqueo.
  Mantener un millón por objeto y rechazar el exceso sin saltarse referencias.
  Cerrar la enumeración comprobando pertenencia, identidades, pin y ausencia de otro
  diario; no afirmar que el preview es un snapshot atómico del sistema de archivos.
- Formar lotes deterministas: **hasta 64 MiB de contenido lógico y 4.096 objetos**,
  sin dividir un objeto. No sumar todos los bytes del almacén contra esa cota.
  Objetos de más de 8 MiB siguen sueltos; se respaldan y restauran igualmente.
- Mantener 50.000 objetos lógicos, 64 MiB por objeto, y los límites ZIP vigentes
  —objetivo 8 MiB, máximo 16 MiB, 8.192 entradas e índice de 1 MiB por paquete—.
  Índices acumulados: 16 MiB. Manifiesto nuevo: máximo 12 MiB; diario nuevo completo,
  incluido manifiesto, progreso y envoltura: máximo 16 MiB.
  Los límites y recuperadores de los diarios antiguos no se reducen.
- El respaldo ZIP sin compresión de cada lote admite hasta 66 MiB físicos,
  incluidos índices/cabeceras. Su cota se calcula, no se confunde con la del paquete:
  64 MiB + 4.096 × 204 bytes + 22 = 67.944.470 bytes, inferior a 66 MiB. Reutilizar
  `_backup_bytes` por lote y `codec.encode` por paquete; liberar cuerpos/salidas
  antes de cargar el siguiente lote. Objetivo de pico
  del proceso completo: **512 MiB**, incluyendo JSON, índices y metadatos, no solo
  buffers. El prototipo debe comprobar ese riesgo antes de desarrollar el flujo.
- Presupuesto de trabajo propuesto por invocación: 600 s; comprobarlo durante
  lecturas/traversal y antes de nuevas fases. La publicación atómica en curso puede
  terminar antes de devolver `paused`, con diario y orden de recuperación. Ningún
  bucle de continuación reinicia ese presupuesto para eludir la cota de campaña.
  Un inventario no terminado
  sigue siendo inválido. No se promete capacidad ilimitada ni se certifican otros
  volúmenes por extrapolar el ensayo de unos 763 MiB.

### Persistencia y compatibilidad

- Introducir `lks-sdd-store-maintenance/2`: un manifiesto con alcance, lotes,
  tamaños/hashes previstos, pin, destinos y previsión de espacio. El diario oficial
  `.lks-sdd/transaction.json` lo incluye íntegro como campo inmutable, más su hash,
  fases y avance compacto; se reescribe por frontera durable, no por objeto.
  Un recibo final acredita el resultado antes de liberar el slot. Sin un archivo
  de control por objeto ni otro catálogo mutable que gobierne la recuperación.
- Adquirir el slot publicando atómicamente ese diario completo, tras validar
  sintaxis, hash y pin. Revalidar el inventario bajo ownership antes de efectos
  externos; los escritores oficiales deben quedar excluidos desde la adquisición.
  Si el preview ya es obsoleto, cerrar como rechazado sin efectos y liberar el slot.
  Las estimaciones de espacio libre y métricas observadas quedan fuera del hash;
  los destinos y la regla de reserva sí quedan vinculados. Derivar staging del hash
  después de calcularlo: sin autorreferencias ni valores variables en el alcance.
- Añadir a `store-preview` el campo explícito `backup_dir`, excluyente de `backup`.
  Activa el formato /2, con `manifest.json` y `batch-NNNN.zip` externos; `restore`
  sigue siendo el destino externo declarado. Las llamadas existentes con `backup`
  mantienen el contrato /1. Documentar la nueva llamada para almacenes grandes;
  el error legado debe indicarla, sin interpretar un nombre ZIP como directorio.
- Reutilizar `--output`, `--input` y `--view operational` para guardar el preview
  completo fuera del consumidor y mostrar una referencia/resumen. No añadir otro
  transporte. El flujo recomendado /2 usa exportación explícita; sin ella la API
  conserva el plan completo. Un fallo de exportación no autoriza compactar.
  `--output` debe estar también fuera de `backup_dir`, restauración y staging para
  no crear anticipadamente un destino que deba ser nuevo. Destinos separados,
  sin enlaces ni solapamientos; en recuperación solo se admite contenido esperado.
- El respaldo nuevo cubre **todos los objetos lógicos del inventario**, incluidos
  grandes y ya empaquetados. La restauración real reconstruye ese conjunto por
  hash en el destino externo, usando staging verificable. Esto no es un respaldo
  integral del repositorio, sus documentos canónicos o su runtime.
- Conservar lectura/recuperación de mantenimiento /1 y diarios de negocio 2.0/2.1.
  Actualizar despachos v2/v3, declaración de capacidades, doctor, comprobaciones de
  cambio de pin e instalador: soportar ZIP no demuestra soportar un diario /2.
  Resolver un diario antiguo con su pin vigente antes de actualizar. Un runtime
  incompatible no puede reemplazar el pin con mantenimiento pendiente; no se
  atribuye a 4.0.0 capacidad para recuperar /2 ni se promete controlar herramientas
  antiguas o cambios manuales ajenos a estos caminos oficiales.
  En concreto, reemplazar el despacho literal /1 de `v2_storage` y el despacho por
  un único `FORMAT` de `v3_storage` por reconocimiento explícito de /1 y /2; probar
  también las comprobaciones del constructor de paquetes. Tras terminar /2, permitir
  un runtime anterior compatible con los datos ZIP; el recibo no es un pendiente.

### Autoridad, ejecución y recuperación

- Un preview global completo fija todos los lotes y destinos bajo un único hash.
  La salida ordinaria muestra resumen, hash y ubicación del manifiesto; el detalle
  completo queda recuperable. Generar preview no escribe en el consumidor ni crea
  respaldos/restauraciones; exportarlo fuera requiere destino explícito.
- Primera autorización exacta: preparar todos los lotes. Comprobar espacio antes
  de escribir y de nuevo al avanzar; consultar espacio libre no lo reserva frente
  a otros procesos. Tratar también el error real de disco lleno. Contabilizar por volumen el pico
  de paquetes, respaldo completo, restauración y staging, sin descontar originales
  aún presentes ni duplicar staging publicado mediante rename.
  Para el corpus, con todos los destinos en una unidad, hacen falta al menos
  `2 × 800.539.116 + 686.951.061 = 2.288.029.293` bytes libres adicionales
  (2,13 GiB), antes de cabeceras, metadatos y temporales. Prever unos 2,5 GiB y
  calcular la admisión efectiva; si hay varias unidades, distribuir los costes.
- Preparar lotes mediante un proceso local: respaldar, publicar paquetes elegibles,
  verificar copias y restaurar. **No retirar ningún original hasta terminar y
  verificar el respaldo/restauración de todo el alcance.** El slot común bloquea
  otros escritores durante el mantenimiento, incluida la espera de autorización.
- Segunda autorización exacta y separada del mismo alcance: retirar únicamente
  duplicados físicos elegibles. Revalidar pin, originales y copias verificadas al
  usarlos, sin sustituir hashes frescos por tamaño/fecha. Los objetos protegidos y
  las referencias lógicas no cambian; todas las copias contradictorias bloquean.
- Reanudar con el diario oficial: verificar efectos durables ya existentes y
  continuar en la primera fase incompleta. No regenerar respaldos/paquetes correctos,
  restaurar otra vez archivos correctos ni repetir retiradas. Resolver también el
  efecto completado justo antes de guardar su checkpoint. Nunca reparar en silencio
  un destino alterado ni sobrescribir archivos ajenos.
- Fases mínimas: `owned` → `preparing` → `awaiting-removal-authorization` →
  `removing` → recibo terminal → liberación. Registrar por lote respaldo, paquetes y
  restauración verificados. Si falta checkpoint, distinguir destino final válido,
  temporal propio incompleto y conflicto; solo el primero se adopta como terminado.
  Identificar temporales propios por operación/lote; nunca limpiarlos por prefijo
  genérico. Tras persistir autoridad de retirada, un original ausente exige copias
  válidas y se registra como ya ausente, sin atribuir una nueva eliminación.
- Permitir finalizar expresamente **sin retirada**, antes de la primera retirada:
  recibo del estado conservado y liberación segura del slot, con todos los originales
  y cualquier paquete publicado íntegros. Un respaldo externo incompleto se declara
  así; no obliga a retirar ni se presenta como compactación terminada. Una copia activa
  corrupta mantiene el bloqueo hasta resolverla. Tras retirar algún
  original, la vía del parche es completar la recuperación autorizada; no hay
  rollback automático ni cancelación que borre el diario.
- El mismo comando procesa y espera localmente, sin llamadas a la IA por lote ni
  autorizaciones repetidas. Al agotarse tiempo devuelve estado recuperable, no
  éxito global. Consultar estado no escribe ni concede autoridad de negocio.
  Reanudar verifica el mismo manifiesto y pin; los datos nuevos fuera de alcance
  se preservan y no se incorporan silenciosamente a la autorización. El recibo
  acredita ese inventario, sin declarar compactado un crecimiento posterior.
  Si ya existe recibo terminal y no hay diario, reconocer la operación completada
  sin volver a escribir; el recibo histórico no certifica integridad actual.
  Si falla la salida tras un efecto, informar pendiente/recibo y estado parcial:
  nunca recomendar repetir `store-compact` como si no hubiera ocurrido nada.

## 3. Tareas y dependencias

| ID · cota propuesta | Trabajo | Dependencias | Criterios de aceptación |
|---|---|---|---|
| **V401-01** · 45 min | Congelar contrato /2, fases, recursos y fixtures. Prototipo focal de inventario, JSON grande/denso, un lote máximo y codificación reproducible; reutilizar el fallo registrado. | Fuente publicada 4.0.0 e incidencia. | AC01: completado en prototipo local; corrección JSON y pico conjunto <512 MiB comprobados. Contrato/fixture fijados, límites mantenidos y sin dependencia ni gramática JSON nuevos. Véase §7; no acredita todavía mantenimiento integral ni aceptación del host. |
| **V401-02** · 75 min | Inventario completo y manifiesto determinista; referencias globales, partición y previsión física sin retener todos los cuerpos. | V401-01. | AC02 completado en la API interna de preparación /2: 80.742.604 bytes en dos lotes, copias verificadas, referencias entre lotes válidas y preview sin escrituras. Cambios de pertenencia/pin rechazados; hash independiente del espacio libre observado. La entrada CLI y recuperación /2 siguen en V401-03/04. Véase §8. |
| **V401-03** · 60 min | Diario /2, ownership, fases, dispatch, capacidades y contrato CLI compatible. | V401-01. | AC03 completado: un escritor; recuperación /1 y negocio 2.0/2.1 conservada, incluidos diarios >16 MiB. Capacidad/pin incompatible bloqueado; recibo terminado admite lector anterior compatible. Preparar y consultar no autorizan retirar. Véase §9. |
| **V401-04** · 90 min | Respaldo por lotes, publicación, restauración, retirada separada y continuación/salida sin retirada. Reutilizar codificadores y supervisor local. | V401-02 y V401-03. | AC04 completado: recuperación por fronteras durables y muerte real pequeña; volumen íntegro tras interrupción, sin paquetes duplicados. Retirada con respaldo/restauración frescos y recibo antes de liberar el slot. Véase §9. |
| **V401-05** · 45 min | Cerrar pruebas focales y CLI, guías, versión/capacidades; congelar fuente, construir un candidato y ejecutar controles exigibles. | V401-04. | AC05 completado sobre 4.0.1-rc.1: focales, contrato, 14 humos, rutas largas y paquetes compatibles. Exportación completa y resumen ≤8 KiB; fallos de salida conservan efectos/recuperación. Gate estable/aprobación no ejecutados. Véase §9. |
| **V401-06** · 45 min | Una campaña de volumen con el candidato congelado, recuperación, ahorro y evidencia final. | V401-05. | AC06 completado: 10.157 objetos/800.539.116 bytes, 13 lotes, recuperación íntegra, −99,08 % neto del alcance compactable, pico <512 MiB y 36 min 33 s de campaña. Fuente/fixture ligados por hash y evidencia externa. Véase §9. |

Orden: **01 → {02, 03} → 04 → 05 → 06**. Las ramas son dependencias lógicas;
no requieren agentes paralelos. Ninguna escritura nueva se prueba con un runtime
fijado que todavía carezca del recuperador /2.
Las pruebas unitarias acompañan a cada tarea; V401-05 integra y cubre huecos,
no vuelve a diseñar ni ejecutar todas las familias desde cero.

## 4. Pruebas pequeñas: reutilizar y ampliar

Extender `tests/test_store_maintenance.py` y casos afectados de
`tests/test_v4_compatibility.py`; reutilizar lector ZIP y pruebas de negocio sin
copiar suites. Emplear una cota interna reducida solo en fixtures para forzar lotes.
Las fronteras reales de 64 MiB se comprueban también con el límite de producción.

| Familia | Cobertura mínima y resultado exigido |
|---|---|
| P1 · Límites e inventario | Tabla pequeña de frontera y corpus real >64 MiB, sin una prueba grande por valor adyacente. Cardinalidad/metadata por datos controlados; no crear 50.001 cuerpos. Nodos acumulados >1 millón deben aceptar si cada objeto cumple; exceso por objeto falla. Medir JSON grande/denso antes de confiar en el guard posterior a `json.loads`. |
| P2 · Referencias y copias | Referencias cruzadas, transitivas y repetidas; objetos sin referencias, grandes, sueltos/empaquetados y duplicados idénticos. Ausencia/tamaño contradictorio, cuerpo/ZIP alterado o enlace bloquean sin retirar. No exigir construir ciclos de hashes de contenido. |
| P3 · Autoridad y concurrencia | Hash incorrecto, preview obsoleto, pin cambiado, segundo proceso recuperador y escritor de negocio. Sin retirada por autorización de preparación, consulta o recuperador de negocio. Validar también finalizar sin retirada y su límite tras retiradas parciales. |
| P4 · Fronteras durables | Un fixture pequeño de tres lotes, parametrizado: fallo al adquirir diario y tras adquirirlo; respaldo o paquete final sin checkpoint; restauración parcial/final sin checkpoint; autorización de retirada persistida; unlink sin checkpoint; recibo antes de liberar slot. Una muerte real de proceso y resto por inyección, sin producto cartesiano. Verificar hashes/estado y ausencia de efectos repetidos. |
| P5 · Recuperación adversa | Respaldo, manifiesto, restauración o paquete alterados; archivo ajeno en staging, falta de espacio inicial/intermedia y diario desconocido. Preservar contenido ajeno y evidencia; no sustituir copias dañadas ni liberar el diario como completado. Recuperación válida tras corregir la causa con procedimiento explícito. |
| P6 · Compatibilidad/CLI | /1 y /2 por CLI real, exclusión `backup`/`backup_dir`, despachos v2/v3 y downgrade pendiente/terminado; diarios 2.0/2.1, incluido el caso legado mayor de 16 MiB. Exportación/resumen y fallos de salida antes/después de efectos; salida heredada conserva su contrato. Reutilizar alias/Unicode/rutas largas afectados. |

No repetir S8, ABBA, migraciones integrales ni el piloto H2. Tras un cambio, repetir
los casos impactados; ampliar solo si aparece una dependencia o fallo no resuelto.
Reutilizar las 12 regresiones existentes de mantenimiento cuando su código cambie;
añadir las diferencias /2. Reutilizar las pruebas de ZIP si `object_zip.py` queda
idéntico; no repetir cutovers/migraciones completos para comprobar un dispatcher.
Modelo de fallo: excepción, terminación de proceso y errores de E/S. No se certifica
resistencia a corte eléctrico ni independencia de hardware por usar otro directorio.

## 5. Única campaña de volumen y recuperación

**Congelar antes de medir** un generador determinista, semilla y manifiesto externo:

- 10.157 objetos lógicos distintos y sueltos; 800.539.116 bytes exactos.
- 10.154 objetos ≤8 MiB, sumando 686.951.061 bytes; tres >8 MiB y ≤64 MiB,
  sumando 113.588.055 bytes. Contenido sintético, sin datos del consumidor real.
- Representar documentos estructurados y cuerpos opacos, referencias entre lotes,
  protegidos referenciados y objetos válidos sin referencias. Congelar tamaños y
  relaciones antes de conocer resultados. No basta rellenar el mismo blob repetido.
  La restauración usa exclusivamente los ZIP externos; una negativa pequeña impide
  leer originales como fallback. No hace falta una segunda copia grande para probarlo.

Recorrido único: generar → preview → autorización de preparación → ejecutar algunos
lotes → interrumpir una vez después de un checkpoint durable → recuperar el mismo
recorrido → verificar toda la restauración → comprobar ausencia de retiradas →
autorización separada de retirada → completar → leer/verificar todos los objetos.
La autorización de ambas fases deberá formar parte del futuro encargo sintético;
validar este documento no retira archivos de ningún consumidor real.

Hay al menos **11 lotes** de contenido compactable con cota de 64 MiB; el respaldo
de todo el almacén requiere **al menos 12**. El manifiesto fija el número efectivo,
que puede ser mayor por partición, cabeceras y cantidad de objetos.

Aceptación del ensayo:

1. Lectura final y restauración independiente de los 10.157 objetos byte a byte
   contra el manifiesto inicial. Referencias resueltas; los tres grandes permanecen
   sueltos e intactos. Markdown, aprobaciones y estado funcional no cambian.
2. Ningún original retirado antes de la segunda autorización; al final, cero diario
   pendiente y recibo durable. Recuperación completa sin efectos duplicados.
3. **≥95 % menos archivos netos en el alcance compactable del corpus**:
   `reducción = (10.154 retirados − altas permanentes internas) / 10.154`.
   Exige **≤507 altas**, incluidos paquetes y recibo. Congelar esa previsión antes
   de retirar; abortar el ensayo si el plan ya no puede alcanzarla. Informar además
   el censo interno total, archivos externos, bytes y pico temporal por separado.
   No prometer ese porcentaje para otros proyectos ni ahorro de bytes con ZIP_STORED.
4. Pico del proceso ≤512 MiB; cuotas de lote/metadata cumplidas. Registrar CPU,
   pared y bytes leídos/escritos por fase. Como mínimo, inventario completo en
   preview y revalidación previa a aplicar; no volver a recorrer todo el almacén
   por cada lote. Verificaciones frescas de recuperación/retirada siguen exigibles.
5. Ventana propuesta máxima de **45 minutos**, incluidos preparación del fixture
   y verificación; reservar los diez finales a recuperación/cierre. Antes de iniciar
   otra fase, comprobar margen. Si no cabe, conservar el estado recuperable y registrar
   incumplimiento; sin reintento completo automático ni relajación de garantías.

Los 45 min son una cota de consumo del ensayo, no un SLA del plugin ni una promesa
de recuperar cualquier fallo en diez minutos. Si queda pendiente, no borrar fixture,
respaldos o diario, no declarar éxito y detallar la recuperación necesaria.

Un supervisor local recoge resultados y espera al proceso; sin sondeo del modelo
por lote. Conservar un JSON de evidencia con huellas, contadores y medidas más un
resumen final. La espera local no implica llamadas continuas a la IA; el consumo
facturado se mantendrá `billed_tokens: null` si no hay telemetría verificable.

## 6. Coste, cierre y decisiones antes de ejecutar

Propuesta concreta: **6 h base + 1 h de contingencia = máximo 7 h**, incluidas
las pruebas, el candidato, la ventana de volumen y recuperación. Las seis cotas de
tarea suman 360 min. La hora restante cubre correcciones y recuperación; no otra
campaña. Se conserva el extremo superior de 0.1, sin prometer el inferior de 5 h.
El usuario autorizó ese máximo de 7 h, inicialmente para V401-01 y posteriormente
para V401-02 y V401-03–06. No es una promesa de duración; no se descuentan reservas de Windows/H2 ni
se reutilizan presupuestos ya cerrados. Una desviación que exija más alcance o
presupuesto se presenta con evidencia antes de abrir otra campaña.

Base de viabilidad temporal: V4-22 registró 320,55 s de preparación y 218,94 s de
finalización para 11.038 objetos y 30.200.874 bytes restaurados. La cardinalidad es
comparable, los bytes no: ese resultado no demuestra tiempos para 800 MB. La
viabilidad de la ventana se decide con V401-01 y el primer inventario del ensayo;
no se obtiene multiplicando linealmente el tiempo anterior ni buscando cargas favorables.
La viabilidad funcional se apoya en lectores/codificadores/locks existentes; memoria,
parsing adverso y duración quedan como riesgos explícitos con parada temprana.

No se exige un porcentaje de aceleración frente a 4.0.0: esta no completa el caso.
El ahorro comprobable será reducción física neta y trabajo/recursos acotados; tiempos
con carga variable se informarán sin convertirlos en ahorro global de tokens.

Actualizar una sola vez `DOCUMENT-STORAGE.md` y la guía de actualización aplicable,
antes de congelar el candidato. Un único candidato final y controles de `docs/VALIDATION.md`:
contrato/fixtures, 14 humos y regresión real de rutas largas. La aprobación explícita
de la versión sigue siendo una condición separada para publicar. El candidato de
desarrollo no ejecuta la puerta estable ni hereda la aprobación de 4.0.0.
Reutilizar el área de evidencia existente, retirar solo fixtures propios tras
recuperación verificada y conservar resultados necesarios para revisión.
No cambiar fuentes/versiones durante el ensayo. Una corrección posterior invalida
solo la evidencia que dependa de ella: identificar hashes y cobertura reutilizada;
si afecta al mantenimiento probado, no atribuirle el volumen anterior ni repetir
la campaña automáticamente. Registrar resultados en un JSON externo y el resumen
final; no crear informes/ledger nuevos por fase ni editar el paquete por el resultado.

Se han presentado y validado V401-01 y V401-02 antes de autorizar V401-03–06; para
intervenir en el consumidor real se revisarán su preview y autorizaciones. La
observación real de Windows/H2 y la percepción humana no se darán por superadas.

## 7. V401-01 — resultado de viabilidad

En V401-01 se usó `tests/probe_store_maintenance_v401.py`, con el adaptador entonces
ubicado en `tests/v401_json_inspector.py` y nueve pruebas focales; fuera de los
entrypoints y del gate automático. En aquella fase no se cambió `scripts/`,
versiones, skills ni runtime instalado. Su integración posterior figura en §8.
Se reutilizó el fallo publicado; no se repitió el preview
antiguo ni se ejecutó el corpus de 800 MB. Evidencia y presupuesto:
[result.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/v401-01/result.json>).

| Comprobación | Resultado final o reutilizado | Pico de working set del worker |
|---|---|---|
| Inventario experimental por objeto | Reutilizado: 21 objetos, 77.899.238 bytes; 1.200.048 nodos acumulados, 12 referencias verificadas y referencia ausente rechazada. Ruta de tokens pequeños sin cambios. | 58,65 MiB |
| Lote real máximo y codecs actuales | Reutilizado por igualdad del código: 64 MiB; respaldo de 67.110.518 bytes, determinismo y lectura ZIP byte a byte. | 224,34 MiB |
| JSON ASCII de 64 MiB | Admitido, dos nodos. | 162,97 MiB |
| JSON de 64 MiB dentro del presupuesto | Admitido, exactamente 1.000.000 de nodos. | 166,84 MiB |
| JSON denso de 64 MiB, por encima del presupuesto | Rechazo explícito por trabajo de decodificación antes de agotar memoria; control reutilizado sin cambio posterior. | 225,90 MiB |
| JSON Unicode válido de 64 MiB | Admitido, dos nodos; ya no produce `MemoryError`. | 162,70 MiB |
| Clave Unicode de 64 MiB | Admitida; identidad temporal de clave preservada por hash, sin materializar la cadena completa. | 162,61 MiB |
| 999.999 claves Unicode, JSON de 64 MiB | Admitido, un millón de nodos; duplicados y claves escapadas cubiertos además por comparación diferencial. | 311,11 MiB |
| JSON de 64 MiB compuesto de Unicode | Admitido; expansión de normalización cercana a 192 MiB. | 452,68 MiB |
| Caso anterior + 50.000 filas y 16 MiB de índices residentes | Admitido; pico de commit privado 483,12 MiB y working set 490,89 MiB, ambos <512 MiB. | **490,89 MiB** |
| Tabla de metadatos de 50.000 entradas | Reutilizada: manifiesto 5.587.729 bytes; diario 5.587.928 bytes, inferiores a 12/16 MiB. Ensayo de estructura, sin inventario físico de 50.000 archivos. | 66,96 MiB |

El supervisor ya existente mide procesos propios; una cuota adicional de **512 MiB
de commit privado por worker** protege el ensayo. No modifica el aislamiento de
Codex ni aplica esa cuota al plugin. Un `MemoryError` bajo esa cuota no mide el pico
que alcanzaría una ejecución sin ella: la asignación denegada no aparece en el pico.
No se elevó la cuota para buscar éxito. Las variantes fallidas y sus fuentes/huellas
permanecen diferenciadas en el JSON; se corrigió el algoritmo y se repitieron los
caminos afectados. Todos los workers terminaron sin descendientes activos y sus
fixtures se retiraron. Contrato del plugin: válido en 4.0.0; gate estable y Windows/H2
no ejecutados. El margen del peor caso es de unos 21 MiB de working set: V401-02
debe respetar el ciclo de vida de buffers y V401-06 medirá el proceso integrado.

### Corrección JSON probada

- Normalizar el texto por fragmentos de 64 KiB, liberar **el buffer en memoria** de
  los bytes originales y después consumir los fragmentos. No se borra ni transforma
  el objeto almacenado en disco. La API experimental fija esa secuencia en
  `prepare` → liberación del buffer → `inspect_prepared`.
- Reutilizar la gramática de objetos/arrays y la validación de cadenas de `json`;
  validar las cadenas largas por fragmentos, sin construir sus valores completos.
  Mantener los campos que reconocen referencias y una proyección temporal mínima;
  las claves grandes conservan identidad temporal por SHA-256, como el CAS.
- Contar trabajo durante la decodificación; los tres campos de una referencia
  terminal válida se descuentan para no reducir el cupo de referencias. Las claves
  repetidas mantienen «última gana», pero decodificar valores luego sustituidos
  también consume presupuesto de trabajo. Exceso/recursión/tiempo fallan explícitamente;
  nunca se convierten en inspección parcial válida ni se omiten referencias para pasar.
  Al integrarlo en V401-02, propagar `ContractError` antes de capturar `ValueError`:
  el primero hereda del segundo y no puede tratarse como contenido opaco.
- Nueve pruebas focales correctas, con al menos 608 comparaciones diferenciales:
  Unicode, escapes entre fragmentos, duplicados, tipos exactos, referencias ausentes,
  JSON truncado y fuentes opacas. La validación de referencias se hace después de
  validar todo el JSON y resolver duplicados. Sin nuevos paquetes ni parser general.
- Verificado con CPython 3.14 del equipo de referencia; se usan callbacks locales de
  la biblioteca estándar, sin parche global del decodificador. La compatibilidad
  del runtime empaquetado se comprobará en las tareas siguientes, no se da por hecha.

### Contrato fijado por el prototipo

- Una tabla de objetos ordenada por hash, con hash, bytes y presencia suelta;
  lotes por rangos y miembros de paquete por índices enteros de esa tabla. Evitar
  repetir cada hash en varias listas: esta representación pasa el ensayo de 50.000.
- Hash sobre el manifiesto canónico, sin espacio libre observado; destinos y regla
  de reserva incluidos. Diario completo vinculado a ese hash; progreso separado y
  autoridad de retirada inicialmente falsa. Sin fichero de autoridad adicional.
- Se mantienen lotes 64 MiB/4.096 objetos, respaldos ≤66 MiB, JSON estándar y
  validación completa de referencias. No se descarta contenido para hacer caber RAM.
- Fixture de volumen congelado por definición, todavía sin generar: 2.499 objetos
  pequeños de 67.654 bytes y 7.655 de 67.653; tres grandes de 37.862.685 bytes cada
  uno. Total exacto del reporte. JSON determinista con ordinal, 128 nodos escalares,
  referencias a protegidos/anteriores y padding ASCII; construcción sin ciclos de
  hashes. Los detalles y la huella de la definición quedan en el resultado JSON.

### Conclusión y siguiente punto de control

**V401-01 y AC01 completados en su alcance de prototipo local.** Inventario, lotes,
metadatos y JSON caben en los límites de los casos probados. Se mantienen los
64 MiB por objeto, 512 MiB, el máximo de 7 h y la definición congelada del fixture.
Al presentar V401-01 no se habían iniciado V401-02–06 ni integrado la corrección.
Su evolución autorizada se recoge en §8. Siguen pendientes el
recorrido público completo, recuperación durable y corpus de 800 MB; no se acredita
todavía su ventana de 45 min ni una cota universal para cualquier combinación de datos.

## 8. V401-02 — inventario y manifiesto implementados

Al cierre de V401-02, `scripts/store_maintenance_batches.py` preparaba el manifiesto /2 mediante
`preview(root, backup_dir, restore)`, sin crear destinos, diarios ni archivos en el
consumidor. Devolvía el manifiesto completo y su hash con `execution_enabled: false`.
La CLI, capacidades y despachos públicos seguían en /1: **no se habilitó escritura
/2 sobre un runtime que aún carecía de recuperador /2**. La integración autorizada
posterior, incluido el recuperador, figura en §9.

El inventario verifica todas las representaciones y sus hashes, incluidos objetos
sin referencias conocidas; comprueba referencias con el mapa global y conserva
solo metadatos entre objetos. La tabla ordenada fija lotes de hasta 64 MiB/4.096
objetos, respaldos completos por lote y paquetes elegibles por índices enteros.
Los grandes y ya empaquetados también quedan incluidos en el respaldo previsto.
Se reutilizan los codificadores actuales con cuerpos de un solo lote; no se ha
cambiado `store_maintenance.py`, `object_zip.py`, el lector ni las versiones.

El inspector validado se ha trasladado a `scripts/store_json_inspector.py` y sus
pruebas/probe importan esa fuente. Su AST, excluyendo el docstring del módulo, es
idéntico al prototipo congelado; se reutilizan los ensayos de memoria de V401-01.
Se respeta `prepare` → liberar buffer original en RAM → `inspect_prepared`.
El pico del proceso integrado y el corpus exacto de 800 MB siguen en V401-06;
esta fase no acredita aún los 512 MiB ni el tiempo del recorrido completo.

| Comprobación focal | Resultado |
|---|---|
| Almacén físico de 22 objetos, 80.742.604 bytes | Preview completo en dos lotes; 18 referencias verificadas, incluidas referencias entre lotes y a un protegido de 9 MiB. Respaldos previstos verificados byte a byte en memoria, sin escribirlos a disco. |
| Copias sueltas/ZIP repetidas y contenido no referenciado | Verificación completa; reutilización de paquetes válidos. Copia dañada aun con otra válida, tamaños contradictorios, referencia ausente y rutas desconocidas rechazados. |
| Presupuestos | Más de un millón de nodos acumulados aceptados por cumplir cada objeto; exceso de tiempo, cardinalidad, manifiesto o falta de espacio fallan sin preview parcial. Partición de 4.096 entradas y objeto de exactamente 64 MiB cubiertos con metadatos controlados. |
| Determinismo y concurrencia | Mismo manifiesto/hash con orden físico inverso y distinto espacio libre. Cambios finales de pertenencia, cuerpo, pin, pending o destino invalidan el preview. |
| Rutas | Identidades nativas consistentes mediante `lstat`; destinos nuevos normalizados por su ancestro existente para conservar el rechazo dentro del consumidor bajo alias 8.3. Ruta Unicode >260 caracteres y junction NTFS real correctas. Sin ajustes del host ni intervención en Windows/H2. |
| Compatibilidad | 13 pruebas nuevas, nueve del inspector y 12 heredadas correctas: **34, sin fallos ni omisiones finales**. Contrato estático 4.0.0 válido; seis skills conservadas. No se repiten los ensayos grandes ni el gate final. |

La reserva física agrupa costes por volumen: todos los respaldos y restauración,
paquetes nuevos y margen explícito para manifiesto/diario/temporales atómicos.
No descuenta originales ni duplica una restauración publicada mediante rename.
La regla y los bytes requeridos están vinculados al hash; los bytes libres
observados quedan fuera y se vuelven a comprobar al final. No es una reserva del SO.
La comprobación final de pertenencia, identidades y pin no constituye un snapshot
atómico; sigue siendo obligatoria la revalidación bajo ownership de V401-03/04.

Evidencia ligera y cómputo acumulado del máximo de 7 h:
[result.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/v401-02/result.json>).
V401-02 permaneció dentro de sus 75 min, sin consumir la campaña de volumen ni
reservas Windows/H2. Se retiraron los fixtures salvo un temporal sintético pequeño
de una primera prueba fallida: la revisión automática bloqueó tanto la limpieza
recursiva como la retirada acotada. Su ubicación privada queda en el resultado;
no se han repetido vías alternativas de borrado. No había procesos propios pendientes,
instalación, publicación ni cambios en el consumidor real.

## 9. V401-03–06 — resultado de ejecución autorizado

**Candidato técnico 4.0.1-rc.1 completado; no instalado ni publicado.** Se conserva
el plan 0.2 y su máximo de 7 h. El recibo consolidado contiene el cómputo acumulado,
las cotas, las huellas y enlaces a las comprobaciones:
[result.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/v401-03-06/result.json>).

### Implementación y garantías

- Diario compartido `lks-sdd-store-maintenance/2` con manifiesto inmutable completo,
  avance por lote y autoridad de retirada inicialmente falsa. Entrada explícita
  `backup_dir`, transporte compatible, estado y finalización sin retirada.
- Respaldo de todos los objetos por lotes ≤64 MiB lógicos, publicación con los ZIP
  existentes y restauración exclusivamente desde el respaldo. Reanuda destinos y
  checkpoints verificables; conserva conflictos y temporales ajenos. La retirada
  comprueba respaldo, restauración y cobertura empaquetada al usarlos; un cambio
  durante el lote preserva el siguiente original.
- Despachos v2/v3, doctor, instalador y constructores reconocen /2; se bloquean
  cambios de pin con mantenimiento pendiente. Se conservan /1, negocio 2.0/2.1,
  las seis skills, contratos canónicos y formatos de datos existentes.
- Las pausas por presupuesto conservan el diario. Las llamadas continúan en un
  proceso local, sin solicitudes al modelo por lote. Un fallo de exportación tras
  efectos informa de recuperación; el recibo histórico no certifica integridad actual.

### Comprobaciones y candidato congelado

| Cobertura | Resultado |
|---|---|
| Focales | 70 correctas; la corrección final de frescura añadió una comprobación distinta y repitió solo dos afectadas: **71 distintas**, sin omisiones finales. Las nueve del inspector y sus ensayos de memoria se reutilizan por igualdad del algoritmo. |
| Fronteras y recuperación | Un recorrido pequeño de tres lotes cubre 15 fronteras durables; muerte real de proceso adicional, concurrencia, disco lleno, copias alteradas, temporales, finalización y fallos de salida. Sin producto cartesiano de recorridos grandes. |
| Controles técnicos | Contrato/fixtures, los 14 humos y la regresión nativa de rutas largas correctos sobre RC1; 352,29 s de pared al ejecutar controles independientes en paralelo. No se ejecuta Windows/H2. |
| Distribución | Cinco ZIP identificados por SHA-256. Núcleo plugin/consumidor idéntico byte a byte; paquete nativo Copilot estructuralmente válido con seis skills, sin aceptación del host. |
| Congelación | Fuente `46fcd4791b0c2725a6f88682aec52bce9062787d26316bdb09d4866e0d47f0e8`, sin cambios durante ni después del ensayo. La evidencia externa y esta actualización del plan no se añaden al paquete congelado. |

Las fuentes y paquetes intermedios anteriores a RC1 quedan diferenciados y
descartados como candidatos. El intento estable detectó referencias de versión
incompletas y ausencia de aprobación 4.0.1: se sincronizaron metadatos y se empleó
el flujo prerelease existente. **No se debilitó el validador ni se fabricó aprobación.**

### Único recorrido de volumen

Se extrajo el candidato en un consumidor sintético, sin instalar el plugin activo.
La definición congelada y validada en V401-01 usa JSON determinista para este
corpus; la ruta opaca está cubierta por las focales, no se atribuye al volumen.
No se ajustaron datos, semilla ni carga tras observar resultados.

| Medida | Resultado observado |
|---|---|
| Alcance | 10.157 objetos distintos, 800.539.116 bytes; 10.154 compactables y tres grandes protegidos; 13 lotes, 17.906 referencias entre lotes. |
| Recuperación | Interrupción tras dos lotes durables; continuación del mismo diario, incluida una pausa por 600 s. Los 10.157 originales seguían presentes al verificar toda la restauración y antes de autorizar retirada. |
| Integridad final | Restauración independiente y lectura final de los 10.157 objetos contra sus hashes iniciales; protegidos sueltos intactos, canónicos/runtime sin cambios, recibo `compacted`, cero diario pendiente. |
| Reducción real | 10.154 originales retirados; **92 paquetes + un recibo = 93 altas internas permanentes**. Reducción neta del alcance compactable **99,08 %**. Censo interno total **10.941 → 880**, reducción **91,96 %**, incluido el runtime fijo. |
| Copias externas | 14 archivos de respaldo —manifiesto y 13 ZIP— más 10.157 objetos restaurados. Se informa de ellos: la reducción interna no equivale a eliminar copias externas. |
| Memoria | Pico de commit privado **258,69 MiB**, working set **259,39 MiB**; ambos positivos y <512 MiB. Sin procesos propios activos al terminar. |
| Tiempo | **2.192,90 s = 36 min 33 s**, incluidos generación, interrupción, recuperación, comprobaciones y limpieza del fixture; <45 min. Preview: 556,12 s. |
| Espacio | Pico observado de longitudes de archivo **3.112.033.823 bytes**, incluyendo originales/runtime y temporales; incremento máximo **2.295.563.882 bytes**, inferior a la admisión calculada de 2.430.682.645 bytes. No mide bloques físicos asignados. |

Los contadores Windows de transferencia registran 50.828.223.318 bytes leídos y
3.150.298.275 escritos entre las fases; incluyen verificaciones y cachés y **no son
E/S física del disco**. No se promete aceleración, ahorro de bytes, de tokens ni
un SLA general: el dato comprobado es la reducción neta de archivos y la ejecución
íntegra de este corpus. Los bytes internos crecen ligeramente por índices y recibo
(816.469.941 → 819.673.030); ZIP_STORED no comprime el contenido.

El fixture se retiró solo después del éxito y de copiar fuera el recibo. Permanecen
las evidencias y los cinco paquetes; no se reconstruye por añadir resultados.
`billed_tokens: null`. El temporal pequeño pendiente de V401-02 no se ha tocado.

### Pendientes separados

Al presentar V401-03–06 todavía no se habían realizado la validación del usuario,
aprobación estable, commit, puerta de release, publicación e instalación. El incidente de
Windows nativo, H2, aceptación del host y consumidor real permanecen pendientes.
No se han consumido sus reservas ni intervenido en esos entornos.

## 10. Cierre estable autorizado — 2026-10-19

El responsable ha validado los resultados de §9 y autorizado los commits e
integración, cierre estable y publicación de 4.0.1 y su distribución posterior en
Codex. La decisión queda en `quality/release-approval-v4.0.1.json`. La evidencia
portable está en `docs/evidence/store-maintenance-4.0.1.json`.

La promoción cambia metadatos de versión, constantes de versión de los inicializadores,
aprobación y documentación. Los scripts del motor y el instalador coinciden con el
candidato probado: se reutiliza su única campaña de volumen y se ejecuta el gate
estable sobre el commit integrado exacto. No se repiten S8, H2 ni el corpus de 800 MB.

Publicación, registro/instalación en Codex y observación en conversación nueva se
verifican por separado y quedan en recibos externos de cierre. Se conserva la
identidad `lks-sdd@lks-sdd-development` y recuperación de versiones anteriores;
ningún runtime o almacén de un consumidor se actualiza por esa instalación.
