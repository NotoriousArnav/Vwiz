# Codegen Craft Playbook

Use this after `director-packet.md` and `preflight-gates.md` when writing `script.py`. It captures prompt-level craft rules from the production workflow that are too implementation-specific for the director packet.

## Core Rules

- Implement the contract, not generic Manim tricks.
- Prefer one stable scaffold and local changes over full-board resets.
- Prefer one live driver per active beat unless a comparison operator declares coordinated drivers.
- Preserve object and symbol identity with transforms, copies, rails, and source anchors.
- Use motion only when it reveals dependency, attention, or state change.
- Use reviewable source anchors for required shots, objects, symbols, camera moves, and assertions.

## Compute, Don't Fake

The scenes that feel authoritative compute their contents from the real math or algorithm instead of hand-posing plausible values. The animation cannot lie because it runs the truth:

- Run the actual algorithm in plain Python first, record a step trace (`("compare", i, j)`, `("swap", i, j)`, ...), then emit one `play` per trace event (`algorithm-choreography.md`).
- Derive transformed positions, warped grids, and output values from the same function the scene claims to visualize — never eyeball them.
- Let domain objects carry their real data (an array mobject owns its list; a matrix mobject owns its ndarray) so labels, readouts, and downstream steps derive from one source of truth.
- If a number appears on screen, something in the code computed it.

This also makes revision cheap: retiming or restyling never risks breaking correctness, because correctness lives in the data layer, not the choreography.

## Token-Safe Equation Morphs

`TransformMatchingTex` only matches tokens it can see as separate submobjects. If a dense expression is built as one string, matching can silently degrade into pop/fade behavior.

Use one of these isolation strategies:

- Pass semantic tokens as separate `MathTex` arguments.
- Use `substrings_to_isolate=[...]`.
- Use double braces in LaTeX when appropriate.

For changed-but-related tokens, use `key_map` so meaning carries across the morph.

```python
eq_before = MathTex(
    r"\frac{d}{dx}", r"\left(", "x^2", r"\right)", "=", "2", "x",
)
eq_after = MathTex(
    r"\frac{d}{dx}", r"\left(", "x^3", r"\right)", "=", "3", "x^2",
).move_to(eq_before)

self.play(
    TransformMatchingTex(
        eq_before,
        eq_after,
        key_map={
            "x^2": "x^3",
            "2": "3",
            "x": "x^2",
        },
        transform_mismatches=True,
    ),
    run_time=1.2,
    rate_func=smooth,
)
self.wait(0.6)
```

Do not use `key_map` on one giant unisolated `MathTex` string. The keys must correspond to isolated submobjects or the morph will not behave as intended.

## Lagged Reveals

Use `LaggedStart` for semantic cascades: derivation rows, repeated cases, list items, sampled points, or staged labels. Keep `lag_ratio` small enough that the reveal feels like one shaped motion, not a slow one-by-one lecture.

```python
rows = VGroup(
    MathTex(r"u = x^2"),
    MathTex(r"du = 2x\,dx"),
    MathTex(r"\int u\,du = \tfrac12 u^2"),
).arrange(DOWN, aligned_edge=LEFT, buff=0.5)

self.play(
    LaggedStart(*[Write(row) for row in rows], lag_ratio=0.12),
    run_time=1.6,
    rate_func=smooth,
)
self.wait(0.5)
```

Avoid dumping every row with one `Write(VGroup(...))`; the viewer loses the reveal order. Also avoid long `lag_ratio` values that turn every item into a separate mini-scene.

## Attention Baton In Code

When focus moves from A to B, dim A and brighten B in the same `self.play(...)`, then use one attention cue.

```python
self.play(
    inactive.animate.set_opacity(0.15),
    active.animate.set_opacity(1.0),
    run_time=0.4,
)
self.play(FocusOn(active), run_time=0.5)
self.wait(0.4)
```

Choose one cue only: `FocusOn`, `Indicate`, `Circumscribe`, `Flash`, or a short arrow. Stacking cues creates noise.

Do not `Indicate`, `Wiggle`, or `Circumscribe` an updater-driven object directly. Use a static proxy, a temporary ring, a lane highlight, or the object center.

## Contract-Driven Pacing

When the director packet has `pacing_plan[*].hold_seconds`, use the literal budget where possible.

```python
self.play(TransformMatchingTex(eq_before, eq_after), run_time=1.2)
self.wait(0.8)  # from pacing_plan for this beat
```

Use an anticipation hold before the key reveal when the packet marks a pre-aha, anchor, threshold, or payoff beat:

```python
self.wait(0.6)  # question forms before answer
self.play(reveal_animation, run_time=1.4)
self.wait(1.0)  # answer lands
```

Avoid three or more long waits inside one beat unless the packet explicitly budgets them. More waiting is not automatically better; it must serve the beat.

## Rate Function Semantics

Choose `rate_func` for meaning, not variety.

