# Promoción de rc.3 a LKS-SDD 3.4.3

El 2026-10-15 el responsable aprueba expresamente integrar rc.3, crear la release
estable, subir el trabajo a GitHub y actualizar LKS-SDD en Codex. La aprobación
está registrada en `quality/release-approval-v3.4.3.json`. Se mantienen schema 3.1,
método 3.1.0 y las fuentes canónicas. La instalación no migra runtimes fijados en
proyectos consumidores.

## Código seleccionado

Los diez módulos de producto coinciden byte a byte con el manifiesto de rc.3,
antes y después de cambiar la versión. La huella de `scripts/v3_contract.py` es
`0b8a6221e61fbf3b6ff814f596108d85bb826d5c8911955aa239f92bf3c5c4ca`.
Se conservan índices, invalidación, observación profunda, guardia de inmutabilidad,
límites de caché, lectura física fresca y hashing por bloques. No se incorporan
las dos variantes de memoria rechazadas en [el experimento rc.4](MEMORY-EXPERIMENT-RC4.md).
Los informes de [rc.1](IMPLEMENTATION-RC1.md), [rc.2](IMPLEMENTATION-RC2.md) y
[rc.3](IMPLEMENTATION-RC3.md) describen su preparación histórica.

## Evidencia y límites

La preparación rc.3 superó 63 pruebas distintas y cada paquete Codex/Copilot
completó 21 comandos públicos y cinco rechazos sin escritura. Después de descartar
rc.4 se restauró rc.3 y se repitieron 22 pruebas focales y el contrato estático.
Estas comprobaciones no sustituyen el gate estable del commit integrado.

El perfil diagnóstico de 1.500 elementos midió 2.563.355 bytes vivos en 3.4.2,
3.723.196 en rc.2 y 3.084.644 en rc.3: −17,2 % frente a rc.2 y +20,3 % frente
a 3.4.2. Son asignaciones trazadas, no memoria total del host ni picos RSS.
La matriz aislada completa rc.3/rc.2/3.4.2 quedó incompleta y su serie anterior
se excluyó. No se presenta como superada. Las mediciones posteriores contra rc.3
permitieron rechazar rc.4; no acreditan por sí solas una mejora general frente a
3.4.2. No se midieron tokens facturados ni aceptación conversacional o piloto.

`docs/evidence/approval-performance-3.4.3.json` vincula las fuentes y las pruebas
anteriores por SHA-256. El archivo de evidencia adjunto a la release conserva las
muestras, paquetes e informes de investigación; se distingue de los assets estables
generados por CI. No se alteran los informes históricos para simular su cierre.

## Publicación y actualización

La puerta de `docs/VALIDATION.md` se ejecuta sobre el commit limpio integrado en
`main`: aprobación, fixtures/contrato, catorce pruebas de humo y rutas largas de
Windows. El preflight genera una vez los paquetes; la etiqueta estable verifica
y reutiliza evidencia del mismo SHA. La referencia Copilot identifica el árbol
nativo del ZIP validado mediante un commit distinto del de mantenimiento.

La instalación de Codex se realiza desde el paquete publicado verificado,
conservando `lks-sdd@lks-sdd-development` y rollback. Los resultados de CI y los
assets publicados acreditan la entrega; el registro local acredita instalación
y descubrimiento de las seis skills. Una conversación nueva sigue siendo necesaria
para observar la activación efectiva de instrucciones actualizadas.
