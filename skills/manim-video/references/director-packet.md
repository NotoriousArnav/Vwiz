# Director Packet

Use this for ambitious, complex, research-teaser-style, multi-scene, or number-heavy animations. It distills a production Text2Animation workflow into a portable pre-code contract that any coding agent can follow without LangGraph, databases, or app-specific services.

The goal is not to make planning heavy. The goal is to make the important directing decisions explicit before codegen so Manim code has something precise to execute.

Table of contents:

- [Why This Exists](#why-this-exists)
- [When To Use It](#when-to-use-it)
- [Portable Workflow](#portable-workflow)
- [Contract Layers](#contract-layers)
- [Director Packet Template](#director-packet-template)
- [Operator Stack](#operator-stack)
- [Pre-Code Gates](#pre-code-gates)
- [Codegen Rules](#codegen-rules)
- [Repair Rules](#repair-rules)
- [Smell Test](#smell-test)

## Why This Exists

High-quality Manim output should come from a strong directing packet before codegen, not from repeated codegen -> visual-fix loops. The packet captures the spatial, temporal, pedagogical, and semantic decisions that code must execute.

A weak packet produces weak code even when the Manim syntax is correct. A strong packet makes the agent preserve the user's requested objects, control attention, keep layout stable, vary pacing, and land a memorable final frame.

For simple animations, `scene-planning.md` is enough. For premium output, write this director packet inside `plan.md` before coding, then run the gates in `preflight-gates.md`.

## When To Use It

Use the director packet when any of these are true:

- The user asks for "premium", "world class", "3Blue1Brown-style", "viral", "alive", "cinematic", or "research teaser" quality.
- The prompt includes a graph, equation handoff, geometry construction, simulation, physical story, comparison, data story, or multiple representations.
- The animation has more than three beats or more than one scene.
- The output should be reusable by another coding tool such as Claude Code, Codex, OpenCode, Antigravity, Goose, Amp, or a custom open-source agent.

Skip the full packet for tiny one-scene snippets, but still keep one core insight, one focal winner, readable holds, and a final payoff.

## Portable Workflow

Use this sequence:

1. **Intent triage**: classify the request as simple, medium, or complex; identify domain, audience, target duration, aspect ratio, and whether one continuous canvas is enough before choosing scene count.
2. **Minimum contract**: extract the non-negotiable teaching spine before style decisions.
3. **Prompt object registry**: extract concrete nouns and visual objects from the user request before rewriting it.
4. **Scene family**: choose the strongest architecture, not a generic text-board scene.
5. **Director packet**: write ledgers, beat graph, layout/motion plan, camera plan, pacing plan, and acceptance rubric.
6. **Pre-code gates**: refuse to code until the gates below and `preflight-gates.md` pass.
7. **Code**: implement the packet exactly, with stable object ids, semantic colors, and source comments for major beats.
8. **Review and repair**: render, review actual output, patch the smallest broken contract, rerender, then stop after bounded passes.

## Contract Layers

Use these layers in order. They are portable names, not app dependencies.

### 1. Minimum Contract

This is the first useful pass. It prevents the agent from jumping straight into code or generic storyboards.

Required fields:

- `animation_brief`: one paragraph describing what the viewer will understand.
- `core_insight`: the one sentence the viewer should remember.
- `motivation_hook`: the concrete failure, tension, or question shown first.
- `narrative_arc`: where the problem is posed, where complexity grows, and where it resolves.
- `viewer_active_moments`: beats where the viewer is expected to predict, compare, or notice something.
- `withheld_for_focus`: ideas intentionally omitted until later or not shown at all.
- `symbol_ledger`: stable ids, visual meaning, color, and persistence for important symbols.
- `layout_assertions`: no-overlap, lane, scaffold, and readability commitments.
- `scene_family_recipe`: selected scene architecture and why it fits the prompt.
- `protected_overlays`: captions, formulas, inspectors, or dashboards that must remain readable.
- `memory_rail`: prior context that stays parked for later reuse.
- `representation_ladder`: concrete visual -> readout -> symbolic/formal step.
- `focus_pacing_policy`: one focal winner per beat, handoff rules, hold policy.
- `pedagogical_checkpoints`: what each beat must make understandable.
- `beat_focus_obligations`: beat-level focus, learner question, and closure condition.
- `shot_plan`: shot ids, camera role, and state handoff.
- `continuity_architecture`: one-canvas default or justified scene split with state handoff.
- `transform_policy`: how object/symbol identity is preserved.
- `composition_units`: semantic groups, lanes, panels, and visual clusters.

### 2. Direction Contract

This is the codegen-facing contract. It turns the minimum contract into executable obligations.

Required fields:

- `visual_thesis`: a concrete visual claim, not "show the concept".
- `object_ledger` and `symbol_ledger`: stable ids with labels, roles, colors, and persistence.
- `beat_contracts`: beat id, shot id, learning claim, active focus, required objects, continuity objects, introduced/exiting objects, required symbols, assertions.
- `focus_baton` or `focus_windows`: what attention moves from, what owns the beat, and what attention moves to.
- `camera_plan`: one entry per beat, even if locked; non-static moves need target, reason, teaching purpose, duration, and restore policy.
- `pacing_plan`: play seconds, hold seconds, readability targets, and hold reason for every beat.
- `payoff_frame`: final must-show objects, must-show relationship, and final hold.
- `acceptance_rubric`: quality, semantic, payoff, and visual assertion checks.
- `manim_grounding`: required Manim capabilities such as `Axes`, `plot`, `Dot`, `c2p`, `ValueTracker`, `always_redraw`, `TransformMatchingTex`, or `MovingCameraScene`.
- `source_map_anchor_requirements`: required shot ids, object ids, and symbol ids that must appear in code comments, variable names, `next_section`, or rendered symbols.
- `revision_scaffold`: preferred patch paths and fields to preserve during repair.

### 3. Layout Motion IR

This is the layout and motion contract. It is the difference between a polished animation and a slide deck.

Required concepts:

- `zones`: named screen lanes such as `world_stage`, `equation_lane`, `graph_stage`, `inspector_hud`, `memory_rail`, `caption_lane`.
- `zone_rects`: approximate frame rectangles for dense layouts, including safe margins and protected overlay bounds.
- `anchors`: named object or camera targets.
- `object_rails`: where repeated objects live across beats, including persistence and allowed zones.
- `collision_extents`: estimated drawn size plus labels, halos, and tag/headroom for nodes, cards, equations, and overlays.
- `fit_policy`: max zone width/height, fixed clearance gaps, scale floor, density cap, and the split/park fallback when objects cannot fit.
- `scaffold_contract`: what stays stable, what can change locally, and whether full-board reset is forbidden.
- `clutter_caps`: max primary focus targets, competing motions, labels, and accent colors.
- `family_contract`: scene-family rules such as graph/equation handoff, physical causality, comparison lanes, or camera-led spatial story.
- `scene_split_policy`: why a new scene class is needed, or why the current scaffold must remain continuous.
- `camera_contract`: overview/detail/restore or static-camera policy.
- `phase_order`: reveal sequence, freeze boundaries, payoff order.
- `representation_links`: how visual objects map to notation, readouts, or alternate views.
- `driver_states`: single source of truth for live dependencies.
- `dependency_bindings`: what updates from which driver.
- `motion_assertions`: connectors, traces, labels, and derived geometry must stay bound to source objects.
- `focal_hierarchy` and `focus_baton`: one primary focus with bounded support.
- `continuity_rules`: symbol color, object identity, and transform continuity.
- `banned_patterns`: full-board churn, decorative motion, unsupported camera moves, generic ids, text-only collapse.

### 4. Codegen View

Before code, compress the packet into a codegen view:

- `beat_contracts`
- `focus_baton`
- `camera_plan`
- `pacing_plan`
- `layout_motion_ir`
- `representation_ladder_contract`
- `symbol_continuity_contract`
- `pedagogical_checkpoint_contract`
- `focus_obligation_contract`
- `manim_grounding`
- `acceptance_rubric`
- `payoff_frame`
- `source_map_anchor_requirements`

Treat this codegen view as authoritative. The original prompt is secondary after the packet is written.

## Director Packet Template

Add this to `plan.md` for every complex scene or short video:

```markdown
## Director Packet

### Intent
- Complexity: simple / medium / complex
- Domain: math / physics / algorithm / data / architecture / paper
- Audience: prerequisites and assumed knowledge
- Core insight: one sentence
- Motivation hook: concrete visible problem first, not a definition
- Misconception guard: wrong implication to avoid
- Final payoff frame: screenshot-worthy final state
- Withheld for focus: omitted ideas and why

### Semantic Intent
- Must-show objects: concrete objects from the user prompt
- Must-show relationships: relationships that must become visible
- Must not reduce to: equation-only narration / caption-only physical explanation / text-only equivalence statement / generic diagram

### Scene Family
- Pattern stack: from `source-backed-patterns.md`
- Scene family: equation_transform_narrative / equation_graph_handoff / dynamic_dependency_linked_views / camera_led_spatial_story / physical_storytelling / geometry_completion / comparison / progressive_disclosure
- Selected operators: stable_scaffold_local_change, attention_baton, commit_hold_next, layer_contract, anti_noise_budget, plus prompt-specific operators
- Continuity architecture: one continuous canvas by default; split only for domain shift, hard reset, render/runtime isolation, renderer change, or density failure
- State handoff: what persists from previous scene and what passes to next; first frame of next scene must recall the previous state when continuity matters

### Object Ledger
| id | label | role | zone | persistence | color |
|----|-------|------|------|-------------|-------|
| obj_axes | Axes | stable scaffold | graph_stage | persistent | DIM |

### Symbol Ledger
| id | symbol | meaning | color | persists? |
|----|--------|---------|-------|-----------|
| sym_x | x | input value | PRIMARY | yes |

### Layout Motion IR
- Zones: main_stage, equation_lane, graph_stage, inspector_hud, memory_rail, caption_lane
- Zone rects: rough frame bounds for dense lanes plus frame margin
- Anchors: named camera/object targets
- Object rails: where repeated objects live across beats
- Collision extents: shape/card/equation sizes including label and halo margin
- Fit policy: max size per zone, fixed gap/buffer policy, scale floor, fallback to split scene or park old context
- Scaffold contract: stable zones stay stable; only the active semantic change moves
- Clutter caps: max 1 primary focus, max 1 competing motion, max 3 labels, max 2 accent colors per beat
- Protected overlays: captions, metrics, formulas, inspectors kept readable
- Driver states: one driver for linked motion when possible
- Dependency bindings: moving labels/connectors/readouts update from the driver
- Representation links: visual object -> readout -> symbol/formula
- Banned patterns: full-board churn, generic ids, decorative camera, text-only collapse

### Beat Graph
| beat | shot | voiceover | primary focus | visual claim | reveal order | motion intent | handoff | camera | play | hold | assertions |
|------|------|-----------|---------------|--------------|--------------|---------------|---------|--------|------|------|------------|
| beat_1 | shot_axes | spoken line | obj_axes | viewer sees the scaffold | axes -> labels | establish context | none -> obj_curve | locked | 1.2 | 0.8 | visible(obj_axes); single_focal_winner(obj_axes) |

### Camera Plan
| beat | shot | action | target | teaching purpose | duration | restore |
|------|------|--------|--------|------------------|----------|---------|
| beat_3 | shot_slope | tighten_for_density | obj_tangent_group | inspect local slope without competing context | 0.8 | restore_after_beat |

### Pacing Plan
| beat | play_seconds | hold_seconds | readability targets | hold reason |
|------|--------------|--------------|---------------------|-------------|
| beat_3 | 1.4 | 1.2 | obj_tangent_group, sym_slope | viewer reads slope before formula lands |

### Manim Grounding
- Required capabilities: Axes, plot, Dot, c2p, ValueTracker, always_redraw, TransformMatchingTex
- Scene class: Scene / MovingCameraScene / ThreeDScene
- Renderer constraints: avoid unsupported APIs listed in `troubleshooting.md`

### Source Map Anchor Requirements
- Required shot ids: shot_axes, shot_slope, shot_payoff
- Required object ids: obj_axes, obj_curve, obj_tangent_group
- Required symbol ids: sym_x, sym_slope

### Acceptance Rubric
- Quality: focal point readable, camera purposeful, pacing readable
- Semantic: must-show objects and relationships survive
- Payoff: final frame proves the core insight
- Visual assertions: visible(...), no_overlap(...), camera_contains(...), read_hold_after_landing(...)

### Revision Scaffold
- Preserve: beat order, focus winners, camera plan, pacing plan, zones, object ids, symbol ids, payoff frame
- Preferred patch order: packet field -> local code fix -> rerender -> review
```

Keep ids semantic and stable: `obj_secant_line`, `sym_dx`, `beat_limit_collapse`, not `thing1`.

## Operator Stack

Start with these default operators for premium output:

- `stable_scaffold_local_change`: keep spatial identity stable; only the active semantic object changes.
- `attention_baton`: every beat has one primary focus and a clear handoff.
- `commit_hold_next`: every semantic landing gets a readable hold.
- `layer_contract`: foreground, labels, overlays, memory, and scaffold have explicit visual hierarchy.
- `anti_noise_budget`: cap simultaneous motion, focus targets, labels, and accent colors.

Add prompt-specific operators only when useful:

- `clocked_dependency_system`: one driver controls linked motion, readouts, labels, and focus gates.
- `live_derived_geometry`: probes, braces, connectors, traces, and labels follow live state until intentionally frozen.
- `stable_numeric_inspector`: numeric readouts stay in stable slots with declared precision.
- `matched_symbol_transform`: repeated symbols keep color and identity across formula transforms.
- `slice_reveal`: dense text or equations appear by semantic slice, not all at once.
- `visual_to_formula_handoff`: visible relationship first, formula second.
- `representation_ladder`: concrete visual -> readout -> symbol -> formal result.
- `freeze_before_formalization`: live geometry or state is copied/static before becoming notation.
- `dual_zone_board`: stable lanes for graph/equation, simulation/readout, or proof/diagram.
- `protected_overlay_panel`: captions, formulas, dashboards, and inspectors remain readable during motion.
- `parking_rail_memory`: prior context parks quietly instead of disappearing.
- `overview_detail_restore_camera`: camera establishes, inspects, settles, then restores context.
- `semantic_group_frame`: frames group meaning, not decoration.
- `crosshair_io_readout`: graph input, output, projections, and readouts share a driver.
- `history_layer`: trails or histories stay quieter than current focus.
- `endpoint_connector`: arrows, braces, and connectors stay bound to live endpoints.
- `parameter_sweeper`: important parameters are visible as controls or readouts.
- `active_code_line_stage`: code, compiler, or algorithm scenes expose the active line/stage.
- `diagram_state_crosslink`: code/math/state artifacts visibly map to diagram objects.
- `route_or_state_packet`: a token, packet, cursor, or state marker carries focus through topology.
- `comparator_stage`: comparison lanes stay stable with deliberate focus handoffs.
- `linked_dual_space_stage`: two panels share one driver and visible synchronization.
- `threshold_intervention`: slow or pause at central threshold crossings.

Each selected operator must add packet fields and acceptance checks. Do not list operators as decoration.

## Pre-Code Gates

Do not write Manim code until these gates pass. See `preflight-gates.md` for the detailed checklist.

- **Prompt coverage**: concrete objects named by the user survive into the object/symbol ledger.
- **Semantic collapse guard**: graph, motion, physical, geometry, comparison, or multi-representation requests do not collapse into text-only or equation-only scenes.
- **One core insight**: the packet is built around one aha, not a survey.
- **Concrete before formal**: the visual intuition appears before the equation unless the user explicitly asks for formal-first proof.
- **Specific text**: no visual thesis like "show the concept" and no beat like "explain idea".
- **One focal winner**: every beat has exactly one primary focus and bounded support.
- **Focus handoff**: every beat after the first names what recedes and what rises.
- **Stable scaffold**: repeated objects have object rails; full-board resets are forbidden unless a new section declares a semantic reset.
- **Scene split justified**: multiple scene classes need a domain shift, hard narrative reset, render/runtime reason, renderer/API reason, or density reason plus a state handoff.
- **Declared zones**: all lanes, HUDs, memory rails, captions, and graph/equation areas are named before placement decisions.
- **Camera earned**: every non-static camera move has target, teaching purpose, duration, guardrails, and restore policy.
- **Numeric pacing**: every beat has play and hold durations; payoff has a readable final hold.
- **Representation ladder**: concrete view -> readout -> symbolic/formal step is ordered, with freeze-before-formalization when needed.
- **Symbol continuity**: repeated terms keep color and identity across transforms.
- **Payoff visible**: final beat contains the must-show objects, relationship, and readable hold.
- **Source anchors planned**: required shot ids, object ids, and symbol ids are listed before code.
- **No template contamination**: no generic ids such as `obj_diagram`, no filler beats such as "show concept", no decorative camera language.

If a gate fails, fix `plan.md` before coding.

## Codegen Rules

- Implement the beat graph in order.
- Use source anchors for major beats. Portable marker:

```python
# manim-skill:shot shot_id=shot_slope beat_id=beat_3
# manim-skill:element object_id=obj_tangent_group
# manim-skill:assert assertion="visible(obj_tangent_group)"
```

- If using the original Text2Animation verifier, use the same fields with `# t2a:` markers:

```python
# t2a:shot shot_id=shot_slope beat_id=beat_3
# t2a:element object_id=obj_tangent_group
# t2a:assert assertion="visible(obj_tangent_group)"
```

- Use `self.next_section("shot_slope")` when useful; shot ids should match the packet.
- Define object variables with ledger-like names when practical.
- Use semantic colors from the symbol ledger.
- Use `ValueTracker`, `always_redraw`, and updaters only for declared live dependencies.
- Clear or suspend updaters before camera moves, formalization freezes, and scene end when they would fight later animations.
- Preserve object identity with `TransformMatchingTex`, `TransformFromCopy`, `ReplacementTransform`, stable side-by-side panels, or dimmed memory rails.
- Do not introduce visual objects that are not in the packet unless they solve a concrete readability issue.
- Do not remove packet-required objects, anchors, holds, or payoff elements to make code easier.

## Repair Rules

When validation or review finds a problem:

1. Map the issue to the director packet: beat, focus, camera, pacing, zone, object rail, symbol, assertion, or payoff.
2. Patch the smallest broken packet field first.
3. Patch code only after the packet still makes sense.
4. Preserve beat order, focus winners, camera plan, pacing plan, object ids, symbol ids, zones, source anchors, and payoff frame.
5. Do not fix one overlap by shrinking the whole scene if only one label needs a local move.
6. Do not remove holds, anchors, or final payoff elements to make the render shorter.
7. Rerender the affected scene and re-review actual output before accepting the fix.

## Smell Test

A strong packet should pass these questions:

- Is there one organizing insight?
- Does the first 15-30 seconds pose a concrete problem or tension?
- Does the animation show before it tells?
- Is every motion load-bearing?
- Are colors semantic and consistent?
- Is the focal point unmistakable in every beat?
- Does pacing vary instead of running like a metronome?
- Is a misconception explicitly guarded against?
- Does the prompt's concrete objects survive into the final payoff?
- Does the final frame land the opening promise?
- Is there one memorable visual idea a viewer could describe later?
