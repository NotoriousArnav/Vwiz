# Preflight Gates

Use these gates before code and after draft code. They are adapted from a production Text2Animation contract pipeline, but written so any coding tool can follow them with plain files, Manim, and ffmpeg.

The rule is simple: weak plans should fail before rendering. Strong plans should leave observable evidence in code and video.

## Gate Order

1. **World contract gate**: Does `plan.md` contain a specific, executable director packet?
2. **Source anchor gate**: Does code preserve the packet's shot ids, object ids, and symbol ids?
3. **Direction execution gate**: Does code execute the camera, pacing, scaffold, representation, and payoff contract?
4. **Beat assertion gate**: Do beat assertions parse and reference real ids?
5. **Visual audit gate**: Does the rendered output pass basic frame and motion checks?
6. **Review gate**: Has the final accepted code been rerendered and reviewed after the last fix?

For simple one-scene snippets, use the world contract gate in lightweight form. For premium work, use all gates.

## 1. World Contract Gate

Do not code until the director packet has these required shapes:

- `beat_contracts`: at least one beat with `beat_id`, `shot_id`, `learning_claim`, `active_focus_id`, and required object/symbol ids.
- `focus_baton` or `focus_windows`: every beat has one active focus and a handoff.
- `camera_plan`: every beat has a camera entry, even if locked/static.
- `pacing_plan`: every beat has play seconds, hold seconds, readability targets, and hold reason.
- `payoff_frame`: final must-show objects, final must-show relationship, and final hold.
- `object_ledger` and `symbol_ledger`: stable ids, roles, colors, zones, and persistence.
- `layout_motion_ir`: zones, zone rectangles for dense layouts, anchors, object rails, scaffold, collision extents, fit policy, clutter caps, focus policy, camera doctrine, continuity rules, reveal order, and banned shortcuts.
- `continuity_architecture` or `scene_split_policy`: one continuous canvas by default, or a justified split with state handoff.
- `manim_grounding`: required Manim capabilities and scene class.
- `source_map_anchor_requirements`: required shot ids, object ids, and symbol ids.
- `revision_scaffold`: what must be preserved during repair.

Hard failures:

- Missing beat contracts, focus contract, camera plan, pacing plan, or payoff frame.
- Payoff frame has no must-show object or no must-show relationship.
- Beat ids, shot ids, object ids, or symbol ids are duplicated.
- Beat, camera, pacing, payoff, or anchor fields reference unknown ids.
- The packet has only generic object ids such as `obj_diagram`, `obj_concept`, `obj_primary_focus`, or `obj_scene`.
- The visual thesis is generic, such as "show the idea", "make it clear", or "visualize the math".
- More than half of beats are template-like, such as "intro", "middle", "final", "show concept", or "explain idea".
- Multiple scene classes are planned for one continuous conceptual thread without a domain shift, hard narrative reset, render/runtime reason, renderer/API reason, density reason, or state handoff.

Fix the packet before coding.

## 2. Prompt Preservation Gate

Before rewriting the user's request, extract a prompt object registry:

```markdown
### Prompt Object Registry
| id | source phrase | type | must survive? |
|----|---------------|------|---------------|
| obj_parabola | "parabola" | graph curve | yes |
| obj_tangent | "tangent line" | derived geometry | yes |
```

Then verify that prompt objects survive into public packet fields:

- `object_ledger`
- `symbol_ledger`
- `beat_contracts`
- `layout_motion_ir`
- `focus_baton`
- `payoff_frame`

Hard failures:

- The prompt asks for a graph/curve/axis/plot, but packet fields contain no graph evidence.
- The prompt asks for motion, transform, sweep, driver, or trajectory, but packet fields contain no motion or dependency evidence.
- The prompt asks for comparison, but packet fields contain no side-by-side, left/right lane, comparison panel, or versus evidence.
- The prompt asks for a physical story, but packet fields contain no force, path, trajectory, vehicle, terrain, or causal physical evidence.
- The prompt asks for multiple representations, but packet fields contain no fraction, decimal, percent, number-line, equivalence, or representation-link evidence.
- The prompt asks for geometry, but packet fields contain no diagram, construction, angle, circle, triangle, theorem, or geometric evidence.

If a prompt object is intentionally omitted, list it under `withheld_for_focus` with a reason.

## 3. Semantic Collapse Gate

Use `semantic_intent.must_not_reduce_to` to block common collapses:

- `equation-only narration`: graph/motion/multi-representation prompts must not become only formulas and captions.
- `caption-only physical explanation`: physical prompts must show physical objects and causal motion.
- `text-only equivalence statement`: multiple representations must be visible, linked, and held.
- `generic diagram`: concrete prompt objects must not become placeholders.

