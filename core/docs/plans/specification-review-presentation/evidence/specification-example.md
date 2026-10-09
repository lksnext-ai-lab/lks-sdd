# Consultar el saldo de una cuenta

## Objetivo

Consultar saldo

## Alcance incluido y excluido

**Incluido:**
- Consulta del titular

**Excluido:**
- Movimientos

## Comportamiento esperado

Devuelve el saldo al titular y deniega el acceso a otras personas

## Solución técnica

### Pantalla de consulta del saldo

**Responsabilidad:** Solicitar y mostrar el saldo de la cuenta seleccionada.

**Situación actual:** Componente propuesto; este ejemplo no acredita una interfaz existente.

**Cambio propuesto:** Añadir la consulta y los estados de carga, saldo disponible, acceso denegado y error temporal.

**Contratos e interfaces:** Solicitar GET /accounts/\{accountId\}/balance; recibir importe y moneda. Una respuesta 403 muestra acceso denegado sin datos de saldo.

**Datos:** Mostrar el importe recibido sin modificar movimientos ni mantener una copia persistente.

**Errores y seguridad:** No mostrar datos anteriores al cambiar de cuenta; permitir reintentar un error temporal sin revelar información de otra persona.

**Comprobación:** Comprobar consulta correcta, cambio de cuenta, denegación de acceso y error temporal.

**Estado:** Propuesto

### Servicio de consulta de cuentas

**Responsabilidad:** Comprobar la titularidad y devolver el saldo autorizado.

**Situación actual:** Servicio propuesto; no se presenta como arquitectura ya observada.

**Cambio propuesto:** Exponer la consulta de saldo con autorización en el servidor y un límite de 30 consultas por minuto.

**Contratos e interfaces:** Recibir la cuenta solicitada y la identidad autenticada; devolver importe y moneda solo al titular.

**Datos:** Leer el saldo sin crear, modificar o eliminar movimientos.

**Errores y seguridad:** Responder con acceso denegado cuando la persona no sea titular; informar del límite de consultas y evitar exponer datos en errores.

**Comprobación:** Probar titular y tercero, ausencia de escrituras y aplicación del límite de consultas.

**Estado:** Propuesto

### Interacción del conjunto

La pantalla solicita el saldo. El servicio comprueba identidad, titularidad y límite de acceso antes de leer y devolver el importe; la pantalla muestra el resultado o el estado de error correspondiente.

### Contenido y condiciones de las fuentes

**Consulta del saldo**

El titular consulta el saldo actual; se conserva el registro de movimientos y el límite de acceso.

**Consultar el saldo de una cuenta**

Permitir consultar el saldo sin cambiar los movimientos.

**Permiso de consulta**

Solo el titular puede consultar. No se permite modificar el saldo; límite de 30 consultas por minuto.

## Impacto

Interfaz de consulta sin nuevas escrituras

## Criterios de aceptación

- El titular ve el saldo; otra persona no accede

## Decisiones pendientes

Ninguno declarado.

La respuesta se aplicará solo al contenido, alcance y efectos mostrados. Validar la especificación permite preparar el plan; ejecutar se autoriza sobre ese plan concreto.

Persona que decide: Operador de prueba.
