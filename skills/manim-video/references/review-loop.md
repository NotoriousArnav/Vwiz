# Review Loop

Use this after a draft render or stitched video exists. The goal is not endless polishing. The goal is one or two targeted feedback passes that catch visual, timing, readability, and pedagogy problems before the final render.

Default loop budget:

1. Run one review pass for every non-trivial video.
2. Run a second pass only if the first pass found concrete issues.
3. Accept only after the latest code has been rerendered and reviewed.
4. Stop after the second pass unless the user explicitly asks for more iteration.

## Review Modes

### Mode A: Direct Video Review

Use this when the agent, model, or tool can inspect the rendered `.mp4` directly.

Ask for a strict review:

```markdown
Review `outputs/final.mp4` or `final.mp4` as an educational Manim animation.
Return PASS or REVISE.
If REVISE, list at most 5 issues with timestamp, severity, why it hurts understanding, and the exact code-level fix.
Prioritize readability, pacing, attention focus, object overlap, camera framing, motion that feels purposeful/alive, and whether the final landing feels earned.
Do not request subjective polish unless it clearly improves understanding.
```

Accept only actionable feedback. Ignore vague comments like "make it more dynamic" unless they name a specific beat, object, or timestamp.

### Mode B: Frame Fallback

Use this when the model cannot inspect video directly. Extract representative frames with the ffmpeg wrapper, then review those images.

The ffmpeg wrapper runs inside Docker, but outputs are written into the mounted project directory. That means `review-frames/` appears beside the user's Manim project files, not only inside the container. These files are temporary and should be cleared before each extraction and deleted after review unless the user asks to keep them.

Prefer semantic sampling over blind sampling when a director packet or beat list exists. Include frames from the hook, each dense reveal, each camera extreme, each comparison/evidence landing, and the final payoff. Blind interval sampling is acceptable as a fallback, but it can miss the exact moment where a camera crop, overlap, or rushed reveal breaks understanding.

The examples assume the final stitched video is `outputs/final.mp4`. If the project intentionally wrote the final video elsewhere, replace that input path only; keep review frames in `review-frames/` and do not use hidden tool/cache folders for review output.

macOS, Linux, WSL, or Git Bash:

```bash
rm -rf review-frames
mkdir -p review-frames
/path/to/manim-video/scripts/ffmpeg.sh -y -i outputs/final.mp4 -vf "fps=1/2,scale=1280:-1" review-frames/frame_%04d.jpg
/path/to/manim-video/scripts/ffmpeg.sh -y -framerate 1 -pattern_type glob -i "review-frames/frame_*.jpg" -vf "scale=320:-1,tile=4x3" review-frames/contact_sheet.jpg
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force review-frames -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force review-frames
& "C:\path\to\manim-video\scripts\ffmpeg.ps1" -y -i outputs/final.mp4 -vf "fps=1/2,scale=1280:-1" review-frames/frame_%04d.jpg
& "C:\path\to\manim-video\scripts\ffmpeg.ps1" -y -framerate 1 -pattern_type glob -i "review-frames/frame_*.jpg" -vf "scale=320:-1,tile=4x3" review-frames/contact_sheet.jpg
```

If glob input is unavailable in the local ffmpeg build, review the numbered frames directly instead of creating a contact sheet.

For longer videos, extract fewer frames:

```bash
/path/to/manim-video/scripts/ffmpeg.sh -y -i outputs/final.mp4 -vf "fps=1/5,scale=1280:-1" review-frames/frame_%04d.jpg
```

Review prompt for extracted frames:

```markdown
Review `review-frames/contact_sheet.jpg` and any relevant individual frames.
Return PASS or REVISE.
If REVISE, list at most 5 issues with frame number, severity, why it hurts understanding, and the exact code-level fix.
Focus on text overlap, tiny labels, crowded frames, weak focal hierarchy, inconsistent colors, bad camera crop, missing final landing, and scenes that look static or slide-like.
```

Frame review cannot judge motion quality perfectly. If the frames pass but the video may still feel rushed, inspect timestamps around dense beats, camera moves, and live-driver moments, or ask a video-capable model/user to review the `.mp4`.

Clean up temporary frames after the final review pass. Do this before the final answer unless the user explicitly asked to keep review evidence:

macOS, Linux, WSL, or Git Bash:

```bash
rm -rf review-frames
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force review-frames
```

## Deterministic Motion Audit

Before any frame review, measure dead air mechanically. `freezedetect` reports every span where the video is completely static:

macOS, Linux, WSL, or Git Bash:

```bash
/path/to/manim-video/scripts/ffmpeg.sh -hide_banner -i outputs/final.mp4 \
  -vf "freezedetect=n=0.0005:d=3" -map 0:v:0 -f null - 2>&1 | grep freeze
```

