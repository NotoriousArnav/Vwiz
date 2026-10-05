# Algorithm Choreography: Logical Motion

How to animate algorithms and data structures so the motion itself carries the logic — elements swapping, pointers advancing, frontiers spreading, distances relaxing — instead of static pictures with captions. Patterns mined from Reducible, vivek3141, ManimSort, git-sim, and Dijkstra/NN explainer repos.

This is the premium layer for algorithm content: viewers pay attention when the data structure visibly *executes*, not when a diagram sits under narration.

## The Sync Law

Three rules govern every algorithm scene:

1. **One logical step = one `play()` call.** Never merge two algorithm steps into one animation, and never split one step across unrelated plays. The viewer's mental single-stepper must stay in lockstep with the visual.
2. **The state change and its cause animate together.** When an edge relaxes, the edge pulse and the distance label change ride in the same `play`. When a swap completes, the comparison highlight that caused it is still visible.
3. **Motion carries logic, captions confirm it.** If the motion were removed, the caption should not be able to explain the step alone. Swap = elements physically crossing; enqueue = the value flying from the node into the queue slot; recursion = the camera descending into a subproblem. If your plan says "highlight X and explain with text", redesign until the change is enacted.

## State→Style Contract

Declare the mapping from algorithm state to visual style once, at the top of the file, and never improvise per-scene. Derive variants from one hue per role (helpers in `visual-polish.md`):

```python
C_STRUCT = "#58C4DD"                       # the data structure itself
C_ACTIVE = "#FFFF00"                        # element(s) under consideration now
C_DONE = "#83C167"                          # processed / accepted / sorted
C_REJECT = "#FF6B6B"                        # discarded / failed comparison

STATE_STYLE = {
    "pending": dict(fill_opacity=0.5, stroke_opacity=0.6),   # not yet reached
    "active":  dict(fill_opacity=1.0, stroke_opacity=1.0),   # current focus
    "done":    dict(fill_opacity=0.8, stroke_opacity=0.4),   # settled, recedes slightly
}
```

The signature "current element" cue from Reducible is a soft glowing ring rather than a hard circle — concentric strokes with fading opacity:

```python
def glow_ring(target, color=C_ACTIVE, n=24, buff_max=0.18):
    r = max(target.width, target.height) / 2
    return VGroup(*[
        Circle(radius=r + buff_max * k / n, stroke_width=1.5,
               color=color, stroke_opacity=(1 - k / n) * 0.8)
        for k in range(n)
    ]).move_to(target)
```

## Arrays: The Two-Layer Index Model

The most reusable sync idiom in the corpus. Keep three things separate: the **logical list** (plain Python, mutated by the algorithm), the **value→box map** (resolves logical index to the box currently holding that value), and **labels bolted to boxes with updaters** (so values ride along automatically when boxes move).

```python
class ArrayBand(VGroup):
    def __init__(self, values, cell=0.9, **kwargs):
        super().__init__(**kwargs)
        self.values = list(values)                       # logical order, mutated on swap
        widest = MathTex(str(max(values)))
        self.boxes, self.box_of = [], {}
        for v in values:
            box = Square(cell).set_stroke(C_STRUCT, 2).set_fill(C_STRUCT, 0.15)
            label = MathTex(str(v)).move_to(box)
            label.add_updater(lambda m, b=box: m.move_to(b))   # label rides its box forever
            box.value_label = label
            self.boxes.append(box)
            self.box_of[v] = box                          # value -> box (values unique)
            self.add(box, label)
        VGroup(*self.boxes).arrange(RIGHT, buff=0.12)

    def box_at(self, i):                                  # logical index -> current box
        return self.box_of[self.values[i]]
```

Index labels, if shown, are a separate static row under the band — indices never move; contents do.

## Compare and Swap

**Compare** = transient promotion of exactly the two candidates: color + slight scale, verdict, restore. **Swap** = the three-phase lift-and-cross, so elements visibly travel over the array, not through it:

