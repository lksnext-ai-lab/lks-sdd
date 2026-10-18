# Actualización y recuperación de LKS-SDD 4.0.1

La versión 4.0.1 promueve el candidato técnico validado `4.0.1-rc.1`. Su cierre
estable y publicación están autorizados en `quality/release-approval-v4.0.1.json`;
el gate sobre el commit final sigue siendo obligatorio. No se hereda la aprobación
de 4.0.0 ni se modifica el control que la exige. La
[evidencia del parche](evidence/store-maintenance-4.0.1.json) conserva sus límites.

4.0.1 incorpora mantenimiento explícito por lotes para almacenes que exceden los
64 MiB totales admitidos por el flujo /1 de 4.0.0. Conserva las seis skills, esquema
3.1, método 3.1.0 y objetos/ZIP existentes. Compactar sigue siendo opcional para
cerrar trabajo. Este documento no acredita publicación, instalación ni aceptación
de host; Windows/H2 y la valoración humana siguen pendientes.

## Antes de actualizar un proyecto

Identificar su pin y diario pendiente. Resolver el mantenimiento pendiente con su
runtime exacto antes de cambiar o retirar el pin. Preparar y autorizar por separado
la actualización del runtime; instalar el plugin personal no actualiza proyectos.
Comprobar `runtime-doctor` y usar la CLI de ese runtime. Un lector ZIP no demuestra
capacidad para recuperar un diario /2. El instalador rechaza cambiar el pin mientras
existe mantenimiento /1 o /2 pendiente.

Los objetos sueltos creados por v3 son candidatos a compactación tras el corte
compatible; no se migran Markdown, historia lógica ni decisiones para reducir
archivos. Un runtime anterior que lea ZIP/1 puede volver a leer los datos una vez
terminado el mantenimiento; no puede recuperar un pendiente /2.

## Preparación sin escrituras

Crear fuera del consumidor un JSON de entrada:

```json
{"backup_dir":"C:/respaldo/nueva-operacion","restore":"C:/restauracion/nueva-operacion"}
```

Ambos destinos deben ser nuevos, separados, sin enlaces y externos al consumidor.
Ejecutar desde la CLI del runtime fijado:

```powershell
python <runtime>/scripts/lks_sdd.py v3 store-preview <proyecto> --input <entrada.json> --output <preview-externo.json> --view operational --json
```

`--output` también debe quedar fuera del respaldo, restauración y staging; no
reemplaza la entrada. El archivo contiene el manifiesto completo. La salida muestra
su referencia, resumen y hash; exportar no equivale a leerlo ni aprobarlo. Sin
`--output`, la API y la vista compatible conservan el manifiesto completo; la vista
operativa indica cómo conservarlo antes de autorizar.

El inventario verifica todas las copias, incluidos objetos no referenciados y
empaquetados, y resuelve referencias contra el mapa completo. Los cambios de
pertenencia, identidades o pin durante el preview lo invalidan. No es un snapshot
atómico; aplicar reconstruye el alcance bajo el propietario exclusivo del diario.
El hash incluye destinos y política de espacio, y excluye bytes libres observados.

## Dos autorizaciones y recuperación

Revisar el manifiesto y autorizar su hash exacto para preparar:

```powershell
python <runtime>/scripts/lks_sdd.py v3 store-compact <proyecto> --input <preview-externo.json> --authorize <hash> --view operational --json
```

El respaldo externo contiene `manifest.json` y `batch-NNNN.zip`; cubre todos los
objetos lógicos, incluidos grandes y ya empaquetados. La restauración reconstruye
ese conjunto por hash. No es un respaldo integral del repositorio ni de su runtime.
La preparación conserva todos los originales y puede terminar en
`awaiting-removal-authorization` o `paused`. El único diario compartido bloquea otros
escritores hasta completar o finalizar explícitamente conservando originales.

```powershell
python <runtime>/scripts/lks_sdd.py v3 store-recover <proyecto> --authorize <hash> --status --view operational --json
python <runtime>/scripts/lks_sdd.py v3 store-recover <proyecto> --authorize <hash> --view operational --json
```

La primera llamada solo consulta estado; no certifica integridad actual ni autoriza
retirar. La segunda verifica el estado durable y continúa localmente. Tras comprobar
respaldo y restauración de todo el alcance, otra autorización permite retirar:

```powershell
python <runtime>/scripts/lks_sdd.py v3 store-recover <proyecto> --authorize <hash> --authorize-removal <hash> --view operational --json
```

Solo se retiran duplicados sueltos elegibles con cobertura empaquetada y copias
verificadas. La autoridad de retirada persistida sobrevive a una interrupción;
reanudarla no exige repetir esa autorización. Un original ya ausente se verifica
contra sus copias, sin atribuir otra eliminación. Los objetos >8 MiB quedan sueltos.

Antes de la primera retirada se puede liberar el diario conservando originales:

```powershell
python <runtime>/scripts/lks_sdd.py v3 store-recover <proyecto> --authorize <hash> --finalize-without-removal --view operational --json
```

Este cierre verifica originales y copias activas, conserva destinos externos y
declara el respaldo como parcial o no verificado. No declara compactación completada.
Una copia activa corrupta mantiene el bloqueo; conflictos externos se conservan.
Después de una retirada parcial hay que completar la recuperación autorizada.

No borrar ni editar el diario, respaldo, paquetes o staging para forzar progreso.
Los temporales se identifican por operación y destino; contenido contradictorio
se preserva. Corregir explícitamente la causa y reanudar el mismo hash. Un fallo de
salida informa del pendiente/recibo: inspeccionar y usar `store-recover`, sin repetir
`store-compact` a ciegas. Un recibo terminal histórico no certifica integridad actual.

## Límites y espacio

- Hasta 50.000 objetos lógicos; 64 MiB por objeto y por lote, hasta 4.096 objetos
  por lote, sin dividir un objeto. El límite de recorrido JSON se aplica por objeto:
  un millón de nodos/trabajo decodificado; exceso, recursión o tiempo fallan explícitamente.
- Respaldo de cada lote ≤66 MiB físicos; objetivo ZIP 8 MiB, máximo 16 MiB,
  8.192 miembros e índice ≤1 MiB; índices acumulados ≤16 MiB. Manifiesto /2 ≤12 MiB
  y diario completo /2 ≤16 MiB. Los diarios de negocio conservan su límite anterior.
- Presupuesto de trabajo por invocación: 600 s. Un preview incompleto no es válido;
  una ejecución puede pausar en una frontera durable. El proceso local espera y
  continúa sin llamadas a la IA por lote. El límite de campaña de desarrollo es separado.
- La previsión suma respaldo y restauración completos, paquetes nuevos y margen
  atómico por volumen, sin descontar originales ni duplicar staging publicado por
  rename. El espacio libre observado no queda reservado frente a otros procesos;
  se comprueba de nuevo al escribir y un error real de disco conserva el pendiente.
- Para 800.539.116 bytes, de los que 686.951.061 son compactables, el contenido
  nuevo requiere al menos 2.288.029.293 bytes antes de cabeceras y márgenes. Revisar
  la admisión calculada, no asumir que basta el tamaño de un ZIP objetivo.

Las llamadas con `backup` conservan el contrato /1 y su límite global de 64 MiB;
no se interpreta un nombre ZIP como directorio. Para almacenes grandes, usar
`backup_dir` tras actualizar explícitamente el runtime. No hay GC ni compactación
automática, y ZIP_STORED reduce archivos sin prometer ahorro de bytes o tokens.
