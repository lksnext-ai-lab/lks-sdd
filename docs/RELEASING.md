# Releases técnicas

## Línea dual 2.0

Codex desktop y Copilot VS Code Agent se distribuyen con una versión, un núcleo y dos
adaptadores. El setup offline facilita instalar y actualizar sin tocar configuraciones
personales. La versión estable es `2.0.2`; tiene aprobación propia del responsable
en `quality/release-approval-v2.0.2.json`, sin reutilizar las aprobaciones de 1.x.
Los paquetes de desarrollo son diagnósticos, no atestaciones publicables. Antes de
promover, declarar el estado real de la [aceptación v2](V2-HOST-ACCEPTANCE.md), superar
gates técnicos, build reproducible limpio y autorización de publicación separada.
La autorización de publicación v2 no acredita los ensayos humanos/host pendientes. El snapshot de evaluación
no debe publicarse como estable aunque permita una instalación local satisfactoria.

## Propósito

Las releases de GitHub fijan hitos reproducibles del plugin LKS-SDD para Codex. Publicar una release técnica no equivale a aprobar el método como política corporativa, instalar el plugin, habilitar soporte oficial ni decidir su distribución por marketplace.

## Versionado

- El manifiesto `.codex-plugin/plugin.json`, la primera entrada de `CHANGELOG.md`, las notas `docs/releases/vX.Y.Z.md` y la etiqueta `vX.Y.Z` deben usar la misma versión SemVer.
- Un hito funcional compatible incrementa la versión menor; una corrección compatible incrementa el parche; una ruptura de contrato incrementa la versión mayor.
- La versión SemVer del plugin no acredita por sí sola un hito metodológico del mismo número. La nota de release declara por separado qué hitos están implementados, preparados, pendientes o `not-run`.
- Los commits intermedios en `main` no generan ni modifican releases. La release se actualiza creando una versión nueva cuando el cambio está cerrado y validado.
- Las etiquetas `vX.Y.Z` son anotadas e inmutables. Una versión publicada nunca se mueve ni se reutiliza.
- Las versiones `candidate` se publican como prerelease. Una versión `stable` exige los canales técnicos definidos en `quality/catalog.json` y una aprobación durable del responsable del proyecto. Los canales semánticos, humanos o de piloto detallados conservan su estado real, pero son evidencia opcional y no sustituyen esa autoridad.

## Puerta de publicación

Antes de publicar una versión:

1. Cerrar el alcance y actualizar versión, changelog, estado documental, ayudas y notas en `docs/releases/`.
2. Ejecutar las validaciones de `docs/VALIDATION.md` y revisar el diff completo.
3. Integrar mediante PR revisable con CI correcto y comprobar el SHA final de `main` y su coincidencia con `origin/main`.
4. Para M5 o posteriores, crear un checkout dedicado y vacío del commit exacto y generar allí una única vez el reporte 1.2 del canal de release. El harness atestigua antes de sus hijos `HEAD`, índice y bytes reales sin ningún archivo no versionado preexistente —también los ignorados—, aplica los presupuestos y valida las certificaciones exactas de todos los perfiles active. Para `stable`, el reporte incorpora además `release-approval`; después se generan dos veces los bundles, se verifican reproducibilidad, manifiesto y checksums y se mantienen fuera del árbol Git. `--preflight-only` queda disponible como diagnóstico completo opcional, no como paso previo redundante.
5. Solo después de superar el harness limpio y el doble build, crear y subir una etiqueta anotada `vX.Y.Z` sobre ese commit.
6. Esperar el workflow correcto de la etiqueta y crear la release desde esa etiqueta,
   como prerelease para `candidate` o normal para `stable`, con notas versionadas y
   el inventario completo de assets aprobado; verificar URL, commit, estado y hashes.

El builder no acepta un SHA ni un reporte de éxito meramente declarativos: el commit debe existir, coincidir con `HEAD` y tener un working tree limpio. Además revalida contra el contenido comprometido el esquema, hashes de inputs y fixtures, inventarios de checks, canales, casos y métricas, resolución de evidencias, consistencia de totales y comparación con la baseline. Empaqueta los blobs del commit, no los bytes del working tree.

## Secuencia reproducible

Los comandos siguientes se ejecutan desde la raíz del repositorio cuando los cambios revisados ya están integrados en un commit local de `main`. Ajuste la versión y la fecha, pero no reutilice una etiqueta existente ni use `git add .` como sustituto de la revisión de rutas:

