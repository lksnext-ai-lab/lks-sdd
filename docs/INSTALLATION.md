# Instalación sencilla: Codex y GitHub Copilot

## Antes de actualizar a v2

Descarga los assets de [v2.1.2](https://github.com/lksnext-ai-lab/lks-sdd/releases/tag/v2.1.2)
y comprueba `SHA256SUMS`. El paquete personal, el runtime del proyecto y el contrato
documental son tres cosas distintas. Un proyecto 1.5 conserva sus fuentes y runtime
hasta autorizar la [migración 1.5 → 2.0](V2-MIGRATION.md); el setup no la sustituye.
Para proyectos nuevos usa [workflows v2](V2-WORKFLOWS.md). Los comandos visuales y
doctor 1.x de esta guía solo aplican a consumidores 1.5: en v2 usa `v2 visual-inspect`,
`validate-project` y `status` según la guía. La aceptación conversacional v2 sigue
el [protocolo por host](V2-HOST-ACCEPTANCE.md), no se infiere de una instalación válida.

La distribución 2.1.2 tiene un núcleo y dos destinos. Para Copilot se recomienda
el **plugin de agente** `lks-sdd-copilot-plugin-v2.1.2.zip` y el procedimiento
de la siguiente sección. No es una extensión VSIX y no requiere crear otra extensión.
Si no conoces estas herramientas, empieza por la [guía desde cero](LEARNING-GUIDE.md).

Para preparar Codex o usar la alternativa de skills de proyecto, el ZIP es
`lks-sdd-setup-v2.1.2.zip`: incluye instalador, manifiesto de integridad y ambos
payloads. No instala Python, extensiones, MCP, credenciales ni herramientas de terceros.
Los paquetes `development-unreleased` son instalables para evaluación, no releases
certificadas. Consulte [la aceptación por host](V2-HOST-ACCEPTANCE.md) antes de distribuirlos.

## Requisitos

- Python 3.11 o posterior y las dependencias fijadas en `requirements-runtime.txt`.
- Codex desktop con acceso propio a las capacidades necesarias; o VS Code con GitHub
  Copilot, modo Agent y skills de proyecto permitidas por la organización.
- Una copia local del repositorio por desarrollador y permisos sobre el destino elegido.
- Para generar imágenes: una persona con acceso a generación integrada en Codex. No se
  factura una API de imágenes desde Copilot ni se comparten licencias o claves.

Verificar el SHA-256 del ZIP contra `SHA256SUMS` obtenido de la fuente de distribución
de confianza. El inventario interno detecta corrupción, pero no es una firma de editor.
Extraer el ZIP completo en una carpeta temporal/local; no ejecutar desde dentro del ZIP.

### Preparar Python para el runtime v2

La validación v2 utiliza [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/).
El setup no instala paquetes Python ni usa red por iniciativa propia. Antes de usar
el runtime, prepara un entorno separado de las dependencias de la aplicación:

```powershell
python -m venv C:\LksSddTools\python-v2
C:\LksSddTools\python-v2\Scripts\python.exe -m pip install --require-hashes -r "<plugin-root>\requirements-runtime.txt"
```

En el ZIP nativo Copilot, `<plugin-root>` es `lks-sdd/core`; en el marketplace Codex
es `plugins/lks-sdd`. Usa ese intérprete para los comandos LKS-SDD o activa el entorno
en la terminal donde trabaja el agente. No instales estos requisitos en el entorno
de producción de la aplicación. Cada equipo prepara su propio entorno; no versiona
la carpeta venv. En un entorno sin red usa un wheelhouse corporativo revisado con
`--no-index --find-links <carpeta>` y el mismo lock con hashes. La distribución no
incluye los wheels y no promete bootstrap offline sin esos prerrequisitos.

## GitHub Copilot: plugin en el panel Plugins (recomendado)

Hay dos pasos distintos: cada persona instala el plugin en su herramienta; una
persona prepara la versión de LKS-SDD que compartirá el proyecto. Instalar el plugin
no modifica automáticamente aplicaciones, no habilita servicios ni concede permisos.

### Distribución al equipo desde el panel

Con la release estable publicada, esta es la vía recomendada. Cada compañero necesita
acceso de lectura al repositorio público de GitHub y Git disponible en su equipo.

1. En VS Code pulsa `Ctrl+Shift+P` y ejecuta **Chat: Install Plugin From Source**.
2. Introduce `https://github.com/lksnext-ai-lab/lks-sdd.git`.
3. El catálogo del repositorio ofrece **lks-sdd**, versión **2.1.2**. Selecciónalo y
   confirma la confianza únicamente después de comprobar el origen LKS.
4. En Agent Customizations → Plugins, comprueba que esté habilitado. Abre una
   conversación nueva en modo Agent y pide «Explícame LKS-SDD sin modificar archivos».
5. Sigue «Preparar el proyecto compartido» más abajo. Instalar el plugin personal y
   preparar el repositorio de la aplicación son pasos distintos.

El catálogo `.github/plugin/marketplace.json` apunta a `v2.1.2`, etiqueta
inmutable del paquete generado en este mismo repositorio. El código se mantiene
solo en `main`; la distribución no se edita manualmente. No pegues URLs de páginas
`/tree/` ni de ZIP en el cuadro que solicita una URL Git.

Si tu versión del panel no interpreta el catálogo desde ese comando, abre Ajustes,
busca **Chat › Plugins: Marketplaces** y añade la misma URL (sin borrar las demás).
Después abre Plugins, busca `lks-sdd` e instala. Si no aparece, comprueba acceso Git,
versión de VS Code y políticas de la organización; no las eludas.

No es necesario aparecer en Featured ni publicar un VSIX. La release no instala ni
activa el plugin automáticamente en las cuentas del equipo. El soporte del mecanismo
se documenta en [Agent plugins en VS Code](https://code.visualstudio.com/docs/agent-customization/agent-plugins);
comprueba el resultado con el [piloto guiado](COPILOT-PILOT.md).

### Alternativa local desde Ajustes (sin editar JSON)

1. Verifica el SHA-256 y extrae `lks-sdd-copilot-plugin-v2.1.2.zip` en una
   carpeta corta y estable, por ejemplo `C:\LksPilot`. Debe quedar
   `C:\LksPilot\lks-sdd\plugin.json` junto a `skills`, `core` y `setup`.
   El paquete 2.1.2 resuelve internamente rutas largas de Windows y mantiene las
   comprobaciones de integridad, enlaces y secretos.
   Si eliges manualmente un destino con un prefijo excepcionalmente largo, no uses una
   extracción parcial: usa una carpeta más corta o un extractor compatible con rutas largas.
2. En VS Code abre Ajustes (`Ctrl+,`), ámbito **User**, busca **Chat: Plugin Locations**
   y pulsa **Add Item**. En Item introduce `C:/LksPilot/lks-sdd` y en Value selecciona
   `true`. La ruta apunta a la carpeta que contiene `plugin.json`, no al ZIP ni a `core`.
   Guarda el elemento y conserva las demás ubicaciones. Es la interfaz gráfica del
   siguiente ajuste; editar JSON es una alternativa, no un requisito:

   ```json
   "chat.pluginLocations": {
     "C:/LksPilot/lks-sdd": true
   }
   ```

3. Abre Agent Customizations → Plugins y comprueba que LKS-SDD esté habilitado.
   El soporte de plugins debe estar permitido (`chat.plugins.enabled`). Si la
   organización lo bloquea, consulta al administrador: no eludas la política.
4. Abre el proyecto consumidor y una conversación nueva en modo Agent. Pide
   «Explícame LKS-SDD sin modificar archivos» o selecciona `/lks-sdd:lks-sdd-help`.
   Comprueba las seis skills. Tener archivos en disco no prueba su descubrimiento.

Este registro local permite probar el plugin en el mismo panel antes de publicarlo.
La ubicación es personal: no la incluyas como ruta absoluta en el repositorio compartido.

### Preparar el proyecto compartido

Desde la carpeta `setup` del plugin ya extraído, con el consumidor existente:

```powershell
.\install.ps1 -Target copilot -Destination C:\Dev\mi-aplicacion
```

Revisa los cambios y confirma `SI` solo si son correctos. Alternativa sin PowerShell:

```powershell
python install.py copilot C:\Dev\mi-aplicacion
python install.py copilot C:\Dev\mi-aplicacion --apply --authorize HASH_DE_LA_VISTA_PREVIA
```

El setup **incluido en el plugin** fija el núcleo y crea instrucciones, lock y recibo,
pero no copia skills a `.github/skills/`: las aporta el plugin. El lock indica
`entrypoints: plugin`. Versiona los archivos generados mediante el flujo autorizado
del equipo; cada compañero instala el plugin y actualiza su clon. No comparte tu caché.
Las seis skills consultan el runtime del proyecto, no sustituyen su versión por la
del plugin instalado. Una actualización del proyecto se hace expresamente con preview.

### Migrar desde los adaptadores de proyecto

No mantengas activas las dos entradas. Ejecuta el setup del plugin sobre el consumidor
con su recibo anterior. La vista previa retira únicamente las seis skills gestionadas
sin modificaciones, conserva instrucciones ajenas y cambia el lock a `plugin`.
Si hay personalizaciones o un relevo pendiente que impide cambiar de runtime, se
detiene. Revisa y resuelve antes de continuar; no borres directorios a mano.
Para volver a la alternativa sin plugin usa su setup, revisa la migración inversa
y deshabilita el plugin para ese workspace. Desinstalar el plugin personal no elimina
el runtime ni los documentos del proyecto.

## Alternativa Copilot: skills instaladas una vez en el proyecto

Esta alternativa usa el ZIP `lks-sdd-setup-v2.1.2.zip`, no el setup incluido en
el plugin nativo. Es útil cuando se prefieren skills versionadas y no se usa plugin.

Desde la carpeta extraída:

```powershell
.\install.ps1 -Target copilot -Destination C:\Dev\mi-aplicacion
```

El asistente muestra destino y cambios y pide escribir `SI`. Después:

1. Abrir esa carpeta en VS Code y usar GitHub Copilot en modo Agent.
2. Abrir una conversación nueva y pedir «Explícame LKS-SDD» o `/lks-sdd-help`.
3. Revisar y versionar los archivos generados mediante el procedimiento Git del equipo.
   El instalador no hace commit ni push. El resto del equipo solo necesita el clon actualizado.

Si la política corporativa no permite ejecutar PowerShell, no la cambie. Use Python:

```powershell
python install.py copilot C:\Dev\mi-aplicacion
python install.py copilot C:\Dev\mi-aplicacion --apply --authorize HASH_DE_LA_VISTA_PREVIA
```

Se añaden las seis skills en `.github/skills/`, el contrato del host, un runtime exacto
en `.lks-sdd/runtime/`, su lock y un recibo de propiedad. Los bloques gestionados de
`AGENTS.md` y `.github/copilot-instructions.md` conservan las instrucciones ajenas.
No se debe editar el runtime generado: actualice el producto y reinstale por el mismo flujo.
No ignore esos archivos en Git; sí excluya configuraciones personales, `.env` y secretos.

Si la instalación detecta archivos propios modificados o colisiones, se detiene antes
de escribir. No ofrece `--force`. Revise el conflicto y conserve las personalizaciones
fuera del bloque gestionado. En una actualización el runtime anterior se retira solo
si todos sus bytes coinciden con el recibo; imágenes, fichas y contrato consumidor quedan intactos.

Las skills de proyecto son una superficie documentada por
[VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills).
No es necesario crear una extensión VSIX para este paquete. Si la organización bloquea
Agent/skills, el instalador no puede levantar esa política ni prometer descubrimiento.

## Codex desktop: paquete de marketplace

Desde la carpeta extraída, elija una carpeta estable y corta, no la del consumidor:

```powershell
.\install.ps1 -Target codex -Destination C:\LksSddDual
```

Esto prepara el marketplace; **no activa el plugin**. Después, con autorización para
instalar, compruebe `codex plugin list` y registre el marketplace si aún no lo tiene:

```powershell
codex plugin marketplace add C:\LksSddDual
codex plugin add lks-sdd@lks-sdd-development
```

Si ya existe `lks-sdd-development` apuntando a otra carpeta, no registre un duplicado:
resuelva el origen en la gestión de plugins antes de reinstalar. No sustituya la
instalación estable accidentalmente. Abra una tarea nueva después de la instalación;
una tarea que ya estaba abierta puede conservar las instrucciones anteriores.

Alternativamente, el ZIP `lks-sdd-marketplace-v2.1.2.zip` se puede extraer en esa
carpeta estable y registrar de la misma manera. El instalador es preferible para
actualizaciones por sus comprobaciones de propiedad, colisiones y recuperación.
La extensión Codex de VS Code está fuera del alcance de esta entrega.

## Proyecto compartido entre ambas herramientas

Prepare el paquete de proyecto una vez con el destino `copilot`, aunque parte del equipo
use Codex. `AGENTS.md` obliga a ambos a usar el runtime y workflows exactos del proyecto,
sin depender de la caché global de un compañero. El destino no fija el «editor del proyecto».
Cada agente identifica su host real; encontrar `.github/` no convierte Codex en Copilot.

Trabaje con un responsable de escritura por alcance compartido. Transfiera cambios
locales, imágenes y decisiones mediante el flujo Git autorizado antes del relevo entre
clones. Un mismo directorio puede usarse secuencialmente; no ejecute ambos escritores
a la vez. Los conflictos de ramas requieren reconciliación, no «última versión gana».
Las reservas distribuidas y escritura paralela sobre el contrato compartido no están
implementadas en esta primera entrega.

El uso normal de Codex no presenta mensajes de relevo. Cuando Copilot necesita nuevos
prototipos, prepara una ficha y ofrece continuar en Codex. Después se puede permanecer
allí o volver. Véase [relevo visual](VISUAL-HANDOFF.md).

## Comprobación, recuperación y retirada

La ruta exacta del runtime aparece en `.lks-sdd/distribution-lock.json`:

```powershell
$runtime = (Get-Content .lks-sdd/distribution-lock.json -Raw | ConvertFrom-Json).runtime
python "$runtime/scripts/lks_sdd.py" runtime-doctor . --json
python "$runtime/scripts/lks_sdd.py" visual-handoff status . --json
```

`valid` acredita integridad de archivos, no aceptación conversacional. Para un proyecto
ya materializado ejecute también `doctor . --quick --json` y `validate-project . --json`.
Un proyecto nuevo no tiene que crearse como efecto secundario de instalar el paquete.

Si una instalación falla tras empezar, conserve `.lks-sdd-install-recovery.json`.
Detenga cualquier instalador activo y ejecute desde el setup:

```powershell
python install.py copilot C:\Dev\mi-aplicacion --recover --apply
```

La recuperación restaura los bytes anteriores y rechaza sobrescribir ediciones hechas
después del fallo. Un lock sin journal requiere inspección manual: no se roba un lock
ni se borra indiscriminadamente una carpeta para desbloquear.

Para retirar solo lo gestionado, use el mismo asistente con `-Remove`, o Python con
`--remove`, vista previa y `--apply --authorize HASH`. No elimina imágenes, documentación,
handoffs ni evidencias; puede dejar carpetas vacías. En Codex, desinstalar/desregistrar el
plugin en la aplicación es un paso separado antes de retirar sus archivos fuente.

## Construcción local para mantenedores

```powershell
python scripts/build_dual_distribution.py --development --output dist/dual-evaluation
```

La carpeta de salida debe ser nueva y su padre debe existir. Este comando toma archivos
versionados más las adiciones explícitas de `distribution/dual.json`, excluye temporales
y no arrastra el sitio web o archivos no versionados ajenos. Emite checksums y etiqueta
el snapshot como `development-unreleased`. El builder de release existente conserva
el requisito de commit limpio, quality report y autorización; ahora añade Copilot y setup.
