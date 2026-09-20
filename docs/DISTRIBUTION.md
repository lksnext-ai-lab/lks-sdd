# Distribución candidate o stable

## Distribución dual 2.1.3

La ruta recomendada para usuarios es el [asistente de instalación](INSTALLATION.md).
Desde esta versión, el builder de release añade `lks-sdd-copilot-vVERSION.zip`,
`lks-sdd-setup-vVERSION.zip`, `lks-sdd-copilot-plugin-vVERSION.zip` y
`distribution-manifest.json` al plugin/marketplace Codex.
Todos contienen el mismo núcleo; los hashes y el inventario de destinos quedan en los
manifiestos. CI compara el inventario declarado, no una constante de cinco archivos.

El ZIP `copilot-plugin` contiene una carpeta `lks-sdd` con manifiesto Agent Plugins
1.0, seis skills, núcleo y setup offline. Puede registrarse localmente antes de
publicarse. Para instalación Git desde el panel, `.github/plugin/marketplace.json`
del repositorio de mantenimiento referencia la etiqueta `copilot-vVERSION` del mismo
repositorio. Esa etiqueta contiene exclusivamente la raíz `lks-sdd/` extraída del
ZIP nativo aprobado, incluidos los archivos ocultos. No apunta al commit de `main`:
ese commit conserva el layout de mantenimiento, no el del plugin nativo.

El árbol nativo se proyecta de forma determinista antes de empaquetarse: conserva
los bytes de cada artefacto de observación y sus SHA-256 completos, pero usa rutas
cortas en el paquete y actualiza el manifiesto derivado que las referencia. Esto
evita que el checkout Git que usa Copilot exceda el límite clásico de Windows. La
evidencia fuente hash-addressed del repositorio de mantenimiento no se reescribe;
el validador del paquete y el test de presupuesto de ruta protegen esta propiedad
antes de publicar.

Tras los gates limpios, extraiga el ZIP nativo en un directorio nuevo y corto,
valídelo y cree un repositorio Git aislado dentro de su carpeta `lks-sdd`. Use una
rama `codex/copilot-distribution` y un commit de distribución cuyo mensaje registre
el SHA de mantenimiento y el SHA-256 del ZIP aprobado. Cree la etiqueta anotada e
inmutable `copilot-vVERSION` sobre ese commit y publique ambos en el remoto autorizado.
No mantenga código manualmente en esa rama ni modifique una etiqueta publicada.
En versiones posteriores, parta de la rama publicada y sustituya solo sus archivos
generados con un paquete nuevo verificado; conserve la historia sin force-push.

Compruebe mediante un clon nuevo de la etiqueta que todos los bytes versionados
coinciden exactamente con el ZIP y que su setup conserva la integridad. Publique
la release de mantenimiento `vVERSION` con sus assets verificados. Hasta terminar
ambas publicaciones, no anuncie la instalación como disponible. El builder no hace
push, instala plugins ni altera la visibilidad privada del repositorio.

El plugin nativo incluye `.gitattributes` para conservar bytes del setup al pasar
por Git con `core.autocrlf=true`; no lo omita al preparar el repositorio de distribución.
Copie también archivos ocultos. El manifiesto de integridad no debe regenerarse para
ocultar modificaciones accidentales: reconstruya el paquete desde fuentes revisadas.

`build_dual_distribution.py --development` permite preparar paquetes locales de
evaluación sin commit ni quality report publicable, marcados `development-unreleased`.
No sustituye los requisitos de release limpia descritos abajo. Las instalaciones de
prueba son aisladas; no se registra un marketplace ni se modifica el plugin activo.
Un candidato instalable no acredita aceptación conversacional ni autoriza publicación.

## Bundle de desarrollo

`scripts/build_candidate_package.py` genera fuera del repositorio el conjunto reproducible:

- `lks-sdd-plugin-vX.Y.Z.zip`, con el plugin bajo `lks-sdd/`;
- `lks-sdd-marketplace-vX.Y.Z.zip`, con `.agents/plugins/marketplace.json` y `plugins/lks-sdd/`.
- `quality-report.json`, evidencia reproducible del gate de release ligado al commit.
- Desde 1.1, ZIP nativo Copilot, ZIP alternativo de proyecto, ZIP setup y
  `distribution-manifest.json`; además `release-manifest.json` y `SHA256SUMS`.

`X.Y.Z` se deriva del manifiesto del plugin; el builder no mantiene una segunda versión hardcodeada. La entrada del marketplace usa la forma estándar `local`, ruta `./plugins/lks-sdd`, instalación `AVAILABLE`, autenticación `ON_INSTALL` y categoría `Developer Tools`.

El builder solo acepta la raíz exacta de un repositorio Git, comprueba que
`--source-commit` exista y coincida con `HEAD`, y exige un árbol de trabajo limpio.
Para publicar acepta el informe compacto del mismo commit, versión y fecha. Ese
informe acredita la aprobación, integridad estática, pruebas de humo y, en stable,
la regresión de rutas largas Windows.

Los bytes del plugin se leen del commit mediante objetos Git, no del working tree. Esto impide atribuir a un SHA contenido sin confirmar, incluso si Git oculta localmente un cambio mediante `assume-unchanged`. También rechaza enlaces, submódulos, salidas dentro del repositorio y patrones de secretos conocidos.