```python
def compare(self, scene, i, j):
    a, b = self.box_at(i), self.box_at(j)
    scene.play(a.animate.set_stroke(C_ACTIVE, 4).scale(1.05),
               b.animate.set_stroke(C_ACTIVE, 4).scale(1.05), run_time=0.4)
    scene.wait(0.3)                                       # verdict beat

def restore_pair(self, scene, i, j):                      # after a no-swap verdict
    a, b = self.box_at(i), self.box_at(j)
    scene.play(a.animate.set_stroke(C_STRUCT, 2).scale(1 / 1.05),
               b.animate.set_stroke(C_STRUCT, 2).scale(1 / 1.05), run_time=0.25)

def swap(self, scene, i, j, lift=1.2):
    a, b = self.box_at(i), self.box_at(j)
    pa, pb = a.get_center().copy(), b.get_center().copy()
    scene.play(a.animate.shift(UP * lift), b.animate.shift(UP * lift), run_time=0.4)
    scene.play(a.animate.move_to(pb), b.animate.move_to(pa), run_time=0.6)  # descend + cross
    scene.play(a.animate.set_stroke(C_STRUCT, 2).scale(1 / 1.05),
               b.animate.set_stroke(C_STRUCT, 2).scale(1 / 1.05), run_time=0.3)
    self.values[i], self.values[j] = self.values[j], self.values[i]   # keep logic in sync
```

(An equivalent single-`play` variant uses `path_arc=PI` on two `move_to` animations; the lift-and-cross reads more clearly at small cell sizes.) When an element reaches its final position, commit it: `box.animate.set_fill(C_DONE, 0.5)` — the sorted region grows visibly. Add a `Brace` under the settled region labeled "sorted" and widen it as the invariant grows: the invariant strip is the algorithm's promise made visible.

## Pointers and Cursors

A pointer is one persistent marker that *travels* — never delete and respawn it:

```python
ptr = Triangle(color=C_ACTIVE, fill_opacity=1).scale(0.15).rotate(PI)
ptr.next_to(band.box_at(0), UP, buff=0.15)
self.play(ptr.animate.next_to(band.box_at(k), UP, buff=0.15), run_time=0.5)
```

Two-pointer algorithms get two markers with distinct colors above/below the band. The marker's journey is the loop variable's story; when the loop ends, fade the marker with the loop's conclusion, not silently.

## Values Flying Between Structures

When a datum moves between structures (node → queue, queue → variable, list → output), animate the value traveling as a copy while the source stays put:

```python
# enqueue: slot grows, value flies from graph node into it
slot = Square(0.6).set_stroke(C_STRUCT, 2).next_to(prev_slot, RIGHT, buff=0)
val = node_label.copy()
self.play(GrowFromCenter(slot), TransformFromCopy(node_label, val.move_to(slot)))

# dequeue: head value becomes the loop variable
self.play(FadeOut(slot), ReplacementTransform(val, var_box_value))
```

This one idiom — `TransformFromCopy` along a visible path between structures — is what makes multi-structure algorithms (BFS queue + graph, heap + tree, stack + recursion) legible as a single system.

## Graphs: Wired, Not Drawn

For quick layouts use the built-in `Graph` (`graphs-and-data.md`). For choreography, build nodes and edges yourself so every part is addressable:

- **Nodes**: `VGroup(Circle, label)`, stored in a dict by vertex id.
- **Edges**: stored in a dict keyed by `(u, v)`, with endpoints trimmed to the circle boundary so lines never pierce nodes:

```python
def make_edge(n_u, n_v, stroke=2, color=GREY_B):
    u, v = n_u.get_center(), n_v.get_center()
    unit = (v - u) / np.linalg.norm(v - u)
    r_u, r_v = n_u.width / 2, n_v.width / 2
    return Line(u + unit * r_u, v - unit * r_v, stroke_width=stroke, color=color)
```

- **Glue edges to nodes with an updater** when nodes will move, so the topology survives any animation:

```python
def unit_towards(a, b):
    d = b.get_center() - a.get_center()
    return d / np.linalg.norm(d)

edge.add_updater(lambda m, a=n_u, b=n_v: m.put_start_and_end_on(
    a.get_center() + unit_towards(a, b) * a.width / 2,
    b.get_center() - unit_towards(a, b) * b.width / 2))
```

Edge labels live at `edge.point_from_proportion(0.2-0.5)` and get the same updater treatment.

## Traversal Choreography

The visit grammar (BFS/DFS/any frontier algorithm), each element one `play`:

1. **Consider**: pulse all neighbors of the expanded node — `self.play(*[Indicate(nodes[w], scale_factor=1.15) for w in nbrs], run_time=0.6)`. This is the visible "look at all adjacent" step.
2. **Visit**: grow a state ring on the chosen node — `self.play(Create(glow_ring(nodes[v], C_DONE)))`.
3. **Traverse**: overlay a thick colored line on the edge, created *in the direction of travel* (start = from-node, end = to-node), so the motion runs along the edge the way the algorithm moved:

```python
sharpie = Line(edge.get_start(), edge.get_end(), stroke_width=5, color=C_DONE)
self.play(Create(sharpie), run_time=0.6)
```

4. **Record**: fly the node's label into a visit-order rail at the frame edge — `TransformFromCopy(nodes[v][1], order_rail[k])`. The output sequence assembles itself from the graph.

The frontier/visited/unvisited states use the STATE_STYLE contract — the spreading wavefront of `done` styling *is* the algorithm.

## Relaxation and Rewiring

**Distance relaxation (Dijkstra, Bellman-Ford)**: distances are `ValueTracker`-backed `DecimalNumber`s so a relaxed value visibly counts down, in the same `play` as the edge pulse that caused it:

```python
tracker = ValueTracker(999)                    # 999 stands in for "infinity" until first relaxation
dist = DecimalNumber(999, num_decimal_places=0).next_to(nodes[v], UP)
dist.add_updater(lambda m: m.set_value(tracker.get_value()))
self.play(
    ShowPassingFlash(edge.copy().set_stroke(C_ACTIVE, 6), time_width=0.6),
    tracker.animate.set_value(new_dist),
    run_time=0.9,
)
```

For the *first* assignment (∞ label transforming into a number), attach the updater only **after** the entrance play — transforming into a mobject whose updater rebuilds it every frame crashes mid-interpolation (`troubleshooting.md`):

```python
tracker.set_value(first_dist)
dist.set_value(first_dist)                     # static for the entrance
self.play(pulse, ReplacementTransform(inf_label, dist), run_time=0.9)
dist.add_updater(lambda m: m.set_value(tracker.get_value()))   # live from now on
```

**Structural rewiring (2-opt, rotations, re-parenting)**: morph old structure into new with `ReplacementTransform(old_edges, new_edges)` — the uncrossing/rebalancing *is* the logic — and transform the cost/metric readout in the same `play` so the number improves exactly as the structure changes.

**Crowd dynamics (random walks, particles, agents)**: batch the per-destination moves and play them as parallel `LaggedStart`s so inflows stagger naturally:

```python
self.play(*[LaggedStart(*moves_to[state], lag_ratio=0.1) for state in states], run_time=1.5)
```

## Synced Pseudocode Panel

The reference pattern: a code panel in its own lane, and a single arrow that `Transform`s from line to line **in real execution order**, interleaved with the data-structure animations. The viewer sees the program counter, the data structure, and the effect simultaneously.

```python
code = Code(
    code_string="""while queue:
    v = queue.pop(0)
    for w in adj[v]:
        if w not in seen:
            seen.add(w)
            queue.append(w)""",
    language="python", background="rectangle", add_line_numbers=False,
    paragraph_config={"font": "Noto Sans Mono", "font_size": 20},
).to_edge(RIGHT, buff=0.6)

arrow = Arrow(ORIGIN, RIGHT * 0.5, color=C_ACTIVE, buff=0)  # buff=0: default buff would collapse a short arrow
arrow.next_to(code.code_lines[0], LEFT, buff=0.2)

def point_at_line(scene, arrow, code, k, run_time=0.4):
    target = arrow.copy().next_to(code.code_lines[k], LEFT, buff=0.2)
    scene.play(Transform(arrow, target), run_time=run_time)
```

