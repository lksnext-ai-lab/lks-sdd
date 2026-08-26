# Distribución candidate M5

## Bundle de desarrollo

`scripts/build_candidate_package.py` genera fuera del repositorio dos ZIP reproducibles:

- `lks-sdd-plugin-vX.Y.Z.zip`, con el plugin bajo `lks-sdd/`;
- `lks-sdd-marketplace-vX.Y.Z.zip`, con `.agents/plugins/marketplace.json` y `plugins/lks-sdd/`.
- `quality-report.json`, evidencia reproducible del gate candidate ligado al commit.

`X.Y.Z` se deriva del manifiesto del plugin; el builder no mantiene una segunda versión hardcodeada. La entrada del marketplace usa la forma estándar `local`, ruta `./plugins/lks-sdd`, instalación `AVAILABLE`, autenticación `ON_INSTALL` y categoría `Developer Tools`.

El builder solo acepta la raíz exacta de un repositorio Git, comprueba que `--source-commit` exista y coincida con `HEAD`, y exige un árbol de trabajo limpio. Además exige `--quality-report`, pero no toma `gate: passed` como prueba suficiente: valida el reporte contra el esquema comprometido, exige la misma versión, fecha y commit, contrasta los hashes exactos del catálogo, los dos corpus, el manifiesto de fixtures y la baseline, verifica los hashes declarados de los fixtures y exige los inventarios exactos de checks, canales, casos y métricas. También comprueba que cada evidencia automatizada resuelva al resultado ejecutado esperado, que los totales y métricas sean internamente consistentes, que los canales opcionales conserven su `not-run` real y que la comparación recalculada contra la baseline seleccionada quede aprobada.

Los bytes del plugin se leen del commit mediante objetos Git, no del working tree. Esto impide atribuir a un SHA contenido sin confirmar, incluso si Git oculta localmente un cambio mediante `assume-unchanged`. También rechaza enlaces, submódulos, salidas dentro del repositorio y patrones de secretos conocidos.

El repositorio fija `eol=lf` para todo texto mediante `.gitattributes` y excluye de esa conversión los formatos binarios declarados. La regresión de portabilidad crea y clona un repositorio real bajo una configuración Git aislada con `core.autocrlf=true`, y exige que las fuentes canónicas, `quality/fixture-manifest.json` y todos los fixtures con hash conserven exactamente sus bytes LF y superen ambos validadores desde el checkout resultante.

El reporte publicable se genera desde un checkout dedicado, recién creado y sin archivos no versionados preexistentes, incluidos los ignorados. Desde la raíz del repositorio principal, una vez integrado y revisado el commit de release:

```powershell
$releaseVersion = "0.12.0"
$releaseDate = "2026-08-26"
$sourceCommit = (git rev-parse HEAD).Trim()
$artifactBase = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion"
$qualityReport = "$artifactBase-quality.json"
$releaseCheckout = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion-$sourceCommit-source"

if (Test-Path -LiteralPath $releaseCheckout) { throw "El checkout dedicado ya existe." }
git worktree add --detach $releaseCheckout $sourceCommit

Push-Location $releaseCheckout
try {
  python scripts\run_quality_harness.py --channel candidate --date $releaseDate --baseline quality\baselines\v0.11.0.json --profile-mode reuse --output $qualityReport
  python scripts\build_candidate_package.py --date $releaseDate --source-commit $sourceCommit --quality-report $qualityReport --output "$artifactBase-a"
  python scripts\build_candidate_package.py --date $releaseDate --source-commit $sourceCommit --quality-report $qualityReport --output "$artifactBase-b"
} finally {
  Pop-Location
}
```

El harness toma el snapshot de fuente antes de ejecutar sus comprobaciones. Por ello, un artefacto creado después por esas comprobaciones no invalida retroactivamente el reporte; sí invalidaría una nueva atestación si ya existiera al comenzarla. El reporte y las carpetas de salida no deben existir antes de sus respectivos comandos. Las dos compilaciones con igual fecha, commit y reporte deben producir hashes idénticos para los dos ZIP, `quality-report.json`, `release-manifest.json` y `SHA256SUMS`. `SHA256SUMS` cubre ambos ZIP, el reporte y el manifiesto de release; este último enumera cada archivo fuente, su tamaño, su hash y la vinculación del gate.

```powershell
$hashesA = Get-ChildItem "$artifactBase-a" -File | Sort-Object Name | ForEach-Object { "$($_.Name):$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
$hashesB = Get-ChildItem "$artifactBase-b" -File | Sort-Object Name | ForEach-Object { "$($_.Name):$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
if (Compare-Object $hashesA $hashesB) { throw "Los dos builds no son reproducibles." }

$manifest = Get-Content -Raw "$artifactBase-a\release-manifest.json" | ConvertFrom-Json
if ($manifest.source_commit -ne $sourceCommit) { throw "El manifiesto no corresponde al commit de release." }
if ($manifest.plugin_version -ne $releaseVersion) { throw "El manifiesto no corresponde a la versión de release." }
if ($manifest.quality.gate -ne "passed") { throw "El manifiesto no acredita el gate candidate." }

Push-Location "$artifactBase-a"
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

Conserve únicamente uno de los dos builds reproducidos como conjunto publicable; el segundo es evidencia de comparación y no un asset distinto. El conjunto publicable contiene cinco archivos.

## Marketplace y activación

Publicar el ZIP de marketplace como asset de GitHub no actualiza una instalación activa. Son estados separados:

1. Descargar o copiar el ZIP de marketplace publicado y verificarlo contra `SHA256SUMS`, `release-manifest.json` y `quality-report.json`.
2. Extraerlo en una carpeta controlada y comprobar `.agents/plugins/marketplace.json` y `plugins/lks-sdd/.codex-plugin/plugin.json`.
3. Consultar `codex plugin marketplace --help` en la versión instalada. El CLI 0.125.0 comprobado para esta release admite `add`, `upgrade` y `remove`; no ofrece subcomandos CLI de instalación, reinstalación, activación o desactivación del plugin.
4. Para un marketplace ya configurado, actualizar su fuente de forma controlada y ejecutar, si la versión instalada lo soporta, `codex plugin marketplace upgrade lks-sdd-development`. Para un alta inicial, usar `codex plugin marketplace add "RUTA_MARKETPLACE"` y completar la activación en la superficie de Codex disponible.
5. Confirmar que Codex resuelve la nueva versión, reiniciar la aplicación y abrir una tarea nueva para cargar sus metadatos y skills.

El bundle 0.12.0 continúa siendo `skills-only` y no instala Atlassian Rovo ni configura Microsoft Entra. Para usar `jira-hybrid` o `milestone-reporting`, el participante debe disponer separadamente del peer Rovo, de una conexión Jira válida y de permisos suficientes. Para probar interoperabilidad Entra debe aportar por separado un tenant y registros de aplicación autorizados, sin persistir credenciales en el bundle. Esa preparación no forma parte del builder ni puede darse por superada mediante un test sintético. Sin Rovo, `repository-only` sigue completo; los perfiles Entra continúan candidate hasta su certificación exacta.

No edite manualmente la caché como mecanismo de actualización. La instalación o activación modifica el entorno Codex del participante, no se automatiza desde este repositorio y requiere autorización separada de la publicación técnica.

## Retirada

Siga `pilot/ROLLBACK.md`. Retirar el plugin no autoriza a revertir automáticamente documentación o código consumidor, borrar evidencia ni mover etiquetas Git.
