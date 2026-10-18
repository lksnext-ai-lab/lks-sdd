**Actualización posterior:** el usuario autorizó cuatro plazas adicionales y 45 min. La nueva serie está completada; saldo conocido/reservado 54/54, H2 protegida. [Resultado vigente](RESULTS-V4-17-SHARED-COMPARISON.md). Las cifras previas se conservan como antecedente.

# Decisión — Medir con variabilidad del equipo compartido

Fecha del cliente: 2026-10-18. Decisión del usuario:
«va a ser imposible tener un mayor control de cargas. Tendremos que tomar
decisiones asumiendo esta variabilidad».

## Disposición vigente

Se retira la exigencia de sesión exclusiva, runner dedicado y dispersión ≤5 %
como condición para continuar el desarrollo o preparar otra medición. No se sigue
buscando estabilidad por repetición ni se solicitan más cierres de aplicaciones.
Las series y los veredictos anteriores permanecen intactos: no se convierten en
favorables ni se atribuye su variación a una causa no demostrada.

| Aspecto | Tratamiento vigente |
|---|---|
| Variación, calentamiento y cargas ajenas | Se registran como limitaciones. La presencia de otra carga no invalida por sí sola una futura muestra; tampoco demuestra su efecto causal. No se promete igualdad instantánea de carga entre brazos. |
| Comparabilidad y garantías | Mismos inputs, caso, límites, efectos y configuración declarada para ambos brazos; fuentes/runtime fijados y sujetos comprobados; job propio y descendientes contabilizados. Cambios de archivos, trabajo desigual, errores propios, resultados incompletos o fallos funcionales mantienen su bloqueo. |
| Evidencia técnica directa | Lecturas evitadas, bytes reales y resultados funcionales se valoran por su cobertura. Proyecciones estáticas se identifican como tales. No equivalen a ahorro de tiempo total o tokens. |
| Tiempo y sobrecoste | Se conserva todo dato bruto, orden, diferencias por pareja y dispersión. Con pocas muestras y carga no controlada, las conclusiones son descriptivas; un resultado favorable aislado no acredita causalidad ni generalización. |

El objetivo temporal S8 ≥20 % no cambia: mediana de las dos reducciones AB/BA,
ambas positivas, sin fallos y con las reglas de memoria originales. AC-40 conserva
su límite de sobrecoste; si el ruido impide acreditarlo, queda inconcluso. No se
certifica ahorro por aceptar variabilidad. Los cuatro S8 anteriores siguen con
rendimiento rechazado y las correcciones posteriores sin validación integral.

## Próxima medición, únicamente cuando esté autorizada y financiada

Congelar antes de empezar la candidata exacta, entradas, orden ABBA y una única
política de afinidad/ejecución para A y B. Conservar arranques en frío y todo coste
previsto del recorrido. Usar una preparación fija y acotada, sin esperar hasta que
el calentamiento o la dispersión resulten favorables. No usar el helper de
calentamiento estable ni `control_ready` del control estricto histórico como puerta
de entrada de esta campaña; su lógica y sus tests se conservan como diagnóstico.
El adaptador de la próxima campaña tendrá que reflejar esta política antes de correr.

Registrar cargas observables sin detenerlas automáticamente; mantener aislamiento
de archivos, identidad y contabilidad del árbol propio. Ejecutar solo los intentos
previstos, conservar todos los válidos y los fallidos con sus causas, no escoger
los más rápidos ni repetir hasta pasar. Informar resultado observado, incertidumbre
y decisiones de producto por separado. No fabricar intervalos de confianza con
solo dos parejas ni cambiar a posteriori los umbrales.

Esta decisión no añade plazas ni horas: registro conocido/reservado 50/50, cero
plazas S8 libres y dos H2 protegidas. No se solicita ni lanza otra serie aquí.
Cualquier nueva serie de cuatro requiere su reserva separada y candidata exacta.
Las seis mejoras, 23 tareas y 44 criterios permanecen. Windows y H2 pendientes;
sin instalación, publicación, commit o push. No hay nuevas pruebas de carga.