The final beat and `payoff_frame` must preserve the requested visual story. If the request is "show why a graph's slope becomes a derivative", the final payoff must include graph evidence and slope/derivative relationship evidence.

## 4. Layout Motion IR Gate

A codegen-ready `layout_motion_ir` should include:

- `zones`
- `zone_rects` or approximate lane bounds for dense layouts
- `anchors`
- `object_rails`
- `collision_extents` for cards, labels, nodes, overlays, and dense groups
- `fit_policy` with max zone size, fixed clearance gaps, scale floor, and split/park fallback
- `focal_hierarchy`
- `focus_baton` or `focus_path`
- `beat_actions`
- `motion_purpose`
- `timing_policy`
- `hold_policy`
- `camera_doctrine`
- `camera_plan`
- `continuity_rules`
- `clutter_caps`
- `reveal_order`
- `assertions` or quality checks
- `banned_shortcuts` or forbidden behaviors

Hard failures:

- A `within_lane(obj_id, zone_id)` assertion references an undeclared zone.
- A repeated focal object appears across beats without a persistent object rail.
- A dense scene has no explicit zones, no collision extents, or no fallback when the planned objects cannot fit.
- A plan handles overflow by saying "make it smaller" without max width, max height, scale floor, or split policy.
- A plan shrinks all buffers/gaps along with objects until elements visually merge.
- World/main-stage objects share space with captions, inspectors, formulas, or HUD overlays without a protected-lane rule.
- Clutter caps are exceeded by multiple primary focus targets, too many visible objects in a zone, or too many competing motions.
- Stable scaffold is declared but the plan requires full-board resets between adjacent beats without a semantic reset.
- Adjacent scenes continue the same idea but the first frame of the later scene does not recall, carry, transform, or park any prior state.
- A protected overlay is declared but there is no plan to keep it readable during camera or object motion.

## 5. Operator Gate

Default premium operators:

- `stable_scaffold_local_change`
- `attention_baton`
- `commit_hold_next`
- `layer_contract`
- `anti_noise_budget`

Each selected operator must have packet evidence:

- Required fields exist.
- Banned failure modes are guarded.
- Acceptance checks can be judged from code or rendered output.

Useful prompt-specific operators:

- Graph/function stories: `visual_to_formula_handoff`, `crosshair_io_readout`, `live_derived_geometry`, `matched_symbol_transform`.
- Simulations or physics: `clocked_dependency_system`, `endpoint_connector`, `history_layer`, `threshold_intervention`.
- Comparisons: `comparator_stage`, `dual_zone_board`, `parking_rail_memory`.
- Dense derivations: `slice_reveal`, `matched_symbol_transform`, `protected_overlay_panel`.
- Code, compiler, and algorithm explainers: `active_code_line_stage`, `diagram_state_crosslink`, `route_or_state_packet`.
- Transform, embedding, complex-map, or differential stories: `linked_dual_space_stage`, `representation_ladder`, `freeze_before_formalization`.
- Recursive, search, or state-space stories: `semantic_group_frame`, `overview_detail_restore_camera`, `parking_rail_memory`.
- Camera-led explanations: `overview_detail_restore_camera`, `protected_overlay_panel`.

Do not list an operator unless it changes the packet.

## 6. Camera And Pacing Gate

Camera rules:

- Static camera is the default.
- Every non-static move needs target, reason, teaching purpose, duration, and guardrails.
- Overview/detail/restore camera needs explicit save or restore intent.
- Do not leave the final payoff trapped in a close-up unless the close-up is the final proof.
- Do not request camera movement in a plain `Scene`; use `MovingCameraScene` or `ThreeDScene` when the API requires it.
- If the prompt asks for no camera movement, the camera plan must stay static.

Pacing rules:

- Every beat needs `play_seconds` and `hold_seconds`.
- Dense reveals need read holds.
- The final payoff hold should be the longest or clearly justified.
- Pacing should vary: setup measured, build quicker, pre-aha hold, payoff climax, recap hold.
- Avoid a metronomic sequence where every beat has identical timing.

## 7. Source Anchor Gate

Code should leave evidence that the packet was executed.

Portable marker style:

```python
# manim-skill:shot shot_id=shot_setup beat_id=beat_1
# manim-skill:element object_id=obj_axes
# manim-skill:symbol symbol_id=sym_x
# manim-skill:camera beat_id=beat_3 target_object_id=obj_tangent purpose="inspect slope locally"
# manim-skill:assert assertion="visible(obj_tangent)"
```

If using the original Text2Animation verifier, use the same fields with `# t2a:`:

```python
# t2a:shot shot_id=shot_setup beat_id=beat_1
# t2a:element object_id=obj_axes
# t2a:symbol symbol_id=sym_x
```

Also use `self.next_section("shot_setup")` when section markers help review.

