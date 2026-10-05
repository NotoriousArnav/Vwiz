# Paper Explainer Workflow

How to turn a research paper into an animated explainer video.

## Why animate a paper?

A research paper is optimized for precision and completeness. A video is optimized for understanding and retention. The translation is NOT "read the paper aloud with pictures" — it's "extract the core insight and make it feel obvious through visual storytelling."

The paper has one job: prove the claim is true. The video has a different job: make the viewer understand WHY the claim is true, and WHY it matters.

## Who is watching?

Before anything, decide the audience:

| Audience | Prerequisites | Pacing | Depth |
|----------|--------------|--------|-------|
| General public | None | Slow, many analogies | Intuition only, skip proofs |
| Undergrad students | Basic math/CS | Medium, some formalism | Key equations, skip derivations |
| Grad students / researchers | Domain knowledge | Faster, more notation | Full equations, sketch proofs |

This determines everything: vocabulary, pacing, which sections to animate, how much math to show.

## Paper grounding contract

Before narration, extract a short source ledger. Do not animate from the abstract alone unless the user only provided the abstract. Every factual claim in the video should trace back to a paper section, figure, table, equation, or quoted phrase in `plan.md`; keep those anchors in the plan or code comments, not necessarily on screen.

If the user attaches a PDF, do not rely on text extraction alone. Text extraction is useful for exact wording, equations, and citations, but it misses the visual intelligence in figures, plots, tables, layouts, screenshots, and architecture diagrams. When the agent or tool can inspect PDF pages visually, review the relevant pages as images before planning. When it cannot, convert key pages/figures to images with an available PDF/image tool or ask the user for screenshots of the important figures. If visual PDF review is unavailable, write that limitation in `plan.md` instead of pretending the figures were seen.

| Field | Question | Visual obligation |
|-------|----------|-------------------|
| `central_claim` | What is the one claim the paper wants believed? | Final payoff must make this claim visible |
| `problem_gap` | What failed or was missing before? | Hook/problem beat shows the failure concretely |
| `method_mechanism` | What actually changes in the method? | Animate the mechanism, not only a box diagram |
| `evidence_metric` | What result supports the claim? | Show metric name, baseline, scale, and delta |
| `baseline_or_comparison` | What is it compared against? | Keep comparison on shared visual scale |
| `scope_limit` | Where does the claim not apply? | Mention or visually bracket the limitation when it changes interpretation |

If a field is unavailable, write `unknown from provided source` instead of inventing it.

For PDF inputs, add a visual source ledger:

```markdown
### PDF Visual Ledger
| id | page/figure/table | what is visible | animation use | trust role |
|----|-------------------|-----------------|---------------|------------|
| fig_arch | Fig. 2 / page 4 | encoder-decoder blocks with skip path | method mechanism scaffold | inspiration + source anchor |
| table_main | Table 1 / page 7 | benchmark metric columns | shared-scale evidence chart | evidence source |
```

Use paper visuals as source-grounded inspiration, not as a screenshot dump. Rebuild them as clear Manim diagrams, charts, or mechanisms unless the user explicitly wants exact figure reproduction.

## The 5-minute template

Most paper explainers fit this structure (scale times proportionally for longer videos):

| Section | Duration | Purpose |
|---------|----------|---------|
| **Hook** | 0:00-0:30 | Surprising result or provocative question |
| **Problem** | 0:30-1:30 | What was broken/missing before this paper |
| **Key insight** | 1:30-3:00 | The core idea, explained visually |
| **How it works** | 3:00-4:00 | Method/algorithm, simplified |
| **Evidence** | 4:00-4:30 | Key result with baseline, scale, and scope |
| **Implications** | 4:30-5:00 | Why it matters, what it enables, what remains bounded |

### What to skip

- Related work survey → one sentence: "Previous approaches did X, which had problem Y"
- Implementation details → skip unless they're the contribution
- Ablation studies → show one chart at most
- Proofs → show the key step, not the full proof
- Hyperparameter tuning → skip entirely
- Limitations → do not skip if they change the central claim; compress to one scope guard

### What to expand