```powershell
$releaseVersion = "2.0.2"
$releaseChannel = "stable"
$releaseDate = Get-Date -Format "yyyy-MM-dd"
$releaseTag = "v$releaseVersion"

git status --short --branch
git diff --check
if ((git status --porcelain)) { throw "El árbol de trabajo no está limpio." }
git push origin main

$sourceCommit = (git rev-parse HEAD).Trim()
$remoteMain = (git ls-remote origin refs/heads/main | ForEach-Object { ($_ -split "`t")[0] }).Trim()
if ($remoteMain -ne $sourceCommit) { throw "origin/main no coincide con el commit de release." }
```

Genere el reporte limpio y los dos builds externos desde el checkout dedicado descrito en `docs/DISTRIBUTION.md`. El harness captura la fuente antes de ejecutar checks: los artefactos creados después no invalidan retroactivamente ese snapshot, pero cualquier archivo no versionado que ya existiera al iniciarlo —aunque estuviera ignorado— lo habría dejado `dirty`. El builder solo necesita el commit exacto; no requiere que ya exista una etiqueta. No cree la etiqueta inmutable hasta que el harness del canal elegido, la comparación de los dos builds, el manifiesto y los checksums hayan superado la puerta. Después etiquete ese mismo commit y verifique la etiqueta remota:

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

$releaseVisibility = if ($releaseChannel -eq "candidate") { @("--prerelease", "--latest=false") } else { @("--latest") }

$approvedManifest = Get-Content (Join-Path $publishRoot 'release-manifest.json') -Raw | ConvertFrom-Json
$approvedNames = @($approvedManifest.artifacts.path) + @('release-manifest.json', 'SHA256SUMS')
$approvedAssets = @($approvedNames | ForEach-Object { Join-Path $publishRoot $_ })
gh release create $releaseTag @approvedAssets `
  --repo lksnext-ai-lab/lks-sdd `
  --title "LKS-SDD $releaseVersion" `
  --notes-file "docs/releases/$releaseTag.md" `
  --verify-tag `
  --fail-on-no-commits `
  @releaseVisibility
```

`--verify-tag` evita que GitHub cree silenciosamente otra etiqueta. `gh release create` usa una fase draft mientras carga los assets y solo publica al completarla; no use `--clobber` para sustituir assets de una versión publicada.

Verificación posterior mínima:

```powershell
$release = gh release view $releaseTag --repo lksnext-ai-lab/lks-sdd `
  --json name,tagName,isDraft,isPrerelease,publishedAt,targetCommitish,url,assets,body | ConvertFrom-Json
if ($release.tagName -ne $releaseTag) { throw "La release no usa la etiqueta esperada." }
if ($release.isDraft) { throw "La release quedó como draft." }
if ($releaseChannel -eq "candidate" -and -not $release.isPrerelease) { throw "La candidate no quedó como prerelease." }
if ($releaseChannel -eq "stable" -and $release.isPrerelease) { throw "La stable quedó marcada como prerelease." }

$expectedAssets = $approvedNames | Sort-Object
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

El cuerpo remoto debe coincidir con `docs/releases/$releaseTag.md`; la release debe
ser no draft y su estado prerelease debe corresponder al canal. La etiqueta debe
resolver al commit esperado y todos los assets declarados deben tener hashes
verificados, incluidos los ZIP Copilot (plugin nativo y alternativa de proyecto) y setup.

Si una validación falla, corríjala antes de etiquetar. Si la carga falla mientras la release aún es draft, inspeccione ese draft antes de reanudar. Una vez publicada, no mueva la etiqueta ni reemplace assets: cierre la corrección en una versión nueva.

## Contenido de las notas

Las notas deben distinguir capacidades implementadas, compatibilidad, validaciones, límites y pendientes. Deben indicar expresamente cualquier estado `candidate` y evitar presentar una release técnica como aprobación corporativa.

Cada nota incluye como mínimo:

- versión y fecha;
- enlace o referencia al changelog;
- matriz o declaración de compatibilidad;
- catálogo de perfiles, estados active/candidate, locks y certificaciones exactas aplicables;
- resultados de tests, evals y canales que siguen `not-run`;
- vulnerabilidades conocidas y otras limitaciones;
- instrucciones de actualización;
- declaración explícita de compatibilidad o incompatibilidad. Para 0.15, schema 1.5/método 1.5.0 es el único contrato de proyecto y no se distribuye migrador; la evidencia histórica compatible permanece inmutable;
- rollback;
- periodo o estado de soporte;
- responsables confirmados o, si todavía no existen, el pendiente explícito.

Para 0.15.0, las notas deben documentar los tiers, la selección por cambios, los presupuestos bloqueantes, el fail-fast y la compatibilidad histórica del quality report 1.1. También conservan los contratos 0.14: aplicabilidad visual por slice, material canónico del `build_id`, separación de `verification_run_id` y flujo G3 → plantilla G4 → evidencia completa. Deben distinguir el OIDC simulado local de la interoperabilidad externa. Los tests sintéticos, previews y recibos no permiten declarar Microsoft Entra o Rovo/Jira real como `passed`; esa evidencia permanece `not-run` hasta una ejecución autorizada.

Para 0.17.0, las notas incluyen además interfaces `INT-###`, scopes tipados, EVID 1.3, el gate full-stack, reglas de mocks, reconciliación histórica y migración no destructiva. El paquete debe superar recertificación exacta del perfil de sistema, instalación limpia aislada y validación extraída sin tocar una instalación activa.

El validador contractual compara dinámicamente la versión del manifiesto con la primera entrada del changelog y `docs/releases/vX.Y.Z.md`. La etiqueta se comprueba únicamente al publicar, porque los commits intermedios no constituyen una release.
