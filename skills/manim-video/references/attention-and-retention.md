# Attention and Retention Grammar

Universal rules for holding viewer attention from first frame to last. These are not style preferences — they are quantified norms mined from the actual 3Blue1Brown video source corpus (2023-2026 files, thousands of `play()` calls measured) plus the strongest community repos. Apply them to every video; use `cinematic-directing.md` for the beat-level directing doctrine and this file for the second-by-second rhythm that keeps people watching.

The core finding from the corpus: **top-tier videos are never static and never chaotic.** Something changes every 1-3 seconds, but only one thing owns attention at a time, and every hold is either short (a read beat) or earned (a finished image worth contemplating).

## The Retention Contract

Every scene must satisfy these constraints. They are checkable in code and in rendered output.

1. **Motion cadence: one idea per ~1-3 seconds.** The workhorse unit is `self.play(...)` of 1-2s followed by `self.wait()` of ~1s. One `play` = one conceptual step. Measured distribution: `run_time=2` is the most common by far, then 3, then 1; camera and ambient sweeps stretch to 5-15s.
2. **No dead frame.** A fully static span over ~4s needs a reason (declared read hold, narration doing the work). During longer narration holds, keep exactly one quiet element alive — a self-advancing tracker, trace, or counter (see Ambient Life below). Verify mechanically with the freezedetect audit in `review-loop.md`.
3. **No metronome.** If every beat has identical `run_time` and identical `wait`, the video feels machine-generated. Vary within the contract: setup measured, build quicker, pre-reveal breath, payoff climax, recap hold.
4. **One attention act every 2-4 plays.** Measured density in flagship scenes: roughly one explicit attention direction (dim, highlight rect, flash) per 2-4 `play()` calls. Less than that and the viewer wanders; more and the emphasis stops being trustworthy.
5. **One focal winner at full brightness.** Everything else dims to 0.2-0.35 opacity (0.5 for "half-receded" context). This is measured practice, not taste: the spotlight beat combines `Create(highlight_rect)` + dim-everything-else in one `play`.
6. **A breath before every reveal.** The single most consistent pre-payoff pattern: build the highlight, `self.wait()` (~1s), then fire the transform. The pause is the "hold your breath" beat that makes the reveal land.
7. **One long sweep per scene.** Reserve one 5-15s continuous motion (`rate_func=linear` tracker sweep, or a slow camera drift) as the scene's "watch it play out" moment. More than one and neither feels special.
8. **Demote, don't delete.** Finished results scale to 0.25-0.75, park in a corner/edge, and fade to 0.5-0.75 opacity — folded into the same `play` that starts the next idea. The viewer keeps a visible trail of what has been established.
9. **Long holds only on finished images.** 3-10s contemplation holds are reserved for a completed, self-explanatory visual — never for a half-built board.

## The 3-Second Loop

Inside every beat, the viewer cycles: **change → read → anticipate**. Write code in that shape:

```python
self.play(TransformMatchingTex(eq1, eq2), run_time=1.5)   # change: one semantic step
self.wait(0.8)                                            # read: absorb the landing
self.play(Circumscribe(eq2[3], color=ACCENT), run_time=0.7)  # anticipate: point at what matters next
self.wait(0.5)
```

One sentence of narration ≈ one loop. If a beat needs two sentences, it is two beats. If a `play` call changes two unrelated things, split it — unless the second thing is the camera or a demotion (see below), which ride along for free.

## Where the Eye Goes: The Attention Thread

The eye follows, in priority order: **motion > brightness > contrast > size > position**. Every beat should exploit exactly one of these, and consecutive beats should form an unbroken thread — the viewer's gaze must never have to jump to an unannounced location.

