# Session handoff: Risk Hub carousel factory

Read this first when continuing the work in a new session.

## Pending task (do this first)

1. In the user's Google Drive, create a folder named **`1. VaR`** inside the folder
   `https://drive.google.com/drive/folders/1QP7ksRQChTo6EfF_FfMBoUh1SIQVnp3Z`
   (parent ID `1QP7ksRQChTo6EfF_FfMBoUh1SIQVnp3Z`). The user typed `"1. VaR "` with a
   trailing space; we used `1. VaR` and asked them to say if they want the space kept.
2. Upload the 7 per-slide videos into that folder, in order:
   `carousel-factory/output/jobs/VAR-001/exports/slides-mp4/slide-01.mp4` … `slide-07.mp4`
   (each 5 s, 1080×1350, H.264 30 fps, silent, about 0.5–0.7 MB).

The previous session could not do this: the Google Drive connector refused every call
(even reading metadata) with "missing a permission". The user was told to reconnect the
connector with all permissions and start a new session.

## What exists

Branch: `claude/peaceful-carson-hqvun4` (all work committed and pushed).

- `carousel-factory/`: the renderer (Node 22, Playwright, GSAP, KaTeX, FFmpeg).
  - `src/render/illustrations/index.js`: seeded 2D SVG vector chart generators (no `<text>`).
  - `src/render/build.js`: spec → layered HTML (bg / animated SVG art / static text).
  - `src/render/assets/runtime.js`: GSAP timelines; refuses to animate any text.
  - `src/render/export.js`: PNG per slide, PDF, MP4 (deterministic frame seeks → FFmpeg).
  - `src/qa/index.js`: 114 automated checks (static text in DOM + pixels, overlap,
    margins, fonts, content, determinism, MP4/PNG agreement, file formats).
  - `src/queue/*`: Google Sheets (service-account REST) and local CSV queue adapters.
    Written but **not tested against a real sheet** (no Google credentials available).
  - `scripts-render-sample.js <design-spec.json>`: renders one spec to `output/jobs/<id>/`.
- `carousel-factory/moodboards/claude/VAR-001/design-spec.json`: the sample carousel's
  content and design (7 slides on Value at Risk), authored by Claude from the user's 5
  reference images.
- `carousel-factory/output/jobs/VAR-001/`: the final render, which passed 114/114 QA
  checks: `exports/carousel.mp4`, `exports/carousel.pdf`, `exports/png/`,
  `exports/slides-mp4/` (the 7 posting clips), `exports/contact-sheet.png`,
  `carousel/` (editable source), `qa/report.json`.

To split a new render into posting clips, cut `exports/carousel.mp4` at each segment in
`carousel/render-config.json` (150 frames per slide at 5 s × 30 fps).

## User preferences learned

- Design references: dark quant-finance carousel style (heavy tight headlines, justified
  bold body, gold labels, LaTeX equations as texture, minimal imagery).
- All text must stay static; only 2D vector illustrations may animate.
- The user posts **one video per slide** as a carousel (not a single long MP4).
- The user said to skip the full automation for now and focus on renders.
- They may upload ~10 reference mood boards; Claude can then author new design specs
  itself (no ChatGPT needed).

## Not done / blocked

- ChatGPT-in-Chrome worker: not written. Cloud sessions cannot reach the user's Chrome,
  and `chatgpt.com` is blocked by the environment's network policy.
- Google Sheets queue: code written, untested (no credentials).
