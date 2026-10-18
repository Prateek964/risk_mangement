"""Build a Risk Hub FRM question explainer (HyperFrames composition).

Usage: build.py questions/qNNN.json build/qNNN-timing.json <project-dir>
Writes <project-dir>/index.html. Assets (logo, fonts, gsap, grain, voiceover.mp3)
are expected in <project-dir>/assets.
"""
import html, json, re, sys

Q = json.load(open(sys.argv[1]))
TM = json.load(open(sys.argv[2]))
PROJ = sys.argv[3]
ROOT = __file__.rsplit("/tools/", 1)[0]
WORDS = TM["words"]
ADUR = round(TM["duration"], 2)
DUR = round(ADUR + 2.2, 2)
SEC = {s["id"]: s for s in TM["sections"]}
esc = html.escape

def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))

def T(phrase, sec=None, nth=0, end=False):
    p = [norm(x) for x in phrase.split()]
    hits = [i for i in range(len(WORDS) - len(p) + 1)
            if (not sec or WORDS[i]["sec"] == sec) and [norm(WORDS[i + k]["w"]) for k in range(len(p))] == p]
    if not hits: sys.exit(f"phrase not found in narration: {phrase!r} (section {sec})")
    i = hits[nth]
    return round(WORDS[i + len(p) - 1]["e"] if end else WORDS[i]["s"], 3)

S = {k: v["s"] for k, v in SEC.items()}
E = {k: v["e"] for k, v in SEC.items()}
order = [s["id"] for s in Q["sections"]]
letters = list(Q["options"].keys())
ans = Q["answer"]
wrong = [l for l in letters if l != ans]

# scene windows
def win(a, b): return (round(a, 3), round(b - a, 3))
SC = {
    "intro": win(0, S["question"] + 0.4),
    "question": win(S["question"], S["options"] + 0.4),
    "options": win(S["options"], S["answer"] + 3.2),
    "answer": win(S["answer"] + 2.6, S["wrong"] + 0.4),
    "wrong": win(S["wrong"], S["takeaway"] + 0.4),
    "takeaway": win(S["takeaway"], DUR),
}

# ---------------------------------------------------------------- captions
keys = [k.lower().split() for k in Q.get("caption_keywords", [])]
hl = [False] * len(WORDS)
for i in range(len(WORDS)):
    for k in keys:
        if [norm(WORDS[i + j]["w"]) if i + j < len(WORDS) else "" for j in range(len(k))] == [norm(x) for x in k]:
            for j in range(len(k)): hl[i + j] = True
chunks, cur = [], []
for i, w in enumerate(WORDS):
    cur.append(i)
    txt = " ".join(WORDS[j]["w"] for j in cur)
    last = i + 1 >= len(WORDS) or WORDS[i + 1]["sec"] != w["sec"]
    gap = i + 1 < len(WORDS) and WORDS[i + 1]["s"] - w["e"] > 0.45
    if last or gap or (re.search(r"[,;:?]$|\.\.\.$", w["w"]) and len(cur) >= 3) or re.search(r"[.!?]$", w["w"]) \
            or len(cur) >= 6 or len(txt) >= 30:
        chunks.append(cur); cur = []
cap_html, cap_js = [], []
for n, c in enumerate(chunks):
    s = WORDS[c[0]]["s"] - 0.06
    nxt = WORDS[chunks[n + 1][0]]["s"] - 0.06 if n + 1 < len(chunks) else ADUR
    e = min(nxt, WORDS[c[-1]]["e"] + 0.7)
    body = " ".join(f'<span class="k">{esc(WORDS[j]["w"])}</span>' if hl[j] else esc(WORDS[j]["w"]) for j in c)
    cap_html.append(f'<div class="cap" id="cap{n}"><span class="cbox">{body}</span></div>')
    cap_js.append(f"capIn('#cap{n}',{s:.3f});capOut('#cap{n}',{max(e - 0.1, s + 0.3):.3f});")

# ---------------------------------------------------------------- markup
def clip(k, inner):
    s, d = SC[k]
    return f'<div id="sc-{k}" class="clip scene" data-start="{s}" data-duration="{d}" data-track-index="1">{inner}</div>'

stem = esc(Q["stem"])
for h in Q.get("stem_highlights", []):
    t = esc(h["text"])
    stem = stem.replace(t, f'<span class="hl" id="hl{Q["stem_highlights"].index(h)}">{t}</span>', 1)

def opt_card(l, cls="opt", idp="op"):
    return (f'<div class="{cls} h" id="{idp}{l}"><div class="lt"><span class="ltx">{l}</span><span class="ck">✓</span><span class="xx">✕</span></div>'
            f'<div class="ot">{esc(Q["options"][l])}</div></div>')