Windows PowerShell:

```powershell
& "C:\path\to\manim-video\scripts\ffmpeg.ps1" -hide_banner -i outputs/final.mp4 `
  -vf "freezedetect=n=0.0005:d=3" -map 0:v:0 -f null - 2>&1 | Select-String freeze
```

Each hit prints `freeze_start`, `freeze_duration`, and `freeze_end` timestamps.

Judge the hits against the retention contract in `attention-and-retention.md`:

- A static span of `3-4s` is fine only when it is a declared read hold after a dense landing, proof gate, or payoff.
- A static span over `~4s` with no narration doing the work is dead air. Fix it: shorten the hold, or keep one quiet live element (counter, trace, gentle driver) running during it.
- Many hits close together mean the scene is a slide deck with transitions. Fix pacing at the beat level, not by trimming individual waits.
- Zero hits on a long video can also be a smell: constant motion with no read holds. Check that landings still get their pause.

## Deterministic Visual Audit

After the motion audit, scan for objective visual smells. These checks can be done by watching the video, reviewing extracted frames, or using ffmpeg-generated contact sheets.

Flag concrete issues:

- **Sparse or underfilled frame**: the main visual occupies too little screen area.
- **Near-empty frame**: important sampled frames are almost blank.
- **No hero frame**: no final or climax frame feels screenshot-worthy.
- **Edge-content risk**: important text, labels, formulas, or objects sit too close to the frame boundary.
- **Low contrast**: active foreground does not separate from background.
- **Static clip**: a supposedly dynamic beat has almost no visible motion.
- **Long static hold**: the video holds without a pedagogical reason.
- **Crowded focal layer**: more than one object appears to own attention.

Map every issue to a packet field when a director packet exists: beat, focus, camera, pacing, zone, object rail, overlay, assertion, or payoff. Then patch the smallest field or code block that fixes it.

## Semantic Critic Pass

After the deterministic visual audit, run a short semantic pass. This is not for taste polishing; it catches scenes that look clean but still teach weakly.

Flag concrete issues:

- **No organizing insight**: the video feels like a topic tour instead of one memorable claim.
- **Weak opening tension**: the first 15-30 seconds do not show a concrete problem, failure, surprise, or question.
- **Abstract before concrete**: notation or text arrives before the viewer has visual evidence.
- **Non-load-bearing motion**: an animation moves but does not reveal dependency, attention, state, comparison, or proof.
- **Color drift**: a color changes meaning across scenes or symbols.
- **Unresolved misconception**: the likely wrong takeaway is not blocked by a visual counterexample, comparison, or note.
- **Payoff mismatch**: the final frame does not visibly answer the opening promise.

Patch these through the director packet first when one exists. Good fixes are usually a stronger hook beat, a visual-before-formula handoff, a clearer focus baton, a parked memory rail, or a more explicit final hero frame.

For premium or "world-class" requests, mark PASS only when the review can point to a clear hook, purposeful camera or stillness, readable semantic landings, and at least one memorable final or climax frame. Do not keep iterating for vague taste. Do keep iterating within the loop budget when the render is static, cramped, confusing, off-camera, visually merged, or missing the promised mechanism.

## Revision Rules

When feedback says REVISE:

1. Map the issue to the director packet when one exists: beat, focus, camera, pacing, zone, object rail, or payoff.
2. Fix only concrete issues tied to timestamps, frames, objects, labels, or beats.
3. Preserve the packet's beat order, focus winners, camera plan, pacing plan, object ids, symbol ids, and payoff frame.
4. Re-render the smallest affected scene first at `-ql` or `-qm`.
5. Re-stitch only after affected scenes pass.
6. Run one more review pass.
7. Do not accept the fixed code until the rerendered output has been reviewed.
8. Stop when feedback is PASS or only subjective preferences remain.

Do not rewrite the whole animation because one label overlaps. Local fixes preserve the original concept and reduce new regressions.

## Review Checklist

Mark PASS only when:

- Text is readable at the target resolution.
- No important label, formula, or object overlaps another.
- Each beat has one focal winner.
- Camera movement has a semantic purpose and does not crop needed context.
- Updaters, counters, and traced motion follow the intended driver.
- Captions or subtitles do not hide the main visual.
- The pacing has readable holds after important reveals.
- The final frame has a clear hero landing.

Common fixes:

- Increase `buff`, reduce `font_size`, or constrain text width.
- Dim context to opacity `0.25`-`0.4` when the active object changes.
- Add `self.wait(0.5)` to `self.wait(1.5)` after a dense reveal.
- Use `SurroundingRectangle`, `Brace`, or `Circumscribe` to mark the focal object.
- Restore camera context after inspection with `Restore(frame)`.
- Split a crowded beat into two beats instead of shrinking everything.
