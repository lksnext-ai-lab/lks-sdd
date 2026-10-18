# Continuar trabajo y registrar resultados

V4-06 añade dos operaciones al CLI compartido. Requieren método 3.1.0 y runtime
fijado que contenga exactamente las capacidades nuevas; instalar un plugin no
actualiza el runtime del consumidor. Los comandos individuales se conservan.

```text
python scripts/lks_sdd.py v3 work-continue ROOT --input intent.json --view operational --json
python scripts/lks_sdd.py v3 work-continue ROOT --input intent.json --apply --view operational --json
python scripts/lks_sdd.py v3 work-record-results ROOT --input results.json --apply --view operational --json
```

Sin `--apply`, se prepara únicamente la siguiente etapa y se entrega el contrato
literal. No se escribe en el consumidor. `--output` conserva el resultado íntegro,
incluido el paquete de esa etapa; la vista operativa omite su payload redundante.
Ese paquete corresponde solo a su etapa; aplicarlo exige autorización vigente.
No concede decisiones ni permisos para etapas futuras.

La entrada es `lks-sdd-operation-request/1`, `version: 1`, con `operation_id: "auto"`,
UID canónico de `task`, UID de `actor`, `basis` y `parameters`. Se rechazan claves
desconocidas, tipos erróneos, cambio de intención con el mismo ID y acciones ajenas.
`work-prepare` entrega `operation_bases[task_uid]`: copiar ese objeto completo en
`basis`. Contiene snapshot documental, rama/HEAD, inventario de código, sujeto
exacto y estado observado. Es una instantánea; no concede autorización.

- `work-continue`: parámetros `action` (`start` o `resume`) y `reason`.
  No recibe ofertas ni aprueba revisiones por flags. Si falta una decisión nueva,
  se utiliza primero el recorrido individual de presentación/respuesta vigente.
- `work-record-results`: `target` (`implemented`, `evidence`, `verified`, `closed`),
  `reason` y lista opcional `evidence` de hasta 20 elementos. Cada elemento contiene
  `tests`, `outcome`, `source`, `artifact`, `artifact_sha256`, `subject` y `explanation`.
  `subject` es exactamente el observado en basis. El archivo debe existir y coincidir
  con su hash. Los resultados proceden de pruebas ejecutadas/observaciones externas;
  este comando no ejecuta código, comandos ni pruebas contenidos en JSON.

La evidencia conserva la procedencia declarada del mecanismo existente; un hash
no autentica al productor ni demuestra por sí solo que una prueba se ejecutó.
Un reporte de otro sujeto se rechaza. `failed`/`not-run` pueden registrarse como
hechos, pero no satisfacen las condiciones de verificación o cierre.

Cada etapa usa su transacción y guardas actuales: permiso, asignación, revisión,
política, alcance, rama, sujeto, calidad y evidencia. Se detiene ante la primera
condición pendiente; puede haberse registrado implementación sin poder verificar.
La base vuelve a comprobarse después de preparar la etapa y antes de aplicarla;
un cambio durante la preparación impide esa escritura y conserva el cambio ajeno.
No integra, publica ni acepta funcionalmente el resultado; una revisión independiente
pendiente sigue correspondiendo a otra persona.

## Reintento y recuperación

La correlación se incorpora al nombre técnico hasheado de la transacción vigente.
La guarda técnica `work_basis` conserva las fuentes iniciales cubiertas por el
preview; sirve para comprobar la secuencia, sin convertirla en autorización.
No se añaden campos al Markdown, estados, permisos, almacenamiento canónico ni un
manifiesto que se convierta en fuente de autoridad. La salida exportada es una ayuda
de localización. La aplicación persiste el journal existente antes del primer
cambio material. El reintento consulta sus recibos y comprueba hechos, tarea, actor,
sujeto, secuencia de fuentes y contenido; no deduce autoría de un estado coincidente.

Reutilizar exactamente la misma entrada/operation_id no repite efectos. Una
interrupción dentro de una escritura devuelve el hash pendiente: usar `recover`
o `rollback` existentes, explícitamente, y después reintentar. La composición no
restaura ni sobrescribe trabajo posterior para fingir atomicidad. Si cambian fuentes,
autoridad, rama o código, conservar lo aplicado y preparar la porción restante con
una base nueva. Los recibos ya completados no conceden permiso para pasos futuros.
En operational, el recibo `completed` evita repetir el campo superior `contract`;
las consultas, previews, bloqueos y aplicaciones parciales siguen entregándolo
íntegro. No se presupone que el host conserve una lectura anterior: antes de nuevo
trabajo hay que consultar el contrato vigente. API/details y los destinos
explícitos output/capture conservan el resultado completo si la entrega tiene
éxito. Un fallo de transporte exige inspeccionar los efectos antes de reintentar.
Tras una reversión que restaura exactamente la base original, una intención nueva
debe distinguirse expresamente, por ejemplo por su motivo; el intento revertido
no se recicla automáticamente.

Estados: `ready`/`completed` código 0; bloqueo o intervención código 2; aplicación
parcial o recuperación pendiente código 3. `effects` identifica etapas y recibos
reales; `writes` solo las escrituras devueltas por las aplicaciones de esta llamada.
Ante pérdida de entrega, los recibos pueden acreditar efectos aunque `writes` esté
incompleto; no es un inventario de auditoría independiente. `--capture-dir` conserva
el diagnóstico externo conforme a DIAGNOSTIC-CAPTURE.md. Un error de exportación o
captura posterior no deshace efectos: inspeccionar el journal antes de reintentar.
Si falla la exportación después de aplicar etapas, la salida conserva `effects`,
`operation_id` y `operation_status`; el código 3 señala esa entrega parcial.

Esta entrega técnica no acredita H2, ahorro completo en host, aceptación humana ni
la versión 4.0 publicada. Las seis skills y la invocación implícita se conservan;
su adaptación completa sigue perteneciendo a V4-11.
