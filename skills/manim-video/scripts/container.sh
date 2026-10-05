#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
  echo "Usage: $0 <command> [args...]" >&2
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Run scripts/setup.sh after installing Docker." >&2
  exit 127
fi

IMAGE="${MANIM_DOCKER_IMAGE:-manim-video-runtime:v0.20.1}"
WORKDIR="${MANIM_PROJECT_DIR:-$PWD}"

if [[ "${MANIM_DOCKER_USE_HOST_UID:-auto}" != "0" && "$(uname -s)" == "Linux" ]]; then
  exec docker run --rm \
    -v "$WORKDIR:/manim" \
    -w /manim \
    -e MPLCONFIGDIR=/tmp/matplotlib \
    -e XDG_CACHE_HOME=/tmp/.cache \
    --user "$(id -u):$(id -g)" \
    "$IMAGE" \
    "$@"
fi

exec docker run --rm \
  -v "$WORKDIR:/manim" \
  -w /manim \
  -e MPLCONFIGDIR=/tmp/matplotlib \
  -e XDG_CACHE_HOME=/tmp/.cache \
  "$IMAGE" \
  "$@"