Hard failures:

- Required shot id has no `next_section`, marker, or equivalent code evidence.
- Required object id has no marker, variable name, or rendered string evidence.
- Required symbol id has no marker, variable name, or rendered MathTex evidence.
- Unknown `next_section` values do not map to packet shot ids.

## 8. Direction Execution Gate

After draft code, check whether code actually executes the contract.

Hard failures:

- A beat contract has no matching section or source marker.
- A required focus/payoff id never appears in code.
- Camera plan requests motion but code does not use a camera-capable scene or camera-frame animation.
- Camera plan has a teaching purpose but code has no matching camera marker or visible camera move.
- Pacing plan has holds but code has too little `self.wait(...)` evidence.
- Pacing plan has play durations but code lacks `run_time=...` evidence on semantic animations.
- Payoff objects or payoff relationship have no final-frame evidence.
- Representation ladder declares a step but code never executes or marks it.
- Freeze-before-formalization is declared but code has no copy/snapshot/updater-clearing evidence.
- Symbol continuity requires carried terms but code does not use `TransformMatchingTex`, `TransformFromCopy`, or equivalent identity-preserving transform.
- Persistent object rails have no code evidence.
- Stable scaffold forbids full reset but code uses `self.clear()`, `self.remove(*self.mobjects)`, or `FadeOut(*self.mobjects)` as a full-board reset between semantic beats.

## 9. Beat Assertion Gate

Use compact assertions in beat contracts. Supported predicates:

| Predicate | Meaning |
|-----------|---------|
| `visible(obj_id)` | Required object is visible in the beat |
| `single_focal_winner(obj_id)` | One object owns attention |
| `no_dead_time()` | Beat has no idle filler |
| `above(a, b)` | Layout relation is intentional |
| `equal_length(a, b)` | Geometry relation is preserved |
| `no_overlap(a, b)` | Readability is protected |
| `alignment_locked(a, b)` | Objects remain aligned |
| `opacity_gating(obj_id)` | Inactive context is dimmed |
| `fade_except(obj_id)` | Only focus remains bright |
| `read_hold_after_landing(obj_id)` | Viewer gets time to read |
| `keep_baton_handoff(a, b)` | Focus handoff is explicit |
| `keep_color(sym_id, color)` | Symbol color remains consistent |
| `max_new_objects(n)` | Beat does not introduce too much |
| `keep_on_screen(obj_id)` | Object stays in frame |
| `preserve_term_id(sym_id, from_id, to_id)` | Symbol identity survives transform |
| `camera_contains(obj_id)` | Camera framing includes focus |
| `within_lane(obj_id, zone_id)` | Object stays in declared zone |

Every real camera move should imply `camera_contains(active_focus_id)`. Every beat should imply `single_focal_winner(active_focus_id)`.

Hard failures:

- Unknown predicate.
- Wrong number of arguments.
- Assertion references an id not in object or symbol ledger.
- `max_new_objects(n)` is exceeded.
- `within_lane` uses an undeclared zone or object rail.
- `keep_color` conflicts with symbol ledger.
- `preserve_term_id` references missing symbols or transform endpoints.

## 10. Visual Audit Gate

After rendering, use direct video review when available. If not, extract frames with `review-loop.md`.

Check these deterministic visual smells:

- **Sparse frame**: content occupies too little of the frame.
- **Underfilled frame**: the main idea feels tiny or unfinished.
- **No hero moment**: no frame has a strong, full, screenshot-worthy landing.
- **Near-empty frame**: key frames are almost blank.
- **Edge-content risk**: important text or geometry lives too close to the frame edge.
- **Merged elements**: objects technically fit but have collapsed whitespace, touching halos, or labels that visually fuse.
- **Low visual contrast**: foreground is hard to read against background.
- **Static clip**: there is almost no visible motion in a supposedly animated beat.
- **Long static hold**: the video holds too long without a pedagogical reason. Measure mechanically with the freezedetect scan in `review-loop.md`; judge hits against the retention contract in `attention-and-retention.md`.

These are signals, not automatic design truth. Use them to find the timestamp, then patch the relevant beat, zone, focus, or pacing field.

## 11. Review Acceptance Gate

Never accept code that was fixed after review until the fixed code has been rerendered and reviewed again.

Acceptance requires:

- The reviewed video or frames came from the current code.
- All blocking review issues are mapped to concrete fixes or explicitly rejected as non-actionable.
- The final payoff is visible, readable, and held.
- The last revision did not delete packet-required objects, anchors, holds, or payoff elements.
- Remaining issues are subjective preferences, not readability, semantic, or render correctness problems.

Bound the loop:

1. Review once for every non-trivial video.
2. Repair only concrete issues.
3. Review one more time after repair.
4. Stop unless the user asks for further polish.