- Use `linear` for measurement, sweeps, simulations, clocks, scans, and parameter changes where constant speed matters.
- Use `smooth` for polished entrances, exits, morphs, and camera settle moves.
- Use `there_and_back` for probes that briefly ask "look here".
- Use `there_and_back_with_pause` for emphasis that should linger at the extreme.
- Use `squish_rate_func(...)` only when layered choreography must share one conceptual beat.

Do not use bouncy or dramatic easing for measurement or proof steps. It makes quantities feel untrustworthy.

## Collections And Groups

If an element name is plural or the description says multiple/several/labels/arcs/lines/markers/points/set, implement it as a group from the start.

```python
vertex_labels = VGroup(
    MathTex("a").next_to(side_a, UP, buff=0.15),
    MathTex("b").next_to(side_b, RIGHT, buff=0.15),
    MathTex("c").next_to(side_c, LEFT, buff=0.15),
)
```

Use `VGroup` for VMobjects such as shapes, `MathTex`, `Tex`, and `Text`. Use `Group` when mixing in `ImageMobject`, trackers, or other non-VMobjects.

## Live Dependencies

Use one driver when several objects should stay synchronized.

```python
x = ValueTracker(1.0)
dot = always_redraw(lambda: Dot(axes.i2gp(x.get_value(), graph), color=ACCENT))
v_line = always_redraw(lambda: axes.get_vertical_line(dot.get_center()))
readout = DecimalNumber(0, num_decimal_places=2)
readout.add_updater(lambda m: m.set_value(x.get_value()))

self.add(dot, v_line, readout)
self.play(x.animate.set_value(5.0), run_time=3.0, rate_func=linear)
```

Use `add_updater` for cheap position/value changes. Use `always_redraw` when the shape itself must be rebuilt, such as an area, brace, secant group, or changing curve.

Updaters constrain entrances too, not just exits: never `Transform`/`ReplacementTransform`/`FadeIn` INTO a mobject whose updater rebuilds it each frame — attach the updater after the entrance play completes (`troubleshooting.md`). Combined with freeze-before-formalizing, the rule is symmetric: updaters attach after a mobject's entrance and detach before its formalization or exit.

## Stable Numeric Inspectors

Use persistent numeric objects in fixed slots. Do not rebuild an entire label or panel every frame when only the number changes.

```python
label = MathTex("x=")
value = DecimalNumber(0, num_decimal_places=2)
inspector = VGroup(label, value).arrange(RIGHT, buff=0.12).to_corner(UR)
value.add_updater(lambda m: m.set_value(x.get_value()))
self.add(inspector)
```

Declare `num_decimal_places`, units, and exact/approximate policy before animation. If values should be integers, use `Integer` or `DecimalNumber(..., num_decimal_places=0)`. If a formula string genuinely changes structure, rebuild that formula with `always_redraw`; otherwise keep text stable and update only the numeric mobject.

## Freeze Before Formalizing

Before converting live geometry into notation, copy it and clear updaters so the formula beat is stable.

```python
static_piece = live_piece.copy()
static_piece.clear_updaters()
self.play(TransformFromCopy(static_piece, formula_term), run_time=0.8)
```

Use this for secants becoming derivatives, areas becoming terms, probes becoming symbols, vectors becoming matrix columns, and route/state objects becoming invariants.

Clear or suspend updaters before:

- camera moves that would fight a frame-relative object
- freezing dynamic geometry into notation
- scene end
- direct animations on an updater-controlled object

## Protected Lanes

For static 2D scenes, reserve lanes with layout discipline:

```python
world_lane = VGroup(graph, probe).to_edge(LEFT, buff=0.8)
inspector_lane = VGroup(equation, readout).arrange(DOWN, aligned_edge=LEFT).to_edge(RIGHT, buff=0.8)
self.add(world_lane, inspector_lane)
```

For camera-moving scenes with fixed overlays, `add_fixed_in_frame_mobjects(...)` requires `ThreeDScene`. It is not available on plain `Scene` or `MovingCameraScene`.

```python
class Scene1(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=0, theta=-PI / 2)
        inspector_lane = VGroup(equation, readout).to_edge(RIGHT, buff=0.6)
        self.add_fixed_in_frame_mobjects(inspector_lane)
```

`mobject.fix_in_frame()` is OpenGL-specific and should not be used for the default Cairo renderer.

## Contract Spatial Encoding

Translate layout fields into code deliberately:

- Build local groups first with `VGroup(...).arrange(...)` or `arrange_in_grid(...)`, then place the group in its declared zone.
- Use packet anchors and rails with `next_to`, `to_edge`, `align_to`, `move_to(anchor)`, and named helper points. Avoid ad hoc coordinates unless the packet declares that coordinate as a stable anchor.
- Convert spacing words into explicit `buff` values: tight `0.18-0.25`, comfortable `0.35-0.55`, wide `0.75+`.
- Apply a single fit pass to the semantic group, not separate random scaling to each child.
- After fitting, rebuild connectors, braces, arrows, and labels from final endpoints so the topology matches the visible layout.

