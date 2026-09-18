"""Freeze synthetic contracts before model generation; no generated-code oracle input."""
import hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parents[1]
O=S/'code-experiment'
O.mkdir(exist_ok=True)

def case(i,name,signature,task,details,ancillary,compact):
    return dict(id=i,name=name,signature=signature,task=task,details=details,ancillary=ancillary,compact=compact)

CASES=[
case('C01','ledger_total','ledger_total(amounts)',
 'Devuelve un string con dos decimales que suma importes en euros recibidos como strings. Usa aritmética decimal y no altera amounts.',
 'Regla contable vigente: cada línea se redondea primero a céntimos con ROUND_HALF_UP; después se suman las líneas. Acepta negativos. La lista vacía devuelve "0.00". Normaliza el cero, incluido negativo, a "0.00". No redondear únicamente el total ni usar float.',
 'Contexto: el libro mayor recibe líneas de facturas de varios emisores; la conciliación compara cada línea ya contabilizada. La interfaz de revisión agrupa por proveedor y permite consultar el documento de origen. Una propuesta histórica de redondeo bancario quedó descartada. Los informes anuales pueden mostrar cuatro decimales, pero pertenecen a otra operación.',
 'amounts:list[str]→str con 2 decimales. Decimal; redondear CADA importe a 0.01 con ROUND_HALF_UP y sumar; negativos válidos; vacío/cero negativo→"0.00"; no float ni mutación.'),
case('C02','local_day_ids','local_day_ids(events, day, tz)',
 'Devuelve los ids, en orden de entrada, de eventos cuyo instante timestamp ISO8601 cae en el día local day (YYYY-MM-DD) de la zona IANA tz. No modifica events.',
 'timestamp debe incluir offset explícito o Z. Un timestamp naive provoca ValueError, incluso si parecería quedar fuera del día. Debe respetar cambios de horario DST: convertir cada instante a la zona indicada. Extremo inicial incluido, final excluido; no suponer días de 24 horas. Entradas válidas y listas vacías son admitidas.',
 'Contexto: el cierre operativo usa el calendario del centro de trabajo, distinto del huso del servidor. La interfaz guarda el día como fecha civil y no como intervalo UTC. El almacén histórico conserva el timestamp original para auditoría. Los turnos semanales y el calendario laboral se gestionan en otro servicio.',
 'events[{id,timestamp ISO8601 offset/Z}], day YYYY-MM-DD, tz IANA→ids en orden. Convertir instantes con zona a fecha local (DST); [inicio día,inicio siguiente). timestamp naive SIEMPRE ValueError. No mutar.'),
case('C03','fold_events','fold_events(events)',
 'Aplica eventos con campos tenant, key, seq (int), event_id, value y deleted (bool), y devuelve dict {(tenant,key):value} del último estado visible. No modifica events.',
 'seq mayor gana sin depender del orden de llegada. deleted=true es tombstone: también participa en comparar seq y suprime la clave del resultado, por lo que una actualización más antigua no la resucita. Duplicados exactamente iguales con mismo (tenant,event_id) se ignoran. Ese identificador con contenido distinto provoca ValueError. Dos eventos distintos con mismo tenant,key,seq también provocan ValueError. event_id está aislado por tenant.',
 'Contexto: el consumidor recibe lotes reintentados y entregas fuera de orden. El almacenamiento de auditoría conserva los eventos originales. Los procesos de compactación física se ejecutan por separado, después de su ventana de retención. El orden de presentación de las claves no es contractual.',
 'Agrupar por (tenant,key), máximo seq gana, tombstone deleted también gana y elimina visible. Duplicado mismo (tenant,event_id) solo si dict idéntico; distinto→ValueError. Distintos eventos igual (tenant,key,seq)→ValueError. event_id tenant-local. Sin mutación.'),
case('C04','can_read','can_read(user, resource)',
 'Devuelve bool para acceso de lectura. user contiene id, tenant, roles (list), disabled. resource contiene tenant, owner_id, public, denied_user_ids. No modifica entradas.',
 'Precedencia obligatoria: disabled implica false; distinto tenant implica false incluso para admin; id en denied_user_ids implica false incluso para admin/propietario/public. Superados esos filtros, permitir si rol admin, owner_id==user.id o public=true. Todo lo demás false. public nunca significa acceso entre tenants.',
 'Contexto: las organizaciones comparten infraestructura física y conservan administración funcional independiente. El rol admin permite administrar los recursos de su organización. La pantalla pública usa el mismo motor de autorización. La edición de recursos exige permisos distintos y queda fuera de esta función.',
 'Deny primero: user.disabled OR tenant distinto OR user.id en resource.denied_user_ids. Después allow: "admin" in roles OR owner_id==id OR public. Else false. Admin/public NUNCA saltan denies. Sin mutación.'),
case('C05','merge_patch','merge_patch(document, patch)',
 'Aplica JSON Merge Patch a valores JSON y devuelve un resultado nuevo sin modificar document ni patch.',
 'Si patch no es dict, reemplaza por una copia profunda de patch, incluso null. Si patch es dict y document no lo es, parte de {}. En objetos: null elimina clave; objetos se fusionan recursivamente; listas reemplazan completas. El resultado no debe compartir listas/dicts mutables con ninguna entrada. Claves que no aparecen en patch se conservan.',
 'Contexto: el endpoint acepta documentos JSON ya parseados y el transporte verifica tamaños. Otros endpoints utilizan JSON Patch basado en operaciones, incompatible con este contrato. El historial de edición mantiene los objetos de entrada y se compara después, por lo que su identidad mutable no puede reutilizarse en el resultado.',
 'JSON Merge Patch: patch no-dict→deepcopy(patch); patch dict→deepcopy(document) si dict, si no {}. Cada clave: null elimina; otro valor aplica recursión. Arrays reemplazan completos. Sin mutar NI compartir containers con entradas.'),
case('C06','page_after','page_after(rows, cursor, limit)',
 'rows tienen id (int) y ts (string ISO UTC de ancho fijo). Devuelve una lista de hasta limit filas posteriores a cursor, que es None o (ts,id).',
 'Orden ascendente por (ts,id); posterior es comparación lexicográfica estricta. Orden de entrada arbitrario. No se pierden filas con mismo timestamp. limit negativo provoca ValueError; cero devuelve []; devolver copias profundas para no compartir estado mutable; no ordenar rows in-place. No filtrar solo por ts.',
 'Contexto: la sincronización incremental intercambia el cursor completo. Los identificadores crecen dentro del mismo origen, mientras los timestamps pueden repetirse. La API permite al cliente detener la paginación pidiendo cero elementos. Las páginas se combinan por separado y esta función no genera el siguiente cursor.',
 'Ordenar copia por (ts,id); filtrar tupla > cursor, o todos si None. Tomar limit; negativo ValueError; cero []. Timestamps iguales usan id. Resultado deepcopy; no mutar rows.'),
case('C07','retry_delay','retry_delay(value, now, cap)',
 'Interpreta Retry-After value (string o None) y devuelve segundos enteros no negativos limitados por cap (entero no negativo). now es datetime aware UTC.',
 'Permitir espacios exteriores. Una cadena de dígitos decimales ASCII significa segundos. Alternativamente aceptar fecha HTTP con zona GMT. Para fecha futura redondear hacia arriba cualquier fracción de segundo. Fecha pasada devuelve 0. Ausencia, fecha inválida, número negativo, decimal o formato distinto devuelve None. Si valor válido excede cap, devolver cap. No interpretar "1.5" ni "+3" como válidos.',
 'Contexto: el planificador calcula el backoff exponencial fuera de esta función cuando el servidor no proporciona una indicación válida. El servidor de pruebas usa fechas HTTP absolutas. La función no duerme, no consulta el reloj del sistema y no añade jitter.',
 'strip value. None→None. ASCII [0-9]+→min(int,cap). Si fecha HTTP GMT válida: min(cap,max(0,ceil((fecha-now).total_seconds()))). Inválido/negativo/decimal/+sign→None. now supplied; sin reloj/sleep/jitter.'),
case('C08','csv_cell','csv_cell(value)',
 'Prepara un valor para escribir una celda CSV con seguridad frente a fórmulas. Devuelve str; value es None, str, int o float (no bool). No realiza quoting CSV.',
 'None devuelve string vacío; números int/float devuelven str(value) sin prefijo protector. Para strings, si el primer carácter tras eliminar espacios ASCII, tabulador, CR y LF es =,+,-,@, anteponer un apóstrofo al STRING ORIGINAL completo. No eliminar espacios originales ni modificar otro contenido. Un string con apariencia numérica, por ejemplo "-12", sigue siendo string y debe protegerse.',
 'Contexto: el módulo csv realiza después las comillas y el escape de separadores. La protección debe conservar el contenido original visible para auditoría, incluidos espacios iniciales. Los números de horas ya vienen tipados desde la capa de dominio y no se convierten en expresiones.',
 'None→""; int/float→str sin protección. str: probar primer char tras lstrip(" \\t\\r\\n"); si =,+,-,@ anteponer apostrofo AL ORIGINAL; else original. "-12" string se protege; no quoting CSV.'),
case('C09','migration_order','migration_order(steps, applied)',
 'steps es lista de {id:str, depends_on:list[str]}; applied es colección de ids aplicados. Devuelve ids pendientes en orden topológico.',
 'Orden determinista: entre nodos actualmente ejecutables elegir id lexicográficamente menor en cada paso. Dependencias ya aplicadas satisfacen el requisito aunque no estén en steps. Dependencia ausente tanto en steps como applied provoca ValueError. ids duplicados provoca ValueError. Ciclo entre pendientes provoca ValueError. Pasos aplicados se excluyen y su lista de dependencias no debe bloquear el plan. No modificar entradas.',
 'Contexto: varios equipos entregan migraciones y los nombres no reflejan necesariamente dependencias. Las ejecuciones anteriores están registradas en applied. Este planificador solo determina secuencia; no ejecuta SQL ni registra nuevas migraciones. La política de despliegue gradual se verifica en otra capa.',
 'Excluir ids en applied. Duplicados steps→ValueError. Dep pendiente debe estar en steps o applied; si no ValueError. Toposort pendientes: elegir mínimo ID lexicográfico de ready CADA paso. Ciclo→ValueError. Ignorar deps de steps ya aplicados. No mutar.'),
case('C10','cache_key','cache_key(tenant, user, scopes)',
 'Devuelve una clave str determinista y sin ambigüedad para tenant, user y scopes, todos strings salvo scopes iterable de strings.',
 'La clave debe ser JSON compacto de la lista [tenant,user,sorted(set(scopes))], ensure_ascii=False y separators=(",",":"). No normalizar Unicode ni convertir mayúsculas ni strip. No concatenar con separadores ambiguos. El orden/duplicado de scopes no afecta; orden de tenant/user sí. No modificar scopes si es lista.',
 'Contexto: un caché compartido distingue cadenas exactas de identificadores externos. La normalización de nombres de presentación pertenece al frontend. Otros cachés usan hash binario, pero aquí se exige la forma JSON porque se valida y depura sin decodificador adicional.',
 'Exacto json.dumps([tenant,user,sorted(set(scopes))], ensure_ascii=False,separators=(",",":")). No Unicode normalization/case/strip. No mutar; scopes orden/duplicados equivalentes.'),
case('C11','update_record','update_record(record, expected_version, changes)',
 'record contiene id, tenant, version y otros campos. Devuelve una nueva copia del registro con cambios y version incrementada. No modifica record ni changes.',
 'Primero comparar expected_version con record.version: desigualdad provoca RuntimeError, incluso si changes vacío. changes no puede incluir id, tenant ni version: cualquiera provoca ValueError, aunque repita valor actual. Con expected correcto y changes vacío devuelve deepcopy(record) sin incrementar. Con cambios no vacíos aplica deepcopy de cada valor y aumenta version en uno, incluso si son iguales a los valores previos.',
 'Contexto: el llamador aplica compare-and-swap atómico en el repositorio; esta función calcula la actualización pero no sustituye esa transacción. Algunos clientes envían formularios sin diferencias. Los campos de identidad son asignados al crear y no son editables por este endpoint.',
 'expected != record.version→RuntimeError PRIMERO. Cualquier id/tenant/version en changes→ValueError. changes vacío→deepcopy(record), misma version. No vacío→deepcopy y update; version+1 incluso mismos valores. Sin alias mutable.'),
case('C12','verify_signature','verify_signature(body, signature, timestamp, now, secret)',
 'Valida firma HMAC-SHA256 de webhook y devuelve bool. body y secret son bytes, signature y timestamp strings, now segundos Unix entero. No IO.',
 'timestamp debe ser cadena decimal ASCII no vacía sin signo. Aceptar antigüedad máxima 300 segundos y futuro máximo 30 segundos, ambos límites incluidos. Firmar exactamente timestamp.encode("ascii") + b"." + body sin parsear ni normalizar body. signature debe tener prefijo exacto "sha256=" seguido de 64 dígitos hexadecimales minúsculos. Usar compare_digest para comparar. Formatos inválidos o fuera de ventana devuelven False, no excepciones.',
 'Contexto: el proveedor firma los bytes recibidos, incluidos espacios de JSON. La cola de entrega puede retrasar un evento y el emisor tiene tolerancia limitada de reloj adelantado. La detección de replays por id se realiza en una capa persistente separada. No registrar secret ni payload.',
 'timestamp ASCII dígitos, sin signo; 0<=now-ts<=300 OR 0<ts-now<=30. HMAC SHA256 sobre timestamp ASCII + b"." + body EXACTO. signature regex sha256=[0-9a-f]{64}. compare_digest. Inválido/fuera ventana→False; sin IO.'),
]

