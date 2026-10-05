# Scene Planning Reference

## Narrative Arc Structures

### Discovery Arc (most common)
1. Hook -- pose a question or surprising result
2. Intuition -- build visual understanding
3. Formalize -- introduce the equation/algorithm
4. Reveal -- the "aha moment"
5. Extend -- implications or generalizations

### Problem-Solution Arc
1. Problem -- what's broken
2. Failed attempt -- obvious approach fails
3. Key insight -- the idea that works
4. Solution -- implement it
5. Result -- show improvement

### Comparison Arc
1. Setup -- introduce two approaches
2. Approach A -- how it works
3. Approach B -- how it works
4. Contrast -- differences
5. Verdict -- which is better

### Build-Up Arc (architecture/systems)
1. Component A -- first piece
2. Component B -- second piece
3. Connection -- how they interact
4. Scale -- add more pieces
5. Full picture -- zoom out

## Continuity Architecture

Default to one continuous canvas for a single conceptual thread. If the viewer should feel that objects are evolving, transforming, or earning a result, keep one stable scaffold and use local transforms, parking rails, dimming, and camera inspection instead of clearing the board.

Split into multiple scene classes only when there is a real reason:

- domain shift or hard narrative reset
- duration or render-risk isolation
- a renderer/API shift such as `Scene` to `ThreeDScene`
- a layout change that would make the current canvas unreadably dense
- a deliberate editorial cut where the next first frame reorients the viewer

For every split, write a state handoff:

- what object, color, symbol, metric, or conclusion persists
- what the first frame of the next scene recalls from the previous scene
- whether the transition is carry-forward, transform bridge, memory rail, or semantic reset
- what is intentionally reset and why

## Scene Transitions

### Semantic Reset
Use this only when the plan declares a real reset. Do not use full-board fadeouts between adjacent beats of the same idea.

```python
self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
self.wait(0.3)
```

### Carry-Forward
Keep one element, fade the rest. Next scene starts with it still on screen.

### Transform Bridge
End scene with a shape, start next scene by transforming it.

## Cross-Scene Consistency

```python
# Shared constants at file top
BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
TITLE_SIZE = 48
BODY_SIZE = 30
LABEL_SIZE = 24
FAST = 0.8; NORMAL = 1.5; SLOW = 2.5
```

## Scene Checklist

- [ ] Background color set
- [ ] Subcaptions on every animation
- [ ] `self.wait()` after every reveal
- [ ] Text buff >= 0.5 for edge positioning
- [ ] No text overlap
- [ ] Color constants used (not hardcoded)
- [ ] Opacity layering applied
- [ ] Scene exit or transition follows continuity architecture
- [ ] No more than 5-6 elements visible at once

## Premium Beat Planning

Use this for advanced, dynamic, research-teaser-style animations. Each beat should have one focal winner and one semantic landing. See `director-packet.md` for the pre-code contract, `cinematic-directing.md` for the full directing doctrine, and `source-backed-patterns.md` for choosing the scene architecture.

```markdown
### Beat N: [Name] (~Ns)
- Pattern: [live derivative / simulation dashboard / pipeline flow / derivation board / comparison / rearrangement / function machine / 3D reveal]
- Focus: [one object/group]
- Viewer should notice: [one sentence]
- Mechanism: [what visibly changes]
- Camera: establish / inspect / edge-follow / restore / hero
- Memory: dim / park / rail / preserve / remove
- Landing: [caption, proof gate, metric, or hero result]
```

Default pacing: commit one semantic change, hold long enough to read it, then move to the next commit. Preserve previous context by dimming, parking, or compressing it instead of deleting everything.

## Duration Estimation

Calibration: narrative beat estimates typically run 1.5-2x longer than the coded reality. After writing the beat graph, sanity-check by summing the actual planned `run_time` + `wait` values — if the target duration matters (voiceover sync, platform limits), budget from that sum, not from the prose estimates below.

| Content | Duration |
|---------|----------|
| Cold-open hook (concrete instance doing its job) | 5-15s |
| Chapter/section card (mid-video only, never the opener) | 2-4s |
| Concept introduction | 10-20s |
| Equation reveal | 15-25s |
| Algorithm step | 5-10s |
| Data comparison | 10-15s |
| "Aha moment" | 15-30s |
| Conclusion | 5-10s |

## Planning Template

```markdown
# [Video Title]

## Overview
- **Topic**: [Core concept]
- **Hook**: [Opening question]
- **Aha moment**: [Key insight]
- **Target audience**: [Prerequisites]
- **Length**: [seconds/minutes]
- **Resolution**: 480p (draft) / 1080p (final)

## Color Palette
- Background: #1C1C1C
- Primary: #58C4DD -- [purpose]
- Secondary: #83C167 -- [purpose]
- Accent: #FFFF00 -- [purpose]

## Arc: [Discovery / Problem-Solution / Comparison / Build-Up]

## Scene 1: [Name] (~Ns)
**Purpose**: [one sentence]
**Layout**: [FULL_CENTER / LEFT_RIGHT / GRID / PROGRESSIVE]

### Visual elements
- [Mobject: type, position, color]

### Animation sequence
1. [Animation] -- [what it reveals] (~Ns)

### Directing beat
- Pattern: [one stack from source-backed-patterns.md, if the scene is complex]
- Director packet: [object ids, symbol ids, zone, primary_focus_id, assertion]
- Focus: [one object/group]
- Camera: [establish / inspect / restore / hero]
- Memory: [what stays visible, dimmed, or parked]
- Landing: [caption, metric, proof gate, or result]

### Subtitle
"[text]"
```