If a requested position would violate a zone, safe margin, or minimum font/gap rule, fix the packet or split the beat. Do not silently place the object somewhere else.

## Frame And Zone Guards

For dense scenes, construct semantic groups, fit them to their declared zone, then clamp the final group inside the frame. Do this before adding complicated animation timing. Keep `buff` and halo spacing meaningful after scaling; shrinking all gaps with the objects makes elements visually merge. For connector-heavy diagrams, place nodes/cards first and build connectors from final positions after the layout lands.

```python
def fit_to_box(mob, max_width, max_height):
    if mob.width > max_width:
        mob.set_width(max_width)
    if mob.height > max_height:
        mob.set_height(max_height)
    return mob


def keep_inside_frame(mob, margin=0.35):
    half_w = config.frame_width / 2 - margin
    half_h = config.frame_height / 2 - margin
    if mob.width > 2 * half_w:
        mob.set_width(2 * half_w)
    if mob.height > 2 * half_h:
        mob.set_height(2 * half_h)

    min_x = -half_w + mob.width / 2
    max_x = half_w - mob.width / 2
    min_y = -half_h + mob.height / 2
    max_y = half_h - mob.height / 2
    x = min(max(mob.get_x(), min_x), max_x)
    y = min(max(mob.get_y(), min_y), max_y)
    mob.move_to([x, y, 0])
    return mob


def assert_frame_safe(mobs, margin=0.25):
    left = -config.frame_width / 2 + margin
    right = config.frame_width / 2 - margin
    bottom = -config.frame_height / 2 + margin
    top = config.frame_height / 2 - margin
    for mob in mobs:
        if (
            mob.get_left()[0] < left
            or mob.get_right()[0] > right
            or mob.get_bottom()[1] < bottom
            or mob.get_top()[1] > top
        ):
            raise ValueError(f"{mob} is outside the safe frame")


def assert_no_overlap(mobs, min_gap=0.08):
    items = list(mobs)
    for index, mob in enumerate(items):
        for other in items[index + 1:]:
            separated = (
                mob.get_right()[0] + min_gap <= other.get_left()[0]
                or other.get_right()[0] + min_gap <= mob.get_left()[0]
                or mob.get_top()[1] + min_gap <= other.get_bottom()[1]
                or other.get_top()[1] + min_gap <= mob.get_bottom()[1]
            )
            if not separated:
                raise ValueError(f"{mob} overlaps or visually merges with {other}")


entity_grid = VGroup(*entity_cards).arrange_in_grid(rows=2, buff=(0.45, 0.35))
fit_to_box(entity_grid, max_width=12.0, max_height=4.8)
entity_grid.move_to(DOWN * 0.25)
keep_inside_frame(entity_grid)
assert_frame_safe(entity_cards)
assert_no_overlap(entity_cards, min_gap=0.12)

connectors = VGroup(
    *[Arrow(a.get_right(), b.get_left(), buff=0.12) for a, b in dependency_pairs]
)
world = VGroup(entity_grid, connectors)
```

If the fitted group becomes unreadable, do not accept the render. Split the beat, reduce simultaneous objects, move details into an inspector, or park old context in a memory rail. A dense layout that only passes because everything became tiny is a failed layout.

## Source Anchors In Code

Use anchors sparingly but consistently. They are not explanatory comments; they are review evidence.

```python
# manim-skill:shot shot_id=shot_slope beat_id=beat_3
self.next_section("shot_slope")

# manim-skill:element object_id=obj_tangent_group
tangent_group = always_redraw(...)

# manim-skill:symbol symbol_id=sym_dx
dx_label = MathTex(r"dx")

# manim-skill:camera beat_id=beat_3 target_object_id=obj_tangent_group purpose="inspect local linearity"

# manim-skill:assert assertion="camera_contains(obj_tangent_group)"
```

If a downstream verifier expects `# t2a:` markers, use the same fields with that prefix.

## Common Rejections

Reject or repair these patterns:

- title cards or intro/outro text that the packet did not request
- formula appears before the visual dependency is clear
- `Write(next_equation)` for a derivation where identity should carry
- independent trackers for objects that should move together
- labels parked away from the object they describe
- numeric readouts rebuilt as fresh `Text`/`MathTex` every frame when `DecimalNumber` would be stable
- dense derivation rows with drifting equals columns or unaligned baselines
- dense diagrams placed with ad hoc coordinates and no frame/zone containment check
- dense layouts that pass by shrinking gaps until separate objects visually merge
- trails faked with static arcs instead of `TracedPath` or updater-bound history
- camera movement with no target, reason, duration, and restore path
- protected overlays placed in the same lane as moving geometry
- source anchors that name ids but do not correspond to real variables or visible objects
