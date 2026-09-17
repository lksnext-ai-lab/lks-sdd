Implementa en Python 3.12+ las doce funciones descritas. Solo biblioteca estándar. Devuelve un módulo .py con las firmas exactas; no ejecución al importar, red, filesystem ni llamadas a herramientas desde las funciones. Los parámetros cumplen los tipos declarados salvo los casos de validación descritos. No añadir requisitos ni mutar entradas. No leas pruebas ni otras variantes del contexto. Si falta detalle usa criterio conservador y documenta supuestos brevemente en comentarios. Esta es una prueba de una sola entrega: no se facilitarán resultados para corregir antes de medir.


## C01 — ledger_total(amounts)
Devuelve un string con dos decimales que suma importes en euros recibidos como strings. Usa aritmética decimal y no altera amounts.
Regla contable vigente: cada línea se redondea primero a céntimos con ROUND_HALF_UP; después se suman las líneas. Acepta negativos. La lista vacía devuelve "0.00". Normaliza el cero, incluido negativo, a "0.00". No redondear únicamente el total ni usar float.

## C02 — local_day_ids(events, day, tz)
Devuelve los ids, en orden de entrada, de eventos cuyo instante timestamp ISO8601 cae en el día local day (YYYY-MM-DD) de la zona IANA tz. No modifica events.
timestamp debe incluir offset explícito o Z. Un timestamp naive provoca ValueError, incluso si parecería quedar fuera del día. Debe respetar cambios de horario DST: convertir cada instante a la zona indicada. Extremo inicial incluido, final excluido; no suponer días de 24 horas. Entradas válidas y listas vacías son admitidas.

## C03 — fold_events(events)
Aplica eventos con campos tenant, key, seq (int), event_id, value y deleted (bool), y devuelve dict {(tenant,key):value} del último estado visible. No modifica events.
seq mayor gana sin depender del orden de llegada. deleted=true es tombstone: también participa en comparar seq y suprime la clave del resultado, por lo que una actualización más antigua no la resucita. Duplicados exactamente iguales con mismo (tenant,event_id) se ignoran. Ese identificador con contenido distinto provoca ValueError. Dos eventos distintos con mismo tenant,key,seq también provocan ValueError. event_id está aislado por tenant.

## C04 — can_read(user, resource)
Devuelve bool para acceso de lectura. user contiene id, tenant, roles (list), disabled. resource contiene tenant, owner_id, public, denied_user_ids. No modifica entradas.
Precedencia obligatoria: disabled implica false; distinto tenant implica false incluso para admin; id en denied_user_ids implica false incluso para admin/propietario/public. Superados esos filtros, permitir si rol admin, owner_id==user.id o public=true. Todo lo demás false. public nunca significa acceso entre tenants.

## C05 — merge_patch(document, patch)
Aplica JSON Merge Patch a valores JSON y devuelve un resultado nuevo sin modificar document ni patch.
Si patch no es dict, reemplaza por una copia profunda de patch, incluso null. Si patch es dict y document no lo es, parte de {}. En objetos: null elimina clave; objetos se fusionan recursivamente; listas reemplazan completas. El resultado no debe compartir listas/dicts mutables con ninguna entrada. Claves que no aparecen en patch se conservan.

## C06 — page_after(rows, cursor, limit)
rows tienen id (int) y ts (string ISO UTC de ancho fijo). Devuelve una lista de hasta limit filas posteriores a cursor, que es None o (ts,id).
Orden ascendente por (ts,id); posterior es comparación lexicográfica estricta. Orden de entrada arbitrario. No se pierden filas con mismo timestamp. limit negativo provoca ValueError; cero devuelve []; devolver copias profundas para no compartir estado mutable; no ordenar rows in-place. No filtrar solo por ts.

## C07 — retry_delay(value, now, cap)
Interpreta Retry-After value (string o None) y devuelve segundos enteros no negativos limitados por cap (entero no negativo). now es datetime aware UTC.
Permitir espacios exteriores. Una cadena de dígitos decimales ASCII significa segundos. Alternativamente aceptar fecha HTTP con zona GMT. Para fecha futura redondear hacia arriba cualquier fracción de segundo. Fecha pasada devuelve 0. Ausencia, fecha inválida, número negativo, decimal o formato distinto devuelve None. Si valor válido excede cap, devolver cap. No interpretar "1.5" ni "+3" como válidos.

## C08 — csv_cell(value)
Prepara un valor para escribir una celda CSV con seguridad frente a fórmulas. Devuelve str; value es None, str, int o float (no bool). No realiza quoting CSV.
None devuelve string vacío; números int/float devuelven str(value) sin prefijo protector. Para strings, si el primer carácter tras eliminar espacios ASCII, tabulador, CR y LF es =,+,-,@, anteponer un apóstrofo al STRING ORIGINAL completo. No eliminar espacios originales ni modificar otro contenido. Un string con apariencia numérica, por ejemplo "-12", sigue siendo string y debe protegerse.

## C09 — migration_order(steps, applied)
steps es lista de {id:str, depends_on:list[str]}; applied es colección de ids aplicados. Devuelve ids pendientes en orden topológico.
Orden determinista: entre nodos actualmente ejecutables elegir id lexicográficamente menor en cada paso. Dependencias ya aplicadas satisfacen el requisito aunque no estén en steps. Dependencia ausente tanto en steps como applied provoca ValueError. ids duplicados provoca ValueError. Ciclo entre pendientes provoca ValueError. Pasos aplicados se excluyen y su lista de dependencias no debe bloquear el plan. No modificar entradas.

## C10 — cache_key(tenant, user, scopes)
Devuelve una clave str determinista y sin ambigüedad para tenant, user y scopes, todos strings salvo scopes iterable de strings.
La clave debe ser JSON compacto de la lista [tenant,user,sorted(set(scopes))], ensure_ascii=False y separators=(",",":"). No normalizar Unicode ni convertir mayúsculas ni strip. No concatenar con separadores ambiguos. El orden/duplicado de scopes no afecta; orden de tenant/user sí. No modificar scopes si es lista.

## C11 — update_record(record, expected_version, changes)
record contiene id, tenant, version y otros campos. Devuelve una nueva copia del registro con cambios y version incrementada. No modifica record ni changes.
Primero comparar expected_version con record.version: desigualdad provoca RuntimeError, incluso si changes vacío. changes no puede incluir id, tenant ni version: cualquiera provoca ValueError, aunque repita valor actual. Con expected correcto y changes vacío devuelve deepcopy(record) sin incrementar. Con cambios no vacíos aplica deepcopy de cada valor y aumenta version en uno, incluso si son iguales a los valores previos.

## C12 — verify_signature(body, signature, timestamp, now, secret)
Valida firma HMAC-SHA256 de webhook y devuelve bool. body y secret son bytes, signature y timestamp strings, now segundos Unix entero. No IO.
timestamp debe ser cadena decimal ASCII no vacía sin signo. Aceptar antigüedad máxima 300 segundos y futuro máximo 30 segundos, ambos límites incluidos. Firmar exactamente timestamp.encode("ascii") + b"." + body sin parsear ni normalizar body. signature debe tener prefijo exacto "sha256=" seguido de 64 dígitos hexadecimales minúsculos. Usar compare_digest para comparar. Formatos inválidos o fuera de ventana devuelven False, no excepciones.
