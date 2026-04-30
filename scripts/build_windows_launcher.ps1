$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Icon = Join-Path $Root "icon\1.ico"
$Args = @("--onefile", "--name", "ChinoBotLauncher")
if (Test-Path $Icon) {
    $Args += @("--icon", $Icon)
}
$Args += "scripts\windows_launcher.py"
python -m PyInstaller @Args
Write-Host "Done: dist\ChinoBotLauncher.exe"
