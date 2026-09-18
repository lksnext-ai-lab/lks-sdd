Implementa en Python 3.12+ las doce funciones descritas. Solo biblioteca estándar. Devuelve un módulo .py con las firmas exactas; no ejecución al importar, red, filesystem ni llamadas a herramientas desde las funciones. Los parámetros cumplen los tipos declarados salvo los casos de validación descritos. No añadir requisitos ni mutar entradas. No leas pruebas ni otras variantes del contexto. Si falta detalle usa criterio conservador y documenta supuestos brevemente en comentarios. Esta es una prueba de una sola entrega: no se facilitarán resultados para corregir antes de medir.


## C01 — ledger_total(amounts)
Contrato de entrada/salida y encargo (literal): Devuelve un string con dos decimales que suma importes en euros recibidos como strings. Usa aritmética decimal y no altera amounts.
Reglas: amounts:list[str]→str con 2 decimales. Decimal; redondear CADA importe a 0.01 con ROUND_HALF_UP y sumar; negativos válidos; vacío/cero negativo→"0.00"; no float ni mutación.

## C02 — local_day_ids(events, day, tz)
Contrato de entrada/salida y encargo (literal): Devuelve los ids, en orden de entrada, de eventos cuyo instante timestamp ISO8601 cae en el día local day (YYYY-MM-DD) de la zona IANA tz. No modifica events.
Reglas: events[{id,timestamp ISO8601 offset/Z}], day YYYY-MM-DD, tz IANA→ids en orden. Convertir instantes con zona a fecha local (DST); [inicio día,inicio siguiente). timestamp naive SIEMPRE ValueError. No mutar.

## C03 — fold_events(events)
Contrato de entrada/salida y encargo (literal): Aplica eventos con campos tenant, key, seq (int), event_id, value y deleted (bool), y devuelve dict {(tenant,key):value} del último estado visible. No modifica events.
Reglas: Agrupar por (tenant,key), máximo seq gana, tombstone deleted también gana y elimina visible. Duplicado mismo (tenant,event_id) solo si dict idéntico; distinto→ValueError. Distintos eventos igual (tenant,key,seq)→ValueError. event_id tenant-local. Sin mutación.

## C04 — can_read(user, resource)
Contrato de entrada/salida y encargo (literal): Devuelve bool para acceso de lectura. user contiene id, tenant, roles (list), disabled. resource contiene tenant, owner_id, public, denied_user_ids. No modifica entradas.
Reglas: Deny primero: user.disabled OR tenant distinto OR user.id en resource.denied_user_ids. Después allow: "admin" in roles OR owner_id==id OR public. Else false. Admin/public NUNCA saltan denies. Sin mutación.

## C05 — merge_patch(document, patch)
Contrato de entrada/salida y encargo (literal): Aplica JSON Merge Patch a valores JSON y devuelve un resultado nuevo sin modificar document ni patch.
Reglas: JSON Merge Patch: patch no-dict→deepcopy(patch); patch dict→deepcopy(document) si dict, si no {}. Cada clave: null elimina; otro valor aplica recursión. Arrays reemplazan completos. Sin mutar NI compartir containers con entradas.

## C06 — page_after(rows, cursor, limit)
Contrato de entrada/salida y encargo (literal): rows tienen id (int) y ts (string ISO UTC de ancho fijo). Devuelve una lista de hasta limit filas posteriores a cursor, que es None o (ts,id).
Reglas: Ordenar copia por (ts,id); filtrar tupla > cursor, o todos si None. Tomar limit; negativo ValueError; cero []. Timestamps iguales usan id. Resultado deepcopy; no mutar rows.

## C07 — retry_delay(value, now, cap)
Contrato de entrada/salida y encargo (literal): Interpreta Retry-After value (string o None) y devuelve segundos enteros no negativos limitados por cap (entero no negativo). now es datetime aware UTC.
Reglas: strip value. None→None. ASCII [0-9]+→min(int,cap). Si fecha HTTP GMT válida: min(cap,max(0,ceil((fecha-now).total_seconds()))). Inválido/negativo/decimal/+sign→None. now supplied; sin reloj/sleep/jitter.

## C08 — csv_cell(value)
Contrato de entrada/salida y encargo (literal): Prepara un valor para escribir una celda CSV con seguridad frente a fórmulas. Devuelve str; value es None, str, int o float (no bool). No realiza quoting CSV.
Reglas: None→""; int/float→str sin protección. str: probar primer char tras lstrip(" \t\r\n"); si =,+,-,@ anteponer apostrofo AL ORIGINAL; else original. "-12" string se protege; no quoting CSV.

## C09 — migration_order(steps, applied)
Contrato de entrada/salida y encargo (literal): steps es lista de {id:str, depends_on:list[str]}; applied es colección de ids aplicados. Devuelve ids pendientes en orden topológico.
Reglas: Excluir ids en applied. Duplicados steps→ValueError. Dep pendiente debe estar en steps o applied; si no ValueError. Toposort pendientes: elegir mínimo ID lexicográfico de ready CADA paso. Ciclo→ValueError. Ignorar deps de steps ya aplicados. No mutar.

## C10 — cache_key(tenant, user, scopes)
Contrato de entrada/salida y encargo (literal): Devuelve una clave str determinista y sin ambigüedad para tenant, user y scopes, todos strings salvo scopes iterable de strings.
Reglas: Exacto json.dumps([tenant,user,sorted(set(scopes))], ensure_ascii=False,separators=(",",":")). No Unicode normalization/case/strip. No mutar; scopes orden/duplicados equivalentes.

## C11 — update_record(record, expected_version, changes)
Contrato de entrada/salida y encargo (literal): record contiene id, tenant, version y otros campos. Devuelve una nueva copia del registro con cambios y version incrementada. No modifica record ni changes.
Reglas: expected != record.version→RuntimeError PRIMERO. Cualquier id/tenant/version en changes→ValueError. changes vacío→deepcopy(record), misma version. No vacío→deepcopy y update; version+1 incluso mismos valores. Sin alias mutable.

## C12 — verify_signature(body, signature, timestamp, now, secret)
Contrato de entrada/salida y encargo (literal): Valida firma HMAC-SHA256 de webhook y devuelve bool. body y secret son bytes, signature y timestamp strings, now segundos Unix entero. No IO.
Reglas: timestamp ASCII dígitos, sin signo; 0<=now-ts<=300 OR 0<ts-now<=30. HMAC SHA256 sobre timestamp ASCII + b"." + body EXACTO. signature regex sha256=[0-9a-f]{64}. compare_digest. Inválido/fuera ventana→False; sin IO.
