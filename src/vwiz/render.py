"""Docker Manim rendering: generated scene in, mp4 out.

Runs the pinned `manimcommunity/manim` image (verified v0.21.0, matching the
system prompt's pin) with sandbox caps: memory/CPU/pids limits, dropped
capabilities, no new privileges, no network, host-UID file ownership. The
generated code is untrusted model output reviewed by a human — the container
is the enforcement.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from vwiz.config import Settings

__all__ = ["RenderError", "find_scene", "find_scenes", "render_scene", "render_beats"]


class RenderError(RuntimeError):
    """Anything that kept a scene from becoming an mp4, with the cause inline."""


def _is_scene_base(base: ast.expr) -> bool:
    return (isinstance(base, ast.Name) and base.id == "Scene") or (
        isinstance(base, ast.Attribute) and base.attr == "Scene"
    )


def find_scenes(code: str) -> list[str]:
    """Every Scene subclass in definition order. Raises RenderError when none."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise RenderError(f"scene has a syntax error and was not rendered: {exc}") from exc
    scenes = [
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and any(_is_scene_base(b) for b in node.bases)
    ]
    # Fall back to a full walk for scenes nested in conditionals (rare).
    if not scenes:
        scenes = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and any(_is_scene_base(b) for b in node.bases)
        ]
    if not scenes:
        raise RenderError("no Scene subclass found — nothing to render")
    return scenes


def find_scene(code: str) -> str:
    """The single Scene subclass to render. Raises RenderError otherwise."""
    scenes = find_scenes(code)
    if len(scenes) > 1:
        raise RenderError(f"found {len(scenes)} scenes ({', '.join(scenes)}); one per render")
    return scenes[0]


def render_scene(
    code: str,
    chat_id: str,
    settings: Settings,
    *,
    quality: str = "-ql",
    tag: str = "preview",
) -> Path:
    """Render `code` in Docker and return the final mp4 path. Raises RenderError."""
    scene = find_scene(code)

    render_id = uuid.uuid4().hex[:8]
    workdir = settings.renders_dir / chat_id / f"{tag}_{render_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "scene.py").write_text(code, encoding="utf-8")
    # The daemon rejects relative bind paths, so resolve before mounting.
    host_dir = str(workdir.resolve())

    cname = f"vwiz-{chat_id[:8]}-{render_id}"
    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        cname,
        "-v",
        f"{host_dir}:/manim",
        "-w",
        "/manim",
        "-e",
        "MPLCONFIGDIR=/tmp/matplotlib",
        "-e",
        "XDG_CACHE_HOME=/tmp/.cache",
        f"--memory={settings.render_memory}",
        f"--cpus={settings.render_cpus}",
        "--pids-limit",
        str(settings.render_pids_limit),
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--network",
        "none",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        settings.render_image,
        "manim",
        quality,
        "scene.py",
        scene,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=settings.render_timeout_s
        )
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "rm", "-f", cname], capture_output=True, check=False)
        raise RenderError(f"render timed out after {settings.render_timeout_s}s") from exc
    except OSError as exc:
        raise RenderError(f"could not start docker ({exc})") from exc

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-3000:]
        raise RenderError(f"manim failed (exit {proc.returncode}):\n{tail}")

    # The output dir varies by quality flag (480p15, 720p30, ...), so locate
    # the scene mp4 instead of hardcoding it. Partial-movie chunks carry hash
    # names and never match `{scene}.mp4`.
    found = sorted(workdir.rglob(f"{scene}.mp4"))
    if not found:
        raise RenderError("render succeeded but no mp4 was produced")
    final = settings.renders_dir / chat_id / f"{scene}_{tag}.mp4"
    shutil.copyfile(found[0], final)
    if final.stat().st_size > settings.render_max_output_bytes:
        final.unlink(missing_ok=True)
        raise RenderError("output exceeded the size cap and was discarded")
    return final


def render_beats(
    code: str,
    chat_id: str,
    settings: Settings,
    *,
    quality: str = "-ql",
    tag: str = "preview",
) -> list[tuple[str, Path]]:
    """Render every Scene in `code` with one container run, in file order.

    Returns [(scene_name, mp4_path)] with finals copied next to the chat's
    other renders. Raises RenderError when any scene's mp4 is missing.
    """
    scenes = find_scenes(code)

    render_id = uuid.uuid4().hex[:8]
    workdir = settings.renders_dir / chat_id / f"{tag}_{render_id}"
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "scene.py").write_text(code, encoding="utf-8")
    host_dir = str(workdir.resolve())

    cname = f"vwiz-{chat_id[:8]}-{render_id}"
    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        cname,
        "-v",
        f"{host_dir}:/manim",
        "-w",
        "/manim",
        "-e",
        "MPLCONFIGDIR=/tmp/matplotlib",
        "-e",
        "XDG_CACHE_HOME=/tmp/.cache",
        f"--memory={settings.render_memory}",
        f"--cpus={settings.render_cpus}",
        "--pids-limit",
        str(settings.render_pids_limit),
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--network",
        "none",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        settings.render_image,
        "manim",
        quality,
        "--disable_caching",
        "scene.py",
        *scenes,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=settings.render_timeout_s
        )
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "rm", "-f", cname], capture_output=True, check=False)
        raise RenderError(f"render timed out after {settings.render_timeout_s}s") from exc
    except OSError as exc:
        raise RenderError(f"could not start docker ({exc})") from exc

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-3000:]
        raise RenderError(f"manim failed (exit {proc.returncode}):\n{tail}")

    out: list[tuple[str, Path]] = []
    for scene in scenes:
        found = sorted(workdir.rglob(f"{scene}.mp4"))
        if not found:
            raise RenderError(f"render succeeded but no mp4 for scene {scene!r}")
        final = settings.renders_dir / chat_id / f"{scene}_{tag}_{render_id}.mp4"
        shutil.copyfile(found[0], final)
        if final.stat().st_size > settings.render_max_output_bytes:
            final.unlink(missing_ok=True)
            raise RenderError(f"{scene!r} exceeded the size cap and was discarded")
        out.append((scene, final))
    return out
