# Visual Polish and Life

Techniques mined from high-production Manim repos (xiaoxiae, manim-kindergarten sandbox, cigar666, Varniex, nccgroup/cranim, far1din) that separate "flat vector graphics" from footage that feels designed and alive.

Polish is a multiplier, not a foundation. Apply it only after attention, pacing, and hierarchy are solved (`cinematic-directing.md`). If a scene feels dead, the fix is almost never "add glow" — it is clearer focus, better pacing, or a live dependency. Use this file when the scene already teaches well and should now feel premium.

## Depth: Glow, Sheen, Gradients

Manim has no blur, so professionals fake soft light by stacking stroked copies with falling opacity. One glow source per scene — the hero object or the payoff, never the scaffold:

```python
def make_glow(source, color=None, layers=16, max_extra_width=22, opacity=0.35):
    color = color if color is not None else source.get_color()
    return VGroup(*[
        source.copy()
        .set_fill(opacity=0)
        .set_stroke(color, width=max_extra_width * (i + 1) / layers,
                    opacity=opacity * (1 - i / layers) ** 2)
        for i in range(layers)
    ]).set_z_index(source.z_index - 1)

halo = make_glow(result_box, color=ACCENT)
self.play(FadeIn(halo, run_time=0.8))
```

Cheaper depth cues for filled shapes:

```python
card.set_sheen(0.3, UL)                      # one lit corner reads as lighting
region.set_color_by_gradient(PRIMARY, SECONDARY)
region.set_sheen_direction(RIGHT)            # align the gradient to a meaningful direction
dot.set_sheen(0.5)                           # glossy marker dots
```

Align gradients with meaning (the direction of improvement, flow, or the objective), not decoration.

## Z-Ladder Discipline

Dense scenes need one z-index contract, declared once, instead of one-off fixes:

```python
Z_BG, Z_CONTENT, Z_FOCUS, Z_LABEL, Z_OVERLAY = -10, 0, 10, 20, 50
grid.set_z_index(Z_BG)
label.set_z_index(Z_LABEL)
```

Text over busy geometry always gets a backplate or backstroke:

```python
caption.add_background_rectangle(opacity=0.8, buff=0.1)
# or, keeps the background visible through the halo:
caption.set_stroke(BLACK, 5, background=True)
```

## Spotlight Dimmer

For a hard "look only here" beat, a full-frame dimmer above everything except the hero beats per-object opacity fiddling:

```python
dimmer = Rectangle(width=config.frame_width, height=config.frame_height)
dimmer.set_fill(BLACK, opacity=0.7).set_stroke(width=0).set_z_index(Z_OVERLAY - 1)
hero.set_z_index(Z_OVERLAY)
self.play(FadeIn(dimmer, run_time=0.4))
# ... hero beat ...
self.play(FadeOut(dimmer, run_time=0.4))
```

Use the dimmer for one-off dramatic isolation; use per-group opacity gating (`cinematic-directing.md`) when the board must stay readable as context.

## Micro-Motion: Anticipation, Settle, Pulse

The rate-function census across polished repos: after `smooth`/`linear`, professionals lean on `rush_from` / `rush_into` (asymmetric ease for snap and settle) and `there_and_back` (pulses). Meaning-preserving pairs:

```python
# Anticipation: pull back slightly before committing (entrances of key objects)
self.play(FadeIn(machine, shift=0.3 * UP), rate_func=running_start, run_time=0.9)

# Snap in, then settle: fast attack for accents (rush_from starts fast, decelerates)
self.play(marker.animate.move_to(target), rate_func=rush_from, run_time=0.5)

# Landing pulse: confirm a result without adding objects
self.play(result.animate.scale(1.06), rate_func=there_and_back, run_time=0.6)

# Highlight swipe: grow with rush_from, collapse with rush_into
sweep = SurroundingRectangle(term, color=ACCENT, fill_opacity=0.25, stroke_width=0)
self.play(GrowFromEdge(sweep, LEFT), rate_func=rush_from, run_time=0.4)
self.play(sweep.animate.stretch(0.001, dim=0, about_edge=RIGHT),
          rate_func=rush_into, run_time=0.35)
self.remove(sweep)
```

Keep measurement and proof steps on `linear`/`smooth` (`codegen-craft.md`); bouncy easing on quantities makes them feel untrustworthy. Micro-motion belongs on accents, entrances, and landings only.

