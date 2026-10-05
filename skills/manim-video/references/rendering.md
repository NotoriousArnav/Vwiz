# Rendering Reference

## Prerequisites

Use the Docker wrappers from this skill by default:

macOS, Linux, WSL, or Git Bash:

```bash
/path/to/manim-video/scripts/setup.sh
/path/to/manim-video/scripts/manim.sh --version
/path/to/manim-video/scripts/ffmpeg.sh -version
```

Windows PowerShell:

```powershell
& "C:\path\to\manim-video\scripts\setup.ps1"
& "C:\path\to\manim-video\scripts\manim.ps1" --version
& "C:\path\to\manim-video\scripts\ffmpeg.ps1" -version
```

Run wrapper commands from the Manim project directory. They mount the current directory into the container at `/manim`. Set `MANIM_PROJECT_DIR=/path/to/project` in Bash or `$env:MANIM_PROJECT_DIR = "C:\path\to\project"` in PowerShell when the shell cannot run from the project directory.

## CLI Reference

macOS, Linux, WSL, or Git Bash:

```bash
/path/to/manim-video/scripts/manim.sh -ql script.py Scene1 Scene2    # draft (480p 15fps)
/path/to/manim-video/scripts/manim.sh -qm script.py Scene1           # medium (720p 30fps)
/path/to/manim-video/scripts/manim.sh -qh script.py Scene1           # production (1080p 60fps)
/path/to/manim-video/scripts/manim.sh -ql --format=png -s script.py Scene1  # preview still
/path/to/manim-video/scripts/manim.sh -ql --format=gif script.py Scene1     # GIF output
```

Windows PowerShell:

```powershell
& "C:\path\to\manim-video\scripts\manim.ps1" -ql script.py Scene1 Scene2
& "C:\path\to\manim-video\scripts\manim.ps1" -qm script.py Scene1
& "C:\path\to\manim-video\scripts\manim.ps1" -qh script.py Scene1
& "C:\path\to\manim-video\scripts\manim.ps1" -ql --format=png -s script.py Scene1
& "C:\path\to\manim-video\scripts\manim.ps1" -ql --format=gif script.py Scene1
```

The Bash and PowerShell wrappers accept the same Manim/ffmpeg arguments. For Windows, map later `/path/to/manim-video/scripts/*.sh` examples to `C:\path\to\manim-video\scripts\*.ps1`.

## Quality Presets

| Flag | Resolution | FPS | Use case |
|------|-----------|-----|----------|
| `-ql` | 854x480 | 15 | Draft iteration (layout, timing) |
| `-qm` | 1280x720 | 30 | Preview (use for text-heavy scenes) |
| `-qh` | 1920x1080 | 60 | Production |

**Text rendering quality:** `-ql` (480p15) produces noticeably poor text kerning and readability. For scenes with significant text, preview stills at `-qm` to catch issues invisible at 480p. Use `-ql` only for testing layout and animation timing.

## Output Structure

```
media/videos/script/480p15/Scene1_Intro.mp4
media/images/script/Scene1_Intro.png  (from -s flag)
outputs/final.mp4                     (recommended stitched export)
```

The Docker wrappers run containers with `--rm`, so container-internal scratch files disappear after each command. The current project directory is mounted at `/manim`; anything Manim or ffmpeg writes there persists on the local machine.

Generated local artifacts:

- `media/`: Manim-generated videos, images, TeX cache, and partial renders. Safe to delete when you want a clean rerender.
- `outputs/`: recommended home for final/shareable `.mp4`, `.gif`, and narrated exports.
- `review-frames/`: temporary frame-review output; delete after the review loop.
- `concat.txt` and `audio_concat.txt`: temporary ffmpeg manifests; recreate as needed.

Final-output rule:

- Always leave the accepted user-facing video under `outputs/`.
- For stitched videos, write directly to `outputs/final.mp4`.
- For a single-scene video, copy the accepted Manim render from `media/videos/...` to `outputs/<descriptive-name>.mp4` or `outputs/final.mp4`.
- Treat `media/videos/...` as Manim's cache/render tree, not the final path to hand off to the user.
- Do not copy final videos into hidden tool-specific folders such as `.gemini/.../brain`, `.codex/`, or `.agents/` unless the host UI explicitly requires that for artifact embedding. If such a copy is required, mention it as a secondary copy and still provide the project-local `outputs/...` path.

Do not delete source files such as `script.py`, `plan.md`, source images/PDFs, narration audio, or approved final exports unless the user explicitly asks.

Single-scene final export:

```bash
mkdir -p outputs
cp media/videos/script/1080p60/SceneName.mp4 outputs/final.mp4
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force outputs
Copy-Item media\videos\script\1080p60\SceneName.mp4 outputs\final.mp4 -Force
```

## Stitching with ffmpeg

macOS, Linux, WSL, or Git Bash:

```bash
mkdir -p outputs
cat > concat.txt << 'EOF'
file 'media/videos/script/480p15/Scene1_Intro.mp4'
file 'media/videos/script/480p15/Scene2_Core.mp4'
EOF
/path/to/manim-video/scripts/ffmpeg.sh -y -f concat -safe 0 -i concat.txt -c copy outputs/final.mp4
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force outputs
@'
file 'media/videos/script/480p15/Scene1_Intro.mp4'
file 'media/videos/script/480p15/Scene2_Core.mp4'
'@ | Set-Content concat.txt
& "C:\path\to\manim-video\scripts\ffmpeg.ps1" -y -f concat -safe 0 -i concat.txt -c copy outputs/final.mp4
```

## Add Voiceover

