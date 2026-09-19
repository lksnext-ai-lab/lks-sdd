# Compatibilidad de LKS-SDD 2.0.0

## Contratos de proyecto

| Proyecto | Comportamiento en v2 |
|---|---|
| Schema 2.0 / método 2.0.0 | Contrato para proyectos nuevos; usar las [guías v2](V2-WORKFLOWS.md) |
| Schema 1.5 / método 1.5.0 | Workflow conservado; no se reinterpreta ni migra al consultar |
| Versiones anteriores o desconocidas | Fuera de la ruta oficial de migración; diagnóstico y decisión explícita, sin conversión por cambio de encabezados |

La versión del plugin, la del método y la del schema no son intercambiables.
`plugin_version` conserva la procedencia de materialización; el runtime activo
se resuelve mediante su lock. Instalar la versión personal 2.0.0 no sustituye el
runtime fijado por otro desarrollador ni convierte sus documentos.

La única conversión oficial es 1.5/1.5.0 → 2.0/2.0.0, con
[diagnóstico, preview, autorización y reconciliación](V2-MIGRATION.md).
No hay downgrade automático del contrato. El rollback transaccional usa el recibo
exacto y se detiene si hay trabajo posterior.

Una migración aplicada deja un corte técnico verificable: `migration-complete`,
recibo con manifiesto de conservación cerrado, rutas activas exclusivamente v2 y
escritores 1.5 bloqueados. `already-v2` solo se informa después de ese guard, no
por el encabezado del índice. La continuidad se evalúa por TASK; una semántica
legacy pendiente bloquea la TASK afectada, no todo el proyecto.

## Evidencia e historia

Los originales, EVID y activos históricos se conservan. La migración no transforma
autorizaciones antiguas en permiso v2 ni pruebas de componente en evidencia de
integración. Los registros antiguos insuficientes requieren reconciliación.
Los elementos `legacy`, `unknown` y `conflict` no adquieren autoridad normativa;
una referencia v2 explícita solo permite localizarlos como antecedente para la
reconciliación. El manifiesto registra para cada fuente si fue transformada,
archivada, preservada fuera de alcance o bloqueada; una entrada no contabilizada
impide el corte.
Los quality reports históricos no certifican una nueva versión: cada release usa
evidencia técnica propia ligada al commit exacto.

La consulta es de solo lectura. La documentación parcial y los desconocidos se
exponen; el código no suple una decisión de negocio. Una síntesis humana no sustituye
el contexto literal necesario para implementar.

## Hosts y distribución

Codex desktop y GitHub Copilot en VS Code Agent reciben adaptadores distintos del
mismo núcleo. El paquete nativo Copilot usa Agent Plugins 1.0; la alternativa de
skills de proyecto no debe activarse simultáneamente. El setup verifica propiedad,
integridad y colisiones sin instalar dependencias personales.

La paridad automática de paquetes no acredita aceptación conversacional. Los
ensayos v2 de versiones/modelos/permisos, navegación, generación visual y relevo
con personas siguen `not-run` hasta completar el
[protocolo de host](V2-HOST-ACCEPTANCE.md). No se hereda aceptación de 1.x.
La extensión Codex de VS Code, ChatGPT Work y Claude están fuera de alcance.

ImageGen se usa si está disponible en Codex. Copilot prepara un relevo visual
explícito cuando hace falta; Codex nativo no lo necesita. Atlassian Rovo sigue
siendo un peer opcional: el paquete no lo instala ni incluye un cliente Jira
alternativo. Los ensayos externos Rovo/Jira y Microsoft Entra sin evidencia real
siguen `not-run`.

## Tecnología y colaboración

La tecnología se declara y confirma en cada proyecto. La compatibilidad técnica se observa de forma estática local, no se infiere de un catálogo, receta o certificación global.

Cada participante usa su clon y el runtime compartido. Hay continuidad y
reconciliación, no locks distribuidos ni garantía de edición simultánea del mismo
alcance. Roles declarados y hashes no autentican actores ni al editor del paquete.

## Diagnóstico

Resolver `<plugin-root>` desde la instalación que contiene el manifest:

```powershell
python -B "<plugin-root>/scripts/lks_sdd.py" runtime-doctor "<project-root>" --json
python -B "<plugin-root>/scripts/lks_sdd.py" validate-project "<project-root>" --json
python -B "<plugin-root>/scripts/lks_sdd.py" status "<project-root>" --json
```

Los resultados distinguen runtime, contrato e integridad; no autorizan implementación,
migración, publicación o entrega. Para v2 use los comandos de
[workflows](V2-WORKFLOWS.md); no mezcle opciones del ciclo 1.5 con el nuevo contrato.
