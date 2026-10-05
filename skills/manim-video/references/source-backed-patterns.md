# Source-Backed Manim Patterns

Use this after `cinematic-directing.md` when the scene needs to feel alive, technical, and carefully directed. This file is a pattern selector, not another API catalog.

The strongest Manim scenes usually do not come from many effects. They come from a small stack of choices:

- one stable scaffold
- one active driver
- one live dependency layer
- one protected inspector or explanation lane
- one attention gate
- one continuity transform
- one memory rail when previous context matters
- one readable landing

Choose the closest pattern stack below before coding. Do not combine every pattern in one scene.

## Pattern Atlas Defaults

For number-heavy, proof-heavy, graph-heavy, or compiler/algorithm scenes, start with this minimum stack:

1. Stable scaffold: `Axes`, `NumberLine`, table, matrix board, pipeline graph, derivation stack, or state map.
2. Driver state: one `ValueTracker`, simulation clock, routed packet, active code line, or focused proof row.
3. Live dependency layer: probe, connector, readout, brace, trace, active edge, or formula slot tied to the driver.
4. Protected inspector: stable `DecimalNumber`, status strip, active invariant, formula lane, or code/math sidecar.
5. Attention gate: dim, spotlight, brace, underline, focus cue, or active-line highlight.
6. Continuity transform: `TransformMatchingTex`, `TransformFromCopy`, local replacement, or stable side-by-side comparison.
7. Read hold: a deliberate pause after each semantic landing.

Decide these before coding:

- precision policy for numeric values
- exact vs approximate display policy
- semantic color map
- memory rail or parked-context policy
- final hero frame

If a scene feels weak, repair in this order: stabilize the scaffold, reduce competing active objects, create one driver, attach labels/readouts to live objects, delay formulas until the visual dependency is clear, justify or remove camera motion, then park old context instead of deleting it.

## Strategy Budget

For an advanced scene, choose a small stack before writing code:

- one primary camera strategy, usually static or overview/detail/restore
- one live dependency strategy, usually a single tracker, clock, packet, or active proof row
- one attention strategy, such as opacity gating, spotlight, active-line highlight, or baton handoff
- one representation strategy, such as visual-to-formula, dual-space, comparison lanes, or approximation ladder
- one conclusion strategy, such as sealed theorem, metric landing, route replay, or hero frame

Do not add 3D, follow-camera, dashboard, dual-space, history, and dense derivation patterns to the same scene unless the director packet names why each one is load-bearing.

## Repeated High-Signal Primitives

Mature Manim projects repeatedly lean on these primitives:

- `LaggedStart` / `AnimationGroup` for choreographed staging
- `ValueTracker`, `always_redraw`, and `add_updater` for live dependencies
- `SurroundingRectangle`, `Brace`, `Indicate`, `Circumscribe`, and dimming for attention control
- `save_state()` / `Restore(...)` for visual memory and camera/object returns
- `self.camera.frame` for semantic inspection, not decorative zoom
- `TransformMatchingTex` and `TransformFromCopy` for preserving identity
- `MoveAlongPath`, `ShowPassingFlash`, and `TracedPath` for routes and history
- `add_fixed_in_frame_mobjects(...)` for protected HUD/caption layers in `ThreeDScene` camera moves

These primitives are only valuable when attached to a clear beat.

## Pattern 1: Live Derivative / Rate

Use for slopes, gradients, marginal change, sensitivity, limits, and "what happens as dx shrinks?"

Stack:

1. Stable graph or number plane.
2. `ValueTracker` for `x` and optionally `dx`.
3. `always_redraw` secant/tangent line, moving points, braces, and labels.
4. Camera inspects the local geometry only after the full graph is established.
5. Freeze the moving geometry, then formalize with `TransformMatchingTex`.
6. Land the final derivative/rate in a sealed result box.

Do:

- let the viewer watch the geometry become the equation
- keep `dx`, rise, run, and slope labels alive during the motion
- hold after the tangent/result appears

