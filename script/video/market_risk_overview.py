#!/usr/bin/env python3
"""Render a 90-second vertical (1080x1920) course overview video for
"Market Risk Modeling".

Frames are drawn with Pillow and piped to ffmpeg; a soft synth soundtrack
is generated with numpy and muxed in.

Usage: python3 script/video/market_risk_overview.py [output.mp4]
"""
import math
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
DURATION = 90.0
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/videos/market-risk-modeling-overview.mp4"

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
CARD = (22, 33, 62)
CARD_EDGE = (44, 60, 102)

FONT_DIR = "/usr/share/fonts/opentype/inter"
_font_cache = {}


def font(size, weight="Regular", display=False):
    key = (size, weight, display)
    if key not in _font_cache:
        fam = "InterDisplay" if display else "Inter"
        _font_cache[key] = ImageFont.truetype(f"{FONT_DIR}/{fam}-{weight}.otf", size)
    return _font_cache[key]


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


def text(d, xy, s, f, col, a=1.0, anchor="la", rise=40, p=None):
    """Draw text fading in and rising by `rise` px as p goes 0 -> 1."""
    p = a if p is None else p
    if p <= 0:
        return
    x, y = xy
    y += (1 - ease_out(p)) * rise
    d.text((x, y), s, font=f, fill=fade(col, ease_out(p)), anchor=anchor)


def rrect(d, box, r, fill, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def polyline(d, pts, col, width):
    if len(pts) >= 2:
        d.line(pts, fill=col, width=width, joint="curve")
        r = width / 2
        for x, y in (pts[0], pts[-1]):
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)


def check(d, cx, cy, s, col, width=7):
    d.line([(cx - s * 0.45, cy), (cx - s * 0.1, cy + s * 0.35), (cx + s * 0.5, cy - s * 0.4)],
           fill=col, width=width, joint="curve")


def make_background():
    g = np.linspace(0, 1, H)[:, None]
    arr = np.zeros((H, W, 3), dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * g
    # subtle grid
    arr[::90, :, :] += 7
    arr[:, ::90, :] += 7
    # soft teal glow top-right, violet bottom-left
    yy, xx = np.mgrid[0:H, 0:W]
    for (cx, cy, rad, col, k) in ((900, 250, 700, TEAL, 0.10), (100, 1750, 800, VIOLET, 0.09)):
        m = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad ** 2 / 2.5)))
        for i in range(3):
            arr[:, :, i] += m * col[i] * k
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- data (seeded)
rng = np.random.default_rng(7)

# scene 1: price path with a late drawdown
_steps = 220
_ret = rng.normal(0.0012, 0.012, _steps)
_ret[150:185] -= 0.016
PRICE = 100 * np.exp(np.cumsum(_ret))

# scene 4: daily P&L distribution (fat left tail)
_pnl = np.concatenate([rng.standard_t(4, 6000) * 1.0])
HIST, EDGES = np.histogram(_pnl, bins=33, range=(-5, 5))
VAR99 = float(np.quantile(_pnl, 0.01))

# scene 6: Vasicek short-rate paths
def vasicek_paths(n=7, steps=120, r0=0.045, k=1.6, theta=0.035, sig=0.006, dt=1 / 24):
    out = np.zeros((n, steps))
    for j in range(n):
        r = r0
        for i in range(steps):
            r += k * (theta - r) * dt + sig * math.sqrt(dt) * rng.normal()
            out[j, i] = r
    return out


PATHS = vasicek_paths(n=6)


def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bsm_call(S, K=100, T=0.5, r=0.04, v=0.25):
    if S <= 0:
        return 0.0
    d1 = (math.log(S / K) + (r + v * v / 2) * T) / (v * math.sqrt(T))
    d2 = d1 - v * math.sqrt(T)
    return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)


# ---------------------------------------------------------------- chrome
def header(d, t, num, title, start=0.0):
    p = prog(t, start, 0.6)
    text(d, (80, 250), f"MODULE {num}", font(34, "SemiBold"), TEAL, p=p, rise=20)
    text(d, (80, 300), title, font(84, "Bold", True), INK, p=prog(t, start + 0.12, 0.6))
    w = 160 * ease_out(prog(t, start + 0.3, 0.6))
    if w > 1:
        d.rectangle((80, 420, 80 + w, 428), fill=TEAL)