```bash
# Mux narration
/path/to/manim-video/scripts/ffmpeg.sh -y -i outputs/final.mp4 -i narration.mp3 -c:v copy -c:a aac -b:a 192k -shortest outputs/final_narrated.mp4

# Concat per-scene audio first
cat > audio_concat.txt << 'EOF'
file 'audio/scene1.mp3'
file 'audio/scene2.mp3'
EOF
/path/to/manim-video/scripts/ffmpeg.sh -y -f concat -safe 0 -i audio_concat.txt -c copy outputs/full_narration.mp3
```

## Add Background Music

```bash
/path/to/manim-video/scripts/ffmpeg.sh -y -i outputs/final.mp4 -i music.mp3 \
  -filter_complex "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=shortest" \
  -c:v copy outputs/final_with_music.mp4
```

## GIF Export

```bash
mkdir -p outputs
/path/to/manim-video/scripts/ffmpeg.sh -y -i scene.mp4 \
  -vf "fps=15,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  outputs/output.gif
```

## Aspect Ratios

```bash
/path/to/manim-video/scripts/manim.sh -ql --resolution 1080,1920 script.py Scene  # 9:16 vertical
/path/to/manim-video/scripts/manim.sh -ql --resolution 1080,1080 script.py Scene  # 1:1 square
```

## Render Workflow

For updater/tracker-heavy scenes, prefer `--disable_caching` from the first draft render: Manim CE's animation cache can silently deadlock while hashing updater closures (render sits at ~0% CPU forever, no error), and disabling the cache either renders normally or surfaces the real exception immediately. See `troubleshooting.md`.

1. Draft render all scenes at `-ql`
2. Preview stills at key moments (`-s`)
3. Fix and re-render only broken scenes
4. Stitch with ffmpeg into `outputs/`
5. Review stitched output with `review-loop.md`
6. Fix only concrete review issues and rerender affected scenes
7. Production render at `-qh`
8. Re-stitch + add audio

After acceptance, clean temporary review/stitch artifacts before final handoff. Ask before deleting `media/`, because it is large but useful for rerenders.

```bash
rm -rf review-frames
rm -f concat.txt audio_concat.txt
# Optional cache reset; rerenders will recreate this:
rm -rf media
```

PowerShell:

```powershell
Remove-Item -Recurse -Force review-frames -ErrorAction SilentlyContinue
Remove-Item -Force concat.txt,audio_concat.txt -ErrorAction SilentlyContinue
# Optional cache reset; rerenders will recreate this:
Remove-Item -Recurse -Force media -ErrorAction SilentlyContinue
```

## manim.cfg — Project Configuration

Create `manim.cfg` in the project directory for per-project defaults:

```ini
[CLI]
quality = low_quality
preview = True
media_dir = ./media

[renderer]
background_color = #0D1117

[tex]
tex_template_file = custom_template.tex
```

This eliminates repetitive CLI flags and `self.camera.background_color` in every scene.

## Sections — Chapter Markers

Mark sections within a scene for organized output:

```python
class LongVideo(Scene):
    def construct(self):
        self.next_section("Introduction")
        # ... intro content ...

        self.next_section("Main Concept")
        # ... main content ...

        self.next_section("Conclusion")
        # ... closing ...
```

Render individual sections: `/path/to/manim-video/scripts/manim.sh --save_sections script.py LongVideo`
This outputs separate video files per section — useful for long videos where you want to re-render only one part.

## manim-voiceover Plugin (Optional Custom Runtime)

The official `manim-voiceover` plugin integrates TTS directly into scene code, auto-syncing animation duration to voiceover length. It is not included in the default Docker runtime for this skill. Use it only after building a custom Docker image that installs the plugin; otherwise use the manual ffmpeg muxing workflow above.

### Installation

Use a custom Docker image instead of installing plugins on the host:

```dockerfile
FROM manim-video-runtime:v0.20.1
USER root
RUN pip3 install --no-cache-dir "manim-voiceover[elevenlabs]"
USER manimuser
```

Then render with:

```bash
MANIM_DOCKER_IMAGE=your-manim-voiceover-image /path/to/manim-video/scripts/manim.sh -qm script.py NarratedScene
```

PowerShell:

```powershell
$env:MANIM_DOCKER_IMAGE = "your-manim-voiceover-image"
& "C:\path\to\manim-video\scripts\manim.ps1" -qm script.py NarratedScene
```

### Usage

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService

class NarratedScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(ElevenLabsService(
            voice_name="Alice",
            model_id="eleven_multilingual_v2"
        ))

        # Voiceover auto-controls scene duration
        circle = Circle()
        with self.voiceover(text="Here is a circle being drawn.") as tracker:
            self.play(Create(circle), run_time=tracker.duration)

        with self.voiceover(text="Now let's transform it into a square.") as tracker:
            self.play(Transform(circle, Square()), run_time=tracker.duration)
```

### Key Features

- `tracker.duration` — total voiceover duration in seconds
- `tracker.time_until_bookmark("mark1")` — sync specific animations to specific words
- Auto-generates subtitle `.srt` files
- Caches audio locally — re-renders don't re-generate TTS
- Works with: ElevenLabs, Azure, Google TTS, pyttsx3 (offline), and custom services

### Bookmarks for Precise Sync

```python
with self.voiceover(text='This is a <bookmark mark="circle"/>circle.') as tracker:
    self.wait_until_bookmark("circle")
    self.play(Create(Circle()), run_time=tracker.time_until_bookmark("circle", limit=1))
```

This is the cleanest approach for narration when the custom runtime includes the plugin. The manual ffmpeg muxing workflow above remains the portable default.
