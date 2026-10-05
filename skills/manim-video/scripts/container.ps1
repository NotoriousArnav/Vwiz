param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

if ($RemainingArgs.Count -eq 0) {
    Write-Error "Usage: scripts/container.ps1 <command> [args...]"
    exit 2
}

try {
    $null = Get-Command docker -ErrorAction Stop
}
catch {
    Write-Error "Docker is required. Run scripts/setup.ps1 after installing Docker."
    exit 127
}

$Image = if ([string]::IsNullOrWhiteSpace($env:MANIM_DOCKER_IMAGE)) {
    "manim-video-runtime:v0.20.1"
}
else {
    $env:MANIM_DOCKER_IMAGE
}

$ProjectDir = if ([string]::IsNullOrWhiteSpace($env:MANIM_PROJECT_DIR)) {
    (Get-Location).Path
}
else {
    $env:MANIM_PROJECT_DIR
}

$DockerArgs = @(
    "run",
    "--rm",
    "-v", "${ProjectDir}:/manim",
    "-w", "/manim",
    "-e", "MPLCONFIGDIR=/tmp/matplotlib",
    "-e", "XDG_CACHE_HOME=/tmp/.cache",
    $Image
) + $RemainingArgs

& docker @DockerArgs
exit $LASTEXITCODE