- **Enter new content from the current gaze point.** `TransformFromCopy(current_focus, new_object)` with `path_arc=45 * DEGREES` flies a copy along a visible curve, so the eye travels with it. This is the corpus's dominant equation-building move (530+ uses of `TransformFromCopy` in two years): the source stays put, a duplicate travels.
- **Slide one highlight, don't spawn many.** Move a single `SurroundingRectangle` from term to term instead of creating a new one each time. The slide itself asserts "this corresponds to that":

```python
rect = SurroundingRectangle(eq_a[2], color=ACCENT, buff=0.1)
self.play(Create(rect))
self.wait(0.6)
self.play(rect.animate.become(
    SurroundingRectangle(eq_b[4], color=ACCENT, buff=0.1)))  # rect walks to the next term
```

- **Hand off focus explicitly.** When attention moves from A to B, dim A and brighten B in the same `play`. A moving spotlight over columns/rows/steps:

```python
self.play(
    items[last].animate.set_opacity(0.35),
    items[cur].animate.set_opacity(1.0),
    col_rect.animate.move_to(items[cur]),
    run_time=0.8,
)
```

- **Flashes are punctuation, not narration.** `Flash`, `Circumscribe`, `Indicate` mark arrival at something important — one per landing, and only a few per scene. Rectangles and opacity carry the ongoing pointing.

## Camera Focus Grammar

Mined rule: **never move the camera in a dead beat.** Camera moves are always fused with the content change that motivates them, in the same `play()`. A camera move with nothing else happening reads as drift.

| Trigger | Camera action | Duration |
|---------|--------------|----------|
| About to do a specific computation / inspect one element | Zoom in (frame width down) onto the semantic group | 1-2s, fused with the content appearing |
| A larger structure is being assembled, or board is being cleared | Zoom out / recenter while the new pieces or the cleanup animate | 1-2s |
| An extra dimension of meaning appears (2D → 3D) | Tilt into 3D exactly at that moment; flatten back when the point lands | 3s each way |
| Narration explains while a finished visual sits | Slow breathing drift with `rate_func=there_and_back` — camera leaves and returns | 8-15s |
| Idea complete, context matters again | `Restore(frame)` to the saved wide shot | 1-1.5s |

```python
class Example(MovingCameraScene):
    def construct(self):
        frame = self.camera.frame
        frame.save_state()
        # zoom fused with the content it motivates
        self.play(
            frame.animate.set(width=focus.width * 1.6).move_to(focus),
            FadeIn(detail_labels, lag_ratio=0.1),
            run_time=1.5,
        )
        # ... local computation beats ...
        self.play(Restore(frame), FadeOut(detail_labels), run_time=1.2)
```

Static camera remains the default (`preflight-gates.md`); this grammar governs the moves you do earn.

## The Overlap Dial

Sequential-only animation feels like slides; everything-at-once feels like noise. The corpus overlaps constantly — `LaggedStart` is the single most used composition tool (893 uses in two years). The `lag_ratio` dial, from measured frequency:

| lag_ratio | Feel | Use for |
|-----------|------|---------|
| 0.01-0.05 | shimmer, one shaped mass | crowds of tiny objects: dots, grid cells, characters |
| 0.1 | default stagger | rows, labels, list items — the go-to value (499 uses) |
| 0.25-0.5 | distinct overlapping beats | "arrow grows, then the term morphs" two-step reveals |
| 1.0 | strictly sequential | rare; only when order itself is the lesson |

```python
self.play(LaggedStart(GrowArrow(arrow), TransformMatchingTex(a.copy(), b),
                      lag_ratio=0.25), run_time=1.5)
```

For heterogeneous sub-animations that should crest at different moments inside one shot, use `squish_rate_func` to window each into a shared `run_time`:

```python
self.play(
    frame.animate.move_to(target),                                     # full 3s
    AnimationGroup(GrowArrow(arr), rate_func=squish_rate_func(smooth, 0.33, 0.66)),
    AnimationGroup(FadeIn(label),  rate_func=squish_rate_func(smooth, 0.5, 1.0)),
    run_time=3,
)
```

The frame never gets a "now everything starts / now everything stops" pulse.

