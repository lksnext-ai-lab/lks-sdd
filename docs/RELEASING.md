# Releases técnicas

## Propósito

Las releases de GitHub fijan hitos reproducibles del plugin LKS-SDD para Codex. Publicar una release técnica no equivale a aprobar el método como política corporativa, instalar el plugin, habilitar soporte oficial ni decidir su distribución por marketplace.

## Versionado

- El manifiesto `.codex-plugin/plugin.json`, la primera entrada de `CHANGELOG.md`, las notas `docs/releases/vX.Y.Z.md` y la etiqueta `vX.Y.Z` deben usar la misma versión SemVer.
- Un hito funcional compatible incrementa la versión menor; una corrección compatible incrementa el parche; una ruptura de contrato incrementa la versión mayor.
- La versión SemVer del plugin no acredita por sí sola un hito metodológico del mismo número. La nota de release declara por separado qué hitos están implementados, preparados, pendientes o `not-run`.
- Los commits intermedios en `main` no generan ni modifican releases. La release se actualiza creando una versión nueva cuando el cambio está cerrado y validado.
- Las etiquetas `vX.Y.Z` son anotadas e inmutables. Una versión publicada nunca se mueve ni se reutiliza.
- Las versiones `candidate` se publican como prerelease y pueden tener canales semánticos, humanos o de piloto pendientes si las notas lo declaran. Una versión `stable` exige todos los canales definidos en `quality/catalog.json`.

## Puerta de publicación

Antes de publicar una versión:

1. Cerrar el alcance y actualizar versión, changelog, estado documental, ayudas y notas en `docs/releases/`.
2. Ejecutar las validaciones de `docs/VALIDATION.md` y revisar el diff completo.
3. Integrar el commit exacto en `main`, subirlo y comprobar que el árbol de trabajo está limpio y sin divergencia con `origin/main`.
4. Para M5 o posteriores, crear un checkout dedicado y vacío del commit exacto, generar allí un reporte candidate 1.1 que atestigüe `HEAD`, índice y bytes reales sin ningún archivo no versionado preexistente —también los ignorados—, generar dos veces los bundles con ese mismo reporte, verificar reproducibilidad, manifiesto y checksums, y mantenerlos fuera del árbol Git.
5. Solo después de superar el harness limpio y el doble build, crear y subir una etiqueta anotada `vX.Y.Z` sobre ese commit.
6. Crear la prerelease de GitHub desde la etiqueta remota existente, con las notas versionadas y los cinco assets candidate; verificar URL, commit, estado, cuerpo, hashes y descargas.

El builder no acepta un SHA ni un reporte de éxito meramente declarativos: el commit debe existir, coincidir con `HEAD` y tener un working tree limpio. Además revalida contra el contenido comprometido el esquema, hashes de inputs y fixtures, inventarios de checks, canales, casos y métricas, resolución de evidencias, consistencia de totales y comparación con la baseline. Empaqueta los blobs del commit, no los bytes del working tree.

## Secuencia reproducible

Los comandos siguientes se ejecutan desde la raíz del repositorio cuando los cambios revisados ya están integrados en un commit local de `main`. Ajuste la versión y la fecha, pero no reutilice una etiqueta existente ni use `git add .` como sustituto de la revisión de rutas:

```powershell
$releaseVersion = "0.7.0"
$releaseDate = "2026-08-20"
$releaseTag = "v$releaseVersion"

git status --short --branch
git diff --check
if ((git status --porcelain)) { throw "El árbol de trabajo no está limpio." }
git push origin main

$sourceCommit = (git rev-parse HEAD).Trim()
$remoteMain = (git ls-remote origin refs/heads/main | ForEach-Object { ($_ -split "`t")[0] }).Trim()
if ($remoteMain -ne $sourceCommit) { throw "origin/main no coincide con el commit de release." }
```

Genere el reporte limpio y los dos builds externos desde el checkout dedicado descrito en `docs/DISTRIBUTION.md`. El harness captura la fuente antes de ejecutar checks: los artefactos creados después no invalidan retroactivamente ese snapshot, pero cualquier archivo no versionado que ya existiera al iniciarlo —aunque estuviera ignorado— lo habría dejado `dirty`. El builder solo necesita el commit exacto; no requiere que ya exista una etiqueta. No cree la etiqueta inmutable hasta que el harness candidate, la comparación de los dos builds, el manifiesto y los checksums hayan superado la puerta. Después etiquete ese mismo commit y verifique la etiqueta remota:

```powershell
git tag -a $releaseTag $sourceCommit -m "LKS-SDD $releaseVersion"
git push origin $releaseTag

