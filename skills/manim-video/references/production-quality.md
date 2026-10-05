# Production Quality Checklist

Standards and checks for ensuring animation output is publication-ready.

## Pre-Code Checklist

Before writing any Manim code:

- [ ] Narration script written with visual beats marked
- [ ] Scene list with purpose, duration, and layout for each
- [ ] Continuity architecture chosen: one continuous canvas by default, or each split scene has a specific reason and state handoff
- [ ] For ambitious output, director packet written in `plan.md`
- [ ] Minimum contract includes core insight, motivation hook, narrative arc, viewer active moments, withheld-for-focus, symbol ledger, scene family, focus policy, and payoff frame
- [ ] Prompt objects survive into object/symbol ledgers
- [ ] Semantic collapse guards are declared for graph, motion, physical, geometry, comparison, or multi-representation prompts
- [ ] For premium output, each beat has focus, mechanism, camera, memory, and landing
- [ ] Each complex beat declares zone, primary focus, handoff, play seconds, hold seconds, assertion, and source anchor requirements
- [ ] Layout Motion IR declares zones, anchors, object rails, scaffold contract, clutter caps, deterministic fit policy, focus baton, camera doctrine, reveal order, and banned shortcuts
- [ ] Selected operators add real packet fields and acceptance checks, not decorative labels
- [ ] Number-heavy or graph-heavy scenes declare scaffold, driver, live dependency layer, protected inspector, attention gate, continuity transform, read holds, precision policy, and memory rail policy
- [ ] Pre-code gates in `preflight-gates.md` pass
- [ ] Color palette defined with meaning assignments (`PRIMARY` = main concept, etc.)
- [ ] `MONO = "Noto Sans Mono"` set as the Docker-safe font constant
- [ ] Target resolution and aspect ratio decided

## Text Quality

### Overlap prevention

```python
# RULE: buff >= 0.5 for edge text
label.to_edge(DOWN, buff=0.5)     # GOOD
label.to_edge(DOWN, buff=0.3)     # BAD — may clip

# RULE: FadeOut previous before adding new at same position
self.play(ReplacementTransform(note1, note2))  # GOOD
self.play(Write(note2))                          # BAD — overlaps note1

# RULE: Reduce font size for dense scenes
# When > 4 text elements visible, use font_size=20 not 28
```

### Width enforcement

Long text strings overflow the frame:

```python
# RULE: Set max width for any text that might be long
text = Text("This is a potentially long description", font_size=22, font=MONO)
if text.width > config.frame_width - 1.0:
    text.set_width(config.frame_width - 1.0)
```

### Font consistency

```python
# RULE: Define MONO once, use everywhere
MONO = "Noto Sans Mono"

# WRONG: mixing fonts
Text("Title", font="Helvetica")
Text("Label", font="Arial")
Text("Code", font="Courier")

# RIGHT: one font
Text("Title", font=MONO, weight=BOLD, font_size=48)
Text("Label", font=MONO, font_size=20)
Text("Code", font=MONO, font_size=18)
```

## Spatial Layout

### The coordinate budget

The visible frame is approximately 14.2 wide × 8.0 tall (default 16:9). With mandatory margins:

```
Usable area: x ∈ [-6.5, 6.5], y ∈ [-3.5, 3.5]
Top title zone: y ∈ [2.5, 3.5]
Bottom note zone: y ∈ [-3.5, -2.5]
Main content: y ∈ [-2.5, 2.5], x ∈ [-6.0, 6.0]
```

### Deterministic layout guard

For dense graphs, entity maps, dashboards, derivations, or split-screen comparisons, do not place objects by feel. Pre-solve the layout before writing the animations:

- Reserve named zones first: title, world/main stage, inspector/HUD, memory rail, caption/footer.
- Keep world objects disjoint from protected overlays. Do not let captions, inspectors, formulas, or memory rails share the same collision space as moving geometry.
- Estimate each element by its full collision extent: drawn shape + label + halo margin + tag/headroom, not only its center point.
- Fit groups into their zone with a max width, max height, fixed clearance gaps, and scale floor. Scale cards/groups, but keep whitespace buffers meaningful; collapsed gaps make objects visually merge even when boxes technically do not overlap.
- If the fit scale would fall below about `0.40` or text below `font_size=18`, treat the layout as failed. Split the scene, reduce entity count, park old context, or move detail to an inspector instead of accepting tiny content.
- After arranging a group, check both frame containment and zone containment before animating it. A correct center position is not enough if the bounding box clips at the edge.
- Keep planning sizes and code sizes synchronized. If a card, node, label, or inspector is drawn larger in Manim, update the layout assumptions too.

### Fill the frame

Empty scenes look unfinished. If the main content is small, add context:
- A dimmed grid/axes behind the content
- A title/subtitle at the top
- A source citation at the bottom
- Low-opacity structural context that helps orientation

### Maximum simultaneous elements

**Hard limit: 6 actively visible elements.** Beyond that, the viewer can't track everything. If you need more:
- Dim old elements to opacity 0.3
- Remove elements that have served their purpose
- Split into two beats or scenes with a state handoff

## Animation Quality

### Premium directing audit

