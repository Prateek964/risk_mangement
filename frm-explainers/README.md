# Risk Hub — FRM Part I explainer videos

Vertical (1080×1920) one-question explainer videos for *FRM Part I, Book 1:
Foundations of Risk Management*, branded with the Risk Hub logo. Built with the
open-source [HyperFrames](https://github.com/heygen-com/hyperframes) framework and
narrated with ElevenLabs.

Each video runs: cover (FRM Part 1 · Book · Chapter · Practice Question) → question → options → "pause & pick" countdown → answer
reveal with a concept graphic → why each wrong option is wrong → key takeaway →
"Follow Risk Hub" end card. Captions are synced word by word, with sound effects on every reveal.

Narration sections may contain ElevenLabs audio tags such as `[warmly]` or `[pause]`;
they are ignored when matching the transcript. Use `answer_at`, `option_at` and
`cover_at` in the question JSON when the narration doesn't use the default phrasing.

## Layout

| Path | What it is |
| --- | --- |
| `questions/qNNN.json` | Everything about one question: text, options, answer, on-screen explanation points, and the narration script split into sections. |
| `audio/qNNN-takeN.mp3` | ElevenLabs narration takes. |
| `tools/scribe_to_timing.py` | Turns an ElevenLabs Scribe word list into `build/qNNN-timing.json` (exact word timings). |
| `tools/align.py` | Fallback timing: aligns the script to the audio's pauses when no transcript is available. |
| `tools/build.py`, `tools/style.css` | The template. Generates `qNNN/index.html` from the question JSON + timing, and `build/qNNN-sfx.json` (sound-effect cues). |
| `sfx/*.mp3`, `tools/mix.py` | ElevenLabs sound effects (sting, whoosh, pop, tick, correct, wrong) and the mixer that lays them under the narration. |
| `questions/q001-conversational.json` | Conversational re-script of Q1 for the 'TrevorT' voice, ready to generate once ElevenLabs credits are available. |
| `qNNN/` | HyperFrames project for one video (assets: logo, fonts, GSAP, voiceover). |
| `output/riskhub-frm-qNNN.mp4` | Finished video. |

## Making the next question

1. Copy `questions/q090.json` to `questions/qNNN.json` and fill in the question,
   options, answer, explanation points and narration `sections`. Every `at` field is
   a phrase from the narration where that element should appear.
2. Generate the narration in ElevenLabs from the section texts joined in order
   (put `[pause]` after the "Pause the video and pick your answer." line), save it as
   `audio/qNNN-take1.mp3`, and set `"audio"` in the JSON.
3. Transcribe it with ElevenLabs Scribe, save the word list as
   `build/qNNN-scribe-words.json`, then:
   ```bash
   python3 tools/scribe_to_timing.py questions/qNNN.json build/qNNN-scribe-words.json build/qNNN-timing.json
   ```
4. Create the project and build:
   ```bash
   npx hyperframes@0.8.146 init qNNN --example blank --resolution portrait --non-interactive
   mkdir -p qNNN/assets && cp -r q090/assets/{fonts,gsap.min.js,grain.png,riskhub-logo.png} qNNN/assets/
   python3 tools/build.py questions/qNNN.json build/qNNN-timing.json qNNN
   python3 tools/mix.py questions/qNNN.json build/qNNN-sfx.json qNNN/assets/voiceover.mp3
   cd qNNN && npx hyperframes@0.8.146 lint && npx hyperframes@0.8.146 render -q high -o ../build/qNNN-master.mp4
   ```
5. Re-encode for sharing:
   `ffmpeg -i build/qNNN-master.mp4 -c:v libx264 -preset slow -crf 20 -movflags +faststart -c:a aac -b:a 192k output/riskhub-frm-qNNN.mp4`