ap = Q["answer_points"]
def meter(col, default):
    w = col.get("meter", default)
    return f'<div class="meter"><i style="width:{w}%"></i></div>' if w is not None else '<div class="mgap"></div>'
chips = "".join(f'<div class="chip h" id="chip{i}">{esc(c["text"])}</div>' for i, c in enumerate(ap["low"]["chips"]))
rows = "".join(f'''<div class="wrow h" id="w{l}"><div class="lt bad"><span>{l}</span></div>
  <div class="wtx"><div class="wopt">{esc(Q["options"][l])}</div><div class="wwhy h" id="wy{l}">{esc(Q["wrong"][l]["reason"])}</div></div></div>''' for l in wrong)
defn = Q.get("definition")
tk = "".join(f'<div class="tk h" id="tk{i}"><span class="tn">{i + 1}</span>{esc(t["text"])}</div>' for i, t in enumerate(Q["takeaway"]))

scenes = [
clip("intro", f'''
  <div class="ilogo" id="ilogo"><img src="assets/riskhub-logo.png" alt="Risk Hub"/></div>
  <div class="ititle h" id="it1">FRM Part 1</div>
  <div class="isub h" id="it2">{esc(Q["book"])}</div>
  <div class="ichap h" id="it4">{esc(Q["chapter"])}</div>
  <div class="ichip h" id="it3">PRACTICE QUESTION</div>'''),
clip("question", f'''
  <div class="qlabel h" id="ql">THE QUESTION</div>
  <div class="qcard h" id="qcard"><p>{stem}</p></div>'''),
clip("options", f'''
  <div class="qshort h" id="qs"><span>Q{Q["number"]}</span>{esc(Q["stem_short"])}</div>
  <div class="pausebar h" id="pb"><span class="pi">❚❚</span> Pause &amp; pick your answer <span class="cd"><b id="cd3">3</b><b id="cd2">2</b><b id="cd1">1</b></span></div>
  <div class="opts">{"".join(opt_card(l) for l in letters)}</div>'''),
clip("answer", f'''
  <div class="alabel h" id="al">CORRECT ANSWER</div>
  {opt_card(ans, "opt win", "ans")}
  <div class="apanel h" id="ap">
    <div class="aptitle">{esc(ap["title"])}</div>
    <div class="cols">
      <div class="col hi h" id="colhi"><div class="cl">{esc(ap["high"]["label"])}</div>{meter(ap["high"], 88)}<div class="ct">{esc(ap["high"]["text"])}</div></div>
      <div class="col lo h" id="collo"><div class="cl">{esc(ap["low"]["label"])}</div>{meter(ap["low"], 28)}<div class="chips">{chips}</div></div>
    </div>
  </div>'''),
clip("wrong", f'''
  <div class="wlabel h" id="wl">WHY NOT THE OTHERS?</div>
  <div class="wrows">{rows}</div>
  {f'<div class="defn h" id="defn"><div class="dt">{esc(defn["term"])}</div><div class="dd">{esc(defn["text"])}</div></div>' if defn else ''}'''),
clip("takeaway", f'''
  <div class="tlabel h" id="tl">KEY TAKEAWAY</div>
  <div class="tks">{tk}</div>
  <div class="endc h" id="endc"><img src="assets/riskhub-logo.png" alt="Risk Hub"/><div class="e1">Follow Risk Hub</div><div class="e2">for more FRM practice</div></div>'''),
]

steps = ["QUESTION", "OPTIONS", "ANSWER", "WHY NOT"]
header = f'''<div class="hdr h" id="hdr">
    <img class="hlogo" src="assets/riskhub-logo.png" alt="Risk Hub"/>
    <div class="htx"><div class="h1">FRM PART 1 · BOOK 1 · CH {Q["chapter_number"]}</div><div class="h2">Foundations of Risk Management</div></div>
    <div class="hq">Q{Q["number"]}</div>
  </div>
  <div class="steps h" id="steps">{"".join(f'<div class="st" id="st{i}">{s}</div>' for i, s in enumerate(steps))}<div class="sbar" id="sbar"></div></div>'''

TT = {
    "q": S["question"], "o": S["options"], "p": S["pause"], "a": S["answer"], "w": S["wrong"], "t": S["takeaway"],
    "ansD": T(Q.get("answer_at", f"answer is {ans}."), "answer", end=True) - 0.3,
    "hi": T(ap["high"]["at"], "answer"), "lo": T(ap["low"]["at"], "answer"),
    "chips": [T(c["at"], "answer") for c in ap["low"]["chips"]],
    "opts": [T(Q.get("option_at", {}).get(l, f"Option {l}."), "options") for l in letters],
    "hls": [T(h["at"], "question") for h in Q.get("stem_highlights", [])],
    "wr": [T(Q["wrong"][l]["at"], "wrong") for l in wrong],
    "defn": T(defn["at"], "wrong") if defn else None,
    "tk": [T(t["at"], "takeaway") for t in Q["takeaway"]],
    "follow": T("Follow Risk Hub", "takeaway"),
    "pauseEnd": S["answer"],
    "cov": [max(0.5, T(p, "intro") - 0.1 + i * 0.35 * (i > 0 and p == Q.get("cover_at", [None] * 4)[i - 1]))
            for i, p in enumerate(Q.get("cover_at", ["FRM Part", "Book 1,", "Chapter 1,", f"Question {Q['number']}."]))],
}

