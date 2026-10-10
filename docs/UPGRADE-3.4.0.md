# Actualizar a 3.4.0 y recuperar la versión anterior

Esta guía acompaña los assets verificados de 3.4.0. Preparar código o paquetes de
desarrollo no acredita una release final. Compruebe el estado y evidencia de
[la implementación](plans/plugin-improvement-feedback/IMPLEMENTATION.md) antes
de actualizar. Publicación e instalación requieren su autorización propia.

## Verificar los paquetes

Conserve los ZIP y la ubicación anterior. Compruebe cada SHA-256 con SHA256SUMS
y compruebe versión/SHA en release-manifest.json, distribution-manifest.json,
informe del gate y validación de paquetes. Todos deben pertenecer al mismo conjunto
final; no mezcle un ZIP de desarrollo con evidencia de release.

```powershell
Get-FileHash -Algorithm SHA256 <ruta-al-zip>
```

Extraiga en directorios nuevos y cortos. No sobrescriba una instalación para probarla.
Mantenga disponible el paquete anterior y su manifiesto para recuperar el origen.

## Codex

El paquete marketplace contiene `plugins/lks-sdd` y su catálogo. Extraiga
`lks-sdd-marketplace-v3.4.0.zip` en una carpeta estable fuera del consumidor, por
ejemplo `C:\LksSdd340`. El comando local `codex plugin marketplace --help` permite
comprobar las operaciones disponibles. Para una fuente local, conserve el registro
y carpeta anterior antes de registrar el marketplace nuevo:

```powershell
codex plugin marketplace add C:\LksSdd340
```

Instale/active lks-sdd desde la gestión de plugins y compruebe 3.4.0. Para un origen
Git ya registrado, `codex plugin marketplace upgrade lks-sdd-development` actualiza
su catálogo solo cuando la referencia remota está publicada y verificada. Reinicie
Codex y abra un chat nuevo para leer las instrucciones nuevas.

Para recuperar, desactive la versión nueva, restaure el registro/origen anterior y
reactive su plugin. Compruebe la versión en un chat nuevo. No borre su carpeta anterior
durante la verificación. Un chat abierto no acredita activación de instrucciones nuevas.

## GitHub Copilot

Para actualización local, extraiga `lks-sdd-copilot-plugin-v3.4.0.zip`; la carpeta
`lks-sdd` contiene plugin.json, skills, core y setup. En los ajustes User de VS Code,
use `chat.pluginLocations` para habilitar la nueva carpeta y deshabilitar la anterior,
conservando las demás ubicaciones. Reinicie/recargue VS Code y abra un chat nuevo.
Este mecanismo figura en la [documentación oficial](https://code.visualstudio.com/docs/agent-customization/agent-plugins).

Para una instalación desde marketplace publicado, compruebe la referencia nativa
`copilot-v3.4.0` y el contenido exacto del ZIP antes de actualizar. VS Code comprueba
actualizaciones mediante **Extensions: Check for Extension Updates**; las opciones
disponibles dependen del harness y de las políticas del equipo. Consulte
[la documentación de actualización](https://code.visualstudio.com/docs/agent-customization/agent-plugins#update-plugins).
Una referencia anunciada en el catálogo todavía no prueba que esté publicada.

Para recuperar la alternativa local, deshabilite la ubicación nueva y reactive la
carpeta anterior conservada. Para el origen remoto, seleccione la referencia anterior
verificada según el procedimiento del equipo. Compruebe versión e instrucciones
en una conversación nueva antes de continuar tareas.

## Runtime fijado del consumidor

Actualizar cualquiera de los plugins del host deja intacto el runtime fijado del
proyecto. Su actualización a la capacidad `lks-sdd-usage/1` requiere el corte explícito
de [V3-MIGRATION](V3-MIGRATION.md), con runtime_bundle nuevo, decisiones vigentes,
preview exacto y recibo de conservación. Mantenga el paquete anterior, su recibo y
las instrucciones de rollback. No recupere un consumidor copiando manualmente el
índice o rebajando sus encabezados: conserva Markdown, objetos y diario juntos.

Las consultas anteriores siguen admitidas. Un lector independiente puede investigar
un diagnóstico sin instalar ni migrar el consumidor. Primero pruebe un caso sintético
de contexto, conservación, reporte, exportación e inspección. La aceptación real
de Codex/Copilot y la comprensión humana deben registrarse después; siguen not-run
hasta observación real.