- **Stable scaffold**: the whole board does not relayout every beat
- **One focal winner**: only one object/group dominates attention at a time
- **Commit-hold-next**: every semantic change lands before the next one begins
- **Protected overlays**: captions, inspectors, and metrics remain readable during camera moves
- **Semantic camera**: camera establishes, inspects, then restores context
- **Live dependency**: moving labels, counters, connectors, or traces follow a driver instead of being manually repositioned
- **Stable inspector**: numbers use persistent `DecimalNumber` / `Integer` slots with declared precision instead of jittering text rebuilds
- **Representation ladder**: concrete visual evidence climbs to readout, symbol, formula, or matrix before the result is sealed
- **Continuity**: old context is dimmed, parked, or transformed forward instead of repeatedly deleted
- **Hero landing**: final result is sealed, readable, and held long enough to remember

### Continuity and variation audit

Check that variation supports meaning instead of fighting continuity:

- Semantic colors keep their meaning across scenes and beats.
- The same concept stays in the same region unless a scene split or camera move has a stated reason.
- Repeated motion vocabulary is acceptable when it teaches the same relationship.
- New layouts, colors, or animation styles appear only for a new scene family, contrast, density fallback, or semantic reset.
- Pacing varies by beat role while preserving read holds and final payoff.

### Tempo curve

A good video follows a tempo curve:

```
Slow ──→ Medium ──→ FAST (climax) ──→ Slow (conclusion)

Scene 1: Slow (introduction, setup)
Scene 2: Medium (building understanding)
Scene 3: Medium-Fast (core content, lots of animation)
Scene 4: FAST (montage of applications/results)
Scene 5: Slow (conclusion, key takeaway)
```

### Transition quality

Between scenes:
- **Continuity first**: carry, park, or transform context forward when scenes continue the same idea
- **Semantic reset only**: use `self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)` when the plan declares a reset or final cleanup
- **Brief pause**: `self.wait(0.3)` after a reset fadeout, before the next scene's first animation
- **Never hard-cut**: always animate the transition

## Color Quality

### Dimming on dark backgrounds

Colors that look vibrant on white look muddy on dark backgrounds (#0D1117, #1C1C1C). Test your palette:

```python
# Colors that work well on dark backgrounds:
# Bright and saturated: #58C4DD, #83C167, #FFFF00, #FF6B6B
# Colors that DON'T work: #666666 (invisible), #2244AA (too dark)

# RULE: Structural elements (axes, grids) at opacity 0.15
# Context elements at 0.3-0.4
# Primary elements at 1.0
```

### Color meaning consistency

Once a color is assigned a meaning, it keeps that meaning for the entire video:

```python
# If PRIMARY (#58C4DD) means "the model" in Scene 1,
# it means "the model" in every scene.
# Never reuse PRIMARY for a different concept later.
```

## Data Visualization Quality

### Minimum requirements for charts

- Axis labels on every axis
- Y-axis range starts at 0 (or has a clear break indicator)
- Bar/line colors match the legend
- Numbers on notable data points (at least the maximum and the comparison point)

### Animated counters

When showing a number changing:
```python
# GOOD: DecimalNumber with smooth animation
counter = DecimalNumber(0, font_size=48, num_decimal_places=0, font="Noto Sans Mono")
self.play(counter.animate.set_value(1000), run_time=3, rate_func=rush_from)

# BAD: Text that jumps between values
```

## Pre-Render Checklist

Before running `/path/to/manim-video/scripts/manim.sh -qh` or `scripts\manim.ps1 -qh`:

- [ ] All scenes render without errors at `-ql`
- [ ] Preview stills at `-qm` for text-heavy scenes (check kerning)
- [ ] Background color set in every scene (`self.camera.background_color = BG`)
- [ ] `add_subcaption()` or `subcaption=` on every significant animation
- [ ] No text smaller than font_size=18
- [ ] No text using proportional fonts (use monospace)
- [ ] buff >= 0.5 on all `.to_edge()` calls
- [ ] Scene ending matches continuity architecture: carry/park/transform forward, or clean exit only for semantic reset/final cleanup
- [ ] `self.wait()` after every reveal
- [ ] One focal winner per beat; non-focus context dimmed or parked
- [ ] Camera moves have semantic purpose and restore context when needed
- [ ] Source anchors exist for required shot ids, object ids, symbol ids, camera moves, and important assertions
- [ ] Repeated focal objects have object rails and are not rebuilt under new names
- [ ] Representation ladder and symbol continuity survive into code
- [ ] Dense layouts have explicit zone containment, collision extents, and a fit/split fallback
- [ ] Final result has a clear hero landing, not just a fadeout
- [ ] Color constants used (no hardcoded hex strings in scene code)
- [ ] All scenes use the same quality flag (don't mix `-ql` and `-qh`)

## Post-Render Checklist

After stitching the final video:

- [ ] Run the feedback loop in `review-loop.md` for non-trivial videos
- [ ] Run the retention audit in `attention-and-retention.md`: freezedetect dead-air scan, metronome check, attention-act density, hook check, payoff check
- [ ] Latest code has been rerendered after the final fix; do not accept stale review evidence
- [ ] Contact sheet or direct video review shows no sparse, near-empty, low-contrast, edge-cropped, or static-unintended frames
- [ ] Watch the complete video at 1x speed — does it feel rushed anywhere?
- [ ] Opening tension, visual-before-formal handoff, misconception guard, and final payoff all connect into one organizing insight
- [ ] Is there a moment where two things animate simultaneously and it's confusing?
- [ ] Does every text label have enough time to be read?
- [ ] Are transitions between scenes smooth (no black frames, no jarring cuts)?
- [ ] Is the audio in sync with the visuals (if using voiceover)?
- [ ] Is the Gibbs-like "first impression" good? The first 5 seconds determine if someone keeps watching
