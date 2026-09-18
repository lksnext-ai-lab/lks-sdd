Implementa en Python 3.12+ las doce funciones descritas. Solo biblioteca estándar. Devuelve un módulo .py con las firmas exactas; no ejecución al importar, red, filesystem ni llamadas a herramientas desde las funciones. Los parámetros cumplen los tipos declarados salvo los casos de validación descritos. No añadir requisitos ni mutar entradas. No leas pruebas ni otras variantes del contexto. Si falta detalle usa criterio conservador y documenta supuestos brevemente en comentarios. Esta es una prueba de una sola entrega: no se facilitarán resultados para corregir antes de medir.


## C01 — ledger_total(amounts)
Encargo: Devuelve un string con dos decimales que suma importes en euros recibidos como strings. Usa aritmética decimal y no altera amounts.

Documentación de dominio: Contexto: el libro mayor recibe líneas de facturas de varios emisores; la conciliación compara cada línea ya contabilizada. La interfaz de revisión agrupa por proveedor y permite consultar el documento de origen. Una propuesta histórica de redondeo bancario quedó descartada. Los informes anuales pueden mostrar cuatro decimales, pero pertenecen a otra operación.

Reglas y excepciones vigentes: Regla contable vigente: cada línea se redondea primero a céntimos con ROUND_HALF_UP; después se suman las líneas. Acepta negativos. La lista vacía devuelve "0.00". Normaliza el cero, incluido negativo, a "0.00". No redondear únicamente el total ni usar float.

## C02 — local_day_ids(events, day, tz)
Encargo: Devuelve los ids, en orden de entrada, de eventos cuyo instante timestamp ISO8601 cae en el día local day (YYYY-MM-DD) de la zona IANA tz. No modifica events.

Documentación de dominio: Contexto: el cierre operativo usa el calendario del centro de trabajo, distinto del huso del servidor. La interfaz guarda el día como fecha civil y no como intervalo UTC. El almacén histórico conserva el timestamp original para auditoría. Los turnos semanales y el calendario laboral se gestionan en otro servicio.

Reglas y excepciones vigentes: timestamp debe incluir offset explícito o Z. Un timestamp naive provoca ValueError, incluso si parecería quedar fuera del día. Debe respetar cambios de horario DST: convertir cada instante a la zona indicada. Extremo inicial incluido, final excluido; no suponer días de 24 horas. Entradas válidas y listas vacías son admitidas.

## C03 — fold_events(events)
Encargo: Aplica eventos con campos tenant, key, seq (int), event_id, value y deleted (bool), y devuelve dict {(tenant,key):value} del último estado visible. No modifica events.

Documentación de dominio: Contexto: el consumidor recibe lotes reintentados y entregas fuera de orden. El almacenamiento de auditoría conserva los eventos originales. Los procesos de compactación física se ejecutan por separado, después de su ventana de retención. El orden de presentación de las claves no es contractual.

Reglas y excepciones vigentes: seq mayor gana sin depender del orden de llegada. deleted=true es tombstone: también participa en comparar seq y suprime la clave del resultado, por lo que una actualización más antigua no la resucita. Duplicados exactamente iguales con mismo (tenant,event_id) se ignoran. Ese identificador con contenido distinto provoca ValueError. Dos eventos distintos con mismo tenant,key,seq también provocan ValueError. event_id está aislado por tenant.

## C04 — can_read(user, resource)
Encargo: Devuelve bool para acceso de lectura. user contiene id, tenant, roles (list), disabled. resource contiene tenant, owner_id, public, denied_user_ids. No modifica entradas.

Documentación de dominio: Contexto: las organizaciones comparten infraestructura física y conservan administración funcional independiente. El rol admin permite administrar los recursos de su organización. La pantalla pública usa el mismo motor de autorización. La edición de recursos exige permisos distintos y queda fuera de esta función.

Reglas y excepciones vigentes: Precedencia obligatoria: disabled implica false; distinto tenant implica false incluso para admin; id en denied_user_ids implica false incluso para admin/propietario/public. Superados esos filtros, permitir si rol admin, owner_id==user.id o public=true. Todo lo demás false. public nunca significa acceso entre tenants.

## C05 — merge_patch(document, patch)
Encargo: Aplica JSON Merge Patch a valores JSON y devuelve un resultado nuevo sin modificar document ni patch.

Documentación de dominio: Contexto: el endpoint acepta documentos JSON ya parseados y el transporte verifica tamaños. Otros endpoints utilizan JSON Patch basado en operaciones, incompatible con este contrato. El historial de edición mantiene los objetos de entrada y se compara después, por lo que su identidad mutable no puede reutilizarse en el resultado.

Reglas y excepciones vigentes: Si patch no es dict, reemplaza por una copia profunda de patch, incluso null. Si patch es dict y document no lo es, parte de {}. En objetos: null elimina clave; objetos se fusionan recursivamente; listas reemplazan completas. El resultado no debe compartir listas/dicts mutables con ninguna entrada. Claves que no aparecen en patch se conservan.

## C06 — page_after(rows, cursor, limit)
Encargo: rows tienen id (int) y ts (string ISO UTC de ancho fijo). Devuelve una lista de hasta limit filas posteriores a cursor, que es None o (ts,id).

Documentación de dominio: Contexto: la sincronización incremental intercambia el cursor completo. Los identificadores crecen dentro del mismo origen, mientras los timestamps pueden repetirse. La API permite al cliente detener la paginación pidiendo cero elementos. Las páginas se combinan por separado y esta función no genera el siguiente cursor.

Reglas y excepciones vigentes: Orden ascendente por (ts,id); posterior es comparación lexicográfica estricta. Orden de entrada arbitrario. No se pierden filas con mismo timestamp. limit negativo provoca ValueError; cero devuelve []; devolver copias profundas para no compartir estado mutable; no ordenar rows in-place. No filtrar solo por ts.

