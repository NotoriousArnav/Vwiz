# Worked Example: Secant → Derivative

A complete, render-verified scene that composes the skill's doctrines into one number-heavy explainer. Use it as an imitation target: the fastest way to internalize the rules is to see them all operating in ~100 lines. The code below rendered clean on Manim CE v0.20.1 in the pinned Docker runtime, produces a 28-second video, and passes the freezedetect retention audit with zero dead spans.

Do not copy it verbatim into unrelated projects — copy its *shape*: hook first, one driver, live numbers, one long sweep, breath, symbolic landing, sealed payoff.

## The Contract (mini director packet)

| beat | focus | mechanism | pacing | landing |
|------|-------|-----------|--------|---------|
| hook | rider dot | curve appears, dot rides it accelerating (`rush_into`) | 4.2s play + 1.2s hold | question overlay, no title card |
| anchor | point P at x=1 | rider becomes P, flash | 1.6s + 0.6s | the question now has a location |
| machine | secant + inspector | one `ValueTracker`, `always_redraw` secant, two `DecimalNumber` readouts | 2.0s + 0.8s | viewer sees slope as a computable number |
| name it | formula lane | slope formula written *after* the dependency is visible | 1.4s + 1.0s | notation inherits meaning from motion |
| sweep | dx → 0.001 | the scene's one long continuous moment, `linear`, 5s | 5s + 1.0s breath | readouts converge: 3.200 → 2.001 |
| landing | limit symbol | `TransformMatchingTex` slope → derivative definition | 2.2s + 1.0s | the limit closes the gap the numbers cannot |
| payoff | f'(1) = 2 | frozen readout `TransformFromCopy` into the exact result, pulse, seal | 2.3s + 2.5s | longest hold of the video |

Semantic colors: curve = PRIMARY (object of study), secant = SECONDARY (the tool we build), ACCENT (current focus and results). Each color keeps its meaning for the whole video.

## script.py

