# Inventario automático y política de entradas

## Encargo y base

Corrección autorizada del inventario automático: omitir las rutas que la política
existente excluye, sin leerlas ni incorporarlas al contrato, y conservar el rechazo
de entradas explícitas prohibidas. Base comprobada: `v3.4.0`, commit
`d6fd5f8de448977866e2e583f9585a68a23e6ad8`. El cambio previo de `AGENTS.md`
se conserva. No se modifican fuentes de `specs/canonical/`.

## Hecho reproducido y causa

Un repositorio temporal independiente, con `app.py` y `.env.example` añadidos al
índice Git, produce antes de la corrección:

```text
ContractError: Sensitive or Git path is not a contract input: .env.example
```

`code_inventory()` enumera archivos versionados y no ignorados con `git ls-files`.
Pasa cada ruta a `subject()`, que utiliza `path_at()` y `relative_parts()`.
La política comprueba todos los componentes de la ruta mediante `SECRET_NAME`
y rechaza componentes `.git`, también con distintas mayúsculas. Esa política es
correcta para una selección explícita; faltaba aplicarla como filtro de la
enumeración automática antes de seleccionar o leer archivos.

## Corrección aplicada

`v2_contract.contract_input_allowed()` reúne la validación léxica y la política
existentes. Devuelve `False` exclusivamente para nombres excluidos, y sigue lanzando
`ContractError` ante rutas mal formadas. `relative_parts()` usa esa función y conserva
el rechazo explícito, incluido el mensaje original.

`code_inventory()` consulta la misma función antes de llamar a `subject()`. No
activa `package_data`, no duplica patrones y no captura excepciones. Los componentes
excluidos no llegan al lector de bytes. Las exclusiones SDD previas se conservan.

Se mantienen el límite de 20.000 rutas antes del filtrado, el límite de salida Git
de 16 MiB, el timeout de 60 segundos y la lectura máxima de 64 MiB por archivo.
Las rutas permitidas siguen pasando por las comprobaciones de integridad, enlaces,
repositorios anidados y permisos. `scope_changes()` conserva su comparación completa
y las eliminaciones versionadas, retiradas del índice o no versionadas.

## Regresiones sintéticas

`tests/test_v3_code_inventory.py` contiene 15 pruebas con repositorios temporales,
sin commits ni datos de consumidores. Antes de modificar el runtime, la primera
prueba falló con el error reproducido tanto en su variante versionada como en la
no versionada.

| Condición | Evidencia |
|---|---|
| `app.py` y `.env.example` | Solo se registra y lee `app.py`; ambas variantes Git. |
| Política general | Nombres sensibles de varias familias, directorios sensibles y `.git` a cualquier profundidad; una ampliación sintética del patrón afecta igualmente al lector y al inventario. |
| Selección explícita | `subject`, `path_at` y `read_bytes` siguen rechazando; seleccionar un directorio que contiene entradas prohibidas también rechaza. La excepción previa de empaquetado no se activa para el inventario. |
| Archivos permitidos | Hashes exactos, nombres similares permitidos, altas, modificaciones, cambios fuera del alcance y tres formas de eliminación. |
| Errores y límites | Rutas mal formadas, UTF-8 inválido, repositorio anidado real, rechazo de enlaces y errores de lectura inyectados, presupuesto real de archivo y límites de cantidad/salida Git y timeout. |

`test_v3_workflow` añade un recorrido de inicio e implementación: persiste una base
con solo el código permitido y conserva el sujeto de código tras cambiar también
el placeholder excluido. Las pruebas existentes mantienen los guards de alcance,
integridad de inventario y caducidad.

## Evidencia y límites

Comprobaciones de desarrollo según [VALIDATION.md](VALIDATION.md), ejecutadas el
11 de octubre de 2026:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v3_code_inventory --module test_v3_workflow
python -B -X utf8 tests/run_unit_tests.py --module test_v2_storage --module test_v3_integration
python -B -X utf8 scripts/validate_plugin_contract.py .
python -B -X utf8 scripts/validate_fixture_manifest.py
git diff --check
```

Resultados: 22 y 7 pruebas superadas respectivamente, 29 casos distintos, sin
fallos ni omisiones. Se volvió a comprobar individualmente la selección explícita
del directorio prohibido y el recorrido añadido tras finalizar sus aserciones;
ambos superados. Contrato del plugin válido, manifiesto válido con 13 fixtures,
sintaxis Python válida en los cuatro archivos añadidos/modificados y diff sin
errores de whitespace. La huella SHA-256 de `AGENTS.md` coincide con la inicial.

La reproducción posterior del repositorio temporal versionado devuelve únicamente:

```text
{'app.py': '0a775022744f64c352863f165f2e125898419999bc57c83204772036d0ef6b2e'}
```

La selección explícita de `.env.example` conserva el rechazo original. No hay
comprobaciones focales pendientes. La evidencia es sintética: no acredita aceptación
humana ni comportamiento de una instalación activa. En esta primera fase no se
ejecutó el gate estable, incluida su regresión completa de rutas largas Windows:
su ejecución requiere autorización de release, commit integrado y checkout limpio.

La primera fase entregó cambios locales sin commits, integración, etiquetas,
publicación ni instalación.
No se han modificado consumidores, cachés, referencias históricas, selección de
contexto ni migraciones.

## Preparación del parche 3.4.1

Tras proponerse la entrega como parche, se preparan localmente los metadatos y
documentación como **3.4.1-rc.1**, con destino estable **3.4.1**. Se mantienen schema
3.1, método 3.1.0 y formatos técnicos. La aprobación de 3.4.0 permanece intacta y
no acredita esta versión nueva. No se crea una aprobación estable ficticia.

Tras revisar la candidata, el responsable autoriza expresamente el 2026-10-11
«autorizado y publicala v 3.4.1». La aprobación nueva de versión, commit/integración
y publicación queda en `quality/release-approval-v3.4.1.json`. Se promueven los
metadatos a **3.4.1**. Gate estable, conjunto exacto de paquetes y publicación se
acreditan en sus informes externos ligados al commit final; las pruebas de
desarrollo no sustituyen esa evidencia. Véase [la guía del parche](UPGRADE-3.4.1.md).
El cambio previo de `AGENTS.md` continúa conservado y debe quedar fuera del commit
de esta corrección salvo autorización específica para incorporarlo.

La preparación 3.4.1-rc.1 supera de nuevo el contrato del plugin, el manifiesto de
13 fixtures y las 15 regresiones de `test_v3_code_inventory`, sin fallos ni omisiones.
Los metadatos de Codex/Copilot, inicializadores, documentación activa y ejemplo/schema
de piloto declaran la misma candidata; el piloto permanece `prepared`, sin personas
ni proyectos. Las comprobaciones de sintaxis y diff también pasan. Las 29 pruebas
del cambio de runtime arriba registradas se conservan como evidencia de desarrollo;
no se presentan como un gate estable del nuevo commit todavía inexistente.
