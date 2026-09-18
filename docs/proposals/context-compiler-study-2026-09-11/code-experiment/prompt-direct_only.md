Implementa en Python 3.12+ las doce funciones descritas. Solo biblioteca estándar. Devuelve un módulo .py con las firmas exactas; no ejecución al importar, red, filesystem ni llamadas a herramientas desde las funciones. Los parámetros cumplen los tipos declarados salvo los casos de validación descritos. No añadir requisitos ni mutar entradas. No leas pruebas ni otras variantes del contexto. Si falta detalle usa criterio conservador y documenta supuestos brevemente en comentarios. Esta es una prueba de una sola entrega: no se facilitarán resultados para corregir antes de medir.


## C01 — ledger_total(amounts)
Devuelve un string con dos decimales que suma importes en euros recibidos como strings. Usa aritmética decimal y no altera amounts.

## C02 — local_day_ids(events, day, tz)
Devuelve los ids, en orden de entrada, de eventos cuyo instante timestamp ISO8601 cae en el día local day (YYYY-MM-DD) de la zona IANA tz. No modifica events.

## C03 — fold_events(events)
Aplica eventos con campos tenant, key, seq (int), event_id, value y deleted (bool), y devuelve dict {(tenant,key):value} del último estado visible. No modifica events.

## C04 — can_read(user, resource)
Devuelve bool para acceso de lectura. user contiene id, tenant, roles (list), disabled. resource contiene tenant, owner_id, public, denied_user_ids. No modifica entradas.

## C05 — merge_patch(document, patch)
Aplica JSON Merge Patch a valores JSON y devuelve un resultado nuevo sin modificar document ni patch.

## C06 — page_after(rows, cursor, limit)
rows tienen id (int) y ts (string ISO UTC de ancho fijo). Devuelve una lista de hasta limit filas posteriores a cursor, que es None o (ts,id).

## C07 — retry_delay(value, now, cap)
Interpreta Retry-After value (string o None) y devuelve segundos enteros no negativos limitados por cap (entero no negativo). now es datetime aware UTC.

## C08 — csv_cell(value)
Prepara un valor para escribir una celda CSV con seguridad frente a fórmulas. Devuelve str; value es None, str, int o float (no bool). No realiza quoting CSV.

## C09 — migration_order(steps, applied)
steps es lista de {id:str, depends_on:list[str]}; applied es colección de ids aplicados. Devuelve ids pendientes en orden topológico.

## C10 — cache_key(tenant, user, scopes)
Devuelve una clave str determinista y sin ambigüedad para tenant, user y scopes, todos strings salvo scopes iterable de strings.

## C11 — update_record(record, expected_version, changes)
record contiene id, tenant, version y otros campos. Devuelve una nueva copia del registro con cambios y version incrementada. No modifica record ni changes.

## C12 — verify_signature(body, signature, timestamp, now, secret)
Valida firma HMAC-SHA256 de webhook y devuelve bool. body y secret son bytes, signature y timestamp strings, now segundos Unix entero. No IO.
