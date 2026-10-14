# The Wall Street Crash of 1929 — Instagram Reel

A 9:16 (1080×1920) documentary-style motion-graphics video built with the
open-source [HyperFrames](https://github.com/heygen-com/hyperframes) framework,
narrated with an ElevenLabs voiceover.

## Layout

| Path | What it is |
| --- | --- |
| `audio/take-A.mp3`, `audio/take-B.mp3` | ElevenLabs voiceover takes (voice: Atlas). Take A is used. |
| `tools/align.py` | Aligns the script to take A's pauses → `build/timing.json` (word timings). |
| `tools/build.py` + `tools/style.css` | Generates the HyperFrames composition `video/index.html`. |
| `video/` | HyperFrames project (composition, fonts, GSAP, grain texture, voiceover). |
| `output/wall-street-crash-1929.mp4` | Final render. |

## Rebuild

```bash
python3 tools/align.py          # only if the voiceover changes
python3 tools/build.py          # regenerate video/index.html
cd video
npx hyperframes@0.8.146 lint
npx hyperframes@0.8.146 render -f 30 -q high -o ../output/wall-street-crash-1929.mp4
```

Edit scene timing, text and animation in `tools/build.py`, and the look in
`tools/style.css`; then rebuild. Don't hand-edit `video/index.html` — it is generated.

Historical figures shown: Dow Jones peak 381.2 (Sept 3, 1929), Black Thursday
(Oct 24), Black Tuesday (Oct 29), Nov 13, 1929 low ~198.7, July 1932 low 41.2
(−89%), ~9,000 U.S. bank failures 1930–33, unemployment ~25% by 1933. The
"prices vs. earnings" chart is illustrative, not data.
