param(
    [Parameter(Mandatory=$true)][ValidateSet('codex','copilot')][string]$Target,
    [Parameter(Mandatory=$true)][string]$Destination,
    [switch]$Remove
)
$ErrorActionPreference = 'Stop'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { throw 'Instala Python 3.11 o posterior y vuelve a ejecutar este asistente.' }
$installer = Join-Path $PSScriptRoot 'install.py'
$installerArgs = @($installer, $Target, $Destination)
if ($Remove) { $installerArgs += '--remove' }
$previewText = & $pythonCommand.Source @installerArgs
if ($LASTEXITCODE -ne 0) { throw ($previewText -join "`n") }
$preview = ($previewText -join "`n") | ConvertFrom-Json
Write-Host ("Destino: {0}. Archivos afectados: {1}" -f $preview.destination, $preview.changes.Count)
$preview.changes | Select-Object path, before, after | Format-Table
$answer = Read-Host '¿Aplicar estos cambios locales? Escribe SI'
if ($answer -cne 'SI') { Write-Host 'Sin cambios.'; return }
& $pythonCommand.Source @installerArgs --apply --authorize $preview.preview_hash
if ($LASTEXITCODE -ne 0) { throw 'Instalación detenida. Conserva la salida y el journal de recuperación si existe.' }
if ($Target -eq 'copilot') {
    Write-Host 'Abre el proyecto en VS Code, selecciona Copilot Agent y abre una conversación nueva. Versiona los archivos gestionados mediante tu flujo Git habitual.'
} elseif (-not $Remove) {
    Write-Host 'Archivos preparados. La activación en Codex es un paso separado:'
    Write-Host ('codex plugin marketplace add "{0}"' -f $preview.destination)
    Write-Host 'codex plugin add lks-sdd@lks-sdd-development'
    Write-Host 'Comprueba antes si ya tienes registrado ese marketplace. Después abre una tarea nueva.'
}