## Hook Architecture: The First 15 Seconds

The corpus never opens with a definition or a bare title card. It opens with **a concrete instance of the thing, already doing its job**, then points at the exact term the video will worry about.

Hook patterns that work:

- **Machine running live**: show the system producing output immediately (a generator autocompleting text, a sort already sorting, a simulation already evolving), with the mechanism as a labeled box. Theory comes after the viewer has watched it work.
- **Equation + pointed worry**: put the governing equation on screen and immediately `Create(rect)` around the one term that motivates everything, slide the rect to narrow onto the single symbol, hold. The question is posed by a highlight, not a paragraph.
- **Concrete artifact first**: one real example (a single character in memory, one image pixel grid, one specific triangle) from which the abstraction is *derived on screen* via `TransformFromCopy`.
- **Failure/tension first**: the obvious approach visibly breaking, before naming the topic.

Anti-hooks: a title card that fades in and out (dead 4 seconds), a definition read aloud, an agenda list, "in this video we will…".

Titles still exist — as a small overlay entering *while* the hook visual plays, or as a chapter card *between* sections, never as the opening beat.

## Mid-Video Retention

- **Open loops**: pose a question the current beat cannot yet answer ("why the minus sign? hold that thought") and park a small visual reminder on the memory rail. Close every loop you open — payoff scheduling is what makes minute 4 feel necessary.
- **Chapter landings every 30-60s**: a mini-payoff (metric lands, sub-result sealed, comparison resolved) with a slightly longer hold. These are the natural re-engagement points.
- **Accelerate learned patterns.** The first instance of a repeated structure gets the full slow treatment; later instances run 2-3x faster (`quick` variants). Repetition at constant speed is the top mid-video killer.
- **Escalate representation, not decoration.** When energy sags, climb the representation ladder (new view of the same object: picture → readout → symbol → matrix) instead of adding effects.

## Ambient Life During Holds

A held frame should never be fully static while narration runs. The corpus keeps holds alive with a self-advancing clock that costs no `play` call:

```python
t_tracker = ValueTracker(0)
t_tracker.add_updater(lambda m, dt: m.increment_value(dt))  # advances every frame on its own
self.add(t_tracker)

mass = always_redraw(lambda: Dot(oscillator_pos(t_tracker.get_value()), color=PRIMARY))
self.add(mass)
# narration hold — the mass keeps oscillating with zero explicit animation
self.wait(6)
```

One ambient element, low contrast, cleared before the next primary beat. See `visual-polish.md` for the budget rules.

## Payoff and Ending

- Assemble the corner-parked results: the demoted equations/sub-results from the memory rail visibly feed the final frame, so the ending proves the journey.
- Literalize the thesis as one physical action when possible (the function flying *into* the transform machine, the pieces snapping into the identity) — the memorable closing image is an action, not a caption.
- Seal the hero result (`SurroundingRectangle` + accent), then the longest hold of the video.
- Never end on a fadeout of an unfinished board.

## Retention Audit

Run after rendering, before acceptance:

1. **Dead air**: freezedetect scan from `review-loop.md`; every static span > 4s must map to a justified hold.
2. **Metronome**: scan `script.py` for 3+ consecutive beats with identical `run_time` and `wait` values; vary them or justify.
3. **Attention density**: per scene, count attention acts (dims, rect moves, flashes) vs `play` calls; flag scenes below ~1 in 4.
4. **Hook check**: does anything conceptually load-bearing happen in the first 10 seconds of the final video? A logo/title alone fails.
5. **Thread check**: step through beats asking "does the viewer know where to look, and how did their eye get there?" Any teleport of attention (new content appearing far from current gaze with no motion bridge, no highlight) is a defect.
6. **Payoff check**: the final frame contains the promised objects/relationship, sealed and held longest.

These map onto the visual-audit and review gates in `preflight-gates.md` and `review-loop.md`; this file supplies the thresholds.
