#!/usr/bin/env python3
"""Render the ~10-minute horizontal (1920x1080) course video for
"Market Risk Modeling".

Each scene's length comes from its voiceover clip in script/video/full/vo/<id>.mp3
(narration text lives in narration.json), so visuals stay in sync with the
narration. Frames are drawn with Pillow and piped to ffmpeg; the voiceover is
mixed over a generated, ducked music bed.

Usage: python3 script/video/full/course_video.py [output.mp4]
       PREVIEW=<scene_id>:<seconds>,... PREVIEW_DIR=dir python3 ...   (stills)
"""
import json
import math
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
W, H = 1920, 1080
FPS = 30
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets/videos/market-risk-modeling-course-overview.mp4")
VO_SRC = os.path.join(HERE, "vo")            # raw ElevenLabs clips, one per scene
VO_DIR = os.path.join(HERE, "vo", "fit")     # trimmed + tempo-adjusted copies (generated)
VO_TEMPO = 1.03
PHOTO_DIR = os.path.join(ROOT, "assets/images/instructors")
LEAD, TAIL = 0.35, 0.6  # silence before / after each narration clip

# ---------------------------------------------------------------- palette
BG_TOP = (9, 14, 32)
BG_BOT = (14, 24, 48)
BG = (11, 18, 38)
INK = (240, 244, 255)
MUTED = (148, 163, 196)
TEAL = (45, 212, 191)
AMBER = (251, 191, 36)
RED = (244, 63, 94)
BLUE = (96, 165, 250)
VIOLET = (167, 139, 250)
GREEN = (52, 211, 153)
CARD = (22, 33, 62)
CARD_EDGE = (44, 60, 102)
GRID = (30, 42, 74)
AXIS = (60, 76, 120)

FONT_DIR = "/usr/share/fonts/opentype/inter"
_fonts = {}


def font(size, weight="Regular", display=False):
    key = (size, weight, display)
    if key not in _fonts:
        fam = "InterDisplay" if display else "Inter"
        _fonts[key] = ImageFont.truetype(f"{FONT_DIR}/{fam}-{weight}.otf", size)
    return _fonts[key]


# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def prog(t, start, dur):
    return clamp((t - start) / dur)


def mix(c1, c2, a):
    a = clamp(a)
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


def fade(col, a):
    return mix(BG, col, a)


def text(d, xy, s, f, col, p=1.0, anchor="la", rise=30):
    if p <= 0:
        return
    x, y = xy
    y += (1 - ease_out(p)) * rise
    d.text((x, y), s, font=f, fill=fade(col, ease_out(p)), anchor=anchor)


def wrap(d, s, f, maxw):
    lines, cur = [], ""
    for w in s.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rrect(d, box, r, fill, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def polyline(d, pts, col, width):
    if len(pts) >= 2:
        d.line(pts, fill=col, width=width, joint="curve")


def check(d, cx, cy, s, col, width=6):
    d.line([(cx - s * 0.45, cy), (cx - s * 0.1, cy + s * 0.35), (cx + s * 0.5, cy - s * 0.4)],
           fill=col, width=width, joint="curve")


def chip(d, x, y, label, col, p, f=None, fill=None):
    f = f or font(26, "SemiBold")
    tw = d.textlength(label, font=f)
    h = f.size + 22
    rrect(d, (x, y, x + tw + 40, y + h), h // 2, fade(fill, p) if fill else None, outline=fade(col, p), width=2)
    d.text((x + 20, y + h / 2), label, font=f, fill=fade(INK, p), anchor="lm")
    return x + tw + 40


def make_background():
    g = np.linspace(0, 1, H)[:, None]
    arr = np.zeros((H, W, 3), dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * g
    arr[::80, :, :] += 6
    arr[:, ::80, :] += 6
    yy, xx = np.mgrid[0:H, 0:W]
    for (cx, cy, rad, col, k) in ((1700, 150, 800, TEAL, 0.09), (150, 1000, 800, VIOLET, 0.08)):
        m = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad ** 2 / 2.5)))
        for i in range(3):
            arr[:, :, i] += m * col[i] * k
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- timeline
NARRATION = json.load(open(os.path.join(HERE, "narration.json")))
TEXT = {n["id"]: n["text"] for n in NARRATION}


def fit_clip(sid):
    """Trim leading/trailing silence and apply VO_TEMPO; cached in VO_DIR."""
    src, dst = os.path.join(VO_SRC, f"{sid}.mp3"), os.path.join(VO_DIR, f"{sid}.wav")
    if os.path.exists(src) and (not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src)):
        os.makedirs(VO_DIR, exist_ok=True)
        trim = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
                        f"{trim},areverse,{trim},areverse,atempo={VO_TEMPO}", "-ar", "44100", "-ac", "1", dst],
                       check=True)
    return dst


def clip_duration(sid):
    path = fit_clip(sid)
    if not os.path.exists(path):  # no voiceover yet: estimate from word count
        return len(TEXT[sid].split()) / 2.3
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


ORDER = [n["id"] for n in NARRATION]
CLIP = {sid: clip_duration(sid) for sid in ORDER}
START, DUR = {}, {}
_t = 0.0
for sid in ORDER:
    START[sid] = _t
    DUR[sid] = LEAD + CLIP[sid] + TAIL
    _t += DUR[sid]
DURATION = _t


def cue(sid, phrase, default=0.0):
    """Approximate scene-local time at which `phrase` is spoken (by character position)."""
    s = TEXT[sid]
    i = s.find(phrase)
    if i < 0:
        return default
    return LEAD + CLIP[sid] * i / len(s)


# ---------------------------------------------------------------- data (seeded)
rng = np.random.default_rng(11)
_ret = rng.normal(0.0009, 0.011, 300)
_ret[200:240] -= 0.014
PRICE = 100 * np.exp(np.cumsum(_ret))
PNL = rng.standard_t(4, 5000)
HIST, EDGES = np.histogram(PNL, bins=41, range=(-6, 6))
VAR99 = float(np.quantile(PNL, 0.01))
ES975 = float(PNL[PNL <= np.quantile(PNL, 0.025)].mean())
DAILY = rng.normal(0, 1, 60) * 0.8
DAILY[[11, 37, 52]] = [-2.6, 2.4, -2.9]
BT_PNL = np.clip(rng.normal(0, 0.75, 250), -1.9, 3.0)
BT_VAR = -2.33 * (0.9 + 0.15 * np.sin(np.linspace(0, 6, 250)))
BT_PNL[[40, 97, 150, 201, 230]] = BT_VAR[[40, 97, 150, 201, 230]] - rng.uniform(0.2, 0.8, 5)
MC_PATHS = np.cumsum(rng.normal(0, 1, (60, 90)) * 0.6, axis=1)
_mkt = rng.normal(0, 1, 120)
BETA_X, BETA_Y = _mkt, 1.24 * _mkt + rng.normal(0, 0.7, 120)
CORR_NORMAL = np.array([[1, .45, .3, -.2, .1, .25], [.45, 1, .35, -.15, .05, .3], [.3, .35, 1, -.1, .2, .4],
                        [-.2, -.15, -.1, 1, .15, -.05], [.1, .05, .2, .15, 1, .2], [.25, .3, .4, -.05, .2, 1]])
CORR_CRISIS = np.where(np.eye(6) == 1, 1, np.clip(np.abs(CORR_NORMAL) * 0.4 + 0.55, 0, 0.95))


def norm_pdf(x):
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


# ---------------------------------------------------------------- chrome
def chrome(d, t, label):
    d.rounded_rectangle((80, 52, 112, 84), radius=8, fill=TEAL)
    d.line([(88, 76), (96, 66), (102, 71), (108, 60)], fill=BG, width=4, joint="curve")
    d.text((126, 46), "RiskHub", font=font(34, "Bold"), fill=INK)
    d.text((W - 80, 52), label, font=font(24, "Medium"), fill=MUTED, anchor="ra")
    d.rounded_rectangle((0, H - 6, W, H), radius=0, fill=(24, 34, 62))
    d.rectangle((0, H - 6, W * t / DURATION, H), fill=TEAL)


def header(d, t, kicker, title, x=120, y=150, size=72, col=TEAL):
    text(d, (x, y), kicker, font(28, "SemiBold"), col, p=prog(t, 0.0, 0.6), rise=16)
    text(d, (x, y + 44), title, font(size, "Bold", True), INK, p=prog(t, 0.1, 0.6))
    w = 140 * ease_out(prog(t, 0.3, 0.6))
    if w > 1:
        d.rectangle((x, y + 60 + size, x + w, y + 66 + size), fill=col)


def panel(d, box, p=1.0):
    rrect(d, box, 28, fade(CARD, p * 0.9), outline=fade(CARD_EDGE, p))