def chrome(d, t):
    # brand + progress bar shown on every frame
    d.rounded_rectangle((80, 110, 112, 142), radius=8, fill=TEAL)
    d.line([(88, 134), (96, 124), (102, 129), (108, 118)], fill=BG, width=4, joint="curve")
    d.text((128, 104), "RiskHub", font=font(38, "Bold"), fill=INK)
    d.text((W - 80, 112), "Market Risk Modeling", font=font(28, "Medium"), fill=MUTED, anchor="ra")
    d.rounded_rectangle((80, 172, W - 80, 178), radius=3, fill=(33, 45, 78))
    d.rounded_rectangle((80, 172, 80 + (W - 160) * t / DURATION, 178), radius=3, fill=TEAL)


# ---------------------------------------------------------------- scenes
def s_hook(d, t, dur):
    # animated price chart
    x0, x1, y0, y1 = 80, W - 80, 700, 1250
    lo, hi = PRICE.min() * 0.97, PRICE.max() * 1.02
    n = int(len(PRICE) * ease_in_out(prog(t, 0.1, 3.6)))
    pts = [(x0 + (x1 - x0) * i / (len(PRICE) - 1), y1 - (y1 - y0) * (PRICE[i] - lo) / (hi - lo))
           for i in range(n)]
    for gy in range(5):
        y = y0 + (y1 - y0) * gy / 4
        d.line([(x0, y), (x1, y)], fill=(30, 42, 74), width=2)
    if n > 1:
        split = min(n, 150)
        polyline(d, pts[:split], TEAL, 7)
        if n > 150:
            polyline(d, pts[149:], RED, 7)
        x, y = pts[-1]
        col = RED if n > 150 else TEAL
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=col)
        d.ellipse((x - 26, y - 26, x + 26, y + 26), outline=col, width=3)
        val = PRICE[n - 1]
        d.text((x1, y0 - 60), f"{val:,.2f}", font=font(46, "Bold"), fill=col, anchor="ra")
    text(d, (80, 400), "Markets move", font(104, "Bold", True), INK, p=prog(t, 0.2, 0.7))
    text(d, (80, 520), "every second.", font(104, "Bold", True), TEAL, p=prog(t, 0.6, 0.7))
    text(d, (80, 1400), "So how much", font(92, "Bold", True), INK, p=prog(t, 2.5, 0.6))
    text(d, (80, 1510), "could you lose?", font(92, "Bold", True), RED, p=prog(t, 3.0, 0.6))


