"""Convert an ElevenLabs Scribe word list into the timing format used by build.py.

Usage: scribe_to_timing.py questions/qNNN.json build/qNNN-scribe-words.json build/qNNN-timing.json
Bracketed audio tags ([pause], [warmly]) are dropped; words are assigned to the
question's narration sections in order, so the section texts must match the take.
"""
import json, re, subprocess, sys

Q = json.load(open(sys.argv[1]))
raw = json.load(open(sys.argv[2]))
raw = raw.get("words", raw) if isinstance(raw, dict) else raw
words = [w for w in raw if w.get("type", "word") == "word" and not re.fullmatch(r"\[.*\]", w["text"].strip())]

def norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())
out, k = [], 0
for sec in Q["sections"]:
    for tok in re.sub(r"\[[^\]]*\]", " ", sec["text"]).split():
        w = words[k]
        if norm(w["text"]) != norm(tok):
            sys.exit(f"mismatch at word {k}: transcript {w['text']!r} vs script {tok!r} (section {sec['id']})")
        out.append({"w": tok, "sec": sec["id"], "s": round(w["start"], 3), "e": round(w["end"], 3)})
        k += 1
if k != len(words):
    sys.exit(f"{len(words) - k} transcript words left over")

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", Q["audio"]],
                           capture_output=True, text=True).stdout)
sections = []
for sec in Q["sections"]:
    ws = [w for w in out if w["sec"] == sec["id"]]
    sections.append({"id": sec["id"], "s": ws[0]["s"], "e": ws[-1]["e"]})
json.dump({"duration": round(dur, 3), "speech_start": out[0]["s"], "speech_end": out[-1]["e"], "sections": sections, "words": out},
          open(sys.argv[3], "w"), indent=1)
print(json.dumps(sections))