## Organic Entrances

Left-to-right glyph-by-glyph `Write` reads as typing. For title moments and logo-like reveals, shuffle the reveal order so assembly feels organic:

```python
import random
random.seed(7)  # deterministic renders; unseeded random breaks caching and review reproducibility

glyphs = list(title_text)
random.shuffle(glyphs)
self.play(LaggedStart(
    *[FadeIn(g, shift=0.25 * DOWN, scale=0.6) for g in glyphs],
    lag_ratio=0.05, run_time=1.4,
))
```

For grids and diagrams, a center-out bloom via distance-sorted `LaggedStart` feels designed:

```python
cells = sorted(grid, key=lambda c: np.linalg.norm(c.get_center() - grid.get_center()))
self.play(LaggedStart(*[GrowFromCenter(c) for c in cells], lag_ratio=0.02, run_time=1.2))
```

Reserve these for openings, chapter cards, and payoffs — ordinary content should enter with the plain vocabulary (`Create`, `Write`, `FadeIn`) so the special moments stay special.

## Data as Style

The strongest ML/matrix visuals map data values directly to visual attributes instead of labeling numbers. A matrix becomes a living heatmap:

```python
vals = data / data.max()
heat = VGroup(*[
    Square(0.32)
    .set_fill(PRIMARY, opacity=float(v))
    .set_stroke(WHITE, width=0.5, opacity=max(0.15, float(v)))
    for v in vals.flatten()
]).arrange_in_grid(rows=vals.shape[0], buff=0.06)
```

Animate the data, and the style animates for free: update fill opacity from the new values with one `LaggedStart` of `.animate.set_fill(opacity=...)` calls. This is how convolution sweeps, attention maps, and activation grids read as alive.

## Symbols as Geometry

Operators that live inside a diagram should be drawn geometry, not text, so they scale with the diagram (from cranim's XOR node, built as `Circle` + two `Line`s instead of `MathTex(r"\oplus")`):

```python
def xor_node(radius=0.22, color=WHITE):
    return VGroup(
        Circle(radius=radius, color=color, stroke_width=3),
        Line(UP * radius, DOWN * radius, color=color, stroke_width=3),
        Line(LEFT * radius, RIGHT * radius, color=color, stroke_width=3),
    )
```

Text scales as text; diagram nodes must scale as diagram. The same applies to arrows-with-heads, plus/minus nodes, and gates. Keep `MathTex` for the equation lane.

## Semantic Palette With State Variants

Professional repos assign colors to meanings once, then derive state variants by interpolation instead of inventing new hues (cranim uses the colorblind-safe Wong palette):

```python
# Wong palette: colorblind-safe, distinct on dark and light backgrounds
WONG = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]

def lighten(color, amount=0.3):
    return interpolate_color(ManimColor(color), WHITE, amount)

def darken(color, amount=0.3):
    return interpolate_color(ManimColor(color), BLACK, amount)

C_DATA = WONG[1]
data_pending = lighten(C_DATA, 0.45)   # not yet processed
data_active  = C_DATA                  # current focus
data_done    = darken(C_DATA, 0.35)    # processed, receded
```

One meaning, one hue, three brightness states. This pairs with the state→style contract in `algorithm-choreography.md` and keeps the accent-color budget honest.

## Ambient Life During Holds

Long narration holds go dead when everything freezes. Keep exactly one quiet, low-contrast element alive — never a competitor for attention:

```python
# Gentle drift on a background particle field or history trace
field.add_updater(lambda m, dt: m.rotate(0.02 * dt, about_point=m.get_center()))

# Or a slow counter/clock that belongs to the scene's story
clock.add_updater(lambda m, dt: m.increment_value(dt))
```

Clear these updaters before the next primary beat. Ambient motion is seasoning: sub-pixel-per-frame speeds, opacity under 0.4, zero color changes.

## Polish Budget

Anti-noise rules for everything in this file:

- One glow source per scene, on the hero or payoff only.
- Pulses and wiggles only on semantic landings, never mid-derivation.
- Organic entrances only at openings, chapter cards, and payoffs.
- Ambient motion only during narration holds, one element, low contrast, cleared afterward.
- Sheen/gradients aligned to meaning; if there is no meaningful direction, skip them.
- Every polish effect must survive the question "does this compete with the focal winner?" If yes, cut it.
- Seed `random` for any randomized effect so renders and reviews are reproducible.
