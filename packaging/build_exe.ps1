<#
    Script de PowerShell para compilar la aplicación como ejecutable Windows
    utilizando PyInstaller. El ejecutable se genera en la carpeta `dist`.

    Uso:
        .\packaging\build_exe.ps1

    Requisitos:
        - Tener PyInstaller instalado (`pip install pyinstaller`).
        - Ejecutar este script desde la raíz del proyecto.
#>
param()

$ErrorActionPreference = 'Stop'

$RootDir = (Resolve-Path $PSScriptRoot\..).Path

Write-Host "Construyendo ejecutable con PyInstaller..."

Push-Location $RootDir

try {
    # Limpiar compilaciones previas
    if (Test-Path 'build') { Remove-Item -Recurse -Force 'build' }
    if (Test-Path 'dist') { Remove-Item -Recurse -Force 'dist' }

    $mainScript = 'cfdi_analyzer_edpp\app\main.py'
    $assetsSpec = 'cfdi_analyzer_edpp\assets;assets'

    & pyinstaller --clean --noconfirm --name 'cfdi_analyzer_edpp' `
        --onefile --windowed --add-data $assetsSpec `
        $mainScript

    Write-Host "Ejecución completada. El ejecutable se encuentra en dist\cfdi_analyzer_edpp.exe"
} finally {
    Pop-Location
}