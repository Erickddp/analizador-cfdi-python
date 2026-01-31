# 1) Build EXE
python -m PyInstaller --noconsole --name AnalizadorCFDI --icon "site\assets\logos\favicon.ico" -m app.main

# 2) ZIP para la web
$zip = "site\assets\downloads\AnalizadorCFDI.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path "dist\AnalizadorCFDI\*" -DestinationPath $zip

Write-Host "✅ Release listo:"
Write-Host " - EXE: dist\AnalizadorCFDI\AnalizadorCFDI.exe"
Write-Host " - ZIP: $zip"
