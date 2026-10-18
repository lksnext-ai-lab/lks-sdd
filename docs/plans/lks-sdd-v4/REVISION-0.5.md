# Plan 4.0 — revisión 0.5 autorizada

Fecha: 2026-10-17, Europe/Madrid. P01 valida separar la incidencia del aislamiento
de Codex/Windows, mantener H2 pendiente, reasignar el saldo y ejecutar **solo V4-06**.
Esta decisión sustituye las paradas anteriores que impedían iniciar V4-06 por H2.

- La incidencia del host se conserva abierta y fuera del camino de implementación.
  Sus perfiles retirados, recursos compartidos y trazas privadas no se reutilizan.
- H2/AC-34 sigue pendiente, con referencia/candidata fijadas y sus dos plazas
  reservadas. No se acredita ahorro, aceptación de host ni percepción humana.
- V4-06 depende de la porción técnica verificada de V4-05A y de V4-02B; no exige
  resolver ese aislamiento ni cerrar AC-34 para desarrollar y verificar código.
- Las seis mejoras y AC-11/12/13 no cambian. La pareja S8 temprana sigue en V4-06,
  desde procesos CLI sobre consumidores sintéticos; no utiliza el aislamiento de
  Codex ni llamadas de modelo. Se mantiene el corte de 600 s por intento y dos plazas.
- Se mantienen compatibilidad Windows, rutas largas, guardas, evidencias y pruebas
  independientes de host. Eludir el aislamiento no es una técnica de validación.
- En la aprobación inicial solo se autorizó V4-06. La petición posterior solicita continuar el desarrollo, sin ampliar tiempo ni autorizar instalación, publicación, commits o push.

## Reasignación y corte

47 turnos cerrados: cargo conciliado **45.027,511956 s**, incluido el descuento
histórico único y 42,341 s de conservación técnica entre turnos ya acreditados.
Saldo al inicio del bloque (22:33:41,408 UTC): **8.972,488044 s = 149 min 32,488 s**
bajo el máximo aprobado de **15 horas**. No se abre otra bolsa ni se reinicia el reloj.
Se reasigna el saldo que antes protegía Windows/H2 a implementación/verificación;
H2 queda con plazas reservadas, sin una nueva reserva de tiempo financiada en este bloque.

| Trabajo de este bloque, desde su inicio | Cota |
|---|---:|
| Conciliación, cambio de plan y diseño concreto | 10 min |
| Adaptadores de continuación y resultados, integración pública | 50 min |
| Pruebas focales, regresión y correcciones | 40 min |
| Preparación y pareja S8 temprana AB, máximo 600 s por intento sujeto al saldo | 25 min |
| Evidencia, diff e informe | 10 min |
| Contingencia protegida para recuperación y cierre | 10 min |
| **Total, incluido el trabajo actual** | **145 min** |

Margen contable inicial: 4 min 32,488 s. Las cotas no prometen terminar. Cada
intento S8 solo se admite con reserva para el otro y el cierre; si no cabe, se
declara pendiente, sin ejecutar media comparación ni reducir cobertura. El saldo
no acredita viabilidad del resto de 4.0. Se contabilizan fallos y correcciones.

Distribución ajustada antes de medir S8: 25 minutos permiten reservar ambos cortes
de 600 s y su preparación sin exigir que el primer intento termine antes del límite.

## V4-06: tareas y aceptación concreta

1. Exponer `work-continue/1` para inicio/reanudación técnica autorizados, sin
   recepción, revisión o decisiones nuevas implícitas.
2. Exponer `work-record-results/1` para implementación, evidencia, verificación y
   cierre técnico elegibles; no ejecutar comandos incluidos en JSON ni integrar,
   publicar o aceptar funcionalmente.
3. Conservar las transacciones individuales y sus guardas frescas por etapa.
   La correlación técnica y la base se vinculan al preview hasheado del journal
   existente; no se necesita almacenamiento canónico nuevo. La salida exportada
   solo localiza paquetes/recibos. El journal conserva el contenido antes del primer
   cambio material y se comprueban los hechos antes de reutilizar efectos.
4. Ante fallo o interrupción devolver los efectos acreditados y la etapa pendiente;
   reintento exacto no duplica efectos y cambios posteriores impiden continuación.
5. Verificar entrada estricta, base, sujeto, runtime, permiso revocado, receptor
   ajeno, revisión independiente, evidencia fallida/antigua, concurrencia,
   interrupciones y compatibilidad con operaciones individuales. AC-11/12/13
   mantienen sus obligaciones literales en VALIDATION.md.
6. Ejecutar las comprobaciones aplicables de docs/VALIDATION.md y revisar el diff.
   Comparación S8 descriptiva; H2 y aceptación final no se sustituyen por pruebas.

Ajuste interno anterior a S8: los hallazgos de frescura durante preparación y de
inyección de errores desplazan 10 min de implementación a validación, sin ampliar
los 145 min ni los máximos globales y sin recortar pruebas. El informe se prepara
durante las esperas. Para admitir la pareja con la preparación ya completada se
exigen 1.200 s para sus dos cortes, 600 s protegidos para recuperación/cierre y
60 s de margen. Son reservas restantes, sin cobrar de nuevo preparación o informe
ya realizados; el cargo real sigue siendo el reloj único del bloque.

Reasignación final antes de medir: el margen contable inicial de 272,488044 s se
incorpora como contingencia ya financiada de V4-06. Se conserva la distribución
ordinaria de 145 min; el corte efectivo máximo es 8.972,488044 s desde el inicio,
01:03:13,896044 UTC, exactamente el saldo dentro de 15 h. No es una ampliación
de horas ni de plazas y no financia tareas posteriores. Se mantiene la admisión
con 1.200 s para ambos intentos, 600 s de recuperación/cierre y 60 s de margen.

## Consolidación y continuación posterior

[V4-06](RESULTS-V4-06.md) queda implementada, con AC-11/12/13 técnicamente verificados,
pero el S8 temprano válido empeora tiempo/memoria/transporte. PERF-V4-06-01 sigue
abierto dentro de M2/M6; no se declara ahorro ni aceptación de 4.0. La ejecución
empleó dos contingencias para corregir un arnés que suponía un `app.py` inexistente;
se conservan ambos intentos fallidos. Quedan dos contingencias y 45/48 plazas
conocidas/reservadas, sin rebajar cobertura.

El usuario solicita después continuar el desarrollo. Esto permite preparar su
continuidad, pero no amplía el máximo de 15 h ni autoriza instalación/publicación.
El cargo anterior cerrado dejó 1.453,005044 s al reanudar a las 11:13:51,150 UTC.
La espera entre sesiones no se carga. El corte UTC 01:03 anterior era el de aquel
turno: no se aplica como reloj de pared a una sesión posterior. El reloj vigente
y saldo, sin doble cargo, están en `v4-06-progress.json` y en el informe de resultados.
El saldo no financia la corrección con verificación completa ni las 14 tareas
restantes. No se inicia producción adicional sin capacidad para comprobarla.