Then drive it in execution order, pairing each pointer move with the data animation it causes: `point_at_line(self, arrow, code, 1)` → dequeue animation; `point_at_line(self, arrow, code, 4)` → node ring + enqueue flight. Never highlight lines in top-to-bottom document order — the jumping of the arrow through loops is what teaches control flow. (`Code.code_lines` is indexable per line in Manim CE ≥ 0.19; a `SurroundingRectangle` sliding between lines works as an alternative cursor.)

## Recursion: The Call-Stack Rail

Recursion needs visible memory of suspended callers:

1. On each call, shrink the caller's state (`scale(0.4)`) and push it onto a stack rail at the frame edge — the parked copies stack downward like real frames.
2. Zoom or move the camera into the subproblem (`camera-and-3d.md` save/zoom/restore).
3. On return, fly the return value from the subproblem back to the top parked frame, pop it (restore scale/position), and continue.

The rail's height *is* the recursion depth; base cases are the beats where the rail stops growing. For divide-and-conquer, `xiaoxiae`-style semantic zoom into one subtree while siblings dim to 0.3 keeps the whole structure in view.

## ML and Neural Networks

- **Build the network in data-flow order**: `TransformFromCopy(input_image, layer0)`, then per layer: `Write(edge_group)` (sent behind with `set_z_index`), then `Write(next_layer)`. The network assembles the way information flows.
- **Forward pass = fill opacity**: activations map to `neuron.set_fill(WHITE, opacity=activation)` layer by layer — a visible wave of light. Store `edges_in` / `edges_out` per neuron when building, so per-neuron propagation pulses (`ShowPassingFlash` on edge copies) are addressable later.
- **The signature move — space warping under the learned function**: subdivide the grid first so bends are smooth, then apply the real function to the whole plane while the data points ride along:

```python
plane.prepare_for_nonlinear_transform()
self.play(
    plane.animate.apply_function(lambda p: model_forward(p)),   # the actual mapping
    Transform(dots, transformed_dots),
    run_time=6,
)
```

Compute `transformed_dots` from the same function — never hand-pose "roughly warped" positions. Correct-by-construction: the animation cannot lie because it runs the real math (the same principle as computing real outputs for any algorithm scene — run the algorithm in plain Python, record the step trace, then choreograph the trace).

## Scene Organization for Long Algorithm Videos

Put all build/highlight/step methods on one utility base scene and subclass it per section — algorithm logic lives once, each `construct` just sequences steps with narration waits:

```python
class SortAnimationUtils(Scene):
    def make_band(self, values): ...
    def compare(self, band, i, j): ...
    def swap(self, band, i, j): ...
    def commit_sorted(self, band, i): ...

class BubbleSortIntro(SortAnimationUtils): ...
class BubbleSortWorstCase(SortAnimationUtils): ...
```

Drive the choreography from a **step trace**: run the real algorithm first, record `("compare", i, j)`, `("swap", i, j)`, `("commit", i)` events, then loop over the trace emitting one `play` per event. This guarantees the animation matches the algorithm exactly, makes retiming trivial, and lets you accelerate later passes (first pass full speed, later passes `run_time * 0.4` per `attention-and-retention.md`).

## Anti-Patterns

- Teleporting elements: any position change without visible travel breaks the physical metaphor.
- Labels drifting from their boxes: always updater-bind value labels to their containers.
- Rebuilding the whole structure each step instead of moving the changed elements.
- Two logical steps in one `play`, or one step smeared across several unrelated plays.
- Highlight order following the source text (top to bottom) instead of execution order.
- Showing a final state without animating the step that caused it (the "and then it's sorted" jump).
- Distances/costs that jump as rebuilt `Text` instead of counting via `DecimalNumber` + tracker.
- A pseudocode panel that exists but never gets pointed at during the run.
- Hand-posed "approximately correct" results instead of running the real algorithm for the trace.