- The core insight → this gets the most screen time
- Geometric/visual intuition → if the paper has math, show what it MEANS
- Before/after comparison → the most compelling evidence

## Pre-code workflow

### Gate 0: Source ledger

Write this before the script:

```markdown
### Paper Claim Ledger
| id | paper anchor | paper wording / paraphrase | video claim | must show? |
|----|--------------|----------------------------|-------------|------------|
| claim_core | Abstract + Sec. 4 | smaller model wins when trained on more tokens | data quality/quantity beats naive scale | yes |

### Evidence Ledger
| id | paper anchor | metric | baseline | result | visual treatment |
|----|--------------|--------|----------|--------|------------------|
| ev_main | Table 2 | accuracy | baseline model | proposed method | shared-axis bar comparison |

### Scope Guard
- What the result does NOT prove:
- Assumptions / dataset / benchmark boundary:

### PDF Visual Ledger
| id | page/figure/table | what is visible | animation use | trust role |
|----|-------------------|-----------------|---------------|------------|
```

The video can be conversational, but the claims cannot float without anchors.

### Gate 1: Narration script

Write the full narration before any code. Every sentence maps to a visual beat. Every factual sentence about the paper maps to a claim or evidence id. If you can't write the narration, you don't understand the paper well enough to animate it.

```markdown
## Hook (30s)
"What if I told you that a model with 7 billion parameters can outperform
one with 70 billion — if you train it on the right data?"

## Problem (60s)
"The standard approach is to scale up. More parameters, more compute.
[VISUAL: bar chart showing model sizes growing exponentially]
[SOURCE: claim_gap, ev_scaling_trend]
But Chinchilla showed us that most models are undertrained..."
```

### Gate 2: Beat and scene architecture

After narration, break it into beats first. A beat is not automatically a Manim class. Prefer one continuous canvas when the hook, problem, insight, method, and evidence are one connected argument. Split into multiple classes only for a domain shift, hard reset, renderer/API reason, runtime isolation, or density failure, and define the state handoff.

```markdown
Beat 1: Hook — surprising stat with animated counter
Beat 2: Problem — model size bar chart grows until the undertraining gap appears
Beat 3: Key insight — training data vs parameters, animated 2D plot
Beat 4: Method — pipeline diagram builds left to right from the same data/model colors
Beat 5: Evidence — before/after comparison on shared scale
Beat 6: Closing — implication plus scope guard

Implementation: one `PaperExplainer` class unless the method/evidence section needs a split.
State handoff if split: obj_data_model_axes and color ledger persist into result comparison.
```

### Gate 2.5: Pattern stack

Before coding each complex beat or section, choose one stack from `source-backed-patterns.md`. Paper explainers usually need only two or three of these across the whole video:

| Paper section | Strong default pattern |
|---------------|------------------------|
| Key equation or loss | Dense Derivation Board |
| Method or architecture | Algorithm / Pipeline Flow |
| Input-output behavior | Function Machine / Multi-Representation |
| Training, simulation, or time evolution | Simulation Dashboard |
| Results and ablations | Before / After Evidence |
| Geometry, physics, or spatial intuition | 3D Reveal With Protected 2D Meaning |

Write the chosen pattern beside the beat or section name in `plan.md`. If no pattern fits, simplify the beat instead of inventing a complex custom structure.

### Gate 2.6: Paper director packet add-ons

For ambitious paper explainers, add these fields to the normal director packet:

- `paper_claim_ledger`: claim ids, paper anchors, video wording, and whether each claim must appear in the final payoff.
- `evidence_ledger`: metric, baseline, result, dataset/benchmark, uncertainty or scope note, and visual treatment.
- `method_mechanism_contract`: what visible object changes because of the method; avoid boxes with no mechanism.
- `result_scale_contract`: shared axis/range/unit, baseline visibility, delta calculation, and no cherry-picked visual scaling.
- `scope_limit_guard`: what the paper does not prove and whether that must be narrated or shown.
- `audience_translation`: which terms become analogies, which equations stay formal, and which details are withheld.
- `pdf_visual_ledger`: page/figure/table anchors, visible design cues, and whether each visual informs a chart, mechanism, analogy, or evidence beat.

