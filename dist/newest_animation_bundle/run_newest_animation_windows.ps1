param(
    [string]$Save = "",
    [Nullable[int]]$Fps = $null,
    [switch]$Reinstall
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$CacheRoot = Join-Path $env:LOCALAPPDATA "GrenailleuseAnimation"
$VenvDir = Join-Path $CacheRoot "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$Requirements = Join-Path $Root "requirements.txt"
$AnimationScript = Join-Path $Root "newest_animation.py"
$MplConfigDir = Join-Path $CacheRoot "mplconfig"
$DepsMarker = Join-Path $VenvDir ".animation_deps_installed"

function Get-BasePythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "Python 3 was not found. Install Python for Windows first."
}

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

New-Item -ItemType Directory -Path $CacheRoot -Force | Out-Null
New-Item -ItemType Directory -Path $MplConfigDir -Force | Out-Null
$env:MPLCONFIGDIR = $MplConfigDir

if (-not (Test-Path $VenvPython)) {
    $BasePython = @(Get-BasePythonCommand)
    Invoke-CommandArray ($BasePython + @("-m", "venv", $VenvDir))
}

if ($Reinstall -or -not (Test-Path $DepsMarker)) {
    Invoke-CommandArray @($VenvPython, "-m", "pip", "install", "--upgrade", "pip")
    Invoke-CommandArray @($VenvPython, "-m", "pip", "install", "-r", $Requirements)
    Set-Content -Path $DepsMarker -Value "ok"
}

$OutputPath = if ($Save -ne "") {
    $Save
} else {
    Join-Path $Root "simulation_movie_latest.mp4"
}

$ArgsList = @($AnimationScript, "--interactive")
$ArgsList += @("--save", $OutputPath)
if ($null -ne $Fps) {
    $ArgsList += @("--fps", "$Fps")
}

& $VenvPython @ArgsList
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$ResolvedOutputPath = $OutputPath
if (-not [System.IO.Path]::IsPathRooted($ResolvedOutputPath)) {
    $ResolvedOutputPath = Join-Path $Root $ResolvedOutputPath
}
if (Test-Path $ResolvedOutputPath) {
    Start-Process $ResolvedOutputPath
}
exit 0
