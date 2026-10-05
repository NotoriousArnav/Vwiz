# Cinematic Directing

Use this when the user asks for output that feels premium, dynamic, alive, research-teaser-like, or world-class. The goal is not more effects. The goal is stronger direction: one clear idea at a time, meaningful motion, readable hierarchy, and a memorable landing.

This file is the beat-level doctrine. For the second-by-second rhythm — change cadence, hook architecture, overlap dial, camera fusion, and the retention audit — pair it with `attention-and-retention.md`. For algorithm and data-structure scenes, add `algorithm-choreography.md`. For the premium finish layer, end with `visual-polish.md`.

## Core Principle

Plan semantic beats before choosing Manim calls.

Do not start with "fade this, move that, write this." Start with:

- what the viewer should notice
- what visual mechanism is being revealed
- what object wins attention now
- what old context must remain in memory
- what proof, metric, comparison, or result earns the next beat

The Manim code should implement the directing choice. It should not become a pile of unrelated animations.

## Minimum Premium Stack

Every ambitious scene should have these pieces:

1. **Stable scaffold**: axes, board, pipeline, derivation stack, comparison stage, or mechanism map that does not constantly relayout.
2. **One active driver**: a `ValueTracker`, simulation clock, routed packet, transform chain, or beat focus that controls the current motion.
3. **Live dependency layer**: labels, readouts, connectors, braces, trails, or helper geometry that follow the active driver.
4. **Protected explanation layer**: title, caption, inspector, metric panel, or formula lane that stays readable during camera movement.
5. **Attention gate**: dim, spotlight, circumscribe, underline, flash, or isolate the current focal object.
6. **Continuity transform**: carry identity with `TransformMatchingTex`, `TransformFromCopy`, stable side-by-side comparison, or local replacement.
7. **Read hold**: pause after each semantic landing.

If a scene feels flat, fix this stack before adding decorative effects.

After this stack is clear, choose the closest implementation pattern from `source-backed-patterns.md`. Use that file to decide whether the scene should be a live derivative, simulation dashboard, pipeline flow, dense derivation board, before/after evidence scene, proof by rearrangement, function machine, or 3D reveal.

## Beat Grammar

Write each beat as a semantic directing unit:

```markdown
### Beat N: [name] (~Ns)
- Focus: [one object/group]
- Viewer should notice: [one sentence]
- Mechanism: [what visibly changes]
- Camera: establish / inspect / edge-follow / restore / hero
- Memory: dim / park / rail / preserve / remove
- Landing: [caption, proof gate, metric, or hero result]
```

Good beat roles:

- **stop-scroll**: show tension or contradiction immediately
- **expose-bottleneck**: reveal why the obvious path fails
- **reveal-mechanism**: show the moving mechanism, not just its label
- **prove-faithfulness**: accept/reject with a clear gate
- **compare-before-after**: keep both states in memory while shifting focus
- **show-evidence**: land a metric, counter, or inspected result
- **make-result-shareable**: final artifact, sealed and held

## Layout Doctrine

Use reserved zones whenever a scene gets dense:

- **title lane**: what video/scene is about
- **memory rail**: previous conclusions, compressed and dimmed
- **world zone**: the mechanism, graph, pipeline, board, or object being animated
- **inspector lane**: live formula, metric, status, or current test
- **caption lane**: one short sentence that names the beat

Keep world objects out of title/caption/inspector space. For static 2D scenes, protected overlays usually only need stable `to_edge` / `to_corner` placement and adequate `buff`. If the camera must move and overlays must stay fixed to the frame, use `ThreeDScene` and `add_fixed_in_frame_mobjects(...)`; that method is not available on plain `Scene` or `MovingCameraScene`. Do not use `mobject.fix_in_frame()` with the default Cairo renderer.

## Camera Doctrine

Camera motion is rhetoric, not decoration.

- Establish the whole map before inspecting detail.
- Zoom only when semantic density rises.
- Frame semantic groups, not arbitrary coordinates.
- Restore when context matters again.
- Keep captions and inspectors readable while the world moves.
- Never use random drift, constant push-ins, or zooms that hide necessary context.
- **Never move the camera in a dead beat.** Fuse every frame move with the content change that motivates it, in the same `self.play(...)`. Zoom in when a specific computation or inspection begins; zoom out while new structure assembles or clutter clears; 2D moves run 1-2s, 3D establishing moves 3s+ (full trigger table in `attention-and-retention.md`).