### Gate 3: Style constants

Before coding scenes, define the visual language:

```python
# In single-file projects, put these at the top of script.py.
# Use an imported style.py only for multi-file projects.
BG = "#0D1117"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
HIGHLIGHT = "#FF6B6B"
DIM = "#6E7681"            # de-emphasized structure: connectors, scaffold strokes
MONO = "Noto Sans Mono"

# Color meanings for THIS paper
MODEL_COLOR = PRIMARY      # "the model"
DATA_COLOR = SECONDARY     # "training data"
BASELINE_COLOR = HIGHLIGHT # "previous approach"
RESULT_COLOR = ACCENT      # "our result"
```

## First-principles equation explanation

When the paper has a key equation, don't just show it — build it from intuition:

### The "what would you do?" pattern

1. Pose the problem in plain language
2. Ask what the simplest solution would be
3. Show why it doesn't work (animate the failure)
4. Introduce the paper's solution as the fix
5. Climb concrete visual -> readout -> symbol -> full equation

```python
# Scene: Why we need attention (for a Transformer paper)
# Step 1: "How do we let each word look at every other word?"
# Step 2: Show naive approach (fully connected = O(n²) everything)
# Step 3: Show it breaks (information overload, no selectivity)
# Step 4: "What if each word could CHOOSE which words to attend to?"
# Step 5: Show attention equation — Q, K, V now mean something
```

### Equation reveal strategy

For expert audiences, it can be useful to show the dimmed destination equation early. For general audiences, delay the full equation until the pieces have visual meaning.

```python
# Show equation dimmed first (full destination)
# substrings_to_isolate is required — set_color_by_tex on an unisolated
# single-string MathTex would color the WHOLE equation (see equations.md)
eq = MathTex(
    r"\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V",
    substrings_to_isolate=["Q", "K", "V"],
)
eq.set_opacity(0.15)
self.play(FadeIn(eq))

# Highlight Q, K, V one at a time with color + label
for part, color, label_text in [
    (r"Q", PRIMARY, "Query: what am I looking for?"),
    (r"K", SECONDARY, "Key: what do I contain?"),
    (r"V", ACCENT, "Value: what do I output?"),
]:
    eq.set_color_by_tex(part, color)
    label = Text(label_text, font_size=18, color=color, font=MONO)
    # position label, animate it, wait, then dim it
```

## Building architecture diagrams

### The progressive build pattern

Don't show the full architecture at once. Build it:

1. First component appears alone → explain
2. Arrow grows → "this feeds into..."
3. Second component appears → explain
4. Repeat until complete

```python
# Component factory
def make_box(label, color, width=2.0, height=0.8):
    box = RoundedRectangle(corner_radius=0.1, width=width, height=height,
                           color=color, fill_opacity=0.1, stroke_width=1.5)
    text = Text(label, font_size=18, font=MONO, color=color).move_to(box)
    return VGroup(box, text)

encoder = make_box("Encoder", PRIMARY)
decoder = make_box("Decoder", SECONDARY).next_to(encoder, RIGHT, buff=1.5)
arrow = Arrow(encoder.get_right(), decoder.get_left(), color=DIM, stroke_width=1.5)

self.play(FadeIn(encoder))
self.wait(1)  # explain encoder
self.play(GrowArrow(arrow))
self.play(FadeIn(decoder))
self.wait(1)  # explain decoder
```

### Data flow animation

After building the diagram, show data moving through it:

```python
# Dot traveling along the pipeline
data_dot = Dot(color=ACCENT, radius=0.1).move_to(encoder)
self.play(FadeIn(data_dot))
self.play(MoveAlongPath(data_dot, arrow), run_time=1)
self.play(data_dot.animate.move_to(decoder), run_time=0.5)
self.play(Flash(data_dot.get_center(), color=ACCENT), run_time=0.3)
```

## Animating results

### Bar chart comparison (most common)

Result charts must be honest before they are dramatic: use shared axes, show the metric/unit, keep baseline visible, and label the delta. If the paper reports uncertainty or benchmark scope, include it in a caption or scope note.