```python
from manim import *
import numpy as np

BG = "#1C1C1C"
PRIMARY = "#58C4DD"    # the curve — the object of study
SECONDARY = "#83C167"  # the secant — the measuring tool we build
ACCENT = "#FFFF00"     # current focus and results
MONO = "Noto Sans Mono"

X0 = 1.0


def f(x):
    return x ** 2


class SecantToDerivative(Scene):
    def construct(self):
        self.camera.background_color = BG

        # Beat 1 — HOOK: the object of study already doing its job (no title card)
        axes = Axes(
            x_range=[0, 2.6, 1], y_range=[0, 5.5, 1], x_length=6.5, y_length=5.2,
            axis_config={"include_numbers": True, "font_size": 20},
        ).to_edge(LEFT, buff=0.7)
        axes.set_opacity(0.35)                          # structural layer stays quiet
        curve = axes.plot(f, x_range=[0, 2.3], color=PRIMARY, stroke_width=5)
        rider = Dot(color=ACCENT).move_to(curve.get_start())

        self.add_subcaption("A point rides this curve, and it keeps speeding up.", duration=4)
        self.play(Create(axes), run_time=1.0)
        self.play(Create(curve), run_time=1.2)
        self.play(MoveAlongPath(rider, curve), run_time=2.0, rate_func=rush_into)
        question = Text("How fast, exactly at x = 1?", font=MONO, font_size=30, color=ACCENT)
        question.to_edge(UP, buff=0.4)
        self.play(Write(question), run_time=1.0)
        self.wait(1.2)

        # Beat 2 — anchor the point of interest; focus lands where the eye already is
        P = Dot(axes.c2p(X0, f(X0)), color=ACCENT)
        p_label = MathTex("x=1", font_size=30).next_to(P, DR, buff=0.15)
        self.play(ReplacementTransform(rider, P), FadeIn(p_label, shift=0.2 * RIGHT), run_time=1.0)
        self.play(Flash(P, color=ACCENT, flash_radius=0.4), run_time=0.6)
        self.wait(0.6)

        # Beat 3 — build the measuring machine: one driver, live geometry, live numbers
        dx = ValueTracker(1.2)

        def secant_line():
            p1 = axes.c2p(X0, f(X0))
            p2 = axes.c2p(X0 + dx.get_value(), f(X0 + dx.get_value()))
            d = p2 - p1
            d = d / np.linalg.norm(d)                   # normalized: no degeneracy as dx -> 0
            return Line(p1 - d * 1.2, p1 + d * 4.8, color=SECONDARY, stroke_width=4)

        secant = always_redraw(secant_line)
        Q = always_redraw(lambda: Dot(
            axes.c2p(X0 + dx.get_value(), f(X0 + dx.get_value())),
            color=SECONDARY, radius=0.06))

        dx_label = MathTex("dx =", font_size=34)
        dx_value = DecimalNumber(1.2, num_decimal_places=3, font_size=34, edge_to_fix=LEFT)
        slope_label = MathTex(r"\text{slope} =", font_size=34, color=ACCENT)
        slope_value = DecimalNumber(0, num_decimal_places=3, font_size=34,
                                    color=ACCENT, edge_to_fix=LEFT)
        dx_value.add_updater(lambda m: m.set_value(dx.get_value()))
        slope_value.add_updater(
            lambda m: m.set_value((f(X0 + dx.get_value()) - f(X0)) / dx.get_value()))
        row1 = VGroup(dx_label, dx_value).arrange(RIGHT, buff=0.15)
        row2 = VGroup(slope_label, slope_value).arrange(RIGHT, buff=0.15)
        inspector = VGroup(row1, row2).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        inspector.to_corner(UR, buff=0.6)

        self.add_subcaption("A second point gives a slope we can actually compute.", duration=4)
        self.play(Create(secant), FadeIn(Q), run_time=1.2)
        self.play(FadeIn(inspector, shift=0.2 * LEFT), run_time=0.8)
        self.wait(0.8)

        # dependency first, formula second: name what the viewer just watched
        slope_formula = MathTex(
            r"\text{slope}", "=", r"\frac{f(x+dx) - f(x)}{dx}", font_size=38)
        slope_formula.to_edge(DOWN, buff=0.5).shift(RIGHT * 2.2)
        self.play(Write(slope_formula), question.animate.set_opacity(0.4), run_time=1.4)
        self.wait(1.0)

        # Beat 4 — THE SWEEP: the scene's one long continuous moment
        self.add_subcaption("Now shrink dx, and watch the slope settle.", duration=5)
        self.play(dx.animate.set_value(0.001), run_time=5.0, rate_func=linear)
        self.wait(1.0)                                  # breath before the reveal

        # Beat 5 — symbolic landing: the limit closes the gap the numbers cannot
        deriv_formula = MathTex(
            r"f'(x)", "=", r"\lim_{dx \to 0}", r"\frac{f(x+dx) - f(x)}{dx}", font_size=38)
        deriv_formula.move_to(slope_formula)
        self.play(TransformMatchingTex(slope_formula, deriv_formula,
                                       transform_mismatches=True), run_time=1.4)
        self.play(Circumscribe(deriv_formula[2], color=ACCENT), run_time=0.8)
        self.wait(1.0)

        # Beat 6 — PAYOFF: the converged number becomes the exact result
        frozen_slope = slope_value.copy()
        frozen_slope.clear_updaters()                   # freeze before formalizing
        result = MathTex("f'(1)", "=", "2", font_size=46, color=ACCENT)
        result.move_to(RIGHT * 3.4 + UP * 0.4)
        self.play(TransformFromCopy(frozen_slope, result), run_time=1.2)
        self.play(result.animate.scale(1.08), rate_func=there_and_back, run_time=0.5)
        seal = SurroundingRectangle(result, color=ACCENT, buff=0.25)
        self.play(Create(seal), run_time=0.6)

        for mob in [dx_value, slope_value, secant, Q]:
            mob.clear_updaters()                        # stop live state before scene end
        self.wait(2.5)                                  # longest hold of the video
```

Render:

```bash
/path/to/manim-video/scripts/manim.sh -ql script.py SecantToDerivative
```

## What To Notice

- **Hook** (`attention-and-retention.md`): the first thing on screen is the curve with a point riding it and visibly accelerating — the question is *earned* before it is asked, and there is no title card.
- **One driver** (`updaters-and-trackers.md`, `codegen-craft.md`): the single `dx` tracker moves the secant, the Q dot, and both readouts. Nothing is repositioned manually.
- **No degenerate geometry**: the secant is rebuilt from a *normalized* direction vector, so it stays a full-length line even at `dx = 0.001`. Deriving the line from raw endpoints would collapse it at the limit.
- **Anti-jitter numbers** (`graphs-and-data.md`): both readouts use `edge_to_fix=LEFT`, so digits grow rightward and the labels never shudder.
- **Dependency first, formula second** (`source-backed-patterns.md`): the slope formula is written only after the viewer has watched the slope being computed.
- **The one long sweep** with `rate_func=linear` is the retention centerpiece — five seconds of continuous, meaningful motion where the numbers converge `3.200 → 2.001` and make the limit *visible*.
- **Breath before the reveal**: one plain `self.wait(1.0)` separates the sweep from the symbolic landing.
- **Numbers-then-symbols close**: the readout can only reach `2.001`; the `\lim` lands exactly on 2. The gap between them *is* the lesson, and the payoff (`TransformFromCopy` from the frozen readout into `f'(1)=2`) resolves it physically.
- **Freeze before formalizing**: the readout is copied and its updaters cleared before it becomes notation; all live updaters are cleared before the scene ends.
- **Retention audit passes**: 22 animations in 28 seconds, no static span over 3 seconds, the longest hold (2.5s) is the sealed payoff.
