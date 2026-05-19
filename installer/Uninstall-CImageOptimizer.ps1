$ErrorActionPreference = "SilentlyContinue"

$appName = "CImageOptimizer"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\$appName"
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$appName"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$appName"

Remove-Item -LiteralPath $desktopShortcut -Force
Remove-Item -LiteralPath $startMenuDir -Recurse -Force
Remove-Item -Path $uninstallKey -Recurse -Force

$currentScript = $MyInvocation.MyCommand.Path
$cleanup = @"
Start-Sleep -Seconds 2
Remove-Item -LiteralPath '$installDir' -Recurse -Force
Remove-Item -LiteralPath '$currentScript' -Force
"@

Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command $cleanup" -WindowStyle Hidden
