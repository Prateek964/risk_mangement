"""Align the narration script to take-A.mp3 using detected pauses.

Word times are interpolated by character count over speech time, then pinned so
that every detected pause lands on a punctuation boundary. Output: build/timing.json
"""
import json, re, subprocess, sys

AUDIO = "audio/take-A.mp3"
SECTIONS = [
 ("hook", "October 1929. Wall Street was about to experience one of the most devastating financial collapses in history. But this disaster didn't begin with panic. It began with greed, easy money, and the belief that stock prices could only go up."),
 ("boom", "Throughout the 1920s, America experienced an economic boom. Businesses expanded, consumer spending increased, and millions of investors rushed into the stock market. Many bought shares using borrowed money, a practice known as buying on margin. As prices climbed, rising prices attracted more buyers. And more buyers pushed prices even higher. The market began to look unstoppable."),
 ("warning", "But beneath the optimism, danger was building. Stock prices had become detached from what many companies could realistically earn. Speculation was rampant, and borrowed money magnified the risks. Eventually, confidence began to weaken. Investors started selling. And suddenly... everyone wanted to get out at once."),
 ("crash", "On October 24, 1929, known as Black Thursday, panic selling shook Wall Street. Five days later, on Black Tuesday, October 29, selling intensified dramatically. Investors rushed to dump their shares. Prices collapsed. Fortunes disappeared, sometimes within hours. Those who had borrowed to invest faced devastating losses, and some were forced to sell simply to repay their debts. The market's upward spiral had turned into a downward avalanche."),
 ("aftermath", "But the crash was not the entire Great Depression. Bank failures, collapsing demand, falling production, and policy mistakes helped turn the stock market disaster into a prolonged economic catastrophe. Businesses shut down. Unemployment soared. Families lost savings, homes, and livelihoods. The crisis spread far beyond Wall Street, affecting economies around the world."),
 ("lesson", "The Wall Street Crash revealed a timeless truth about financial markets. When speculation replaces fundamentals, debt magnifies risk, and confidence turns into panic, a boom can become a disaster. Because markets don't just run on money. They run on trust. And once that trust disappears, the consequences can last for years."),
]

def silences():
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", AUDIO, "-af", "silencedetect=noise=-35dB:d=0.35", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    dur = float(re.search(r"Duration: (\d+):(\d+):([0-9.]+)", out).groups()[2]) + 60 * int(re.search(r"Duration: (\d+):(\d+)", out).group(2))
    return list(zip(st, en + [dur] * (len(st) - len(en)))), dur

gaps, dur = silences()
speech_start = gaps[0][1] if gaps[0][0] < 0.05 else 0.0
inner = [g for g in gaps if g[0] > speech_start + 0.1 and g[1] < dur - 0.05]
speech_end = gaps[-1][0] if gaps[-1][1] >= dur - 0.05 else dur

words = []  # (text, section, weight, punct_after)
for sec, text in SECTIONS:
    for w in text.split():
        p = 2 if re.search(r"[.?!]$|\.\.\.$", w) else (1 if re.search(r"[,;:]$", w) else 0)
        words.append({"w": w, "sec": sec, "wt": len(re.sub(r"\W", "", w)) + 1.5, "p": p})
    words[-1]["p"] = 3  # section boundary

# boundaries: index i = boundary after word i
cum = [0.0]
for w in words: cum.append(cum[-1] + w["wt"])

def interp(pins):
    """pins: list of (word_boundary_index, real_start_time_of_next, real_end_time_of_prev) -> per-word times"""
    times = [None] * len(words)
    for (b0, t0), (b1, t1) in zip(pins, pins[1:]):
        # boundary b0 => next word starts at t0; boundary b1 => word b1-1 ends at t1
        span = cum[b1] - cum[b0]
        for i in range(b0, b1):
            s = t0 + (t1 - t0) * (cum[i] - cum[b0]) / span
            e = t0 + (t1 - t0) * (cum[i + 1] - cum[b0]) / span
            times[i] = (s, e)
    return times

# Greedy pinning: walk gaps in order; estimate each boundary's time with current pins, pin the best punctuation boundary.
pins_start = [(0, speech_start)]
total_speech = (speech_end - speech_start) - sum(g[1] - g[0] for g in inner)
def est_time(b):
    # speech-time proportional estimate, re-inserting gaps
    ts = speech_start + total_speech * cum[b] / cum[-1]
    for g in inner:
        if ts > g[0]: ts += g[1] - g[0]
    return ts

pairs = []  # (boundary, gap)
last_b = 0
for g in inner:
    mid = (g[0] + g[1]) / 2
    cands = [b for b in range(last_b + 1, len(words)) if words[b - 1]["p"] > 0]
    if not cands: break
    b = min(cands, key=lambda b: abs(est_time(b) - mid) - 0.6 * words[b - 1]["p"])
    pairs.append((b, g)); last_b = b

# Build piecewise segments: speech runs between gaps
times = [None] * len(words)
segs = []
prev_b, prev_t = 0, speech_start
for b, g in pairs:
    segs.append((prev_b, prev_t, b, g[0])); prev_b, prev_t = b, g[1]
segs.append((prev_b, prev_t, len(words), speech_end))
for b0, t0, b1, t1 in segs:
    span = cum[b1] - cum[b0]
    for i in range(b0, b1):
        times[i] = (round(t0 + (t1 - t0) * (cum[i] - cum[b0]) / span, 3), round(t0 + (t1 - t0) * (cum[i + 1] - cum[b0]) / span, 3))

out_words = [{"w": w["w"], "sec": w["sec"], "s": t[0], "e": t[1]} for w, t in zip(words, times)]
sections = []
for sec, _ in SECTIONS:
    ws = [w for w in out_words if w["sec"] == sec]
    sections.append({"id": sec, "s": ws[0]["s"], "e": ws[-1]["e"]})
json.dump({"duration": dur, "speech_start": speech_start, "speech_end": speech_end, "sections": sections, "words": out_words},
          open("build/timing.json", "w"), indent=1)
for b, g in pairs:
    print(f"{g[0]:7.2f}-{g[1]:6.2f}  after: ...{' '.join(w['w'] for w in words[max(0,b-4):b])}")
print(json.dumps(sections, indent=0))
