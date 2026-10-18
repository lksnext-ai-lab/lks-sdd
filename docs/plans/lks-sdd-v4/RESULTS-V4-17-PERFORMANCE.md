# V4-17A — Cuatro ejecuciones finales: rendimiento no aceptado

Fecha del cliente: 2026-10-18. **Las cuatro ejecuciones han terminado, pero no se
acepta el rendimiento de la candidata.** Se conserva la evidencia adversa y se ha
corregido después un defecto de asignación de memoria con comprobaciones focales.
Esa corrección posterior no sustituye los bytes de la candidata medida.

## Resultado observado

Referencia 3.4.3: `bf4d059c98826039097d606121ab6406d762fcc7`.
Candidata medida: `cd148d56a17c81e00b25b1f79ff33bdbee1bfc8095024d1a115053538dfd993d`.
Fuente medida: `working-tree:11964e0b710b0f0ea678dbb388eddc83f510109cba175c6f5ce22a6ffaa9535d`.
Los cuatro paquetes fijados ejecutaron el mismo caso de 338 elementos y 35
tecnologías, en orden AB/BA, con originales y decisiones sin renovar, base confiable
intacta y TEMP/TMP de 299 caracteres. Procesos nuevos; caché física no forzada a fría.
Se reutilizaron el coordinador de negocio y los umbrales originales. Sin perfilador
ni otras pruebas concurrentes; no se sustituyen muestras por su resultado.

| Intento | Tiempo completo, s | Pico comprometido del job, MiB | Ventana |
|---|---:|---:|---|
| 1-A | 202.287 | 112.71 | Completo y aislado |
| 2-B | 162.363 | 141.56 | Completo y aislado |
| 3-B | 179.241 | 141.50 | Completo y aislado |
| 4-A | 100.217 | 112.56 | Completo y aislado |

Las dos parejas son completas y válidas en las condiciones de admisión:
- AB: reducción temporal **19.74 %**;
  crecimiento de memoria **25.60 %**.
- BA: reducción temporal **-78.85 %**;
  crecimiento de memoria **25.71 %**.
- Mediana pareada de reducción **-29.56 %**: no cumple
  >=20 % ni la condición de ambas parejas positivas. El techo absoluto de 512 MiB
  pasa, pero el cociente <=1,1 falla en ambas parejas.
- La referencia varía de 202,287 a 100,217 s; la fase de parseo fijo también mostró
  variación de CPU sin Python ajenos. No se atribuye causalmente esa dispersión a
  Windows, hardware o plugin sin evidencia adicional. Tampoco se usa para borrar
  la regresión observada ni aprobar la candidata.
- Llamadas públicas **12 -> 9 (-25 %)**, pero stdout/stderr aumentan aproximadamente
  **86,4 %** y el flujo completo de entrada/salida **39,8 %** en ambas parejas.
  Menos llamadas no acredita ahorro integral ni de tokens. S8 no sustituye las
  ventanas/casos E1/E2/E3 originales de host.

El coste completo de los cuatro recorridos fue
**644.109 s**, incluidos arranque, CLI, E/S,
prueba Python real, cierre, integración sin aceptación y diagnóstico. Preparación,
controles focales y análisis son costes separados; no se trasladan fuera del
denominador trabajos necesarios del recorrido.

## Garantías y actividad

Todos pasan la prueba real de `greeting() == 'Hola'` sin parámetros, fuentes
literales y prosa no clasificada, documentos iniciales y runtime íntegros,
conservación e inspección de diagnóstico, cierre e integración sin aceptación
funcional. Cero journals pendientes al finalizar; originales/base confiable y los
cuatro consumidores se conservan como evidencia. Las regresiones de autoridad,
caducidad y cambios entre preparación/aplicación se reutilizan donde no cambió el
código pertinente. No se crea una autorización ni se renueva una decisión.

