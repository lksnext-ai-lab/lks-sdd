# Capacidad puntual de LKS-SDD 4.0.3

Versión 4.0.3. La validación técnica no acredita aceptación del consumidor real ni H2.

El límite de un documento no se aplica a objetos CAS ya válidos: el lector lógico
comprueba hasta los 64 MiB de su representación, longitud, SHA-256 y todas las
copias sueltas/ZIP. Esto corrige el bloqueo del guard de `close-proposal` sin
pedir permiso adicional por un objeto que ya era válido.

## Solicitud y respuesta

Ante un presupuesto operativo insuficiente, la CLI devuelve código 2 y
`status: capacity-approval-required`, con `capacity_request`. Describe proyecto,
operación, huella de entrada/estado, recurso alcanzado, valor observado, presupuesto
ordinario y ampliaciones finitas. La previsión agrupa las capas compatibles de la
operación para reducir preguntas sucesivas. No es una aprobación funcional.
Son cotas máximas: no reservan recursos ni cambian preferencias globales.

Presentar al usuario los recursos, cantidades y posible coste adicional de RAM,
tiempo y disco. Solicitar su OK explícito. Nunca fabricar, preseleccionar ni
interpretar el silencio como autorización. Si lo rechaza, conservar el trabajo
pendiente sin aplicar el cambio. No cambiar a otra operación para eludir el límite.

Solo después del OK, conservar fuera del consumidor un JSON:

```json
{
  "request": "Sustituir por el objeto capacity_request exacto, sin cambiar sus campos",
  "approved": true,
  "statement": "Respuesta literal explícita del usuario"
}
```

Repetir la misma operación añadiendo `--capacity-approval <archivo-externo.json>`.
La respuesta debe copiar un objeto en `request`, no la cadena explicativa del ejemplo.
No hay un flag que acepte límites automáticamente ni una configuración permanente.
Cambiar el proyecto, operación, entrada o generación transaccional invalida el
consentimiento. El recibo de presentación se verifica normalmente; renovarlo sin
cambiar la intención no concede ni requiere por sí solo otra autorización de recursos.

## Aplicación y recuperación

Las guardas del paquete conservan la respuesta completa. Su hash queda incluido
en el preview autorizado. `apply`, `recover` y `rollback` restauran esos presupuestos
para la misma transacción, también en procesos nuevos y mediante el recuperador
compartido. No necesitan repetir el OK original ni crear otra decisión funcional.
El consentimiento no se consume como permiso global para tareas futuras.
Las escrituras ampliadas exigen un recuperador compatible fijado en el consumidor;
un runtime anterior requiere su actualización explícita. No se actualiza automáticamente.
El mantenimiento /2 conserva la respuesta en su manifiesto autorizado, manteniendo
la autorización separada de retirada de originales.

Si aparece una necesidad superior, se requiere otra respuesta explícita. Si ya
hay diario pendiente, la CLI informa `partial`, identifica el hash y dirige a
`recover`; no debe repetirse ciegamente la operación original. Se mantienen los
controles de fuentes, cambios posteriores, integridad y autoridad existentes.

## Presupuestos compatibles y fronteras

La ampliación cubre lecturas ordinarias, carga documental, inventarios de fuentes,
código/sujetos, mapas técnicos, estados documentales, índices ZIP acumulados,
cantidad/volumen de paquetes y lotes/ventanas/material diagnóstico. Los números
propuestos se muestran en el `capacity_request`; no son límites nuevos globales.

La política no cambia representaciones: siguen vigentes 64 MiB por objeto,
64 MiB por descriptor de paquete, geometría ZIP y formatos/diarios de mantenimiento
/1 y /2, incluidos sus presupuestos declarados. No se ofrece una autorización que
pueda producir datos incompatibles con esos lectores. Superar estas fronteras
requiere evolución compatible del formato, fuera de esta corrección puntual;
compactar no es requisito para continuar trabajo funcional. La recuperación de
negocio conserva su límite compatible de diario y no debe escribir uno ilegible.

No se flexibilizan rutas, enlaces/junctions, hashes, contenido obligatorio,
permisos, aprobación de especificaciones o aceptación. No hay limpieza ni
actualización automática de consumidores. Windows/H2 siguen pendientes.
