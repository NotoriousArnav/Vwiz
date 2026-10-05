#!/usr/bin/env bash
set -euo pipefail

G="\033[0;32m"
Y="\033[0;33m"
R="\033[0;31m"
N="\033[0m"

ok() { printf "  ${G}+${N} %s\n" "$1"; }
warn() { printf "  ${Y}!${N} %s\n" "$1"; }
fail() { printf "  ${R}x${N} %s\n" "$1"; }

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
DEFAULT_IMAGE="manim-video-runtime:v0.20.1"
BASE_IMAGE="${MANIM_BASE_IMAGE:-manimcommunity/manim:v0.20.1}"
IMAGE="${MANIM_DOCKER_IMAGE:-$DEFAULT_IMAGE}"
PULL_IMAGE=1
REBUILD_IMAGE=0
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/manim-video-setup.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ "${1:-}" == "--check" || "${1:-}" == "--no-pull" ]]; then
  PULL_IMAGE=0
elif [[ "${1:-}" == "--rebuild" ]]; then
  REBUILD_IMAGE=1
fi

printf "\nManim Video Lab - Docker Setup\n\n"

errors=0

if command -v docker >/dev/null 2>&1; then
  ok "Docker CLI found: $(docker --version)"
else
  fail "Docker CLI not found. Install Docker Desktop or Docker Engine first."
  exit 1
fi

if docker info >/dev/null 2>&1; then
  ok "Docker daemon is running"
else
  fail "Docker daemon is not running. Start Docker and rerun this script."
  exit 1
fi

if [[ -z "${MANIM_DOCKER_IMAGE:-}" && "$REBUILD_IMAGE" -eq 1 ]]; then
  warn "Rebuilding $IMAGE from $BASE_IMAGE ..."
  if docker build --build-arg "MANIM_BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" "$SKILL_DIR"; then
    ok "Built $IMAGE"
  else
    fail "Could not build $IMAGE"
    errors=$((errors + 1))
  fi
elif docker image inspect "$IMAGE" >/dev/null 2>&1; then
  ok "Image already available: $IMAGE"
elif [[ -z "${MANIM_DOCKER_IMAGE:-}" ]]; then
  warn "Image not found locally. Building $IMAGE from $BASE_IMAGE ..."
  if docker build --build-arg "MANIM_BASE_IMAGE=$BASE_IMAGE" -t "$IMAGE" "$SKILL_DIR"; then
    ok "Built $IMAGE"
  else
    fail "Could not build $IMAGE"
    errors=$((errors + 1))
  fi
elif [[ "$PULL_IMAGE" -eq 1 ]]; then
  warn "Image not found locally. Pulling $IMAGE ..."
  if docker pull "$IMAGE"; then
    ok "Pulled $IMAGE"
  else
    fail "Could not pull $IMAGE"
    errors=$((errors + 1))
  fi
else
  warn "Image not found locally: $IMAGE"
  warn "Run: docker pull $IMAGE"
  errors=$((errors + 1))
fi

if [[ "$errors" -eq 0 ]]; then
  if docker run --rm "$IMAGE" manim --version >"$TMP_DIR/manim-version.txt" 2>"$TMP_DIR/manim-version.err"; then
    ok "Manim available in container: $(head -n 1 "$TMP_DIR/manim-version.txt")"
  else
    fail "Manim command failed inside $IMAGE"
    errors=$((errors + 1))
  fi

  if docker run --rm "$IMAGE" ffmpeg -version >"$TMP_DIR/ffmpeg-version.txt" 2>"$TMP_DIR/ffmpeg-version.err"; then
    ok "ffmpeg available in container: $(head -n 1 "$TMP_DIR/ffmpeg-version.txt")"
  else
    fail "ffmpeg command failed inside $IMAGE"
    errors=$((errors + 1))
  fi

  if docker run --rm "$IMAGE" bash -c 'command -v pdflatex' >"$TMP_DIR/pdflatex-path.txt" 2>"$TMP_DIR/pdflatex-path.err"; then
    ok "LaTeX available in container: $(cat "$TMP_DIR/pdflatex-path.txt")"
  else
    warn "pdflatex was not found in $IMAGE. MathTex/Tex scenes may need a custom image."
  fi
fi

printf "\n"
if [[ "$errors" -eq 0 ]]; then
  printf "${G}Ready.${N} Render from any Manim project directory with:\n"
  printf "  path/to/manim-video/scripts/manim.sh -ql script.py SceneName\n\n"
else
  printf "${R}%s setup check(s) failed.${N}\n\n" "$errors"
  exit 1
fi