Avoid:

- opening with the final formula
- moving labels manually when they should follow the points

## Pattern 2: Function Machine / Multi-Representation

Use for functions, transforms, embeddings, encoders, mappings, and input-output reasoning.

Stack:

1. Left lane: input object or sample.
2. Center lane: machine, graph, transformation, or model.
3. Right lane: output object, prediction, or transformed representation.
4. Active packet/dot moves through the system.
5. Synchronized formula/inspector lane updates with the packet.
6. Final state compares input and output side by side.

Do:

- keep all lanes stable
- use color to preserve identity across representations
- transform copied pieces into notation only after the visual example is clear

Avoid:

- rebuilding the whole layout for each input
- showing a black-box model without visible data flow

## Pattern 3: Dense Derivation Board

Use for algebra-heavy proofs, optimization objectives, probability identities, and symbolic reductions.

Stack:

1. Alignment-locked equation stack.
2. Memory rail for previous conclusions.
3. One active row at full opacity, older rows dimmed.
4. `TransformMatchingTex` for conserved symbols.
5. `SurroundingRectangle`, underline, or brace marks the reason for the step.
6. Final theorem/result gets isolated and held.

Do:

- preserve symbol identity whenever possible
- name the reason for each major transformation
- use short captions instead of dense paragraphs

Avoid:

- writing unrelated equations from scratch
- letting old rows compete with the active step

## Pattern 4: Simulation Dashboard

Use for SIR models, optimization runs, training curves, queueing systems, cellular automata, agent movement, and time evolution.

Stack:

1. One clock `ValueTracker` or simulation step variable.
2. Main world area updates from the clock.
3. Side dashboard shows live counters, phase, loss, error, or status.
4. History graph samples the run over time.
5. Threshold/intervention events are staged as semantic beats.
6. Final dashboard freezes with the key metric highlighted.

Do:

- make all readouts depend on the same clock
- separate world, dashboard, and caption zones
- show a visible intervention or threshold crossing, not just the final number

Avoid:

- independent animations that drift out of sync
- counters changing without a visible cause

## Pattern 5: Algorithm / Pipeline Flow

Use for algorithms, compiler stages, distributed systems, neural network blocks, data pipelines, and architecture diagrams.

Stack:

1. Stable node/box topology.
2. Arrows or paths laid down before traffic starts.
3. Packets/tokens route with `MoveAlongPath`.
4. `ShowPassingFlash`, highlighted edges, or active code-line highlight shows the current operation.
5. Inspector lane reports current operation, invariant, bottleneck, state, or compiler artifact.
6. Code/math sidecar cross-links the active line to the visible diagram state when code is part of the explanation.
7. Final route or comparison is visible at the landing.

Do:

- establish topology first, then animate flow
- make each packet mean something with color or label
- spotlight bottlenecks and invariants
- keep code, state, and diagram in one stable stage when all three matter

Avoid:

- hiding the graph while a packet moves
- moving many unrelated packets without an active focus
- showing code as decoration with no live diagram effect

## Pattern 6: Before / After Evidence

Use for model improvements, optimization gains, baselines vs new methods, proofs by counterexample, and product/architecture comparisons.

Stack:

1. Two stable panels or one shared axis.
2. Baseline appears first and earns context.
3. New method appears second with matching scale.
4. Difference is measured with brace, delta label, counter, or highlighted area.
5. Camera/focus moves to the evidence, then restores.
6. Result lands as one readable metric or claim.

Do:

- keep scales honest and shared
- preserve both states in memory
- show the delta, not just two finished pictures

Avoid:

- swapping scenes so the viewer must remember the baseline
- using different axes or visual scales for comparison

## Pattern 7: Proof by Rearrangement

Use for geometry proofs, area arguments, combinatorics, identities, invariants, and "same object, new arrangement" explanations.

Stack:

1. Start with pieces in a concrete visual configuration.
2. Label pieces before they move.
3. Move, rotate, split, or regroup while preserving color identity.
4. Use ghost outlines or previous-state dimming when needed.
5. Transform the final arrangement into the symbolic identity.
6. Seal the equality or invariant after the visual proof.

Do:

- let the rearrangement be the proof
- keep colors and labels stable
- use `TransformFromCopy` when a piece becomes part of an equation

Avoid:

- explaining the identity before the viewer sees the conservation
- changing colors when object identity matters

## Pattern 8: 3D Reveal With Protected 2D Meaning

Use for surfaces, rotations, geometry in space, vector fields, manifolds, and physical mechanisms.

Stack:

1. Establish the idea in a readable 2D or cross-section view.
2. Add a fixed HUD/caption/inspector before moving the camera.
3. Tilt or rotate only when it reveals hidden structure.
4. Use labels sparingly and keep them readable.
5. Return to a simple view before the final conclusion.

Do:

- use `ThreeDScene.add_fixed_in_frame_mobjects(...)` for HUD elements during 3D camera moves
- keep camera moves short and motivated
- show why 3D was necessary

Avoid:

- rotating continuously as decoration
- placing essential text in world space where it becomes unreadable

## Pattern 9: Dual-Space / Local Differential

Use for complex maps, embeddings, transforms, local linearization, Jacobians, sensitivity, and "input space -> output space" explanations.

Stack:

1. Two stable spaces or panels with matching scale language.
2. One driver controls the input probe and output probe together.
3. Local neighborhood, tiny vector, or differential box appears around the input.
4. The corresponding output response is shown in lockstep.
5. Visual pieces transform into notation only after the coupling is visible.
6. Final condition, matrix, derivative, or invariant is sealed and held.

Do:

- move input and output probes in the same `self.play(...)`
- use color identity across spaces and formulas
- freeze local geometry before converting it to a matrix or equation

Avoid:

- animating one space while the other waits passively
- jumping directly to a Jacobian, derivative, or condition without the local visual witness

## Pattern 10: Recursive / State-Space Zoom

Use for recursion, search trees, dynamic programming, graph traversal, state machines, compiler IR passes, and large proof/state maps.

Stack:

1. Establish the full map or state lattice.
2. Frame one semantic cluster, subtree, row, or state group.
3. Perform local work inside the cluster.
4. Park or dim the local conclusion in a memory rail.
5. Restore or travel to the sibling/next cluster.
6. Final frame shows the path through the state space, not only the last state.

Do:

- use overview -> detail -> restore/travel
- frame semantic groups, not arbitrary coordinates
- keep a visible breadcrumb or memory rail for visited states

Avoid:

- zooming until the viewer loses the parent map
- deleting the previous state before the next state has inherited its meaning

## Selection Table

| User request sounds like... | Start with this pattern |
|-----------------------------|-------------------------|
| "show why slope/gradient/limit works" | Live Derivative / Rate |
| "map input to output" | Function Machine / Multi-Representation |
| "derive/prove this equation" | Dense Derivation Board |
| "simulate over time" | Simulation Dashboard |
| "visualize this algorithm/system/compiler/model" | Algorithm / Pipeline Flow |
| "show improvement over baseline" | Before / After Evidence |
| "prove by moving pieces" | Proof by Rearrangement |
| "explain a spatial object" | 3D Reveal With Protected 2D Meaning |
| "show input/output spaces, local derivative, Jacobian, transform, embedding" | Dual-Space / Local Differential |
| "show recursion, graph traversal, state space, compiler IR passes" | Recursive / State-Space Zoom |

## Anti-Selection Rules

- If the user asks for clarity, choose the simplest stack that can reveal the mechanism.
- If a single static diagram would teach better, do not force motion.
- If the scene has no live dependency, do not add updaters just for sophistication.
- If the camera move does not answer "why this focus now?", remove it.
- If the viewer must remember too much offscreen context, preserve it in a rail or side-by-side panel.
- If the final frame is not screenshot-worthy, redesign the landing before adding more animation.