$remoteTaggedCommit = (git ls-remote origin "refs/tags/$releaseTag^{}" | ForEach-Object { ($_ -split "`t")[0] }).Trim()
if ($remoteTaggedCommit -ne $sourceCommit) { throw "La etiqueta remota no apunta al commit de release." }
```

Publique exactamente uno de los dos conjuntos reproducidos:

```powershell
$artifactBase = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion"
$publishRoot = "$artifactBase-a"

gh release create $releaseTag `
  (Join-Path $publishRoot "lks-sdd-plugin-v$releaseVersion.zip") `
  (Join-Path $publishRoot "lks-sdd-marketplace-v$releaseVersion.zip") `
  (Join-Path $publishRoot "quality-report.json") `
  (Join-Path $publishRoot "release-manifest.json") `
  (Join-Path $publishRoot "SHA256SUMS") `
  --repo lksnext-ai-lab/lks-sdd `
  --title "LKS-SDD $releaseVersion" `
  --notes-file "docs/releases/$releaseTag.md" `
  --verify-tag `
  --fail-on-no-commits `
  --prerelease `
  --latest=false
```

`--verify-tag` evita que GitHub cree silenciosamente otra etiqueta. `gh release create` usa una fase draft mientras carga los assets y solo publica al completarla; no use `--clobber` para sustituir assets de una versión publicada.

Verificación posterior mínima:

```powershell
$release = gh release view $releaseTag --repo lksnext-ai-lab/lks-sdd `
  --json name,tagName,isDraft,isPrerelease,publishedAt,targetCommitish,url,assets,body | ConvertFrom-Json
if ($release.tagName -ne $releaseTag) { throw "La release no usa la etiqueta esperada." }
if ($release.isDraft -or -not $release.isPrerelease) { throw "La release no quedó publicada como prerelease." }

$expectedAssets = @("lks-sdd-plugin-v$releaseVersion.zip", "lks-sdd-marketplace-v$releaseVersion.zip", "quality-report.json", "release-manifest.json", "SHA256SUMS") | Sort-Object
$actualAssets = @($release.assets.name) | Sort-Object
if (Compare-Object $expectedAssets $actualAssets) { throw "Los assets publicados no coinciden con el conjunto aprobado." }
foreach ($asset in $release.assets) {
  $localDigest = (Get-FileHash -LiteralPath (Join-Path $publishRoot $asset.name) -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($asset.digest -and $asset.digest -ne "sha256:$localDigest") { throw "Digest remoto incorrecto: $($asset.name)" }
}

$localBody = (Get-Content -Raw "docs/releases/$releaseTag.md").Replace("`r`n", "`n").TrimEnd()
$remoteBody = $release.body.Replace("`r`n", "`n").TrimEnd()
if ($localBody -ne $remoteBody) { throw "Las notas publicadas no coinciden con el archivo versionado." }

git ls-remote --heads --tags origin
```

El cuerpo remoto debe coincidir con `docs/releases/$releaseTag.md`; la release debe ser no draft y prerelease, la etiqueta debe resolver al commit esperado y deben existir los dos ZIP, `quality-report.json`, `release-manifest.json` y `SHA256SUMS` con los hashes verificados.

Si una validación falla, corríjala antes de etiquetar. Si la carga falla mientras la release aún es draft, inspeccione ese draft antes de reanudar. Una vez publicada, no mueva la etiqueta ni reemplace assets: cierre la corrección en una versión nueva.

## Contenido de las notas

Las notas deben distinguir capacidades implementadas, compatibilidad, validaciones, límites y pendientes. Deben indicar expresamente cualquier estado `candidate` y evitar presentar una release técnica como aprobación corporativa.

Cada nota incluye como mínimo:

- versión y fecha;
- enlace o referencia al changelog;
- matriz o declaración de compatibilidad;
- perfiles y locks aplicables;
- resultados de tests, evals y canales que siguen `not-run`;
- vulnerabilidades conocidas y otras limitaciones;
- instrucciones de actualización;
- migración o declaración explícita de que no se requiere; si `human_review_required` contiene entradas, las notas deben indicar que la aplicación queda siempre bloqueada antes de escribir hasta resolver cada entrada en el origen y repetir el preview con lista vacía. La `Identity` agregada se traslada aparte a tres dominios `pending`: no bloquea la escritura de la migración, pero sí readiness hasta su resolución en 1.1;
- rollback;
- periodo o estado de soporte;
- responsables confirmados o, si todavía no existen, el pendiente explícito.

El validador contractual compara dinámicamente la versión del manifiesto con la primera entrada del changelog y `docs/releases/vX.Y.Z.md`. La etiqueta se comprueba únicamente al publicar, porque los commits intermedios no constituyen una release.
