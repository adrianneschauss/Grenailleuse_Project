param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $Root)
$VenvDir = Join-Path $Root ".build-venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$Requirements = Join-Path $Root "build_requirements.txt"
$SpecPath = Join-Path $Root "newest_animation.spec"
$DistRoot = Join-Path $ProjectRoot "dist"
$BuildRoot = Join-Path $ProjectRoot "build\pyinstaller"
$ReleaseDir = Join-Path $DistRoot "newest_animation_windows_exe"
$ExecutablePath = Join-Path $ReleaseDir "NewestAnimation.exe"

function Invoke-CommandArray {
    param(
        [string[]]$Command
    )
    $Executable = $Command[0]
    $Arguments = @()
    if ($Command.Length -gt 1) {
        $Arguments = $Command[1..($Command.Length - 1)]
    }
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $($Command -join ' ')"
    }
}

function Get-BasePythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "Python 3 was not found. Install Python for Windows first."
}

if ($Clean) {
    Remove-Item -Recurse -Force $BuildRoot -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $ReleaseDir -ErrorAction SilentlyContinue
}

if (-not (Test-Path $VenvPython)) {
    $BasePython = @(Get-BasePythonCommand)
    Invoke-CommandArray ($BasePython + @("-m", "venv", $VenvDir))
}

Invoke-CommandArray @($VenvPython, "-m", "pip", "install", "--upgrade", "pip")
Invoke-CommandArray @($VenvPython, "-m", "pip", "install", "-r", $Requirements)

if (-not (Test-Path $DistRoot)) {
    New-Item -ItemType Directory -Path $DistRoot | Out-Null
}

Invoke-CommandArray @(
    $VenvPython,
    "-m",
    "PyInstaller",
    "--clean",
    "--noconfirm",
    "--distpath",
    $ReleaseDir,
    "--workpath",
    $BuildRoot,
    $SpecPath
)

if (-not (Test-Path $ExecutablePath)) {
    throw "Expected executable was not created: $ExecutablePath"
}

Copy-Item (Join-Path $Root "README.md") (Join-Path $ReleaseDir "README.md") -Force

Write-Host "Standalone executable ready:"
Write-Host $ExecutablePath
