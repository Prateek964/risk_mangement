"""Align the narration script to take-A.mp3 using detected pauses.

Word times are interpolated by character count over speech time, then pinned so
that every detected pause lands on a punctuation boundary. Usage: align.py questions/qNNN.json build/qNNN-timing.json
"""
import json, re, subprocess, sys

import os
Q = json.load(open(sys.argv[1]))
AUDIO = Q["audio"]
OUT = sys.argv[2]
SECTIONS = [(x["id"], x["text"]) for x in Q["sections"]]

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

# Global monotone matching of pauses to punctuation boundaries (DP).
B = [b for b in range(1, len(words)) if words[b - 1]["p"] > 0]
G = inner
INF = float("inf")
def mcost(gi, bi):
    g, b = G[gi], B[bi]
    mid = (g[0] + g[1]) / 2
    return ((est_time(b) - mid) / 4.0) ** 2 - 1.0 * words[b - 1]["p"] - 2.0 * min(g[1] - g[0], 1.5)
def gskip(gi):
    gl = G[gi][1] - G[gi][0]
    return 0.0 if gl < 0.45 else 3.0 * gl
def bskip(bi):
    return 0.3 * words[B[bi] - 1]["p"]
nG, nB = len(G), len(B)
D = [[INF] * (nB + 1) for _ in range(nG + 1)]
P = [[None] * (nB + 1) for _ in range(nG + 1)]
D[0][0] = 0.0
for i in range(nG + 1):
    for j in range(nB + 1):
        if D[i][j] == INF: continue
        if i < nG and D[i][j] + gskip(i) < D[i + 1][j]:
            D[i + 1][j] = D[i][j] + gskip(i); P[i + 1][j] = (i, j, False)
        if j < nB and D[i][j] + bskip(j) < D[i][j + 1]:
            D[i][j + 1] = D[i][j] + bskip(j); P[i][j + 1] = (i, j, False)
        if i < nG and j < nB:
            c = D[i][j] + mcost(i, j)
            if c < D[i + 1][j + 1]:
                D[i + 1][j + 1] = c; P[i + 1][j + 1] = (i, j, True)
pairs = []
i, j = nG, nB
while (i, j) != (0, 0):
    pi, pj, m = P[i][j]
    if m: pairs.append((B[pj], G[pi]))
    i, j = pi, pj
pairs.reverse()

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
          open(OUT, "w"), indent=1)
for b, g in pairs:
    print(f"{g[0]:7.2f}-{g[1]:6.2f}  after: ...{' '.join(w['w'] for w in words[max(0,b-4):b])}")
print(json.dumps(sections, indent=0))

