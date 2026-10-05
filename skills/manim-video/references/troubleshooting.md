# Troubleshooting

## LaTeX Errors

**Missing raw string** (the #1 error):
```python
# WRONG: MathTex("\\frac{1}{2}")  -- \\f is form-feed
# RIGHT: MathTex(r"\frac{1}{2}")
```

**Unbalanced braces**: `MathTex(r"\frac{1}{2")` -- missing closing brace.

**LaTeX not found in Docker image**: run `scripts/setup.sh` from macOS/Linux/WSL/Git Bash or `scripts\setup.ps1` from Windows PowerShell in the skill folder. If `pdflatex` is missing or a package is unavailable, extend the skill Dockerfile from `manimcommunity/manim:v0.20.1` and rebuild, or set `MANIM_DOCKER_IMAGE` to a custom image.

**Missing package**: Add to preamble:
```python
tex_template = TexTemplate()
tex_template.add_to_preamble(r"\usepackage{mathrsfs}")
MathTex(r"\mathscr{L}", tex_template=tex_template)
```

The default Manim Docker image ships with a minimal TeX Live install. Extra packages such as CJK/ctex support may need to be installed in a custom image.

## VGroup TypeError

**Error:** `TypeError: Only values of type VMobject can be added as submobjects of VGroup`

**Cause:** `VGroup` accepts vector mobjects only. `Text`, `Tex`, `MathTex`, shapes, lines, and arrows are vector mobjects and can be grouped with `VGroup`. `ImageMobject` and some custom/non-vector mobjects need `Group`.

```python
# WRONG: ImageMobject is not a VMobject
group = VGroup(circle, ImageMobject("screenshot.png"))

# RIGHT: use Group for raster or mixed non-vector collections
group = Group(circle, ImageMobject("screenshot.png"))

# RIGHT: VGroup is fine for vector mobjects, including Text and MathTex
label_group = VGroup(circle, Text("Label"), MathTex(r"x"))
```

**Rule:** use `VGroup` for vector-only layout and styling. Use `Group` when the collection may contain raster images or other non-VMobjects.

**FadeOut everything:** Always use `Group(*self.mobjects)`, not `VGroup(*self.mobjects)`:
```python
self.play(FadeOut(Group(*self.mobjects)))  # safe for mixed types
```

## Mixed Group save_state() / restore() Caution

When a collection mixes vector and raster/non-vector mobjects, broad group-level transforms and save/restore flows can be harder to reason about.

Prefer a `VGroup` when everything is vector. For mixed groups, save/restore individual important objects or use local fade/shift transforms.

```python
# Good for vector-only groups
panel = VGroup(rectangle, Text("label"))
panel.save_state()
self.play(panel.animate.shift(RIGHT))
self.play(Restore(panel))

# For mixed groups, keep state changes local and explicit
img = ImageMobject("screenshot.png")
caption = Text("caption")
self.play(FadeIn(Group(img, caption), shift=UP * 0.3))
```

## letter_spacing Is Not a Valid Parameter

**Error:** `TypeError: Mobject.__init__() got an unexpected keyword argument 'letter_spacing'`

**Cause:** `Text()` does not accept `letter_spacing`. Manim uses Pango for text rendering and does not expose kerning controls on `Text()`.

```python
# WRONG
Text("HERMES", letter_spacing=6)

# RIGHT: use MarkupText with Pango attributes for spacing control
MarkupText('<span letter_spacing="6000">HERMES</span>', font_size=18)
# Note: Pango letter_spacing is in 1/1024 of a point
```

## Animation Errors

**Invisible animation** -- mobject never added:
```python
# WRONG: circle = Circle(); self.play(circle.animate.set_color(RED))
# RIGHT: self.play(Create(circle)); self.play(circle.animate.set_color(RED))
```

**Transform confusion** -- after Transform(A, B), A is on screen, B is not. Use ReplacementTransform if you want B.

**Duplicate animation** -- same mobject twice in one play():
```python
# WRONG: self.play(c.animate.shift(RIGHT), c.animate.set_color(RED))
# RIGHT: self.play(c.animate.shift(RIGHT).set_color(RED))
```

**Updater fights animation**:
```python
mob.suspend_updating()
self.play(mob.animate.shift(RIGHT))
mob.resume_updating()
```

**Render hangs at ~0% CPU, no error** (updater-heavy scenes): Manim CE's animation-caching layer can deadlock while hashing scenes with many updater/tracker closures — the process sits idle forever with a live `multiprocessing.resource_tracker` child and no traceback. Rerun with `--disable_caching`: it either completes normally or immediately surfaces the real exception that the cache path was masking. Diagnose with `docker stats` (0% CPU + stale partial files = stalled, not slow).

**`ValueError: zip() argument ... is shorter` mid-Transform**: you played `Transform`/`ReplacementTransform`/`FadeIn` INTO a mobject whose updater rebuilds it every frame (e.g. a `DecimalNumber` with a `set_value` updater). The updater churns the target's submobjects while the transform holds interpolation pairs. Fix: attach the updater AFTER the entrance animation completes, or `suspend_updating()` during it:

```python
dist.set_value(new_val)                      # static value for the entrance
self.play(ReplacementTransform(inf_label, dist))
dist.add_updater(lambda m: m.set_value(tracker.get_value()))  # attach after
```

**`wait() has a duration of 0` error**: Manim CE rejects `self.wait(0)`. Guard variable holds: `if hold > 0: self.wait(hold)`.

**Render-time Manim CE traps**:

- Use `TransformMatchingTex(key_map=...)` only when the mapped terms are isolated as separate `MathTex` arguments, double-braced LaTeX parts, or `substrings_to_isolate` entries. If tokens are not isolated or structures are incompatible, use `FadeTransform`, `ReplacementTransform`, `TransformMatchingShapes`, or a manual grouped transform.
- Do not use unsupported `TransformMatchingTex(matched_keys=...)`; Manim CE exposes `key_map`, `transform_mismatches`, and `fade_transform_mismatches`.
- Do not use `GrowArrow` on `CurvedArrow`; use `Create`.
- Do not use `GlowDot`, `RadialGradient`, or `LinearGradient`; these are not reliable in Manim CE.
- Do not pass raw hex strings to `interpolate_color`; wrap with `ManimColor(...)`.
- Do not animate the same mobject twice in one `self.play(...)`; chain `.animate` calls instead.
- Clear or suspend continuous updaters before camera moves, formalization freezes, and scene end when they would fight later animations.

## Rendering Issues

**Blurry output**: Using -ql (480p). Switch to -qm/-qh for final.

**Slow render**: Use -ql during development. Reduce Surface resolution. Shorter self.wait().

**Stale output**: `/path/to/manim-video/scripts/manim.sh -ql --disable_caching script.py Scene`

**ffmpeg concat fails**: All clips must match resolution/FPS/codec. Use `/path/to/manim-video/scripts/ffmpeg.sh` unless the user explicitly wants host ffmpeg.

**Docker image missing on Windows**: run `.\scripts\setup.ps1` from the skill folder. Then render from a project directory with `& "C:\path\to\manim-video\scripts\manim.ps1" -ql script.py Scene`.

**Project files not visible inside Docker**: run the wrapper from the project directory, or set `MANIM_PROJECT_DIR=/path/to/project` in Bash / `$env:MANIM_PROJECT_DIR = "C:\path\to\project"` in PowerShell.

## Common Mistakes

**Text clips at edge**: `buff >= 0.5` for `.to_edge()`

**Overlapping text**: Use `ReplacementTransform(old, new)`, not `Write(new)` on top.

**Too crowded**: Max 5-6 elements visible. Split into scenes or use opacity layering.

**No breathing room**: `self.wait(0.6)` to `self.wait(1.0)` after routine steps, `self.wait(1.5)` to `self.wait(2.0)` after key reveals and landings. Missing holds and uniform holds are both failures — see `attention-and-retention.md`.

**Missing background color**: Set `self.camera.background_color = BG` in every scene.

## Debugging Strategy

1. Render a still: `/path/to/manim-video/scripts/manim.sh -ql -s script.py Scene` or `scripts\manim.ps1 -ql -s script.py Scene` -- instant layout check
2. Isolate the broken scene -- render only that one
3. Replace `self.play()` with `self.add()` to see final state instantly
4. Print positions: `print(mob.get_center())`
5. Clear cache: delete `media/` directory
