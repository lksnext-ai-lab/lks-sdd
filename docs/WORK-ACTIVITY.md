# Actividad e interrupción de las operaciones V4

`v3 ... --activity` emite por stderr líneas JSON breves como
`{"activity":"prepare"}`. Stdout conserva un único resultado JSON y las opciones
de presentación y captura existentes. Es una señal de proceso vivo y fase actual:
no prueba avance del cálculo, porcentaje, tiempo restante ni autorización.
Sin la opción no se crea el hilo de señales ni se escribe actividad. No requiere TTY.

El canal intenta una señal inmediata y después cada 1,5 segundos, con máximo de
16 KiB por invocación y menos de 1 KiB por evento. Un canal cerrado se desactiva;
un pipe sin lector no bloquea el hilo principal. El presupuesto permite cubrir el
intento experimental de hasta 600 segundos. Agotarlo detiene las señales, nunca
el trabajo. La planificación del sistema y llamadas nativas pueden retrasarlas;
las cotas se verifican en las superficies declaradas, no son garantías de tiempo
real ni aceptación observada de Codex/Copilot.

Ctrl+C es cooperativo en `work-prepare`, `work-continue` y
`work-record-results`, desde la entrada en la CLI compartida. Los checkpoints están
en lectura de fuentes, carga de modelo, bloques de parseo, consultas memoizadas y
fronteras de preparación, guardas y etapas. Las lecturas, Git, hashing, serialización
y otras llamadas nativas pueden terminar antes del siguiente checkpoint. Una
escritura material completa su etapa y conserva su recibo antes de reconocer la
parada. No se interrumpe a mitad de un `replace` ni se ejecuta `cancel` de negocio.
Otros comandos conservan su tratamiento de interrupciones previo.

La salida conserva efectos y recibos reales; una parada sin efecto sale con 130,
con efectos o journal pendiente con 3. Nunca presenta la parada como éxito. Un
journal pendiente exige `recover`/`rollback` explícito con su hash y guardas
existentes. Reintentar el mismo intento reconoce etapas durables sin duplicarlas;
cambios posteriores pueden bloquearlo y se preservan. Ni detener ni recuperar
borra objetos inmutables compartidos, trabajo ajeno o directorios por prefijos.

La captura externa puede haber publicado objetos o una entrada antes de detenerse.
Se informa de inspección pendiente y se conserva su área; no se repite una operación
normativa para reparar transporte. No se promete cero artefactos ni aborto instantáneo.
No se añaden estados canónicos, servicios, hooks ni instalación. El arranque del
host, la incidencia de aislamiento de Windows y H2 permanecen fuera de esta prueba.
