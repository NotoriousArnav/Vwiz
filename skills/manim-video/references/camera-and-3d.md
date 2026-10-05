# Camera and 3D Reference

## MovingCameraScene (2D Camera Control)

```python
class ZoomExample(MovingCameraScene):
    def construct(self):
        circle = Circle(radius=2, color=BLUE)
        self.play(Create(circle))
        # Zoom in
        self.play(self.camera.frame.animate.set(width=4).move_to(circle.get_top()), run_time=2)
        self.wait(2)
        # Zoom back out
        self.play(self.camera.frame.animate.set(width=14.222).move_to(ORIGIN), run_time=2)
```

### Camera Operations

```python
self.camera.frame.animate.set(width=6)     # zoom in
self.camera.frame.animate.set(width=20)    # zoom out
self.camera.frame.animate.move_to(target)  # pan
self.camera.frame.save_state()             # save
self.play(Restore(self.camera.frame))      # restore
```

### Save, Zoom, Follow, Restore

The core camera excursion: save the wide shot, punch in on the active object, optionally follow it, then restore so the viewer gets the whole map back.

```python
frame = self.camera.frame
frame.save_state()

focus = VGroup(active_object, active_label)  # frame semantic groups, not coordinates
self.play(frame.animate.move_to(focus).set(width=max(4.0, focus.width * 1.5)), run_time=1.5)
# ... local beat ...
frame.add_updater(lambda m: m.move_to(dot))       # follow while the actor travels
self.play(MoveAlongPath(dot, path), run_time=3, rate_func=linear)
frame.clear_updaters()                             # always clear before other frame moves
self.play(Restore(frame), run_time=1.5)
```

Rules: zoom only when semantic density rises, clear frame updaters before `Restore`, and never leave the payoff trapped in a close-up.

Avoid introducing new floating labels *while zoomed*. A zoomed region is dense by definition — that is why the camera went there — so a new tag usually crops at a frame edge or occludes the exact object being inspected. The highlight cue, the value change, and the subcaption already carry a zoomed beat; prefer them (anti-noise budget). If a zoom-time label is genuinely load-bearing:

- Place it against the camera frame's current bounds, never `config.frame_width` (a placement that fits the wide shot crops in the zoomed shot): `label.set_x(self.camera.frame.get_center()[0])` plus a y offset into verified open space.
- Keep it off the focus object's own line — occluding the thing being inspected is worse than no label.
- Backstroke it (`label.set_stroke(BLACK, 4, background=True)`) against any edge it crosses.

### Follow Camera With Scale Compensation

Aggressive zooms shrink stroke widths and markers into invisibility. Compensate from the frame height:

```python
h0 = frame.height
base_h = dot.height
frame.add_updater(lambda m: m.move_to(dot.get_center()))
path.add_updater(lambda m: m.set_stroke(width=6 * frame.height / h0))
dot.add_updater(lambda m: m.set_height(base_h * frame.height / h0))
```

The hero stays readable at any zoom level. Clear all three updaters when the excursion ends.

### Travel Between Prebuilt Boards

For multi-part explanations, prebuild boards side by side off-screen and move the camera across them instead of clearing and rebuilding. Continuity survives because the old board still exists — the camera is a navigator, not a reset button.

```python
board_a.move_to(ORIGIN)
board_b.move_to(RIGHT * 16)          # one frame-width apart
self.add(board_a, board_b)
# ... work on board_a ...
self.play(frame.animate.move_to(board_b), run_time=1.8)
# board_a remains alive; travel back any time or frame both for comparison
```

## ThreeDScene

```python
class ThreeDExample(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=60*DEGREES, theta=-45*DEGREES)
        axes = ThreeDAxes()
        surface = Surface(
            lambda u, v: axes.c2p(u, v, np.sin(u) * np.cos(v)),
            u_range=[-PI, PI], v_range=[-PI, PI], resolution=(30, 30)
        )
        surface.set_color_by_gradient(BLUE, GREEN, YELLOW)
        self.play(Create(axes), Create(surface))
        self.begin_ambient_camera_rotation(rate=0.2)
        self.wait(5)
        self.stop_ambient_camera_rotation()
```

### Camera Control in 3D

```python
self.set_camera_orientation(phi=70*DEGREES, theta=-45*DEGREES)
self.move_camera(phi=45*DEGREES, theta=30*DEGREES, run_time=2)
self.begin_ambient_camera_rotation(rate=0.2)
```

### 3D Mobjects

```python
sphere = Sphere(radius=1).set_color(BLUE).set_opacity(0.7)
cube = Cube(side_length=2, fill_color=GREEN, fill_opacity=0.5)
arrow = Arrow3D(start=ORIGIN, end=[2, 1, 1], color=RED)
# Fixed overlay text in a ThreeDScene camera move:
label = Text("Label", font_size=30)
self.add_fixed_in_frame_mobjects(label)
```

`add_fixed_in_frame_mobjects(...)` is a `ThreeDScene` method. In a plain `Scene` or `MovingCameraScene`, keep labels readable with stable `to_edge` / `to_corner` lanes instead of calling this method.

### Parametric Curves

```python
helix = ParametricFunction(
    lambda t: [np.cos(t), np.sin(t), t / (2*PI)],
    t_range=[0, 4*PI], color=YELLOW
)
```

## When to Use 3D
- Surfaces, vector fields, spatial geometry, 3D transforms
## When NOT to Use 3D
- 2D concepts, text-heavy scenes, flat data (bar charts, time series)

## ZoomedScene — Inset Zoom

Show a magnified inset of a detail while keeping the full view visible:

```python
class ZoomExample(ZoomedScene):
    def __init__(self, **kwargs):
        super().__init__(
            zoom_factor=0.3,           # how much of the scene the zoom box covers
            zoomed_display_height=3,   # size of the inset
            zoomed_display_width=3,
            zoomed_camera_frame_starting_position=ORIGIN,
            **kwargs
        )

    def construct(self):
        self.camera.background_color = BG
        # ... create your scene content ...

        # Activate the zoom
        self.activate_zooming()

        # Move the zoom frame to a point of interest
        self.play(self.zoomed_camera.frame.animate.move_to(detail_point))
        self.wait(2)

        # Deactivate
        self.play(self.get_zoomed_display_pop_out_animation(), rate_func=lambda t: smooth(1-t))
```

Use cases: zooming into a specific term in an equation, showing fine detail in a diagram, magnifying a region of a plot.

## LinearTransformationScene — Linear Algebra

Pre-built scene with basis vectors and grid for visualizing matrix transformations:

```python
class LinearTransformExample(LinearTransformationScene):
    def __init__(self, **kwargs):
        super().__init__(
            show_coordinates=True,
            show_basis_vectors=True,
            **kwargs
        )

    def construct(self):
        matrix = [[2, 1], [1, 1]]

        # Add a vector before applying the transform
        vector = self.get_vector([1, 2], color=YELLOW)
        self.add_vector(vector)

        # Apply the transformation — grid, basis vectors, and your vector all transform
        self.apply_matrix(matrix)
        self.wait(2)
```

This produces the signature 3Blue1Brown "Essence of Linear Algebra" look — grid lines deforming, basis vectors stretching, determinant visualized through area change.