def s_title(d, t, dur):
    text(d, (80, 620), "A RISKHUB COURSE", font(38, "SemiBold"), TEAL, p=prog(t, 0.0, 0.6), rise=20)
    text(d, (80, 700), "Market Risk", font(150, "Black", True), INK, p=prog(t, 0.15, 0.8))
    text(d, (80, 865), "Modeling", font(150, "Black", True), TEAL, p=prog(t, 0.35, 0.8))
    w = 420 * ease_out(prog(t, 0.8, 0.8))
    if w > 1:
        d.rectangle((84, 1060, 84 + w, 1072), fill=AMBER)
    for i, line in enumerate(["Measure, model and manage the risk", "of trading portfolios — from first",
                              "principles to regulatory capital."]):
        text(d, (80, 1130 + i * 62), line, font(46, "Regular"), MUTED, p=prog(t, 1.2 + i * 0.15, 0.7))
    chips = ["VaR & ES", "Option pricing", "Rate models", "Basel / FRTB"]
    x = 80
    for i, c in enumerate(chips):
        f = font(34, "SemiBold")
        tw = d.textlength(c, font=f)
        p = ease_out(prog(t, 2.2 + i * 0.2, 0.5))
        if p > 0:
            y = 1380 + (1 - p) * 30 + (i // 2) * 100
            xx = 80 if i % 2 == 0 else x
            rrect(d, (xx, y, xx + tw + 56, y + 76), 38, fade(CARD, p), outline=fade(CARD_EDGE, p))
            d.text((xx + 28, y + 38), c, font=f, fill=fade(INK, p), anchor="lm")
            if i % 2 == 0:
                x = xx + tw + 56 + 24


RISKS = [
    ("Equity", "Stocks & indices", TEAL),
    ("Interest rate", "Yield-curve shifts", BLUE),
    ("Currency", "FX rate moves", AMBER),
    ("Commodity", "Oil, metals, grains", RED),
    ("Margining", "Collateral & margin calls", VIOLET),
    ("Basis", "Hedge vs. exposure gap", (52, 211, 153)),
]


def s_types(d, t, dur):
    header(d, t, "01", "Know the risks")
    text(d, (80, 480), "Six sources of market risk, and", font(44), MUTED, p=prog(t, 0.6, 0.6))
    text(d, (80, 536), "what drives each of them.", font(44), MUTED, p=prog(t, 0.7, 0.6))
    cw, ch, gap = (W - 160 - 40) / 2, 300, 40
    for i, (name, sub, col) in enumerate(RISKS):
        p = ease_out(prog(t, 1.2 + i * 0.45, 0.6))
        if p <= 0:
            continue
        cx = 80 + (i % 2) * (cw + gap)
        cy = 680 + (i // 2) * (ch + gap) + (1 - p) * 60
        rrect(d, (cx, cy, cx + cw, cy + ch), 28, fade(CARD, p), outline=fade(CARD_EDGE, p))
        d.rounded_rectangle((cx + 36, cy + 40, cx + 100, cy + 104), radius=16, fill=fade(col, p))
        d.text((cx + 68, cy + 72), f"{i + 1}", font=font(36, "Bold"), fill=fade(BG, p) if p > 0.5 else fade(col, p),
               anchor="mm")
        d.text((cx + 36, cy + 150), name, font=font(50, "Bold"), fill=fade(INK, p))
        d.text((cx + 36, cy + 222), sub, font=font(33), fill=fade(MUTED, p))
    text(d, (W / 2, 1760), "Equity · Rates · FX · Commodities", font(36, "Medium"), MUTED,
         anchor="ma", p=prog(t, 4.4, 0.8))


def s_var(d, t, dur):
    header(d, t, "02", "Value at Risk")
    text(d, (80, 480), "The loss you won't exceed on", font(48, "Medium"), INK, p=prog(t, 0.6, 0.6))
    text(d, (80, 540), "99 days out of 100.", font(48, "Bold"), AMBER, p=prog(t, 0.75, 0.6))
    # histogram
    x0, x1, yb, hmax = 80, W - 80, 1260, 520
    nb = len(HIST)
    bw = (x1 - x0) / nb
    mx = HIST.max()
    for i, c in enumerate(HIST):
        p = ease_out(prog(t, 1.2 + i * 0.04, 0.5))
        if p <= 0:
            continue
        h = hmax * c / mx * p
        tail = EDGES[i + 1] <= VAR99 + 1e-9
        col = RED if tail and t > 3.4 else (BLUE if not tail else BLUE)
        if tail and t > 3.4:
            col = mix(BLUE, RED, prog(t, 3.4, 0.5))
        d.rectangle((x0 + i * bw + 3, yb - max(h, 3), x0 + (i + 1) * bw - 3, yb), fill=fade(col, p))
    d.line([(x0, yb + 2), (x1, yb + 2)], fill=(60, 76, 120), width=3)
    text(d, (x0, yb + 20), "Loss", font(30, "Medium"), MUTED, p=prog(t, 1.2, 0.5), rise=0)
    text(d, (x1, yb + 20), "Profit", font(30, "Medium"), MUTED, anchor="ra", p=prog(t, 1.2, 0.5), rise=0)
    # VaR marker
    pv = ease_out(prog(t, 3.6, 0.7))
    if pv > 0:
        vx = x0 + (x1 - x0) * (VAR99 - EDGES[0]) / (EDGES[-1] - EDGES[0])
        ytop = yb - hmax - 40
        d.line([(vx, yb), (vx, yb - (yb - ytop) * pv)], fill=AMBER, width=6)
        rrect(d, (vx - 10, ytop - 92, vx + 330, ytop - 10), 20, fade(AMBER, pv))
        d.text((vx + 160, ytop - 51), "99% 1-day VaR", font=font(38, "Bold"), fill=fade(BG, pv), anchor="mm")
        text(d, (vx + 30, yb - 260), "1% tail", font(32, "SemiBold"), RED, p=prog(t, 4.2, 0.6), rise=10)
    # methods
    text(d, (80, 1400), "Three ways to compute it", font(40, "SemiBold"), MUTED, p=prog(t, 5.6, 0.6))
    methods = [("Historical", TEAL), ("Parametric", BLUE), ("Monte Carlo", VIOLET)]
    cw = (W - 160 - 2 * 24) / 3
    for i, (m, col) in enumerate(methods):
        p = ease_out(prog(t, 6.2 + i * 0.35, 0.6))
        if p <= 0:
            continue
        cx, cy = 80 + i * (cw + 24), 1480 + (1 - p) * 40
        rrect(d, (cx, cy, cx + cw, cy + 150), 24, fade(CARD, p), outline=fade(col, p), width=3)
        d.text((cx + cw / 2, cy + 75), m, font=font(38, "Bold"), fill=fade(INK, p), anchor="mm")
    text(d, (80, 1690), "…plus Expected Shortfall, backtesting & stress.", font(36), MUTED,
         p=prog(t, 8.0, 0.7))


def s_pricing(d, t, dur):
    header(d, t, "03", "Pricing")
    text(d, (80, 480), "Black–Scholes–Merton: the link between", font(42), MUTED, p=prog(t, 0.6, 0.6))
    text(d, (80, 534), "an option and its underlying.", font(42), MUTED, p=prog(t, 0.7, 0.6))
    # formula typed in; the e^(-rT) exponent is drawn as a raised run
    segs = [("C = S·N(d₁) − K·e", 0), ("−rT", 1), ("·N(d₂)", 0)]
    fb, fs = font(66, "Bold"), font(40, "Bold")
    total_w = sum(d.textlength(sg, font=fs if sup else fb) for sg, sup in segs)
    n = int(sum(len(sg) for sg, _ in segs) * prog(t, 1.2, 1.6))
    rrect(d, (80, 630, W - 80, 790), 28, CARD, outline=CARD_EDGE)
    x = (W - total_w) / 2
    for sg, sup in segs:
        f = fs if sup else fb
        shown = sg[:max(0, n)]
        n -= len(sg)
        if shown:
            d.text((x, 685 if sup else 710), shown, font=f, fill=AMBER if sup else INK, anchor="lm")
        x += d.textlength(sg, font=f)
    # call value vs spot
    x0, x1, y0, y1 = 140, W - 100, 880, 1300
    smin, smax = 60, 140
    d.line([(x0, y1), (x1, y1)], fill=(60, 76, 120), width=3)
    d.line([(x0, y0), (x0, y1)], fill=(60, 76, 120), width=3)
    vmax = 45

    def pt(S, v):
        return (x0 + (x1 - x0) * (S - smin) / (smax - smin), y1 - (y1 - y0) * v / vmax)

    pp = ease_in_out(prog(t, 2.6, 1.6))
    k = int(80 * pp)
    payoff = [pt(smin + i, max(smin + i - 100, 0)) for i in range(k + 1)]
    value = [pt(smin + i, bsm_call(smin + i)) for i in range(k + 1)]
    if k > 1:
        for i in range(0, len(payoff) - 1, 2):
            d.line([payoff[i], payoff[i + 1]], fill=MUTED, width=4)
        polyline(d, value, TEAL, 7)
    text(d, (x0 + 40, y0), "— Option value today", font(32, "SemiBold"), TEAL, p=prog(t, 3.6, 0.5), rise=10)
    text(d, (x0 + 40, y0 + 50), "- - Payoff at expiry", font(32, "SemiBold"), MUTED, p=prog(t, 3.8, 0.5), rise=10)
    text(d, (x1, y1 + 16), "Spot price  S", font(30, "Medium"), MUTED, anchor="ra", p=prog(t, 2.6, 0.5), rise=0)
    # five inputs
    text(d, (80, 1390), "Five inputs", font(40, "SemiBold"), MUTED, p=prog(t, 4.6, 0.6))
    inputs = [("S", "Spot"), ("K", "Strike"), ("T", "Time"), ("σ", "Volatility"), ("r", "Rate")]
    cw = (W - 160 - 4 * 18) / 5
    for i, (sym, lab) in enumerate(inputs):
        p = ease_out(prog(t, 5.1 + i * 0.3, 0.6))
        if p <= 0:
            continue
        cx, cy = 80 + i * (cw + 18), 1460 + (1 - p) * 40
        rrect(d, (cx, cy, cx + cw, cy + 200), 24, fade(CARD, p), outline=fade(CARD_EDGE, p))
        d.text((cx + cw / 2, cy + 80), sym, font=font(72, "Bold"), fill=fade(AMBER, p), anchor="mm")
        d.text((cx + cw / 2, cy + 155), lab, font=font(28, "Medium"), fill=fade(MUTED, p), anchor="mm")
    text(d, (80, 1720), "Then the Greeks: how price reacts to each.", font(36), MUTED, p=prog(t, 7.6, 0.7))


def s_rates(d, t, dur):
    header(d, t, "04", "Interest rate models")
    text(d, (80, 480), "Simulate where rates go next —", font(42), MUTED, p=prog(t, 0.6, 0.6))
    text(d, (80, 534), "and what that does to bond prices.", font(42), MUTED, p=prog(t, 0.7, 0.6))
    x0, x1, y0, y1 = 80, W - 80, 700, 1300
    rlo, rhi = 0.02, 0.055
    for gy in range(8):
        y = y1 - (y1 - y0) * gy / 7
        d.line([(x0, y), (x1, y)], fill=(30, 42, 74), width=2)
        if gy % 2 == 0:
            d.text((x0, y - 8), f"{(rlo + (rhi - rlo) * gy / 7) * 100:.1f}%", font=font(26), fill=MUTED, anchor="lb")
    steps = PATHS.shape[1]
    cols = [TEAL, BLUE, VIOLET, AMBER, (52, 211, 153), RED, (125, 211, 252)]
    for j in range(PATHS.shape[0]):
        p = prog(t, 1.2 + j * 0.25, 2.6)
        n = int(steps * ease_in_out(p))
        if n < 2:
            continue
        pts = [(x0 + 60 + (x1 - x0 - 60) * i / (steps - 1), y1 - (y1 - y0) * (PATHS[j, i] - rlo) / (rhi - rlo))
               for i in range(n)]
        polyline(d, pts, mix(BG, cols[j % len(cols)], 0.85), 4)
    # long-run mean
    pm = ease_out(prog(t, 4.0, 0.8))
    if pm > 0:
        ym = y1 - (y1 - y0) * (0.035 - rlo) / (rhi - rlo)
        xe = x0 + 60 + (x1 - x0 - 60) * pm
        for xs in np.arange(x0 + 60, xe, 34):
            d.line([(xs, ym), (min(xs + 18, xe), ym)], fill=INK, width=4)
        text(d, (x1, y0 - 70), "- -  long-run mean θ", font(32, "SemiBold"), INK, anchor="ra", p=pm, rise=10)
    text(d, (80, 1400), "Short-rate models", font(40, "SemiBold"), MUTED, p=prog(t, 2.4, 0.6))
    models = [("Vasicek", TEAL), ("CIR", BLUE), ("Hull–White", VIOLET)]
    cw = (W - 160 - 2 * 24) / 3
    for i, (m, col) in enumerate(models):
        p = ease_out(prog(t, 2.8 + i * 0.6, 0.6))
        if p <= 0:
            continue
        cx, cy = 80 + i * (cw + 24), 1480 + (1 - p) * 40
        rrect(d, (cx, cy, cx + cw, cy + 150), 24, fade(CARD, p), outline=fade(col, p), width=3)
        d.text((cx + cw / 2, cy + 75), m, font=font(40, "Bold"), fill=fade(INK, p), anchor="mm")
    text(d, (80, 1690), "Build, calibrate and stress the yield curve.", font(36), MUTED, p=prog(t, 5.0, 0.7))


REGS = [
    ("Basel III & FRTB", "How banks capitalise trading books", TEAL),
    ("Expected Shortfall 97.5%", "The tail measure that replaced VaR", AMBER),
    ("Backtesting", "Proving your model against reality", BLUE),
    ("Stress testing", "Surviving the scenarios history forgot", RED),
]


def s_regs(d, t, dur):
    header(d, t, "05", "Regulation")
    text(d, (80, 480), "Where the models meet the rulebook.", font(42), MUTED, p=prog(t, 0.6, 0.6))
    for i, (title, sub, col) in enumerate(REGS):
        p = ease_out(prog(t, 1.1 + i * 0.6, 0.7))
        if p <= 0:
            continue
        y = 620 + i * 260
        x = 80 + (1 - p) * 120
        rrect(d, (x, y, W - 80, y + 220), 28, fade(CARD, p), outline=fade(CARD_EDGE, p))
        d.rectangle((x, y + 30, x + 10, y + 190), fill=fade(col, p))
        d.text((x + 56, y + 62), title, font=font(52, "Bold"), fill=fade(INK, p))
        d.text((x + 56, y + 138), sub, font=font(36), fill=fade(MUTED, p))
    text(d, (W / 2, 1700), "From model to capital charge.", font(40, "SemiBold"), TEAL, anchor="ma",
         p=prog(t, 4.0, 0.7))


OUTCOMES = [
    "Quantify portfolio risk with VaR & ES",
    "Price options with Black–Scholes–Merton",
    "Model and simulate interest rates",
    "Speak the language of regulators",
]


def s_outcomes(d, t, dur):
    text(d, (80, 300), "By the end,", font(96, "Bold", True), INK, p=prog(t, 0.0, 0.6))
    text(d, (80, 410), "you'll be able to", font(96, "Bold", True), TEAL, p=prog(t, 0.15, 0.6))
    for i, s in enumerate(OUTCOMES):
        p = ease_out(prog(t, 0.8 + i * 0.6, 0.6))
        if p <= 0:
            continue
        y = 640 + i * 240 + (1 - p) * 40
        d.ellipse((80, y, 180, y + 100), fill=fade(TEAL, p))
        pc = prog(t, 1.0 + i * 0.6, 0.4)
        if pc > 0:
            check(d, 130, y + 52, 50 * ease_out(pc), BG, 9)
        words = s.split(" ")
        line1, line2 = s, ""
        if d.textlength(s, font=font(46, "SemiBold")) > W - 320:
            cut = len(words) // 2 + 1
            line1, line2 = " ".join(words[:cut]), " ".join(words[cut:])
        d.text((220, y + 10 if line2 else y + 50), line1, font=font(46, "SemiBold"), fill=fade(INK, p),
               anchor="la" if line2 else "lm")
        if line2:
            d.text((220, y + 68), line2, font=font(46, "SemiBold"), fill=fade(INK, p))


def s_cta(d, t, dur):
    p = ease_out(prog(t, 0.0, 0.8))
    text(d, (W / 2, 620), "MARKET RISK", font(110, "Black", True), INK, anchor="ma", p=p)
    text(d, (W / 2, 750), "MODELING", font(110, "Black", True), TEAL, anchor="ma", p=prog(t, 0.15, 0.8))
    text(d, (W / 2, 940), "Turn market moves into", font(50), MUTED, anchor="ma", p=prog(t, 0.5, 0.7))
    text(d, (W / 2, 1008), "numbers you can manage.", font(50), MUTED, anchor="ma", p=prog(t, 0.6, 0.7))
    pb = ease_out(prog(t, 1.0, 0.7))
    if pb > 0:
        pulse = 1 + 0.03 * math.sin(max(0, t - 1.7) * 5) * (t > 1.7)
        bw, bh = 640 * pulse, 150 * pulse
        cx, cy = W / 2, 1230 + (1 - pb) * 40
        rrect(d, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), int(bh / 2), fade(TEAL, pb))
        d.text((cx, cy), "Enroll now  →", font=font(58, "Bold"), fill=fade(BG, pb), anchor="mm")
    text(d, (W / 2, 1400), "riskhub.org/courses/", font(42, "SemiBold"), INK, anchor="ma", p=prog(t, 1.4, 0.7))
    text(d, (W / 2, 1456), "market-risk-modeling", font(42, "SemiBold"), INK, anchor="ma", p=prog(t, 1.5, 0.7))

INSTRUCTORS = [
    ("Prateek Yadav", "CEO, RiskHub", "prateek-yadav", ["FRM", "CQF"],
     "JP Morgan · EY · PwC", "IIT Kanpur", TEAL),
    ("Sudhanshu Kanwar", "Instructor, RiskHub", "sudhanshu-kanwar", ["FRM", "CQF"],
     "Goldman Sachs · HSBC", "IIM Ahmedabad", AMBER),
]
PHOTO_DIR = "assets/images/instructors"
_photo_cache = {}


def avatar(slug, size):
    """Circular headshot from PHOTO_DIR/<slug>.(jpg|png), or None if absent."""
    if slug not in _photo_cache:
        _photo_cache[slug] = None
        for ext in ("jpg", "jpeg", "png", "webp"):
            path = os.path.join(PHOTO_DIR, f"{slug}.{ext}")
            if os.path.exists(path):
                im = Image.open(path).convert("RGB")
                side = min(im.size)
                im = im.crop(((im.width - side) // 2, 0, (im.width + side) // 2, side))
                im = im.resize((size, size), Image.LANCZOS)
                mask = Image.new("L", (size * 4, size * 4), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, size * 4, size * 4), fill=255)
                _photo_cache[slug] = (im, mask.resize((size, size), Image.LANCZOS))
                break
    return _photo_cache[slug]


def s_instructors(d, t, dur):
    img = d._image
    text(d, (80, 250), "LEARN FROM", font(34, "SemiBold"), TEAL, p=prog(t, 0.0, 0.6), rise=20)
    text(d, (80, 300), "Your instructors", font(84, "Bold", True), INK, p=prog(t, 0.12, 0.6))
    for i, (name, role, slug, creds, work, edu, col) in enumerate(INSTRUCTORS):
        delay = dur * 0.42
        if INSTRUCTOR2_AT is not None:
            delay = INSTRUCTOR2_AT - STARTS[SCENE_FNS.index(s_instructors)] - 0.6
        p = ease_out(prog(t, 0.6 + i * delay, 0.7))
        if p <= 0:
            continue
        y = 480 + i * 650 + (1 - p) * 60
        rrect(d, (80, y, W - 80, y + 600), 36, fade(CARD, p), outline=fade(CARD_EDGE, p))
        # avatar
        size, ax, ay = 200, 130, y + 50
        d.ellipse((ax - 8, ay - 8, ax + size + 8, ay + size + 8), fill=fade(col, p))
        ph = avatar(slug, size)
        if ph and p > 0.05:
            face, mask = ph
            img.paste(Image.blend(Image.new("RGB", face.size, BG), face, p), (int(ax), int(ay)), mask)
        else:
            d.ellipse((ax, ay, ax + size, ay + size), fill=fade((30, 44, 80), p))
            initials = "".join(w[0] for w in name.split())
            d.text((ax + size / 2, ay + size / 2), initials, font=font(84, "Bold", True),
                   fill=fade(col, p), anchor="mm")
        d.text((380, y + 80), name, font=font(54, "Bold"), fill=fade(INK, p))
        d.text((380, y + 156), role, font=font(36, "Medium"), fill=fade(col, p))
        cx = 380
        for c in creds:
            f = font(30, "Bold")
            tw = d.textlength(c, font=f)
            rrect(d, (cx, y + 214, cx + tw + 40, y + 266), 26, None, outline=fade(col, p), width=3)
            d.text((cx + 20 + tw / 2, y + 240), c, font=f, fill=fade(INK, p), anchor="mm")
            cx += tw + 56
        for j, (label, val) in enumerate((("EXPERIENCE", work), ("EDUCATION", edu))):
            ry = y + 320 + j * 130
            d.line([(130, ry - 20), (W - 130, ry - 20)], fill=fade(CARD_EDGE, p), width=2)
            d.text((130, ry), label, font=font(28, "SemiBold"), fill=fade(MUTED, p))
            d.text((130, ry + 42), val, font=font(44, "SemiBold"), fill=fade(INK, p))


SCENE_FNS = [s_hook, s_title, s_types, s_var, s_pricing, s_rates, s_regs, s_outcomes, s_instructors, s_cta]
# Scene start times; overridden by the voiceover timings file when present so
# each scene lines up with its narration paragraph.
VOICEOVER = "script/video/voiceover.mp3"
TIMINGS = "script/video/voiceover_timings.json"
STARTS = [0.0, 7.0, 13.0, 23.0, 36.0, 48.0, 58.0, 66.0, 73.0, 85.0]
INSTRUCTOR2_AT = None  # absolute time the second instructor card appears
if os.path.exists(TIMINGS):
    import json
    _tm = json.load(open(TIMINGS))
    STARTS = _tm["scene_starts"]
    INSTRUCTOR2_AT = _tm.get("instructor2_start")
SCENES = [(STARTS[i], STARTS[i + 1] if i + 1 < len(STARTS) else DURATION, fn) for i, fn in enumerate(SCENE_FNS)]
FADE = 0.4


def render_frame(bg, t):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    for start, end, fn in SCENES:
        if start <= t < end:
            fn(d, t - start, end - start)
            alpha = 1.0
            if fn is not s_cta:
                alpha = clamp((end - t) / FADE)
            if alpha < 1:
                img = Image.blend(bg, img, alpha)
                d = ImageDraw.Draw(img)
            break
    chrome(d, t)
    return img


# ---------------------------------------------------------------- audio
def make_audio(path, sr=44100):
    n = int(DURATION * sr)
    tt = np.arange(n) / sr
    out = np.zeros(n)
    # slow chord progression: Am – F – C – G (each 8 s), soft pad
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [196.0, 246.94, 293.66]]
    seg = 8.0
    for k in range(int(math.ceil(DURATION / seg))):
        s0 = int(k * seg * sr)
        s1 = min(n, int((k + 1) * seg * sr + 1.5 * sr))
        if s0 >= n:
            break
        lt = tt[s0:s1] - k * seg
        env = np.clip(lt / 1.5, 0, 1) * np.clip((seg + 1.5 - lt) / 1.5, 0, 1)
        for f in chords[k % 4]:
            for det in (-0.6, 0.6):
                out[s0:s1] += 0.05 * env * np.sin(2 * np.pi * (f + det) * lt)
            out[s0:s1] += 0.02 * env * np.sin(2 * np.pi * f / 2 * lt)
    # gentle pulse
    beat = 60 / 96
    for b in np.arange(0, DURATION, beat):
        s0 = int(b * sr)
        L = int(0.25 * sr)
        lt = np.arange(min(L, n - s0)) / sr
        out[s0:s0 + len(lt)] += 0.08 * np.exp(-lt * 18) * np.sin(2 * np.pi * 55 * lt)
    # transition swells
    for start, _, _ in SCENES[1:]:
        s0 = int((start - 0.6) * sr)
        L = int(0.9 * sr)
        lt = np.arange(L) / sr
        noise = rng.normal(0, 1, L)
        noise = np.convolve(noise, np.ones(30) / 30, mode="same")
        out[s0:s0 + L] += 0.12 * noise * np.sin(np.pi * lt / 0.9) ** 2
    # master fade in/out
    out *= np.clip(tt / 1.0, 0, 1) * np.clip((DURATION - tt) / 2.0, 0, 1)
    out /= np.max(np.abs(out)) / 0.6
    if os.path.exists(VOICEOVER):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", VOICEOVER, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                             capture_output=True, check=True).stdout
        vo = np.frombuffer(raw, dtype=np.float32)[:n]
        vo = np.pad(vo, (0, n - len(vo)))
        vo /= np.max(np.abs(vo)) + 1e-9
        # duck music to ~30% while the narrator is speaking
        env = np.convolve(np.abs(vo), np.ones(sr // 4) / (sr // 4), mode="same")
        duck = 1 - 0.7 * np.clip(env / 0.05, 0, 1)
        out = out * duck * 0.55 + vo * 0.9
        out /= max(1.0, np.max(np.abs(out)) / 0.95)
    data = (out * 32767).astype(np.int16)
    stereo = np.column_stack([data, data]).ravel()
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(stereo.tobytes())


def main():
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    bg = make_background()
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "music.wav")
        make_audio(wav)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-i", wav,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        total = int(DURATION * FPS)
        for i in range(total):
            proc.stdin.write(render_frame(bg, i / FPS).tobytes())
            if i % 300 == 0:
                print(f"frame {i}/{total}", flush=True)
        proc.stdin.close()
        proc.wait()
    print("wrote", OUT)


if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        bg = make_background()
        for ts in os.environ["PREVIEW"].split(","):
            render_frame(bg, float(ts)).save(f"{os.environ.get('PREVIEW_DIR', '.')}/frame_{ts}.png")
    else:
        main()