Useful grammar:

```python
frame = self.camera.frame
frame.save_state()
focus = VGroup(active_object, active_label)
self.play(
    frame.animate.move_to(focus).set(width=max(4.0, focus.width * 1.5)),
    FadeIn(detail_labels, lag_ratio=0.1),   # fused with the content that motivates the move
    run_time=1.2,
)
# local beat
self.play(Restore(frame), run_time=1.0)
```

## Attention Doctrine

One focal winner per beat.

Use the attention baton:

1. isolate the focus
2. label it
3. transform or route through it
4. conclude with a caption, inspector update, proof gate, or metric

Keep context visible but quiet:

```python
self.play(inactive.animate.set_opacity(0.25), active.animate.set_opacity(1.0), run_time=0.35)
self.play(Circumscribe(active, color=ACCENT), run_time=0.6)
```

Measured norms from the strongest source corpus: inactive context sits at 0.2-0.35 opacity (0.5 for half-receded), one explicit attention act lands every 2-4 `play()` calls, and a single `SurroundingRectangle` slides from term to term instead of spawning fresh ones. Flashes are punctuation for landings, not continuous narration.

## Motion Doctrine

Motion should expose dependency.

Prefer one driver that controls many dependents:

```python
t = ValueTracker(0)
dot = always_redraw(lambda: Dot(path.point_from_proportion(t.get_value()), color=ACCENT))
label = always_redraw(lambda: Text("active", font=MONO, font_size=20).next_to(dot, UP))
readout = DecimalNumber(0, font_size=28, color=ACCENT)
readout.add_updater(lambda m: m.set_value(t.get_value()))
self.add(dot, label, readout)
self.play(t.animate.set_value(1), run_time=3, rate_func=linear)
```

Use:

- `always_redraw` for derived geometry
- `add_updater` for labels, counters, connectors, and HUD-like readouts
- `put_start_and_end_on` for live connector lines
- `TracedPath` when the history of motion is meaningful
- `MoveAlongPath` plus `ShowPassingFlash` for routed packets through a pipeline

## Continuity Doctrine

World-class animation preserves identity.

- Keep the scaffold stable and change only the active piece.
- Transform conserved symbols before introducing new symbols.
- Freeze dynamic geometry before formalizing it into notation.
- Park old conclusions in a memory rail instead of deleting all context.
- In comparisons, keep both sides visible and shift opacity/focus rather than swapping the whole scene.

For derivations:

```python
self.play(old_row.animate.set_opacity(0.30), run_time=0.25)
self.play(TransformMatchingTex(old_eq, new_eq), run_time=1.2)
self.play(Circumscribe(new_piece, color=ACCENT), run_time=0.6)
self.wait(0.6)
```

## Pacing Doctrine

Use commit -> hold -> next commit.

- One semantic change per beat.
- Hold 0.5-1.5s after normal landings.
- Hold 1.5-3.0s after proof gates, hard ideas, metric landings, and final hero results.
- Repeated structures can accelerate after the viewer learns the pattern.
- Avoid flat timing where every action uses the same `run_time`.
- Insert one ~1s breath immediately before each key reveal: build the highlight, wait, then fire the transform.
- Reserve one long continuous sweep (5-15s, `rate_func=linear` tracker or slow camera drift) per scene as the "watch it play out" moment; keep long contemplation holds for finished, self-explanatory images only.
- Full quantified rhythm — cadence, overlap dial, dead-air limits, audit — in `attention-and-retention.md`.

## Hero Landing

The final result should be screenshot-worthy.

Good hero landing ingredients:

- full mechanism route or final comparison visible
- one result object sealed with `SurroundingRectangle`
- headline metric or equation large enough to read
- accent flash or passing highlight
- camera restored or slightly hero-framed
- final hold

Do not end by merely fading out. End by making the result feel earned.

## Anti-Patterns

Avoid:

- low-level action lists as the plan
- moving every object at once
- formula-first exposition when a visual dependency can come first
- deleting all context every beat
- unprotected captions during camera motion
- camera movement that does not correspond to meaning
- dense paragraphs, tiny labels, or many simultaneous active objects
- decorative polish before attention, pacing, and hierarchy are solved