def axes(d, x0, y0, x1, y1, p, xlabel="", ylabel=""):
    d.line([(x0, y1), (x1, y1)], fill=fade(AXIS, p), width=3)
    d.line([(x0, y0), (x0, y1)], fill=fade(AXIS, p), width=3)
    if xlabel:
        d.text((x1, y1 + 14), xlabel, font=font(22, "Medium"), fill=fade(MUTED, p), anchor="ra")
    if ylabel:
        d.text((x0 + 10, y0 - 34), ylabel, font=font(22, "Medium"), fill=fade(MUTED, p))


# ---------------------------------------------------------------- module visuals
# Each takes (d, img, box, t, dur) and draws inside box = (x0, y0, x1, y1).

def v_pnl(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    mid = (y0 + y1) / 2
    lim = 2.2
    sc = (y1 - y0) / 2 / 3.2
    n = len(DAILY)
    bw = (x1 - x0) / n
    for gy in (-lim, lim):
        y = mid - gy * sc
        for xs in np.arange(x0, x1, 28):
            d.line([(xs, y), (min(xs + 14, x1), y)], fill=AMBER, width=3)
    d.text((x1, mid - lim * sc - 40), "Risk limit", font=font(24, "SemiBold"), fill=AMBER, anchor="ra")
    d.line([(x0, mid), (x1, mid)], fill=AXIS, width=2)
    k = int(n * ease_in_out(prog(t, 0.5, dur * 0.4)))
    for i in range(k):
        v = DAILY[i]
        col = RED if abs(v) > lim else (TEAL if v >= 0 else BLUE)
        yv = mid - v * sc
        d.rectangle((x0 + i * bw + 3, min(mid, yv), x0 + (i + 1) * bw - 3, max(mid, yv)), fill=col)
    d.text((x0, y1 + 10), "Daily P&L by trading day", font=font(24, "Medium"), fill=MUTED)


def v_matrix(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    cols = ["Linear", "Non-linear"]
    rows = ["Trading book", "Banking book"]
    cells = [["Stocks · FX spot\nFutures · Forwards", "Options\nConvertibles"],
             ["Loans · Deposits\nBanking-book bonds", "Prepayment\noptions (IRRBB)"]]
    lw = 190
    cw = (x1 - x0 - lw) / 2
    ch = (y1 - y0 - 70) / 2
    for j, c in enumerate(cols):
        text(d, (x0 + lw + cw * j + cw / 2, y0), c, font(30, "Bold"), [TEAL, AMBER][j], anchor="ma",
             p=prog(t, 0.6, 0.5), rise=10)
    for i, r in enumerate(rows):
        text(d, (x0, y0 + 70 + ch * i + ch / 2 - 18), r, font(28, "Bold"), INK, p=prog(t, 0.8, 0.5), rise=10)
        for j in range(2):
            p = ease_out(prog(t, 1.2 + (i * 2 + j) * dur * 0.08, 0.6))
            if p <= 0:
                continue
            cx, cy = x0 + lw + cw * j, y0 + 70 + ch * i
            rrect(d, (cx + 10, cy + 10, cx + cw - 10, cy + ch - 10), 20, fade((28, 42, 78), p),
                  outline=fade([TEAL, AMBER][j], p), width=2)
            for k, line in enumerate(cells[i][j].split("\n")):
                d.text((cx + cw / 2, cy + ch / 2 - 20 + k * 40), line, font=font(24, "Medium"),
                       fill=fade(INK, p), anchor="mm")


def v_classes(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    classes = [("Interest rate", BLUE), ("Equity", TEAL), ("Foreign exchange", AMBER), ("Commodity", RED)]
    tw, th = (x1 - x0 - 30) / 2, 110
    for i, (name, col) in enumerate(classes):
        p = ease_out(prog(t, cue("m2", "four standard") + i * 0.5, 0.6))
        if p <= 0:
            continue
        cx, cy = x0 + (i % 2) * (tw + 30), y0 + (i // 2) * (th + 24)
        rrect(d, (cx, cy, cx + tw, cy + th), 20, fade(mix(CARD, col, 0.2), p), outline=fade(col, p), width=3)
        d.text((cx + tw / 2, cy + th / 2), name, font=font(34, "Bold"), fill=fade(INK, p), anchor="mm")
    y = y0 + 2 * (th + 24) + 20
    x = x0
    for k, (lab, col, phrase) in enumerate((("Credit spread", VIOLET, "credit spread risk"),
                                            ("Volatility", VIOLET, "volatility risk"),
                                            ("Basis", GREEN, "basis risk"),
                                            ("Directional vs relative value", GREEN, "directional"))):
        p = ease_out(prog(t, cue("m2", phrase), 0.6))
        if p > 0:
            x = chip(d, x, y, lab, col, p, font(24, "SemiBold")) + 12
        if k == 1:
            x, y = x0, y + 64
    # multi-leg decomposition: a cross-currency swap split into its exposures
    p = ease_out(prog(t, cue("m2", "decompose"), 0.8))
    if p <= 0:
        return
    by = y1 - 120
    rrect(d, (x0, by, x0 + 250, by + 90), 18, fade(CARD, p), outline=fade(INK, p), width=2)
    d.text((x0 + 125, by + 45), "Cross-currency swap", font=font(22, "Bold"), fill=fade(INK, p), anchor="mm")
    legs = [("USD rates", BLUE), ("EUR rates", BLUE), ("EUR/USD FX", AMBER)]
    for i, (lab, col) in enumerate(legs):
        pl = ease_out(prog(t, cue("m2", "decompose") + 0.4 + i * 0.3, 0.5))
        if pl <= 0:
            continue
        lx, ly = x0 + 400, by - 70 + i * 80
        d.line([(x0 + 250, by + 45), (lx, ly + 28)], fill=fade(col, pl), width=3)
        rrect(d, (lx, ly, lx + 260, ly + 56), 16, fade(mix(CARD, col, 0.2), pl), outline=fade(col, pl), width=2)
        d.text((lx + 130, ly + 28), lab, font=font(24, "SemiBold"), fill=fade(INK, pl), anchor="mm")


def v_greeks(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    items = [("Delta  Δ", 0.82, TEAL), ("Gamma  Γ", 0.35, BLUE), ("Vega  ν", -0.58, VIOLET),
             ("PV01", -0.71, AMBER), ("Curvature", -0.22, RED)]
    mid = x0 + 300 + (x1 - x0 - 300) / 2
    half = (x1 - x0 - 300) / 2 - 20
    rh = (y1 - y0) / len(items)
    d.line([(mid, y0), (mid, y1)], fill=AXIS, width=3)
    for i, (lab, v, col) in enumerate(items):
        p = ease_out(prog(t, 1.0 + i * dur * 0.07, 0.8))
        y = y0 + i * rh + rh / 2
        text(d, (x0, y - 18), lab, font(32, "Bold"), INK, p=prog(t, 0.6 + i * 0.15, 0.5), rise=0)
        if p > 0:
            xe = mid + v * half * p
            d.rounded_rectangle((min(mid, xe), y - 24, max(mid, xe), y + 24), radius=10, fill=col)
            d.text((xe + (14 if v > 0 else -14), y), f"{v * p:+.2f}", font=font(26, "SemiBold"),
                   fill=INK, anchor="lm" if v > 0 else "rm")


def v_curve(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    axes(d, x0, y0, x1, y1, 1, "Maturity (years)", "Yield")
    mats = np.linspace(0.25, 30, 80)
    base = 4.0 + 1.6 * (1 - np.exp(-mats / 6))
    par = base + 0.8
    steep = base + (mats / 30) * 1.2 - 0.4

    def pts(curve, frac):
        n = max(2, int(len(mats) * frac))
        return [(x0 + (x1 - x0) * m / 30, y1 - (y1 - y0) * (c - 2.5) / 5) for m, c in zip(mats[:n], curve[:n])]

    polyline(d, pts(base, ease_in_out(prog(t, 0.6, 2.0))), TEAL, 6)
    shock = cue("m4", "duration and convexity")
    twist = cue("m4", "key rate durations")
    if t > shock - 0.5:
        polyline(d, pts(par, ease_in_out(prog(t, shock, 1.5))), AMBER, 4)
        polyline(d, pts(steep, ease_in_out(prog(t, twist, 1.5))), VIOLET, 4)
    for k, (lab, col, st) in enumerate((("Base curve", TEAL, 1.0), ("Parallel +80bp", AMBER, shock),
                                        ("Steepener", VIOLET, twist))):
        text(d, (x0 + 40, y0 + k * 40), "■ " + lab, font(24, "SemiBold"), col, p=prog(t, st, 0.5), rise=0)
    p = ease_out(prog(t, cue("m4", "term structure models"), 0.6))
    x = x0 + 330
    for m in ("Vasicek", "CIR", "Hull–White"):
        x = chip(d, x, y0 - 6, m, BLUE, p, font(22, "SemiBold")) + 10


def v_smile(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    axes(d, x0, y0, x1, y1, 1, "Strike / Spot", "Implied vol")
    ks = np.linspace(0.7, 1.3, 60)
    for j, (lab, col, a, b) in enumerate((("1M", RED, 0.9, 0.18), ("6M", AMBER, 0.55, 0.2), ("2Y", TEAL, 0.3, 0.22))):
        p = ease_in_out(prog(t, 0.8 + j * 1.0, 1.6))
        n = int(len(ks) * p)
        vol = b + a * (ks - 1.02) ** 2 - 0.05 * (ks - 1)
        pts = [(x0 + (x1 - x0) * (k - 0.7) / 0.6, y1 - (y1 - y0) * (v - 0.12) / 0.22) for k, v in zip(ks[:n], vol[:n])]
        polyline(d, pts, col, 5)
        text(d, (x1 - 20, y0 + j * 40), f"■ {lab} expiry", font(24, "SemiBold"), col, anchor="ra",
             p=prog(t, 0.8 + j, 0.5), rise=0)
    p = ease_out(prog(t, cue("m5", "delta and gamma"), 0.6))
    x = x0 + 40
    for m in ("Delta", "Gamma", "Vega", "Theta", "Rho"):
        x = chip(d, x, y1 - 64, m, VIOLET, p, font(22, "SemiBold")) + 10


def _hist(d, box, t, start, show_var=True, show_es=False, normal=False):
    x0, y0, x1, y1 = box
    nb = len(HIST)
    bw = (x1 - x0) / nb
    mx = HIST.max()
    hmax = (y1 - y0) - 90
    for i, c in enumerate(HIST):
        p = ease_out(prog(t, start + i * 0.03, 0.5))
        if p <= 0:
            continue
        tail = EDGES[i + 1] <= VAR99 + 1e-9
        col = mix(BLUE, RED, prog(t, start + 2.0, 0.5)) if tail and show_var else BLUE
        h = hmax * c / mx * p
        d.rectangle((x0 + i * bw + 2, y1 - max(h, 3), x0 + (i + 1) * bw - 2, y1), fill=fade(col, p))
    d.line([(x0, y1 + 2), (x1, y1 + 2)], fill=AXIS, width=3)
    d.text((x0, y1 + 12), "Loss", font=font(24, "Medium"), fill=MUTED)
    d.text((x1, y1 + 12), "Profit", font=font(24, "Medium"), fill=MUTED, anchor="ra")

    def xv(v):
        return x0 + (x1 - x0) * (v - EDGES[0]) / (EDGES[-1] - EDGES[0])

    if normal:
        pn = ease_in_out(prog(t, start + 3.0, 1.5))
        xs = np.linspace(-6, 6, 120)[: int(120 * pn)]
        sd = PNL.std()
        pts = [(xv(x), y1 - hmax * norm_pdf(x / sd) / norm_pdf(0) * 0.92) for x in xs]
        polyline(d, pts, AMBER, 4)
    if show_var:
        pv = ease_out(prog(t, start + 2.0, 0.7))
        if pv > 0:
            vx = xv(VAR99)
            d.line([(vx, y1), (vx, y1 - (hmax + 20) * pv)], fill=AMBER, width=5)
            rrect(d, (vx - 8, y0 - 6, vx + 250, y0 + 50), 16, fade(AMBER, pv))
            d.text((vx + 121, y0 + 22), "99% VaR", font=font(30, "Bold"), fill=fade(BG, pv), anchor="mm")
    if show_es:
        pe = ease_out(prog(t, start + 3.5, 0.7))
        if pe > 0:
            ex = xv(ES975)
            d.line([(ex, y1), (ex, y1 - (hmax * 0.6) * pe)], fill=RED, width=5)
            rrect(d, (ex - 8, y0 + 70, ex + 290, y0 + 126), 16, fade(RED, pe))
            d.text((ex + 141, y0 + 98), "97.5% ES", font=font(30, "Bold"), fill=fade(INK, pe), anchor="mm")


def v_var(d, img, box, t, dur):
    _hist(d, box, t, 0.6, show_var=True, normal=True)
    p = ease_out(prog(t, cue("m6", "variance-covariance"), 0.6))
    x = box[2] - 330
    for m, c in (("Parametric", AMBER), ("Historical", BLUE)):
        x = chip(d, x, box[1] + 80, m, c, p, font(22, "SemiBold")) + 10


def v_mc(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    xs_end = x0 + (x1 - x0) * 0.72
    mid = (y0 + y1) / 2
    sc = (y1 - y0) / 2 / 20
    steps = MC_PATHS.shape[1]
    cols = [TEAL, BLUE, VIOLET, AMBER, GREEN]
    for j in range(MC_PATHS.shape[0]):
        p = ease_in_out(prog(t, 0.6 + j * 0.06, 2.5))
        n = int(steps * p)
        if n < 2:
            continue
        pts = [(x0 + (xs_end - x0) * i / (steps - 1), mid - MC_PATHS[j, i] * sc) for i in range(n)]
        polyline(d, pts, mix(BG, cols[j % 5], 0.6), 2)
    ph = ease_out(prog(t, 4.5, 1.0))
    if ph > 0:
        term = MC_PATHS[:, -1]
        hist, edges = np.histogram(term, bins=14, range=(-16, 16))
        bh = (edges[1] - edges[0]) * sc
        for i, c in enumerate(hist):
            yc = mid - (edges[i] + edges[i + 1]) / 2 * sc
            w = (x1 - xs_end - 40) * c / hist.max() * ph
            col = RED if edges[i + 1] <= -9 else TEAL
            d.rectangle((xs_end + 30, yc - bh / 2 + 2, xs_end + 30 + w, yc + bh / 2 - 2), fill=col)
        text(d, (xs_end + 30, y0 - 10), "Simulated P&L", font(24, "SemiBold"), MUTED, p=ph, rise=0)
    p = ease_out(prog(t, cue("m7", "variance reduction"), 0.6))
    x = x0
    for m in ("Variance reduction", "Non-linear portfolios"):
        x = chip(d, x, y1 - 10, m, VIOLET, p) + 12


def v_es(d, img, box, t, dur):
    _hist(d, box, t, 0.6, show_var=True, show_es=True)
    text(d, (box[0], box[3] + 50), "VaR: where the tail starts", font(26, "SemiBold"), AMBER,
         p=prog(t, cue("m8", "coherent risk measures"), 0.5), rise=0)
    text(d, (box[2], box[3] + 50), "ES: how bad it gets", font(26, "SemiBold"), RED, anchor="ra",
         p=prog(t, cue("m8", "how bad the tail"), 0.5), rise=0)


def v_reval(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    axes(d, x0, y0, x1, y1, 1, "Yield change (bp)", "Bond P&L")
    dy = np.linspace(-300, 300, 121)
    D, C = 7.5, 80.0
    full = 100 * ((1 + 0.05) ** 10 / (1 + 0.05 + dy / 10000) ** 10 - 1)
    dur_only = -D * dy / 100
    dur_conv = dur_only + 0.5 * C * (dy / 10000) ** 2 * 100

    def pts(c, frac):
        n = max(2, int(len(dy) * frac))
        return [(x0 + (x1 - x0) * (a + 300) / 600, (y0 + y1) / 2 - (y1 - y0) * b / 70) for a, b in zip(dy[:n], c[:n])]

    curves = [("Full revaluation", TEAL, full, "full revaluation"),
              ("Duration only", AMBER, dur_only, "partial revaluation"),
              ("Duration + convexity", VIOLET, dur_conv, "sensitivity-based")]
    for j, (lab, col, c, phrase) in enumerate(curves):
        st = cue("m9", phrase, 2 + j)
        polyline(d, pts(c, ease_in_out(prog(t, st, 1.5))), col, 5)
        text(d, (x1 - 10, y0 + j * 40), "■ " + lab, font(24, "SemiBold"), col, anchor="ra", p=prog(t, st, 0.5),
             rise=0)
    pe = ease_out(prog(t, cue("m9", "where the shortcut"), 0.8))
    if pe > 0:
        i = 116  # large rate rise: duration alone overstates the loss
        xa, ya = pts(full, 1)[i]
        _, yb = pts(dur_only, 1)[i]
        d.line([(xa, ya), (xa, yb)], fill=fade(RED, pe), width=4)
        d.text((xa - 16, (ya + yb) / 2), "approximation error", font=font(24, "SemiBold"), fill=fade(RED, pe),
               anchor="rm")


def v_pca(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    axes(d, x0, y0, x1, y1, 1, "Maturity", "Factor loading")
    mid = (y0 + y1) / 2
    d.line([(x0, mid), (x1, mid)], fill=GRID, width=2)
    m = np.linspace(0, 1, 60)
    facs = [("Level", TEAL, 0.55 + 0.05 * m), ("Slope", AMBER, -0.6 + 1.2 * m),
            ("Curvature", VIOLET, 0.7 - 2.6 * m + 2.4 * m * m)]
    for j, (lab, col, f) in enumerate(facs):
        p = ease_in_out(prog(t, cue("m9", "level") - 0.5 + j * 0.8 if j else 0.8, 1.5))
        n = int(len(m) * p)
        pts = [(x0 + (x1 - x0) * a, mid - (y1 - y0) * 0.45 * b) for a, b in zip(m[:n], f[:n])]
        polyline(d, pts, col, 5)
        text(d, (x1 - 20, y0 + j * 40), f"■ {lab}", font(24, "SemiBold"), col, anchor="ra",
             p=prog(t, 0.8 + j * 0.8, 0.5), rise=0)


def v_beta(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    axes(d, x0, y0, x1, y1, 1, "Market return", "Stock return")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sx, sy = (x1 - x0) / 7, (y1 - y0) / 9
    n = int(len(BETA_X) * ease_out(prog(t, 0.6, 2.5)))
    for i in range(n):
        x, y = cx + BETA_X[i] * sx, cy - BETA_Y[i] * sy
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=mix(BG, BLUE, 0.8))
    pl = ease_in_out(prog(t, cue("m10", "beta, factor models", 3.0), 1.2))
    if pl > 0:
        xa, xb = -3.2, -3.2 + 6.4 * pl
        d.line([(cx + xa * sx, cy - 1.24 * xa * sy), (cx + xb * sx, cy - 1.24 * xb * sy)], fill=AMBER, width=6)
        rrect(d, (x0 + 30, y0 + 10, x0 + 250, y0 + 70), 18, fade(AMBER, pl))
        d.text((x0 + 140, y0 + 40), "β = 1.24", font=font(32, "Bold"), fill=fade(BG, pl), anchor="mm")


def v_fx(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    ccys = [("USD", 0.9), ("EUR", -0.55), ("GBP", 0.35), ("JPY", -0.7), ("SGD", 0.25)]
    mid = (y0 + y1) / 2
    bw = (x1 - x0) / len(ccys)
    sc = (y1 - y0) / 2 - 40
    d.line([(x0, mid), (x1, mid)], fill=AXIS, width=3)
    ph = ease_out(prog(t, cue("m11", "hedging strategies"), 1.0))
    for i, (c, v) in enumerate(ccys):
        p = ease_out(prog(t, 0.8 + i * 0.25, 0.8))
        cx = x0 + bw * i + bw / 2
        yv = mid - v * sc * p
        d.rounded_rectangle((cx - 50, min(mid, yv), cx + 10, max(mid, yv)), radius=8, fill=TEAL if v > 0 else RED)
        if ph > 0:
            yh = mid + v * sc * 0.85 * ph
            d.rounded_rectangle((cx + 16, min(mid, yh), cx + 60, max(mid, yh)), radius=8,
                                fill=mix(BG, MUTED, 0.6))
        d.text((cx, y1 + 10), c, font=font(28, "Bold"), fill=INK, anchor="ma")
    text(d, (x0, y0 - 10), "■ Net exposure", font(24, "SemiBold"), TEAL, p=prog(t, 0.8, 0.5), rise=0)
    text(d, (x0 + 260, y0 - 10), "■ Hedge", font(24, "SemiBold"), MUTED, p=ph, rise=0)


def v_commodity(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    axes(d, x0, y0, x1, y1, 1, "Delivery month", "Futures price")
    m = np.arange(0, 24)
    contango = 70 + 0.6 * m + 1.5 * np.sin(m / 12 * 2 * np.pi)
    back = 84 - 0.7 * m + 1.5 * np.sin(m / 12 * 2 * np.pi)
    for j, (lab, col, c) in enumerate((("Contango", TEAL, contango), ("Backwardation", AMBER, back))):
        st = cue("m12", "contango") if j == 0 else cue("m12", "backwardation")
        p = ease_in_out(prog(t, st, 1.5))
        n = int(len(m) * p)
        pts = [(x0 + (x1 - x0) * a / 23, y1 - (y1 - y0) * (b - 60) / 35) for a, b in zip(m[:n], c[:n])]
        polyline(d, pts, col, 5)
        for x, y in pts:
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=col)
        text(d, (x1 - 20, y0 + j * 40), f"■ {lab}", font(24, "SemiBold"), col, anchor="ra", p=p, rise=0)


def v_corr(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    labels = ["Equity", "Credit", "Rates", "USD", "Gold", "Oil"]
    n = 6
    size = min(x1 - x0 - 140, y1 - y0 - 60)
    cs = size / n
    gx, gy = x0 + 130, y0 + 40
    a = ease_in_out(prog(t, cue("m13", "copulas"), 2.5))
    mat = CORR_NORMAL + (CORR_CRISIS - CORR_NORMAL) * a
    for i in range(n):
        for j in range(n):
            p = ease_out(prog(t, 0.6 + (i + j) * 0.08, 0.5))
            v = mat[i, j]
            col = mix((30, 44, 80), RED if v > 0 else BLUE, abs(v))
            d.rectangle((gx + j * cs + 2, gy + i * cs + 2, gx + (j + 1) * cs - 2, gy + (i + 1) * cs - 2),
                        fill=fade(col, p))
            if p > 0.5:
                d.text((gx + j * cs + cs / 2, gy + i * cs + cs / 2), f"{v:.2f}", font=font(20, "SemiBold"),
                       fill=INK, anchor="mm")
        d.text((gx - 14, gy + i * cs + cs / 2), labels[i], font=font(22, "Medium"), fill=MUTED, anchor="rm")
        d.text((gx + i * cs + cs / 2, gy - 10), labels[i], font=font(20, "Medium"), fill=MUTED, anchor="md")
    lab = "Calm market" if a < 0.5 else "Stress: dependence rises in the tails"
    text(d, (gx, gy + size + 18), lab, font(26, "SemiBold"), AMBER if a < 0.5 else RED, p=1, rise=0)


def v_stress(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    sc = [("2008 crisis replay", -0.92, RED), ("COVID shock 2020", -0.71, RED), ("Rates +200bp", -0.44, AMBER),
          ("Equity −30%", -0.58, AMBER), ("Reverse stress: break point", -1.0, VIOLET)]
    lw = 380
    rh = (y1 - y0) / len(sc)
    right = x1 - 20
    full = x1 - x0 - lw - 120
    for i, (lab, v, col) in enumerate(sc):
        st = cue("m14", "reverse stress") if i == 4 else 0.8 + i * 0.5
        p = ease_out(prog(t, st, 0.8))
        y = y0 + i * rh + rh / 2
        text(d, (x0, y - 16), lab, font(28, "SemiBold"), INK, p=prog(t, st, 0.5), rise=0)
        if p > 0:
            w = full * -v * p
            d.rounded_rectangle((right - w, y - 22, right, y + 22), radius=10, fill=col)
            d.text((right - w - 12, y), f"{v * 100 * p:.0f}%", font=font(24, "Bold"), fill=INK, anchor="rm")
    d.text((right, y1 + 6), "Portfolio P&L under scenario (% of capital buffer)", font=font(22), fill=MUTED,
           anchor="ra")


def v_backtest(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    x1b = x1 - 220
    mid = (y0 + y1) / 2
    sc = (y1 - y0) / 2 / 3.6
    n = len(BT_PNL)
    bw = (x1b - x0) / n
    k = int(n * ease_in_out(prog(t, 0.6, dur * 0.35)))
    d.line([(x0, mid), (x1b, mid)], fill=AXIS, width=2)
    exc = 0
    for i in range(k):
        v = BT_PNL[i]
        y = mid - v * sc
        breach = v < BT_VAR[i]
        exc += breach
        d.line([(x0 + i * bw, mid), (x0 + i * bw, y)], fill=RED if breach else mix(BG, BLUE, 0.8), width=2)
        if breach:
            d.ellipse((x0 + i * bw - 7, y - 7, x0 + i * bw + 7, y + 7), fill=RED)
    pts = [(x0 + i * bw, mid - BT_VAR[i] * sc) for i in range(k)]
    polyline(d, pts, AMBER, 4)
    text(d, (x0, y0 - 6), "— 99% VaR    | daily P&L    ● exception", font(22, "SemiBold"), MUTED,
         p=prog(t, 0.6, 0.5), rise=0)
    # traffic light
    tx = x1 - 150
    zone = 0 if exc <= 4 else (1 if exc <= 9 else 2)
    rrect(d, (tx - 60, y0 + 40, tx + 60, y0 + 330), 30, (16, 24, 46), outline=CARD_EDGE)
    for z, col in enumerate((GREEN, AMBER, RED)):
        cy = y0 + 95 + z * 90
        lit = [GREEN, AMBER, RED][zone] == col
        d.ellipse((tx - 34, cy - 34, tx + 34, cy + 34), fill=col if lit else mix(BG, col, 0.2))
    d.text((tx, y0 + 360), f"{exc} exceptions", font=font(26, "Bold"), fill=INK, anchor="ma")
    d.text((tx, y0 + 396), "Basel traffic light", font=font(22), fill=MUTED, anchor="ma")


def v_capital(d, img, box, t, dur):
    x0, y0, x1, y1 = box
    stacks = [("Standardised\napproach", [("Delta", 0.30, TEAL), ("Vega", 0.12, BLUE), ("Curvature", 0.10, VIOLET),
                                          ("DRC", 0.18, AMBER), ("RRAO", 0.05, RED)]),
              ("Internal models\napproach", [("ES", 0.40, TEAL), ("NMRF", 0.10, VIOLET),
                                             ("DRC", 0.15, AMBER)])]
    base = y1 - 70
    hmax = y1 - y0 - 120
    cw = 200
    for k, (lab, parts) in enumerate(stacks):
        st = cue("m16", "standardised") if k == 0 else cue("m16", "internal models")
        cx = x0 + 40 + k * 380
        y = base
        for i, (name, v, col) in enumerate(parts):
            p = ease_out(prog(t, st + i * 0.35, 0.6))
            if p <= 0:
                continue
            h = hmax * v * p
            d.rectangle((cx, y - h, cx + cw, y), fill=col)
            if p > 0.6:
                d.text((cx + cw + 16, y - h / 2), name, font=font(24, "SemiBold"), fill=INK, anchor="lm")
            y -= h + 4
        for j, line in enumerate(lab.split("\n")):
            text(d, (cx + cw / 2, base + 14 + j * 32), line, font(26, "Bold"), INK, anchor="ma",
                 p=prog(t, st, 0.5), rise=0)
    p = ease_out(prog(t, cue("m16", "risk governance"), 0.6))
    chip(d, x1 - 290, y0 - 20, "Limits & reporting", AMBER, p, font(22, "SemiBold"))


# ---------------------------------------------------------------- modules
PARTS = {1: ("Foundations & risk factors", TEAL), 2: ("Modeling by asset class", BLUE),
         3: ("Measuring & aggregating risk", AMBER), 4: ("Testing, validation & governance", VIOLET)}
MODULES = [  # (title, part, the four lessons, narration phrase that introduces each lesson, visual)
    ("Foundations of Market Risk", 1,
     ["Defining and Measuring Market Risk", "Market Risk vs Other Financial Risks",
      "The Trading Book, Banking Book, and Real-World Context", "Choosing and Testing a Market Risk Measure"],
     ["defining market risk", "differs from credit", "trading book", "choose a market risk measure"], v_pnl),
    ("Types and Classification of Market Risk Exposure", 1,
     ["The Four Standard Market-Risk Classes", "Credit Spread Risk and Volatility Risk",
      "Basis Risk and Directional vs Relative-Value Exposure", "Multi-Leg Exposure Decomposition"],
     ["four standard", "credit spread risk", "basis risk", "decompose"], v_classes),
    ("Risk Factors and Sensitivities", 1,
     ["Foundations of Risk Factors", "Sensitivity: Meaning and Measurement",
      "Curvature, Approximation Error, and Risk Factor Mapping", "FRTB Sensitivities, Common Confusions, and Review"],
     ["foundations of risk factors", "what a sensitivity", "curvature", "sensitivities required under FRTB"], v_greeks),
    ("Interest Rate Risk Modeling", 2,
     ["Yield Curve Fundamentals", "Duration and Convexity", "Key Rate Duration and Curve Risk",
      "Interest Rate Derivatives and Term Structure Models"],
     ["yield curve fundamentals", "duration and convexity", "key rate durations", "interest rate derivatives"], v_curve),
    ("Volatility and Options Risk (Greeks)", 2,
     ["Option Pricing Foundations", "Delta, Gamma, and Price Sensitivity", "Vega, Theta, and Rho",
      "Volatility Surfaces and Smile (Skew)"],
     ["foundations of option pricing", "delta and gamma", "vega, theta", "volatility surfaces"], v_smile),
    ("Value at Risk (VaR): Parametric and Historical", 3,
     ["VaR Foundations and Definitions", "Parametric (Variance-Covariance) VaR", "Historical Simulation VaR",
      "VaR Limitations and Method Comparison"],
     ["VaR foundations", "parametric", "historical simulation", "limitations"], v_var),
    ("Monte Carlo Simulations and Advanced VaR", 3,
     ["Monte Carlo Simulation Foundations", "Monte Carlo VaR Implementation", "Variance Reduction Techniques",
      "Simulation for Complex Portfolios"],
     ["foundations of Monte Carlo", "implement Monte Carlo VaR", "variance reduction", "complex portfolios"], v_mc),
    ("Expected Shortfall and Tail Risk", 3,
     ["Beyond VaR: Coherent Risk Measures", "Expected Shortfall Fundamentals", "Extreme Value Theory",
      "Fat Tails and Tail Dependence"],
     ["coherent risk measures", "fundamentals of expected shortfall", "extreme value theory", "fat tails"], v_es),
    ("Fixed Income Risk Modeling", 2,
     ["Fixed Income Instruments and Risk Factors", "Full Revaluation VaR for Fixed Income Portfolios",
      "Partial Revaluation and Sensitivity-Based VaR", "Comparing Partial and Full Revaluation in Practice"],
     ["fixed income instruments", "full revaluation", "partial revaluation", "compare partial"], v_reval),
    ("Equity Risk Modeling", 2,
     ["Equity Risk Fundamentals", "Beta, Factor Models, and CAPM", "Equity Volatility and Correlation",
      "Equity Derivatives Risk"],
     ["fundamentals of equity risk", "beta, factor models", "volatility and correlation", "equity derivatives"], v_beta),
    ("Foreign Exchange Risk Modeling", 2,
     ["FX Market Fundamentals", "FX Exposure Types", "FX Hedging Strategies", "FX Derivatives and Cross-Currency Risk"],
     ["how F-X markets work", "types of F-X exposure", "hedging strategies", "F-X derivatives"], v_fx),
    ("Commodity Risk Modeling", 2,
     ["Commodity Market Fundamentals", "Commodity Futures Curves and Basis", "Commodity Volatility and Seasonality",
      "Commodity Derivatives Risk"],
     ["commodity market fundamentals", "futures curves and basis", "volatility and seasonality",
      "commodity derivatives"], v_commodity),
    ("Correlation, Covariance and Portfolio Aggregation", 3,
     ["Correlation and Covariance Fundamentals", "Covariance Matrix Estimation", "Portfolio VaR Aggregation",
      "Copulas and Dependence Modeling"],
     ["fundamentals of correlation", "estimate covariance", "Aggregate VaR", "copulas"], v_corr),
    ("Stress Testing and Scenario Analysis", 4,
     ["Stress Testing Fundamentals", "Historical Scenario Analysis", "Hypothetical and Reverse Stress Testing",
      "Regulatory Stress Testing Frameworks"],
     ["stress testing fundamentals", "historical scenarios", "hypothetical and reverse", "regulatory stress testing"],
     v_stress),
    ("Backtesting and Model Validation", 4,
     ["Backtesting Fundamentals", "Backtesting Statistical Tests", "Model Validation Frameworks",
      "Model Risk Management"],
     ["backtesting fundamentals", "statistical tests", "model validation frameworks", "model risk management"],
     v_backtest),
    ("Regulatory Capital and Governance: Basel and FRTB", 4,
     ["Basel Framework Evolution", "FRTB Standardized Approach", "FRTB Internal Models Approach",
      "Risk Governance, Limits, and Reporting"],
     ["Basel framework evolved", "standardised approach", "internal models approach", "risk governance"], v_capital),
]


def make_module_scene(idx):
    title, part, lessons, cues, visual = MODULES[idx]
    sid = f"m{idx + 1}"
    pname, pcol = PARTS[part]

    def scene(d, img, t, dur):
        # left column
        text(d, (120, 150), f"MODULE {idx + 1:02d} / 16", font(28, "SemiBold"), pcol, p=prog(t, 0, 0.5), rise=16)
        pp = ease_out(prog(t, 0.1, 0.5))
        if pp > 0:
            chip(d, 120 + d.textlength(f"MODULE {idx + 1:02d} / 16", font=font(28, "SemiBold")) + 24, 144,
                 pname, pcol, pp, font(22, "SemiBold"))
        f = font(56, "Bold", True)
        lines = wrap(d, title, f, 790)
        for i, line in enumerate(lines):
            text(d, (120, 200 + i * 66), line, f, INK, p=prog(t, 0.15 + i * 0.1, 0.6))
        y = 200 + len(lines) * 66 + 30
        d.rectangle((120, y, 120 + 120 * ease_out(prog(t, 0.4, 0.6)), y + 6), fill=pcol)
        y += 36
        starts = [cue(sid, c, LEAD + CLIP[sid] * (0.15 + 0.2 * i)) - 0.3 for i, c in enumerate(cues)]
        lf = font(30, "SemiBold")
        for i, lesson in enumerate(lessons):
            p = ease_out(prog(t, starts[i], 0.6))
            if p <= 0:
                continue
            # the lesson being narrated is highlighted; earlier ones stay visible but quieter
            active = starts[i] <= t < (starts[i + 1] if i + 1 < len(starts) else dur)
            yy = y + i * min(138, (1000 - y) / 4) + (1 - p) * 20
            edge = pcol if active else CARD_EDGE
            rrect(d, (120, yy, 900, yy + 122), 22, fade(mix(CARD, pcol, 0.14 if active else 0.0), p),
                  outline=fade(edge, p), width=3 if active else 2)
            d.ellipse((146, yy + 37, 194, yy + 85), fill=fade(pcol, p))
            d.text((170, yy + 61), str(i + 1), font=font(28, "Black", True), fill=fade(BG, p), anchor="mm")
            ls = wrap(d, lesson, lf, 660)[:2]
            for j, line in enumerate(ls):
                d.text((220, yy + 61 + (j - (len(ls) - 1) / 2) * 38), line, font=lf,
                       fill=fade(INK if active else mix(INK, MUTED, 0.35), p), anchor="lm")
        # right visual
        pv = ease_out(prog(t, 0.3, 0.7))
        panel(d, (980, 150, 1840, 990), pv)
        if pv > 0.3:
            visual(d, img, (1060, 260, 1760, 880), t, dur)

    return sid, scene


# ---------------------------------------------------------------- other scenes
def s_hook(d, img, t, dur):
    x0, x1, y0, y1 = 1000, 1840, 260, 820
    lo, hi = PRICE.min() * 0.97, PRICE.max() * 1.02
    for gy in range(6):
        y = y0 + (y1 - y0) * gy / 5
        d.line([(x0, y), (x1, y)], fill=GRID, width=2)
    n = int(len(PRICE) * ease_in_out(prog(t, 0.3, dur * 0.35)))
    pts = [(x0 + (x1 - x0) * i / (len(PRICE) - 1), y1 - (y1 - y0) * (PRICE[i] - lo) / (hi - lo)) for i in range(n)]
    if n > 1:
        polyline(d, pts[:200], TEAL, 5)
        if n > 200:
            polyline(d, pts[199:], RED, 5)
        x, y = pts[-1]
        col = RED if n > 200 else TEAL
        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=col)
        d.text((x1, y0 - 50), f"{PRICE[n - 1]:,.2f}", font=font(40, "Bold"), fill=col, anchor="ra")
    text(d, (120, 230), "Markets move", font(96, "Bold", True), INK, p=prog(t, 0.3, 0.7))
    text(d, (120, 340), "every day.", font(96, "Bold", True), TEAL, p=prog(t, 0.6, 0.7))
    for i, (yr, lab) in enumerate((("2008", "Global financial crisis"), ("2020", "COVID market shock"))):
        p = ease_out(prog(t, cue("hook", "In 2008") + i * 0.8, 0.7))
        if p > 0:
            bx = 120 + i * 400
            rrect(d, (bx, 520 + (1 - p) * 20, bx + 370, 660 + (1 - p) * 20), 24, fade(CARD, p), outline=fade(RED, p))
            d.text((bx + 30, 540 + (1 - p) * 20), yr, font=font(52, "Black", True), fill=fade(RED, p))
            d.text((bx + 30, 608 + (1 - p) * 20), lab, font=font(26, "Medium"), fill=fade(MUTED, p))
    text(d, (120, 740), "Someone has to measure it,", font(48, "SemiBold"), INK, p=prog(t, cue("hook", "The people"), 0.7))
    text(d, (120, 802), "model it, and keep it in check.", font(48, "SemiBold"), INK,
         p=prog(t, cue("hook", "The people") + 0.5, 0.7))
    text(d, (120, 900), "This course is how you become that person.", font(40, "Bold"), AMBER,
         p=prog(t, cue("hook", "This course"), 0.7))


def s_glance(d, img, t, dur):
    text(d, (120, 200), "A RISKHUB COURSE", font(32, "SemiBold"), TEAL, p=prog(t, 0, 0.6), rise=16)
    text(d, (120, 250), "Market Risk", font(132, "Black", True), INK, p=prog(t, 0.15, 0.8))
    text(d, (120, 395), "Modeling", font(132, "Black", True), TEAL, p=prog(t, 0.35, 0.8))
    w = 380 * ease_out(prog(t, 0.8, 0.8))
    if w > 1:
        d.rectangle((124, 570, 124 + w, 580), fill=AMBER)
    for i, line in enumerate(["From the foundations of market risk to the", "models banks use every day."]):
        text(d, (120, 630 + i * 54), line, font(40), MUTED, p=prog(t, 1.0 + i * 0.15, 0.7))
    stats = [("16", "Modules", TEAL, cue("glance", "sixteen modules")),
             ("2", "Capstone projects", AMBER, cue("glance", "capstone")),
             ("Python", "Hands-on labs", BLUE, cue("glance", "hands-on")),
             ("✓", "Certificate of Completion", GREEN, cue("glance", "Certificate"))]
    for i, (big, lab, col, st) in enumerate(stats):
        p = ease_out(prog(t, st, 0.7))
        if p <= 0:
            continue
        cx = 1080 + (i % 2) * 380
        cy = 230 + (i // 2) * 300 + (1 - p) * 30
        rrect(d, (cx, cy, cx + 350, cy + 260), 28, fade(CARD, p), outline=fade(col, p), width=3)
        if big == "✓":
            d.ellipse((cx + 40, cy + 40, cx + 130, cy + 130), fill=fade(col, p))
            check(d, cx + 85, cy + 87, 44, BG, 8)
        else:
            d.text((cx + 40, cy + 30), big, font=font(96 if len(big) < 3 else 72, "Black", True), fill=fade(col, p))
        for j, line in enumerate(wrap(d, lab, font(32, "SemiBold"), 290)):
            d.text((cx + 40, cy + 160 + j * 40), line, font=font(32, "SemiBold"), fill=fade(INK, p))


INSTRUCTORS = [
    ("Prateek Yadav", "CEO, RiskHub", "prateek-yadav", ["FRM", "CQF"], "J.P. Morgan · EY · PwC", "IIT Kanpur", TEAL,
     "Prateek"),
    ("Sudhanshu Kanwar", "Instructor, RiskHub", "sudhanshu-kanwar", ["FRM", "CFA", "CQF"], "Goldman Sachs · HSBC",
     "IIM Ahmedabad", AMBER, "Sudhanshu"),
]
_photos = {}


def photo(slug, w, h, radius=28):
    key = (slug, w, h)
    if key not in _photos:
        _photos[key] = None
        for ext in ("jpg", "jpeg", "png", "webp"):
            path = os.path.join(PHOTO_DIR, f"{slug}.{ext}")
            if os.path.exists(path):
                im = Image.open(path).convert("RGB")
                ar = w / h
                if im.width / im.height > ar:
                    cw = int(im.height * ar)
                    im = im.crop(((im.width - cw) // 2, 0, (im.width + cw) // 2, im.height))
                else:
                    ch = int(im.width / ar)
                    top = int((im.height - ch) * 0.3)
                    im = im.crop((0, top, im.width, top + ch))
                im = im.resize((w, h), Image.LANCZOS)
                mask = Image.new("L", (w * 3, h * 3), 0)
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * 3, h * 3), radius=radius * 3, fill=255)
                _photos[key] = (im, mask.resize((w, h), Image.LANCZOS))
                break
    return _photos[key]


def instructor_card(d, img, x, y, inst, p, pw=300, ph=360):
    name, role, slug, creds, work, edu, col, _ = inst
    rrect(d, (x, y, x + 820, y + 420), 32, fade(CARD, p), outline=fade(CARD_EDGE, p))
    px, py = x + 30, y + 30
    d.rounded_rectangle((px - 5, py - 5, px + pw + 5, py + ph + 5), radius=32, fill=fade(col, p))
    ph_ = photo(slug, pw, ph)
    if ph_ and p > 0.05:
        face, mask = ph_
        img.paste(Image.blend(Image.new("RGB", face.size, BG), face, p), (int(px), int(py)), mask)
    tx = x + pw + 70
    d.text((tx, y + 40), name, font=font(46, "Bold"), fill=fade(INK, p))
    d.text((tx, y + 104), role, font=font(30, "Medium"), fill=fade(col, p))
    cx = tx
    for c in creds:
        cx = chip(d, cx, y + 156, c, col, p, font(24, "Bold")) + 12
    for j, (label, val) in enumerate((("EXPERIENCE", work), ("EDUCATION", edu))):
        ry = y + 240 + j * 86
        d.line([(tx, ry - 14), (x + 790, ry - 14)], fill=fade(CARD_EDGE, p), width=2)
        d.text((tx, ry), label, font=font(22, "SemiBold"), fill=fade(MUTED, p))
        d.text((tx, ry + 30), val, font=font(32, "SemiBold"), fill=fade(INK, p))


def s_instructors(d, img, t, dur):
    header(d, t, "LEARN FROM PRACTITIONERS", "Your instructors")
    for i, inst in enumerate(INSTRUCTORS):
        st = 0.6 if i == 0 else cue("instructors", "Sudhanshu") - 0.3
        p = ease_out(prog(t, st, 0.8))
        if p > 0:
            instructor_card(d, img, 120 + i * 880, 400 + (1 - p) * 40, inst, p)


def s_roadmap(d, img, t, dur):
    header(d, t, "THE CURRICULUM", "16 modules, four parts")
    cues = [cue("roadmap", "First"), cue("roadmap", "Then, risk modeling"), cue("roadmap", "Then, how risk"),
            cue("roadmap", "And finally")]
    # legend
    for part, (pname, pcol) in PARTS.items():
        p = ease_out(prog(t, cues[part - 1], 0.5))
        if p > 0:
            lx, ly = 1060 + ((part - 1) % 2) * 400, 215 + ((part - 1) // 2) * 50
            d.ellipse((lx, ly - 11, lx + 22, ly + 11), fill=fade(pcol, p))
            d.text((lx + 34, ly), pname, font=font(26, "SemiBold"), fill=fade(INK, p), anchor="lm")
    cw, ch = 405, 140
    for i, (title, part, *_rest) in enumerate(MODULES):
        r, c = divmod(i, 4)
        cx, cy = 120 + c * (cw + 20), 400 + r * (ch + 18)
        pcol = PARTS[part][1]
        base = ease_out(prog(t, 0.5 + i * 0.08, 0.5))
        lit = ease_out(prog(t, cues[part - 1], 0.6))
        if base <= 0:
            continue
        rrect(d, (cx, cy, cx + cw, cy + ch), 20, fade(mix(CARD, pcol, 0.18 * lit), base),
              outline=fade(mix(CARD_EDGE, pcol, lit), base), width=3)
        d.text((cx + 22, cy + 18), f"{i + 1:02d}", font=font(30, "Black", True), fill=fade(mix(MUTED, pcol, lit), base))
        for j, line in enumerate(wrap(d, title, font(25, "SemiBold"), cw - 44)[:3]):
            d.text((cx + 22, cy + 58 + j * 28), line, font=font(25, "SemiBold"), fill=fade(INK, base))


CAPSTONES = [  # (title, stages, narration phrase for each stage, colour)
    ("Interest Rate Swap Pricing Model Validation",
     ["The Swap, the Curves, and the Valuation Framework", "Independent Replication and Benchmarking",
      "Testing the Model: Sensitivity, Stress and Outcomes", "Findings, Remediation and the Validation Decision"],
     ["set out the swap", "replicate and benchmark", "test the model's sensitivities", "findings, remediation"], BLUE),
    ("Historical VaR Model Validation",
     ["The Portfolio, the Risk Factors and the VaR Engine", "Independent Replication of the VaR Calculation",
      "Testing the Model: Backtesting, Stress and Attribution", "Findings, Capital Impact and the Validation Decision"],
     ["document the portfolio", "replicate the VaR calculation", "test the model with backtesting",
      "findings, the capital impact"], AMBER),
]


def s_capstones(d, img, t, dur):
    header(d, t, "APPLY EVERYTHING", "Two capstone projects", col=AMBER)
    text(d, (1800, 210), "Each one a full, bank-style model validation", font(30, "Medium"), MUTED, anchor="ra",
         p=prog(t, cue("capstones", "Each one"), 0.6), rise=10)
    cw = 820
    intro = [cue("capstones", "In the first"), cue("capstones", "In the second")]
    for k, (title, stages, phrases, col) in enumerate(CAPSTONES):
        p = ease_out(prog(t, intro[k] - 0.3, 0.8))
        if p <= 0:
            continue
        cx, cy = 120 + k * (cw + 40), 360 + (1 - p) * 30
        rrect(d, (cx, cy, cx + cw, cy + 640), 30, fade(CARD, p), outline=fade(col, p), width=3)
        d.text((cx + 40, cy + 34), f"CAPSTONE PROJECT {k + 1}", font=font(24, "Bold"), fill=fade(col, p))
        for j, line in enumerate(wrap(d, title, font(40, "Bold"), cw - 80)[:2]):
            d.text((cx + 40, cy + 74 + j * 48), line, font=font(40, "Bold"), fill=fade(INK, p))
        for i, (stage, phrase) in enumerate(zip(stages, phrases)):
            st = cue("capstones", phrase, intro[k] + 2 + i * 2.5) - 0.3
            ps = ease_out(prog(t, st, 0.6))
            if ps <= 0:
                continue
            sy = cy + 200 + i * 106 + (1 - ps) * 16
            rrect(d, (cx + 30, sy, cx + cw - 30, sy + 92), 18, fade(mix(CARD, col, 0.12), ps),
                  outline=fade(mix(CARD_EDGE, col, 0.6), ps), width=2)
            d.ellipse((cx + 52, sy + 24, cx + 96, sy + 68), fill=fade(col, ps))
            d.text((cx + 74, sy + 46), str(i + 1), font=font(26, "Black", True), fill=fade(BG, ps), anchor="mm")
            ls = wrap(d, stage, font(28, "SemiBold"), cw - 170)[:2]
            for j, line in enumerate(ls):
                d.text((cx + 120, sy + 46 + (j - (len(ls) - 1) / 2) * 34), line, font=font(28, "SemiBold"),
                       fill=fade(INK, ps), anchor="lm")


def s_certificate(d, img, t, dur):
    header(d, t, "EARN YOUR CREDENTIAL", "Certificate of Completion", col=GREEN)
    text(d, (120, 420), "Complete all 16 modules", font(40, "SemiBold"), INK, p=prog(t, 0.6, 0.6))
    text(d, (120, 480), "and the capstone projects.", font(40, "SemiBold"), INK, p=prog(t, 0.8, 0.6))
    text(d, (120, 580), "Add it to your résumé", font(36), MUTED, p=prog(t, cue("certificate", "ready to add"), 0.6))
    text(d, (120, 630), "and LinkedIn profile.", font(36), MUTED,
         p=prog(t, cue("certificate", "ready to add") + 0.2, 0.6))
    p = ease_out(prog(t, cue("certificate", "Certificate of Completion") - 0.8, 1.0))
    if p <= 0:
        return
    cream, ink, gold = (250, 246, 236), (22, 30, 52), (184, 145, 60)
    x0, y0 = 960, 330 + (1 - p) * 40
    x1, y1 = x0 + 860, y0 + 600
    rrect(d, (x0, y0, x1, y1), 12, fade(cream, p))
    d.rectangle((x0 + 18, y0 + 18, x1 - 18, y1 - 18), outline=fade(gold, p), width=4)
    d.rectangle((x0 + 30, y0 + 30, x1 - 30, y1 - 30), outline=fade(gold, p), width=1)
    cx = (x0 + x1) / 2
    d.text((cx, y0 + 70), "RiskHub", font=font(34, "Bold"), fill=fade(ink, p), anchor="ma")
    d.text((cx, y0 + 130), "CERTIFICATE OF COMPLETION", font=font(40, "Black", True), fill=fade(gold, p), anchor="ma")
    d.text((cx, y0 + 200), "This certifies that", font=font(24, "Italic"), fill=fade(ink, p), anchor="ma")
    d.text((cx, y0 + 240), "Your Name", font=font(56, "BoldItalic"), fill=fade(ink, p), anchor="ma")
    d.line([(cx - 260, y0 + 312), (cx + 260, y0 + 312)], fill=fade(gold, p), width=2)
    d.text((cx, y0 + 330), "has successfully completed", font=font(24, "Italic"), fill=fade(ink, p), anchor="ma")
    d.text((cx, y0 + 370), "Market Risk Modeling", font=font(44, "Bold"), fill=fade(ink, p), anchor="ma")
    d.text((cx, y0 + 428), "16 modules · 2 capstone projects", font=font(24), fill=fade(ink, p), anchor="ma")
    for k, (nm, rl) in enumerate((("Prateek Yadav", "CEO, RiskHub"), ("Sudhanshu Kanwar", "Instructor, RiskHub"))):
        sx = x0 + 110 + k * 450
        d.text((sx + 140, y0 + 480), nm, font=font(30, "MediumItalic"), fill=fade(ink, p), anchor="ma")
        d.line([(sx, y0 + 522), (sx + 280, y0 + 522)], fill=fade(ink, p), width=2)
        d.text((sx + 140, y0 + 532), rl, font=font(20), fill=fade(ink, p), anchor="ma")
    # seal
    sx, sy = cx, y0 + 520
    d.ellipse((sx - 42, sy - 42, sx + 42, sy + 42), fill=fade(gold, p))
    check(d, sx, sy + 2, 40, fade(cream, p), 6)


ROLES = [
    ("Market Risk Analyst", "₹8–18 LPA", "$75k–120k"),
    ("Model Validation Analyst", "₹12–25 LPA", "$90k–150k"),
    ("Quantitative Risk Analyst", "₹15–35 LPA", "$100k–175k"),
    ("FRTB / Regulatory Capital Specialist", "₹18–40 LPA", "$120k–200k"),
    ("Market Risk Manager / VP", "₹35–60+ LPA", "$150k–250k+"),
]


def s_careers(d, img, t, dur):
    header(d, t, "WHERE THIS LEADS", "Roles and salaries", col=BLUE)
    x0, x1 = 120, 1800
    c1, c2 = 1060, 1440
    y = 380
    ph = ease_out(prog(t, 0.6, 0.6))
    if ph > 0:
        d.text((x0 + 30, y), "ROLE", font=font(24, "Bold"), fill=fade(MUTED, ph))
        d.text((c1, y), "INDIA (₹ / year)", font=font(24, "Bold"), fill=fade(TEAL, ph))
        d.text((c2, y), "UNITED STATES ($ / year)", font=font(24, "Bold"), fill=fade(AMBER, ph))
    india_at, us_at = cue("careers", "In India"), cue("careers", "In the United States")
    for i, (role, inr, usd) in enumerate(ROLES):
        st = cue("careers", "Market risk analysts") + i * 0.9
        p = ease_out(prog(t, st, 0.6))
        if p <= 0:
            continue
        ry = y + 50 + i * 96
        rrect(d, (x0, ry, x1, ry + 82), 18, fade(CARD, p), outline=fade(CARD_EDGE, p))
        d.text((x0 + 30, ry + 41), role, font=font(32, "SemiBold"), fill=fade(INK, p), anchor="lm")
        pi = ease_out(prog(t, india_at + i * 0.25, 0.5))
        if pi > 0:
            d.text((c1, ry + 41), inr, font=font(34, "Bold"), fill=fade(TEAL, pi * p), anchor="lm")
        pu = ease_out(prog(t, us_at + i * 0.25, 0.5))
        if pu > 0:
            d.text((c2, ry + 41), usd, font=font(34, "Bold"), fill=fade(AMBER, pu * p), anchor="lm")
    text(d, (x0, 1000), "Indicative ranges compiled from public salary data (2026). Actual pay varies by firm, "
                        "city and experience.", font(22), MUTED, p=prog(t, cue("careers", "Actual pay"), 0.6), rise=0)


def s_cta(d, img, t, dur):
    cx = W / 2
    text(d, (cx, 220), "MARKET RISK MODELING", font(104, "Black", True), INK, anchor="ma", p=prog(t, 0, 0.8))
    text(d, (cx, 350), "16 modules · 2 capstone projects · Certificate of Completion", font(40, "SemiBold"), TEAL,
         anchor="ma", p=prog(t, 0.4, 0.7))
    for i, inst in enumerate(INSTRUCTORS):
        p = ease_out(prog(t, 0.8 + i * 0.2, 0.7))
        if p <= 0:
            continue
        ax = cx - 340 + i * 420
        ph = photo(inst[2], 120, 120, radius=60)
        d.ellipse((ax - 5, 455, ax + 125, 585), fill=fade(inst[6], p))
        if ph:
            img.paste(Image.blend(Image.new("RGB", (120, 120), BG), ph[0], p), (int(ax), 460), ph[1])
        d.text((ax + 145, 490), inst[0], font=font(30, "Bold"), fill=fade(INK, p))
        d.text((ax + 145, 532), inst[1], font=font(24), fill=fade(MUTED, p))
    pb = ease_out(prog(t, cue("cta", "Enroll now") - 0.4, 0.7))
    if pb > 0:
        pulse = 1 + 0.025 * math.sin(max(0, t - cue("cta", "Enroll now")) * 5)
        bw, bh = 560 * pulse, 130 * pulse
        cy = 740 + (1 - pb) * 30
        rrect(d, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), int(bh / 2), fade(TEAL, pb))
        d.text((cx, cy), "Enroll now  →", font=font(54, "Bold"), fill=fade(BG, pb), anchor="mm")
        text(d, (cx, 860), "riskhub.org/courses/market-risk-modeling", font(40, "SemiBold"), INK, anchor="ma", p=pb)


SCENE_FN = {"hook": s_hook, "glance": s_glance, "instructors": s_instructors, "roadmap": s_roadmap,
            "capstones": s_capstones, "certificate": s_certificate, "careers": s_careers, "cta": s_cta}
for _i in range(16):
    _sid, _fn = make_module_scene(_i)
    SCENE_FN[_sid] = _fn
LABELS = {"hook": "Market Risk Modeling", "glance": "Course overview", "instructors": "Instructors",
          "roadmap": "Curriculum", "capstones": "Capstone projects", "certificate": "Certificate",
          "careers": "Careers", "cta": "Enroll"}
FADE = 0.4


def render_frame(t, bg=None):
    bg = bg if bg is not None else BG_IMG
    img = bg.copy()
    d = ImageDraw.Draw(img)
    sid = ORDER[-1]
    for s in ORDER:
        if START[s] <= t < START[s] + DUR[s]:
            sid = s
            break
    lt = t - START[sid]
    SCENE_FN[sid](d, img, lt, DUR[sid])
    alpha = clamp((DUR[sid] - lt) / FADE) if sid != ORDER[-1] else 1.0
    alpha = min(alpha, clamp(lt / 0.3) if sid != ORDER[0] else 1.0)
    if alpha < 1:
        img = Image.blend(bg, img, alpha)
        d = ImageDraw.Draw(img)
    label = LABELS.get(sid) or f"Module {int(sid[1:])} of 16"
    chrome(d, t, label)
    return img


BG_IMG = make_background()


def _frame_bytes(i):
    return render_frame(i / FPS).tobytes()


# ---------------------------------------------------------------- audio
def load_audio(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def make_audio(path, sr=44100):
    n = int(DURATION * sr) + sr
    tt = np.arange(n) / sr
    music = np.zeros(n)
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [196.0, 246.94, 293.66]]
    seg = 8.0
    for k in range(int(math.ceil(DURATION / seg)) + 1):
        s0 = int(k * seg * sr)
        if s0 >= n:
            break
        s1 = min(n, int((k + 1) * seg * sr + 1.5 * sr))
        lt = tt[s0:s1] - k * seg
        env = np.clip(lt / 1.5, 0, 1) * np.clip((seg + 1.5 - lt) / 1.5, 0, 1)
        for f in chords[k % 4]:
            for det in (-0.6, 0.6):
                music[s0:s1] += 0.05 * env * np.sin(2 * np.pi * (f + det) * lt)
            music[s0:s1] += 0.02 * env * np.sin(2 * np.pi * f / 2 * lt)
    beat = 60 / 92
    for b in np.arange(0, DURATION, beat):
        s0 = int(b * sr)
        lt = np.arange(min(int(0.25 * sr), n - s0)) / sr
        music[s0:s0 + len(lt)] += 0.06 * np.exp(-lt * 18) * np.sin(2 * np.pi * 55 * lt)
    music /= np.max(np.abs(music)) / 0.6
    voice = np.zeros(n)
    for sid in ORDER:
        p = fit_clip(sid)
        if os.path.exists(p):
            v = load_audio(p, sr)
            s0 = int((START[sid] + LEAD) * sr)
            v = v[: n - s0]
            voice[s0:s0 + len(v)] += v
    if np.max(np.abs(voice)) > 0:
        voice /= np.max(np.abs(voice))
    env = np.convolve(np.abs(voice), np.ones(sr // 4) / (sr // 4), mode="same")
    duck = 1 - 0.75 * np.clip(env / 0.04, 0, 1)
    out = music * duck * 0.5 + voice * 0.9
    out *= np.clip(tt / 1.0, 0, 1) * np.clip((DURATION - tt) / 2.5, 0, 1)
    out /= max(1.0, np.max(np.abs(out)) / 0.95)
    data = (out[: int(DURATION * sr)] * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(np.column_stack([data, data]).ravel().tobytes())


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    print(f"duration {DURATION:.1f}s", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "audio.wav")
        make_audio(wav)
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
               "-i", wav,
               "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        total = int(DURATION * FPS)
        with mp.Pool(max(1, (os.cpu_count() or 2) - 1)) as pool:
            for i, buf in enumerate(pool.imap(_frame_bytes, range(total), chunksize=8)):
                proc.stdin.write(buf)
                if i % 1800 == 0:
                    print(f"frame {i}/{total}", flush=True)
        proc.stdin.close()
        proc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        out_dir = os.environ.get("PREVIEW_DIR", ".")
        for spec in os.environ["PREVIEW"].split(","):
            sid, sec = spec.split(":")
            render_frame(START[sid] + float(sec)).save(os.path.join(out_dir, f"{sid}_{sec}.png"))
    else:
        main()