## C07 — retry_delay(value, now, cap)
Encargo: Interpreta Retry-After value (string o None) y devuelve segundos enteros no negativos limitados por cap (entero no negativo). now es datetime aware UTC.

Documentación de dominio: Contexto: el planificador calcula el backoff exponencial fuera de esta función cuando el servidor no proporciona una indicación válida. El servidor de pruebas usa fechas HTTP absolutas. La función no duerme, no consulta el reloj del sistema y no añade jitter.

Reglas y excepciones vigentes: Permitir espacios exteriores. Una cadena de dígitos decimales ASCII significa segundos. Alternativamente aceptar fecha HTTP con zona GMT. Para fecha futura redondear hacia arriba cualquier fracción de segundo. Fecha pasada devuelve 0. Ausencia, fecha inválida, número negativo, decimal o formato distinto devuelve None. Si valor válido excede cap, devolver cap. No interpretar "1.5" ni "+3" como válidos.

## C08 — csv_cell(value)
Encargo: Prepara un valor para escribir una celda CSV con seguridad frente a fórmulas. Devuelve str; value es None, str, int o float (no bool). No realiza quoting CSV.

Documentación de dominio: Contexto: el módulo csv realiza después las comillas y el escape de separadores. La protección debe conservar el contenido original visible para auditoría, incluidos espacios iniciales. Los números de horas ya vienen tipados desde la capa de dominio y no se convierten en expresiones.

Reglas y excepciones vigentes: None devuelve string vacío; números int/float devuelven str(value) sin prefijo protector. Para strings, si el primer carácter tras eliminar espacios ASCII, tabulador, CR y LF es =,+,-,@, anteponer un apóstrofo al STRING ORIGINAL completo. No eliminar espacios originales ni modificar otro contenido. Un string con apariencia numérica, por ejemplo "-12", sigue siendo string y debe protegerse.

## C09 — migration_order(steps, applied)
Encargo: steps es lista de {id:str, depends_on:list[str]}; applied es colección de ids aplicados. Devuelve ids pendientes en orden topológico.

Documentación de dominio: Contexto: varios equipos entregan migraciones y los nombres no reflejan necesariamente dependencias. Las ejecuciones anteriores están registradas en applied. Este planificador solo determina secuencia; no ejecuta SQL ni registra nuevas migraciones. La política de despliegue gradual se verifica en otra capa.

Reglas y excepciones vigentes: Orden determinista: entre nodos actualmente ejecutables elegir id lexicográficamente menor en cada paso. Dependencias ya aplicadas satisfacen el requisito aunque no estén en steps. Dependencia ausente tanto en steps como applied provoca ValueError. ids duplicados provoca ValueError. Ciclo entre pendientes provoca ValueError. Pasos aplicados se excluyen y su lista de dependencias no debe bloquear el plan. No modificar entradas.

## C10 — cache_key(tenant, user, scopes)
Encargo: Devuelve una clave str determinista y sin ambigüedad para tenant, user y scopes, todos strings salvo scopes iterable de strings.

Documentación de dominio: Contexto: un caché compartido distingue cadenas exactas de identificadores externos. La normalización de nombres de presentación pertenece al frontend. Otros cachés usan hash binario, pero aquí se exige la forma JSON porque se valida y depura sin decodificador adicional.

Reglas y excepciones vigentes: La clave debe ser JSON compacto de la lista [tenant,user,sorted(set(scopes))], ensure_ascii=False y separators=(",",":"). No normalizar Unicode ni convertir mayúsculas ni strip. No concatenar con separadores ambiguos. El orden/duplicado de scopes no afecta; orden de tenant/user sí. No modificar scopes si es lista.

## C11 — update_record(record, expected_version, changes)
Encargo: record contiene id, tenant, version y otros campos. Devuelve una nueva copia del registro con cambios y version incrementada. No modifica record ni changes.

Documentación de dominio: Contexto: el llamador aplica compare-and-swap atómico en el repositorio; esta función calcula la actualización pero no sustituye esa transacción. Algunos clientes envían formularios sin diferencias. Los campos de identidad son asignados al crear y no son editables por este endpoint.

Reglas y excepciones vigentes: Primero comparar expected_version con record.version: desigualdad provoca RuntimeError, incluso si changes vacío. changes no puede incluir id, tenant ni version: cualquiera provoca ValueError, aunque repita valor actual. Con expected correcto y changes vacío devuelve deepcopy(record) sin incrementar. Con cambios no vacíos aplica deepcopy de cada valor y aumenta version en uno, incluso si son iguales a los valores previos.

## C12 — verify_signature(body, signature, timestamp, now, secret)
Encargo: Valida firma HMAC-SHA256 de webhook y devuelve bool. body y secret son bytes, signature y timestamp strings, now segundos Unix entero. No IO.

Documentación de dominio: Contexto: el proveedor firma los bytes recibidos, incluidos espacios de JSON. La cola de entrega puede retrasar un evento y el emisor tiene tolerancia limitada de reloj adelantado. La detección de replays por id se realiza en una capa persistente separada. No registrar secret ni payload.

Reglas y excepciones vigentes: timestamp debe ser cadena decimal ASCII no vacía sin signo. Aceptar antigüedad máxima 300 segundos y futuro máximo 30 segundos, ambos límites incluidos. Firmar exactamente timestamp.encode("ascii") + b"." + body sin parsear ni normalizar body. signature debe tener prefijo exacto "sha256=" seguido de 64 dígitos hexadecimales minúsculos. Usar compare_digest para comparar. Formatos inválidos o fuera de ventana devuelven False, no excepciones.
