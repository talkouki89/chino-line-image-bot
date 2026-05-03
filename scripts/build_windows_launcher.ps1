$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
$Icon = Join-Path $Root "pic\icon.ico"
$PicDir = Join-Path $Root "pic"

$CliName = "ChinoBotLauncher-$Version-cli"
$GuiName = "ChinoBotLauncher-$Version-gui"

$CommonArgs = @("--onefile", "--clean")
if (Test-Path $Icon) {
    $CommonArgs += @("--icon", $Icon)
}

$CliArgs = @($CommonArgs + @("--name", $CliName, "scripts\windows_launcher.py"))
python -m PyInstaller @CliArgs
Write-Host "Done: dist\$CliName.exe"

$GuiArgs = @($CommonArgs + @("--noconsole", "--name", $GuiName))
if (Test-Path $PicDir) {
    $GuiArgs += @("--add-data", "$PicDir;pic")
}
$GuiArgs += "scripts\windows_launcher_gui.py"
python -m PyInstaller @GuiArgs
Write-Host "Done: dist\$GuiName.exe"
