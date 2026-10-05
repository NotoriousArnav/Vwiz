param(
    [switch]$Check,
    [switch]$NoPull,
    [switch]$Rebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  + " -NoNewline -ForegroundColor Green
    Write-Host $Message
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ! " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  x " -NoNewline -ForegroundColor Red
    Write-Host $Message
}

function Test-DockerImage {
    param([string]$Image)
    $null = & docker image inspect $Image 2>$null
    return ($LASTEXITCODE -eq 0)
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir
$DefaultImage = "manim-video-runtime:v0.20.1"
$BaseImage = if ([string]::IsNullOrWhiteSpace($env:MANIM_BASE_IMAGE)) {
    "manimcommunity/manim:v0.20.1"
}
else {
    $env:MANIM_BASE_IMAGE
}
$Image = if ([string]::IsNullOrWhiteSpace($env:MANIM_DOCKER_IMAGE)) {
    $DefaultImage
}
else {
    $env:MANIM_DOCKER_IMAGE
}
$UsingCustomImage = -not [string]::IsNullOrWhiteSpace($env:MANIM_DOCKER_IMAGE)
$PullImage = -not ($Check -or $NoPull)
$Errors = 0

Write-Host ""
Write-Host "Manim Video Lab - Docker Setup"
Write-Host ""

try {
    $DockerVersion = & docker --version
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker CLI found: $DockerVersion"
    }
    else {
        Write-Fail "Docker CLI not found. Install Docker Desktop or Docker Engine first."
        exit 1
    }
}
catch {
    Write-Fail "Docker CLI not found. Install Docker Desktop or Docker Engine first."
    exit 1
}

$null = & docker info 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Docker daemon is running"
}
else {
    Write-Fail "Docker daemon is not running. Start Docker and rerun this script."
    exit 1
}

if ((-not $UsingCustomImage) -and $Rebuild) {
    Write-Warn "Rebuilding $Image from $BaseImage ..."
    & docker build --build-arg "MANIM_BASE_IMAGE=$BaseImage" -t $Image $SkillDir
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Built $Image"
    }
    else {
        Write-Fail "Could not build $Image"
        $Errors += 1
    }
}
elseif (Test-DockerImage $Image) {
    Write-Ok "Image already available: $Image"
}
elseif (-not $UsingCustomImage) {
    Write-Warn "Image not found locally. Building $Image from $BaseImage ..."
    & docker build --build-arg "MANIM_BASE_IMAGE=$BaseImage" -t $Image $SkillDir
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Built $Image"
    }
    else {
        Write-Fail "Could not build $Image"
        $Errors += 1
    }
}
elseif ($PullImage) {
    Write-Warn "Image not found locally. Pulling $Image ..."
    & docker pull $Image
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Pulled $Image"
    }
    else {
        Write-Fail "Could not pull $Image"
        $Errors += 1
    }
}
else {
    Write-Warn "Image not found locally: $Image"
    Write-Warn "Run: docker pull $Image"
    $Errors += 1
}

if ($Errors -eq 0) {
    $ManimVersion = & docker run --rm $Image manim --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Manim available in container: $($ManimVersion | Select-Object -First 1)"
    }
    else {
        Write-Fail "Manim command failed inside $Image"
        $Errors += 1
    }

    $FfmpegVersion = & docker run --rm $Image ffmpeg -version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "ffmpeg available in container: $($FfmpegVersion | Select-Object -First 1)"
    }
    else {
        Write-Fail "ffmpeg command failed inside $Image"
        $Errors += 1
    }

    $PdflatexPath = & docker run --rm $Image bash -c "command -v pdflatex" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "LaTeX available in container: $PdflatexPath"
    }
    else {
        Write-Warn "pdflatex was not found in $Image. MathTex/Tex scenes may need a custom image."
    }
}

Write-Host ""
if ($Errors -eq 0) {
    Write-Host "Ready. Render from any Manim project directory with:" -ForegroundColor Green
    Write-Host "  path\to\manim-video\scripts\manim.ps1 -ql script.py SceneName"
    Write-Host ""
}
else {
    Write-Host "$Errors setup check(s) failed." -ForegroundColor Red
    Write-Host ""
    exit 1
}
