$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $projectRoot "dist"
$sourceExe = Join-Path $distDir "main.exe"
$payloadDir = Join-Path $PSScriptRoot "payload"
$installerExe = Join-Path $distDir "CImageOptimizer-Setup.exe"
$setupSource = Join-Path $PSScriptRoot "Setup.cs"

if (-not (Test-Path -LiteralPath $sourceExe)) {
    throw "Missing PyInstaller output: $sourceExe. Build it first with: pyinstaller --noconsole --onefile main.py"
}

New-Item -ItemType Directory -Path $payloadDir -Force | Out-Null
Copy-Item -LiteralPath $sourceExe -Destination (Join-Path $payloadDir "CImageOptimizer.exe") -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "Uninstall-CImageOptimizer.ps1") -Destination (Join-Path $payloadDir "Uninstall-CImageOptimizer.ps1") -Force

$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path -LiteralPath $csc)) {
    $csc = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe"
}
if (-not (Test-Path -LiteralPath $csc)) {
    throw "Could not find the .NET Framework C# compiler."
}

& $csc /nologo /target:winexe /platform:anycpu /optimize+ /out:"$installerExe" /reference:System.Windows.Forms.dll /resource:"$payloadDir\CImageOptimizer.exe,CImageOptimizer.exe" /resource:"$payloadDir\Uninstall-CImageOptimizer.ps1,Uninstall-CImageOptimizer.ps1" "$setupSource"
if ($LASTEXITCODE -ne 0) {
    throw "C# compiler failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $installerExe)) {
    throw "Compiler completed but did not create $installerExe"
}

Write-Host "Created installer: $installerExe"