```python
# Before/after bars
before_data = [45, 52, 38, 61]
after_data = [78, 85, 72, 91]
labels = ["Task A", "Task B", "Task C", "Task D"]

before_chart = BarChart(before_data, bar_names=labels,
    y_range=[0, 100, 20], bar_colors=[HIGHLIGHT]*4).scale(0.6).shift(LEFT*3)
after_chart = BarChart(after_data, bar_names=labels,
    y_range=[0, 100, 20], bar_colors=[SECONDARY]*4).scale(0.6).shift(RIGHT*3)

before_label = Text("Baseline", font_size=20, color=HIGHLIGHT, font=MONO).next_to(before_chart, UP)
after_label = Text("Ours", font_size=20, color=SECONDARY, font=MONO).next_to(after_chart, UP)
metric_label = Text("Accuracy (%) on benchmark", font_size=18, color=WHITE, font=MONO).to_edge(DOWN)

# Reveal baseline first, then ours (dramatic comparison)
self.play(Create(before_chart), FadeIn(before_label), FadeIn(metric_label))
self.wait(1.5)
self.play(Create(after_chart), FadeIn(after_label))
self.wait(0.5)

# Highlight the improvement
improvement = Text("+35% avg", font_size=24, color=ACCENT, font=MONO)
improvement.next_to(VGroup(before_label, after_label), UP, buff=0.25)
self.play(Circumscribe(after_chart, color=ACCENT), FadeIn(improvement))
```

### Training curve (for ML papers)

```python
axes = Axes(
    x_range=[0, 10, 2], y_range=[0, 1, 0.2],
    x_length=7, y_length=4,
    axis_config={"include_numbers": True, "font_size": 20},
)
axes_labels = axes.get_axis_labels("epoch", "score")
tracker = ValueTracker(0)
curve = always_redraw(lambda: axes.plot(
    lambda x: 1 - 0.8 * np.exp(-x / 3),
    x_range=[0, max(0.001, tracker.get_value())], color=PRIMARY
))
epoch_label = always_redraw(lambda: Text(
    f"Epoch {int(tracker.get_value())}", font_size=18, font=MONO
).to_corner(UR))

self.add(axes, axes_labels, curve, epoch_label)
self.play(tracker.animate.set_value(10), run_time=5, rate_func=linear)
```

## Domain-specific patterns

### ML papers
- Show data flow through the model (animated pipeline)
- Training curves with `ValueTracker`
- Attention heatmaps as colored grids
- Embedding space as 2D scatter (PCA/t-SNE visualization)
- Loss landscape as 3D surface with gradient descent dot

### Physics/math papers
- Use `LinearTransformationScene` for linear algebra
- Vector fields with `ArrowVectorField` / `StreamLines`
- Phase spaces with `NumberPlane` + trajectories
- Wave equations with time-parameterized plots

### Systems/architecture papers
- Pipeline diagrams built progressively
- `ShowPassingFlash` for data flow along arrows
- `ZoomedScene` for zooming into components
- Before/after latency/throughput comparisons

## Common mistakes

1. **Trying to cover the whole paper.** A 5-minute video can explain ONE core insight well. Covering everything means explaining nothing.
2. **Reading the abstract as narration.** Academic writing is designed for readers, not listeners. Rewrite in conversational language.
3. **Showing notation without meaning.** Never show a symbol without first showing what it represents visually.
4. **Skipping the motivation.** Jumping straight to "here's our method" without showing why the problem matters. The Problem section is what makes the viewer care.
5. **Identical pacing throughout.** The hook and key insight need the most visual energy. The method section can be faster. Evidence should land with impact (pause after showing the big number).
6. **Overclaiming beyond the evidence.** Do not turn "works on this benchmark under these assumptions" into "solves the whole field."
7. **Result chart without shared scale.** Baseline and proposed method must share axes, units, and visual scale.
8. **Boxology without mechanism.** Architecture boxes are weak unless data, state, gradient, packet, or information visibly flows through them.
9. **Scene churn.** Do not split every paper section into a fresh class and clear the board; carry symbols, colors, axes, or comparison state forward.
10. **No scope guard.** A strong paper explainer earns trust by saying what the result does not prove.