JS = f"""
const T = {json.dumps(TT)};
const SC = {json.dumps(SC)};
const ANS = {json.dumps(ans)}, LET = {json.dumps(letters)}, WRONG = {json.dumps(wrong)};
const tl = gsap.timeline({{ paused: true }});
const EZ = 'power3.out';
function inn(s, t, v = {{}}, d = 0.6) {{ tl.fromTo(s, Object.assign({{ opacity: 0, y: 36 }}, v.from || {{}}), Object.assign({{ opacity: 1, y: 0, x: 0, scale: 1, duration: d, ease: EZ }}, v.to || {{}}), t); }}
function out(s, t, d = 0.4) {{ tl.fromTo(s, {{ opacity: 1 }}, {{ opacity: 0, duration: d, ease: 'power2.in', immediateRender: false }}, t); }}
function capIn(s, t) {{ tl.fromTo(s, {{ opacity: 0, y: 18 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: 'power2.out' }}, t); }}
function capOut(s, t) {{ tl.fromTo(s, {{ opacity: 1 }}, {{ opacity: 0, duration: 0.12, ease: 'none', immediateRender: false }}, t); }}

for (const [k, [s, d]] of Object.entries(SC)) {{
  if (s > 0) tl.fromTo('#sc-' + k, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.45, ease: 'none' }}, s);
}}
tl.fromTo('#grain', {{ x: 0, y: 0 }}, {{ x: -400, y: -330, duration: {DUR}, ease: 'steps({int(DUR * 12)})' }}, 0);
tl.fromTo('#bggrid', {{ y: 0 }}, {{ y: -120, duration: {DUR}, ease: 'none' }}, 0);

// header + step tracker
inn('#hdr', T.q - 0.2, {{ from: {{ y: -30 }} }});
inn('#steps', T.q, {{ from: {{ y: -10 }} }});
const stepAt = [T.q, T.o, T.ansD, T.w];
stepAt.forEach((t, i) => {{
  tl.to('#sbar', {{ x: i * 240, duration: 0.5, ease: 'power2.inOut' }}, t);
  tl.fromTo('#st' + i, {{ opacity: 0.4 }}, {{ opacity: 1, duration: 0.3, immediateRender: i === 0 }}, t);
  if (i > 0) tl.to('#st' + (i - 1), {{ opacity: 0.4, duration: 0.3 }}, t);
}});
out('#hdr', T.follow - 0.2); out('#steps', T.follow - 0.2);

// intro
tl.fromTo('#ilogo', {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.9, ease: 'back.out(1.6)' }}, 0.05);
inn('#it1', T.cov[0]); inn('#it2', T.cov[1]); inn('#it4', T.cov[2]); inn('#it3', T.cov[3], {{ from: {{ scale: 0.8, y: 0 }} }});

// question
inn('#ql', T.q + 0.1); inn('#qcard', T.q + 0.25, {{}}, 0.7);
T.hls.forEach((t, i) => tl.fromTo('#hl' + i, {{ backgroundColor: 'rgba(245,184,61,0)' }}, {{ backgroundColor: 'rgba(245,184,61,0.55)', duration: 0.5, ease: 'none' }}, t));

// options
inn('#qs', T.o + 0.05);
LET.forEach((l, i) => inn('#op' + l, T.opts[i] - 0.1, {{ from: {{ x: 70, y: 0 }} }}, 0.5));
out('#qs', T.p - 0.2, 0.3);
inn('#pb', T.p, {{ from: {{ y: -20 }} }}, 0.4);
const cdStep = (T.pauseEnd - T.p - 0.6) / 3;
['#cd3', '#cd2', '#cd1'].forEach((s, i) => {{
  tl.fromTo(s, {{ opacity: 0, scale: 1.6 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: 'power2.out' }}, T.p + 0.3 + i * cdStep);
  tl.to(s, {{ opacity: 0, duration: 0.15 }}, T.p + 0.3 + (i + 1) * cdStep - 0.05);
}});
out('#pb', T.pauseEnd - 0.1, 0.3);
WRONG.forEach(l => tl.to('#op' + l, {{ opacity: 0.3, scale: 0.97, duration: 0.4 }}, T.ansD));
tl.to('#op' + ANS, {{ scale: 1.03, duration: 0.4, ease: 'back.out(2)' }}, T.ansD);
tl.to('#op' + ANS, {{ borderColor: '#22A565', boxShadow: '0 0 0 6px rgba(34,165,101,0.35)', duration: 0.3 }}, T.ansD);
tl.to('#op' + ANS + ' .lt', {{ backgroundColor: '#22A565', duration: 0.3 }}, T.ansD);
tl.fromTo('#op' + ANS + ' .ltx', {{ opacity: 1 }}, {{ opacity: 0, duration: 0.2 }}, T.ansD);
tl.fromTo('#op' + ANS + ' .ck', {{ opacity: 0, scale: 0.3 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(3)' }}, T.ansD);

// answer
inn('#al', SC.answer[0] + 0.1);
inn('#ans' + ANS, SC.answer[0] + 0.15, {{ from: {{ y: 60 }} }});
inn('#ap', SC.answer[0] + 0.6);
inn('#colhi', T.hi - 0.1, {{ from: {{ x: -50, y: 0 }} }});
inn('#collo', T.lo - 0.1, {{ from: {{ x: 50, y: 0 }} }});
T.chips.forEach((t, i) => inn('#chip' + i, t - 0.05, {{ from: {{ scale: 0.6, y: 0 }} }}, 0.4));

// wrong
inn('#wl', T.w + 0.1);
WRONG.forEach((l, i) => {{
  inn('#w' + l, T.wr[i] - 0.15, {{ from: {{ x: -60, y: 0 }} }}, 0.5);
  inn('#wy' + l, T.wr[i] + 0.5, {{ from: {{ y: 14 }} }}, 0.5);
  tl.fromTo('#w' + l + ' .wopt', {{ textDecorationColor: 'rgba(229,72,77,0)' }}, {{ textDecorationColor: 'rgba(229,72,77,1)', duration: 0.45, ease: 'none' }}, T.wr[i] + 0.3);
}});
if (T.defn !== null) {{ inn('#defn', T.defn, {{ from: {{ scale: 0.9, y: 30 }} }}); const nx = T.wr.find(t => t > T.defn); if (nx !== undefined) out('#defn', nx - 0.2, 0.3); }}

// takeaway
inn('#tl', T.t + 0.05);
T.tk.forEach((t, i) => inn('#tk' + i, t - 0.1, {{ from: {{ x: -60, y: 0 }} }}, 0.5));
out('#tl', T.follow - 0.3); out('.tks', T.follow - 0.3);
tl.fromTo('#endc', {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.8, ease: 'back.out(1.5)' }}, T.follow);

{"".join(cap_js)}
window.__timelines = window.__timelines || {{}};
window.__timelines['main'] = tl;
"""