El repositorio fija `eol=lf` para todo texto mediante `.gitattributes` y excluye de
esa conversión los formatos binarios declarados. El builder lee los bytes exactos del
commit acreditado y los manifiestos de integridad detectan cualquier alteración.

El reporte publicable se genera desde un checkout dedicado, recién creado y sin archivos no versionados preexistentes, incluidos los ignorados. Desde la raíz del repositorio principal, una vez integrado y revisado el commit de release:

```powershell
$releaseVersion = "2.1.3"
$releaseDate = Get-Date -Format "yyyy-MM-dd"
$sourceCommit = (git rev-parse HEAD).Trim()
$artifactBase = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion"
$qualityReport = "$artifactBase-quality.json"
$releaseCheckout = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion-$sourceCommit-source"

if (Test-Path -LiteralPath $releaseCheckout) { throw "El checkout dedicado ya existe." }
git worktree add --detach $releaseCheckout $sourceCommit

Push-Location $releaseCheckout
try {
  python scripts\run_release_gate.py --channel stable --date $releaseDate --release-approval "quality\release-approval-v$releaseVersion.json" --output $qualityReport
  python scripts\build_candidate_package.py --date $releaseDate --source-commit $sourceCommit --quality-report $qualityReport --output $artifactBase
} finally {
  Pop-Location
}
```

El gate toma el snapshot antes de ejecutar sus comprobaciones. Un artefacto creado
después no invalida retroactivamente ese reporte; sí invalidaría una nueva atestación
si ya existiera al comenzarla. Reporte y carpeta de salida deben ser nuevos.
`SHA256SUMS` cubre todos los ZIP, reportes y manifiestos; el de release enumera
fuentes, tamaños, hashes y vinculación del gate. No ejecute suites amplias ni evals
antes de publicar: son diagnósticos y no sustituyen este reporte.

```powershell
$manifest = Get-Content -Raw "$artifactBase\release-manifest.json" | ConvertFrom-Json
if ($manifest.source_commit -ne $sourceCommit) { throw "El manifiesto no corresponde al commit de release." }
if ($manifest.plugin_version -ne $releaseVersion) { throw "El manifiesto no corresponde a la versión de release." }
if ($manifest.quality.gate -ne "passed") { throw "El manifiesto no acredita el gate de release." }

Push-Location $artifactBase
try {
  Get-Content SHA256SUMS | ForEach-Object {
    $expected, $relative = $_ -split "\s+", 2
    $actual = (Get-FileHash -LiteralPath ($relative.Trim()) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Checksum incorrecto: $relative" }
  }
} finally {
  Pop-Location
}
```

El inventario se obtiene de `release-manifest.json`, no de una cantidad fija de
archivos. El build único es el conjunto publicable.

## Marketplace y activación

Publicar el ZIP de marketplace como asset de GitHub no actualiza una instalación activa. Son estados separados:

1. Descargar o copiar el ZIP de marketplace publicado y verificarlo contra `SHA256SUMS`, `release-manifest.json` y `quality-report.json`.
2. Extraerlo en una carpeta controlada y comprobar `.agents/plugins/marketplace.json` y `plugins/lks-sdd/.codex-plugin/plugin.json`.
3. Consultar `codex plugin marketplace --help` en la versión instalada. El CLI 0.125.0 comprobado para esta release admite `add`, `upgrade` y `remove`; no ofrece subcomandos CLI de instalación, reinstalación, activación o desactivación del plugin.
4. Para esta fuente local no Git, conservar la carpeta de la versión anterior y registrar su ruta para rollback; ejecutar `codex plugin marketplace remove lks-sdd-development` y `codex plugin marketplace add "RAÍZ_2.1.3_VERIFICADA"`. No usar `upgrade` para esta fuente. Para un alta inicial basta `add`; completar la activación en la superficie de Codex disponible.
5. Confirmar que Codex resuelve la nueva versión, reiniciar la aplicación y abrir una tarea nueva para cargar sus metadatos y skills.

El bundle 2.1.3 continúa siendo `skills-only` y no instala Atlassian Rovo ni configura Microsoft Entra. Para usar `jira-hybrid` o `milestone-reporting`, el participante debe disponer separadamente del peer Rovo, de una conexión Jira válida y de permisos suficientes. La aprobación stable no convierte esas interoperabilidades en `passed`. Sin Rovo, `repository-only` sigue completo; las declaraciones tecnológicas de los proyectos continúan siendo decisiones locales, sin soporte global implícito.

No edite manualmente la caché como mecanismo de actualización. La instalación o activación modifica el entorno Codex del participante y exige autorización separada. Si falla registro o carga, restaurar la fuente anterior verificada con el mismo remove/add y comprobarla.

## Retirada

Siga `pilot/ROLLBACK.md`. Retirar el plugin no autoriza a revertir automáticamente documentación o código consumidor, borrar evidencia ni mover etiquetas Git.

La prueba de instalación se realiza contra un marketplace y un directorio de configuración temporales. Debe validar manifest, seis skills, schemas, declaraciones tecnológicas, fixtures y scripts desde el bundle extraído; nunca se usa la caché activa como área de ensayo.
