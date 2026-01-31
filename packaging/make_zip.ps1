<#
    Script de PowerShell para generar un archivo ZIP con el proyecto.

    Uso:
        .\packaging\make_zip.ps1

    El script crea el archivo `dist\cfdi_analyzer_edpp.zip` en la raíz del
    proyecto utilizando el cmdlet `Compress-Archive`. Archivos y carpetas
    temporales como `__pycache__`, `.git` y `dist` se excluyen.
#>
param()

$RootDir = (Resolve-Path $PSScriptRoot\..).Path
$DistDir = Join-Path $RootDir 'dist'
$ZipName = Join-Path $DistDir 'cfdi_analyzer_edpp.zip'

if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir | Out-Null
}

# Excluir carpetas y archivos no deseados
$excludeDirs = @('__pycache__', '.git', 'dist', '.pytest_cache')
$excludeFiles = @('make_zip.ps1')

Write-Host "Generando ZIP en $ZipName..."

# Recopilar todos los archivos a comprimir
$items = Get-ChildItem -Path $RootDir -Recurse -File | Where-Object {
    $relative = $_.FullName.Substring($RootDir.Length + 1)
    # Verificar exclusiones
    $parts = $relative.Split([System.IO.Path]::DirectorySeparatorChar)
    if ($parts | Where-Object { $excludeDirs -contains $_ }) { return $false }
    if ($excludeFiles -contains $_.Name) { return $false }
    return $true
}

Compress-Archive -LiteralPath $items.FullName -DestinationPath $ZipName -Force
Write-Host "ZIP creado satisfactoriamente."