PREFIX='''Implementa en Python 3.12+ las doce funciones descritas. Solo biblioteca estándar. Devuelve un módulo .py con las firmas exactas; no ejecución al importar, red, filesystem ni llamadas a herramientas desde las funciones. Los parámetros cumplen los tipos declarados salvo los casos de validación descritos. No añadir requisitos ni mutar entradas. No leas pruebas ni otras variantes del contexto. Si falta detalle usa criterio conservador y documenta supuestos brevemente en comentarios. Esta es una prueba de una sola entrega: no se facilitarán resultados para corregir antes de medir.\n'''

for arm in ['full','direct_only','compact_complete']:
    sections=[PREFIX]
    for c in CASES:
        if arm=='full':
            body=f"Encargo: {c['task']}\n\nDocumentación de dominio: {c['ancillary']}\n\nReglas y excepciones vigentes: {c['details']}"
        elif arm=='direct_only':
            body=c['task']
        else:
            body=c['compact']
        sections.append(f"## {c['id']} — {c['signature']}\n{body}")
    p=O/f'prompt-{arm}.md'
    p.write_text('\n\n'.join(sections)+'\n',encoding='utf-8')
(O/'contracts.json').write_text(json.dumps(CASES,ensure_ascii=False,indent=2),encoding='utf-8')
receipt={'design':'12 synthetic coding microtasks; 3 arms; one model batch per arm; manual compact-complete is a representation upper bound, not automatic compiler output.',
 'frozen_inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('prompt-*.md')},
 'confounders':['One delivery per arm; no confidence estimate','Same model family, existing agent histories differ','No editing full applications, browser QA or production load','direct_only deliberately lacks normative details; not a strong RAG baseline','Compact uses hand-checked source, not an implemented semantic compiler'],
 'quality_evidence':'Hidden executable assertions authored before model code; future tests not used to repair measured candidates.'}
(O/'design.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'cases':len(CASES),'arms':3,'path':str(O)}))

if __name__=='__main__':
    pass