CSS = open(f"{ROOT}/tools/style.css").read()
page = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>Risk Hub · FRM Q{Q["number"]}</title>
<script src="assets/gsap.min.js"></script>
<style>
@font-face{{font-family:'Inter';font-weight:100 900;font-display:block;src:url('assets/fonts/Inter.woff2') format('woff2');}}
@font-face{{font-family:'Source Serif 4';font-weight:200 900;font-display:block;src:url('assets/fonts/SourceSerif4.woff2') format('woff2');}}
{CSS}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
  <div class="bg"></div>
  <div class="gridwrap"><div id="bggrid"></div></div>
  {header}
{chr(10).join(scenes)}
  <div class="caps">{"".join(cap_html)}</div>
  <div class="grainwrap"><div id="grain"></div></div>
  <audio id="vo" src="assets/voiceover.mp3" data-start="0" data-duration="{ADUR}" data-track-index="2" data-volume="1"></audio>
</div>
<script>
{JS}
</script>
</body>
</html>
"""
open(f"{PROJ}/index.html", "w").write(page)

# ---------------------------------------------------------------- sound effects
cd_step = (TT["pauseEnd"] - TT["p"] - 0.6) / 3
cues = [("sting", 0.05, -11)]
cues += [("whoosh", SC[k][0], -10) for k in ["question", "options", "answer", "wrong", "takeaway"]]
cues += [("pop", t - 0.1, -12) for t in TT["opts"]]
cues += [("tick", TT["p"] + 0.3 + i * cd_step, -8) for i in range(3)]
cues += [("correct", TT["ansD"], -6)]
cues += [("pop", t - 0.05, -14) for t in TT["chips"]]
cues += [("wrong", t - 0.15, -9) for t in TT["wr"]]
cues += [("pop", t - 0.1, -12) for t in TT["tk"]]
cues += [("sting", TT["follow"], -11)]
cues = sorted((round(max(t, 0), 3), n, g) for n, t, g in cues)
json.dump([{"t": t, "sfx": n, "gain_db": g} for t, n, g in cues], open(sys.argv[2].replace("-timing.json", "-sfx.json"), "w"), indent=1)
print("scenes", SC, "captions", len(chunks))