Las señales de los dos recorridos B cumplen cadencia/volumen y conservan JSON.
El primer control local de sobrecoste quedó demasiado corto por calibrarse con
el primer parseo frío (~0,2 s medidos); su resultado inconcluso se conserva.
Se hizo una única corrección de calibración, con los mismos bytes, umbrales y orden
ABBAAB, calentamiento común y unas fases de 5–7 s. Las diferencias medianas
(0,314 s de tiempo y 0,297 s CPU) quedan bajo sus límites (0,327 y 0,323 s), pero
las dispersiones de 15–26 % superan el 5 % preregistrado. **AC-40 sigue inconcluso**;
no se repite hasta conseguir un resultado favorable ni se modifica el umbral.

## Defecto de memoria corregido después de medir

`diagnostic_capture.read_file` pedía `maximum+1` bytes: hasta 64 MiB aun cuando
el archivo observado era pequeño. Ahora pide `size+1`, manteniendo el límite,
rechazo ante crecimiento/lectura corta, rutas seguras, huellas y recuperación.
La prueba nueva comprueba el tamaño pedido, crecimiento, reducción y rechazo del
presupuesto antes de abrir. **8 regresiones focales pasan**; se reutilizan las 41
comprobaciones anteriores en su alcance no afectado. Contrato y 13 fixtures válidos.

En dos procesos nativos nuevos, leyendo el mismo archivo de cinco bytes con las
funciones reales anterior/posterior, el pico comprometido pasó de
**85.38 a 21.34 MiB**: se elimina una asignación de aproximadamente
64 MiB en ese componente. Se registran código, hashes, resultado y contabilidad del
job. **No es una nueva pareja S8 ni acredita el pico o el tiempo del recorrido.**

Fuente posterior: `working-tree:77087026c10d517a26c6f99a965a64381ea5119d33b16acc6e6627215b3f765f`. Aún sin empaquetar ni revalidar en S8. Los cinco ZIP
reproducibles previos conservan la candidata medida; no se presentan como si ya
incluyeran esta corrección. No se cambia contrato canónico, esquema, autoridad o
semántica de negocio. No se declara cerrada la regresión global de memoria.

## Pendientes concretos y presupuesto

1. Localizar y corregir el coste y las entregas repetidas en preparación/composición
   y captura, preservando el contrato íntegro y la frescura. Las regresiones de fase
   >10 % quedan abiertas; integración/presentación y resultados destacan en las
   comparaciones conservadas. Ninguna optimización opcional M6 se acredita aquí.
2. Establecer una medición local de actividad suficientemente estable sin relajar
   los límites. Investigar la dispersión antes de otra campaña; aislamiento de Python
   por sí solo no la explica ni la elimina.
3. Solo después, empaquetar el código corregido y validar ese candidato exacto con
   una nueva serie completa. Los cuatro intentos autorizados están consumidos:
   **cero plazas S8 libres**, registro conocido/reservado **50/50**, dos plazas H2
   intactas. Una nueva serie requiere cuatro plazas adicionales, sin tomarlas de H2
   ni inferir horas extra o un saldo global certificado.

AC-42 pasa para la candidata medida; AC-43 falla, AC-40 sigue inconcluso y AC-26 no
se acepta. El cambio posterior obliga a distinguir esa cobertura de la futura
candidata. E1/E2/E3 en host, H2/AC-34, Copilot y percepción humana sostenida conservan
su estado previo. Windows sigue apartado. No se instala, publica, hace commit ni push.

Los cuatro servidores originales quedaron cerrados (tres detenidos y uno ya
finalizado); después, con otra autorización explícita, se detuvieron los 14 nuevos
procesos identificados de visualización/documentación. Sus archivos se conservaron.
No se reinician automáticamente los servicios detenidos. Ambos recibos y el
manifiesto original permanecen; `continuation-window.json` declara la ventana actual
sin borrar la expiración anterior ni reiniciar el contador de intentos.

Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-17\performance`. `results.json`, `comparison.json`, cuatro salidas completas,
capturas, auditoría de procesos, controles de actividad anteriores/corregidos,
`allocation-tests.json`, `allocation-component-result.json` y
`post-allocation-correction.json`. Tokens facturados/observados del host: `null`.
