"""Generate video/index.html (HyperFrames composition) from build/timing.json."""
import json, math, random, re, html

ROOT = __file__.rsplit("/tools/", 1)[0]
TM = json.load(open(f"{ROOT}/build/timing.json"))
WORDS = TM["words"]
ADUR = round(TM["duration"], 2)
DUR = round(ADUR + 2.0, 2)
SEC = {s["id"]: s for s in TM["sections"]}
W, H = 1080, 1920

def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower())

def T(phrase, sec=None, nth=0, end=False):
    """Start (or end) time of the nth occurrence of phrase, optionally within a section."""
    p = [norm(x) for x in phrase.split()]
    hits = []
    for i in range(len(WORDS) - len(p) + 1):
        if sec and WORDS[i]["sec"] != sec: continue
        if [norm(WORDS[i + k]["w"]) for k in range(len(p))] == p:
            hits.append(i)
    i = hits[nth]
    return round(WORDS[i + len(p) - 1]["e"] if end else WORDS[i]["s"], 3)

S = {k: round(v["s"], 3) for k, v in SEC.items()}
order = ["hook", "boom", "warning", "crash", "aftermath", "lesson"]
SCENE = {}
for i, k in enumerate(order):
    st = 0 if i == 0 else S[k]
    en = DUR if i == len(order) - 1 else S[order[i + 1]] + 0.6
    SCENE[k] = (round(st, 3), round(en - st, 3))

# ---------------------------------------------------------------- captions
KEY = ["october 1929", "greed", "easy money", "economic boom", "buying on margin", "unstoppable", "danger",
       "speculation", "black thursday", "black tuesday", "prices collapsed", "avalanche", "great depression",
       "unemployment soared", "trust", "panic", "disaster", "debts", "borrowed money"]
keyset = [k.split() for k in KEY]
hl = [False] * len(WORDS)
for i in range(len(WORDS)):
    for k in keyset:
        if [norm(WORDS[i + j]["w"]) if i + j < len(WORDS) else "" for j in range(len(k))] == k:
            for j in range(len(k)): hl[i + j] = True

chunks, cur = [], []
for i, w in enumerate(WORDS):
    cur.append(i)
    txt = " ".join(WORDS[j]["w"] for j in cur)
    endp = re.search(r"[.,?!;]$|\.\.\.$", w["w"])
    nxt_sec = i + 1 >= len(WORDS) or WORDS[i + 1]["sec"] != w["sec"]
    if nxt_sec or (endp and len(cur) >= 2) or len(cur) >= 5 or len(txt) >= 26 or re.search(r"[.?!]$", w["w"]):
        chunks.append(cur); cur = []
if cur: chunks.append(cur)

cap_html, cap_js = [], []
for n, c in enumerate(chunks):
    s = WORDS[c[0]]["s"] - 0.08
    nxt = WORDS[chunks[n + 1][0]]["s"] - 0.08 if n + 1 < len(chunks) else DUR - 0.2
    e = min(nxt, WORDS[c[-1]]["e"] + 0.9)
    words = []
    for j in c:
        t = html.escape(WORDS[j]["w"])
        words.append(f'<span class="k">{t}</span>' if hl[j] else t)
    cap_html.append(f'<div class="cap" id="cap{n}">{" ".join(words)}</div>')
    cap_js.append(f"capIn('#cap{n}',{s:.3f});capOut('#cap{n}',{max(e - 0.12, s + 0.3):.3f});")

# ---------------------------------------------------------------- art
rnd = random.Random(1929)
def skyline():
    out = []
    x = -20
    layers = [("#2a1d10", 0.55, 1100, 1500), ("#160f08", 0.8, 1180, 1650), ("#0a0704", 1.0, 1280, 1760)]
    for col, sc, base_lo, base_hi in layers:
        x = -40
        while x < W + 40:
            bw = rnd.randint(70, 150) * sc + 30
            top = rnd.randint(int(base_lo - 650 * sc), int(base_hi - 500 * sc))
            out.append(f'<rect x="{x:.0f}" y="{top}" width="{bw:.0f}" height="{H - top}" fill="{col}"/>')
            # setbacks / spire
            if rnd.random() < 0.55:
                sw = bw * 0.6; st = top - rnd.randint(40, 120)
                out.append(f'<rect x="{x + (bw - sw) / 2:.0f}" y="{st}" width="{sw:.0f}" height="{top - st + 2}" fill="{col}"/>')
                if rnd.random() < 0.5:
                    out.append(f'<polygon points="{x + bw / 2 - 10:.0f},{st} {x + bw / 2:.0f},{st - rnd.randint(60, 160)} {x + bw / 2 + 10:.0f},{st}" fill="{col}"/>')
            if sc >= 0.8:
                for wy in range(top + 20, H, 34):
                    for wx in range(int(x + 10), int(x + bw - 14), 22):
                        if rnd.random() < 0.13:
                            a = rnd.choice([0.35, 0.55, 0.8])
                            out.append(f'<rect x="{wx}" y="{wy}" width="8" height="14" fill="#f2b84b" opacity="{a}"/>')
            x += bw + rnd.randint(-10, 8)
    return f'<svg class="skyline" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{"".join(out)}</svg>'

def person(x, h, hat, lean):
    s = h / 300
    return (f'<g transform="translate({x},{0}) scale({s}) rotate({lean} 0 300)" fill="#050403">'
            f'<circle cx="0" cy="48" r="22"/>'
            + (f'<rect x="-30" y="20" width="60" height="8" rx="3"/><rect x="-18" y="2" width="36" height="22" rx="4"/>' if hat else '')
            + '<path d="M-38 300 L-34 120 Q-30 76 0 74 Q30 76 34 120 L38 300 Z"/>'
            '<rect x="-30" y="200" width="22" height="100"/><rect x="8" y="200" width="22" height="100"/></g>')

def breadline():
    figs = []
    for i in range(11):
        figs.append(person(60 + i * 92, rnd.randint(250, 300), rnd.random() < 0.75, rnd.uniform(-3, 4)))
    return f'<svg class="breadline" viewBox="0 0 1100 320" width="1100" height="320">{"".join(figs)}</svg>'

# Dow Jones (approximate closes)
UP = [(1921.62, 63.9), (1922.0, 81), (1922.7, 102), (1923.2, 105), (1923.8, 86), (1924.5, 98), (1924.95, 120),
      (1925.5, 135), (1925.95, 156), (1926.3, 140), (1926.7, 165), (1927.0, 155), (1927.5, 170), (1927.95, 200),
      (1928.4, 215), (1928.9, 290), (1929.0, 300), (1929.4, 295), (1929.67, 381.2)]
DOWN = [(1929.67, 381.2), (1929.81, 305), (1929.83, 230), (1929.87, 199), (1930.29, 294), (1930.95, 165),
        (1931.2, 190), (1931.95, 78), (1932.52, 41.2)]

def path(pts, x0, x1, y0, y1, w, h):
    P = [((a - x0) / (x1 - x0) * w, h - (b - y0) / (y1 - y0) * h) for a, b in pts]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in P)
    L = sum(math.dist(P[i], P[i + 1]) for i in range(len(P) - 1))
    return d, round(L + 2), P

CW, CH = 880, 560
boom_d, boom_L, boomP = path(UP, 1921.5, 1929.8, 0, 420, CW, CH)
full_up_d, full_up_L, _ = path(UP, 1921.5, 1932.6, 0, 420, CW, CH)
full_dn_d, full_dn_L, fdP = path(DOWN, 1921.5, 1932.6, 0, 420, CW, CH)
crash_d, crash_L, crP = path(DOWN, 1929.6, 1932.6, 0, 420, CW, CH)
# warning scene: prices vs earnings (schematic, 1925=100)
PR = [(1925, 100), (1926, 112), (1927, 135), (1928, 190), (1929, 300)]
ER = [(1925, 100), (1926, 112), (1927, 118), (1928, 132), (1929, 150)]
pr_d, pr_L, prP = path(PR, 1925, 1929, 60, 320, CW, 520)
er_d, er_L, erP = path(ER, 1925, 1929, 60, 320, CW, 520)
gap_poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in prP) + " " + " ".join(f"{x:.1f},{y:.1f}" for x, y in reversed(erP))

def grid(w, h, ys, y0, y1, xs=None, x0=None, x1=None):
    g = []
    for v in ys:
        y = h - (v - y0) / (y1 - y0) * h
        g.append(f'<line x1="0" x2="{w}" y1="{y:.1f}" y2="{y:.1f}" class="gl"/><text x="-14" y="{y + 9:.1f}" class="gt" text-anchor="end">{v}</text>')
    for v in xs or []:
        x = (v - x0) / (x1 - x0) * w
        g.append(f'<text x="{x:.1f}" y="{h + 44}" class="gt" text-anchor="middle">\'{str(v)[2:]}</text>')
    return "".join(g)

sells = []
for i in range(46):
    x = rnd.randint(40, 880); y = rnd.randint(330, 1120); r = rnd.uniform(-14, 14)
    sells.append(f'<div class="sell" id="sell{i}" style="left:{x}px;top:{y}px;transform:rotate({r:.1f}deg)">SELL</div>')

tape = "  ".join(f"{s} {v} ▼{d}" for s, v, d in [("US STEEL", "174", "17½"), ("GEN ELEC", "222", "47¾"), ("RCA", "26", "13½"),
        ("GEN MOTORS", "40", "6¾"), ("WESTINGHSE", "100", "34½"), ("AT&T", "204", "28"), ("MONTGOMERY W", "50", "15¾"),
        ("UNION CARBIDE", "65", "20"), ("ANACONDA", "70", "15")]) + "  "

cities = [("LONDON", -250, -170), ("BERLIN", 230, -220), ("PARIS", -330, 40), ("VIENNA", 300, 20),
          ("TOKYO", 260, 230), ("BUENOS AIRES", -240, 250), ("SYDNEY", 30, 330), ("TORONTO", -40, -300)]

T_ = dict(
    oct=T("October 1929", "hook"), title=T("Wall Street was", "hook"), panic1=T("But this disaster", "hook"),
    greed=T("greed,", "hook"), easy=T("easy money,", "hook"), belief=T("the belief", "hook"),
    boom=S["boom"], biz=T("Businesses expanded", "boom"), spend=T("consumer spending", "boom"), inv=T("millions of investors", "boom"),
    many=T("Many bought shares", "boom"), margin=T("buying on margin", "boom"), loop=T("As prices climbed", "boom"),
    rising=T("rising prices attracted", "boom"), more=T("And more buyers", "boom"), higher=T("even higher", "boom"),
    unstop=T("The market began", "boom"), unstopW=T("unstoppable.", "boom"),
    warn=S["warning"], detached=T("Stock prices had become", "warning"), spec=T("Speculation was rampant", "warning"),
    borrowed=T("borrowed money magnified", "warning"), conf=T("Eventually, confidence", "warning"), weaken=T("weaken.", "warning"),
    selling=T("Investors started selling", "warning"), sudden=T("And suddenly...", "warning"), everyone=T("everyone wanted", "warning"),
    crash=S["crash"], thursday=T("Black Thursday", "crash"), five=T("Five days later", "crash"), tuesday=T("Black Tuesday", "crash"),
    rushed=T("Investors rushed", "crash"), collapsed=T("Prices collapsed", "crash"), fortunes=T("Fortunes disappeared", "crash"),
    those=T("Those who had borrowed", "crash"), forced=T("some were forced", "crash"), spiral=T("The market's upward", "crash"),
    avalanche=T("downward avalanche", "crash"),
    after=S["aftermath"], bank=T("Bank failures", "aftermath"), demand=T("collapsing demand", "aftermath"),
    prod=T("falling production", "aftermath"), policy=T("policy mistakes", "aftermath"), helped=T("helped turn", "aftermath"),
    shut=T("Businesses shut down", "aftermath"), unemp=T("Unemployment soared", "aftermath"), families=T("Families lost", "aftermath"),
    spread=T("The crisis spread", "aftermath"), world=T("around the world", "aftermath"),
    lesson=S["lesson"], truth=T("timeless truth", "lesson"), when=T("When speculation", "lesson"), debt=T("debt magnifies", "lesson"),
    confP=T("and confidence turns", "lesson"), boomD=T("a boom can", "lesson"), because=T("Because markets", "lesson"),
    trust=T("They run on trust", "lesson"), trustW=T("trust.", "lesson"), once=T("And once that trust", "lesson"),
    years=T("for years.", "lesson", end=True),
)
SC = {k: v for k, v in SCENE.items()}

def clip(k, inner, extra=""):
    s, d = SC[k]
    return f'<div id="sc-{k}" class="clip scene" data-start="{s}" data-duration="{d}" data-track-index="1"{extra}>{inner}</div>'

CH_LABEL = {"hook": "OCTOBER 1929", "boom": "CHAPTER I &nbsp;·&nbsp; THE BOOM", "warning": "CHAPTER II &nbsp;·&nbsp; WARNING SIGNS",
            "crash": "CHAPTER III &nbsp;·&nbsp; THE CRASH", "aftermath": "CHAPTER IV &nbsp;·&nbsp; THE AFTERMATH",
            "lesson": "CHAPTER V &nbsp;·&nbsp; THE LESSON"}
def chap(k): return f'<div class="chap" id="chap-{k}"><span class="rule"></span>{CH_LABEL[k]}</div>'

oct_chars = "".join(f'<span class="tc">{c if c != " " else "&nbsp;"}</span>' for c in "OCTOBER 1929")

scenes = []
scenes.append(clip("hook", f'''
  <div class="sky"></div>
  <div class="sun"></div>
  <div class="skywrap" id="skywrap">{skyline()}</div>
  <div class="shade"></div>
  <div class="typed" id="octtype">{oct_chars}</div>
  <div class="title" id="title1">
    <div class="t-a h" id="t1a">The Wall Street</div>
    <div class="t-b h" id="t1b">Crash</div>
    <div class="t-c h" id="t1c">of 1929</div>
    <div class="t-rule h" id="t1r"></div>
  </div>
  <div class="trio" id="trio">
    <div class="card h" id="tr1">GREED</div>
    <div class="card h" id="tr2">EASY MONEY</div>
    <div class="card h it" id="tr3">“prices only go up”</div>
  </div>'''))

scenes.append(clip("boom", f'''
  {chap("boom")}
  <div class="chips">
    <div class="chip h" id="ch1">BUSINESSES <b>▲</b></div>
    <div class="chip h" id="ch2">SPENDING <b>▲</b></div>
    <div class="chip h" id="ch3">INVESTORS <b>▲</b></div>
  </div>
  <div class="chart" id="boomchart">
    <div class="clabel">DOW JONES INDUSTRIAL AVERAGE</div>
    <div class="counter"><span id="dowv">63.9</span></div>
    <svg width="{CW}" height="{CH + 60}" viewBox="-60 0 {CW + 60} {CH + 60}" style="margin-left:-60px">
      <g>{grid(CW, CH, [100, 200, 300, 400], 0, 420, [1922, 1924, 1926, 1928], 1921.5, 1929.8)}</g>
      <path d="{boom_d} L{CW},{CH} L0,{CH} Z" class="area" id="boomarea"/>
      <path d="{boom_d}" class="line" id="boomline" style="stroke-dasharray:{boom_L};stroke-dashoffset:{boom_L}"/>
      <circle cx="{boomP[-1][0]:.1f}" cy="{boomP[-1][1]:.1f}" r="12" class="dot h" id="boomdot"/>
    </svg>
  </div>
  <div class="margin h" id="margin">
    <div class="mtitle">BUYING ON MARGIN</div>
    <div class="mbar"><div class="mcash" id="mcash">$10<small>your cash</small></div><div class="mloan" id="mloan">$90<small>borrowed from your broker</small></div></div>
    <div class="mtotal">= <b>$100</b> of stock</div>
  </div>
  <div class="loop h" id="loop">
    <svg width="620" height="620" viewBox="-310 -310 620 620" class="ring" id="ring">
      <circle r="230" class="ringc"/>
      <path d="M 0 -230 A 230 230 0 0 1 199 115" class="ringa"/><polygon points="199,115 170,95 214,85" class="ringh" transform="rotate(8 199 115)"/>
      <path d="M 199 115 A 230 230 0 0 1 -199 115" class="ringa"/><polygon points="-199,115 -180,145 -214,140" class="ringh"/>
      <path d="M -199 115 A 230 230 0 0 1 0 -230" class="ringa"/><polygon points="0,-230 -30,-215 -12,-252" class="ringh"/>
    </svg>
    <div class="node h" id="nd1" style="left:310px;top:80px">PRICES<br/>RISE</div>
    <div class="node h" id="nd2" style="left:510px;top:425px">MORE<br/>BUYERS</div>
    <div class="node h" id="nd3" style="left:110px;top:425px">PRICES<br/>RISE HIGHER</div>
  </div>
  <div class="stamp h" id="stamp">UNSTOPPABLE</div>'''))

scenes.append(clip("warning", f'''
  {chap("warning")}
  <div class="chart" id="warnchart">
    <div class="clabel">STOCK PRICES vs. WHAT COMPANIES EARNED <span class="dim">(illustrative)</span></div>
    <svg width="{CW}" height="580" viewBox="0 -20 {CW} 600">
      <polygon points="{gap_poly}" class="gap h" id="gap"/>
      <path d="{er_d}" class="line2" id="erline" style="stroke-dasharray:{er_L};stroke-dashoffset:{er_L}"/>
      <path d="{pr_d}" class="line" id="prline" style="stroke-dasharray:{pr_L};stroke-dashoffset:{pr_L}"/>
      <text x="{prP[-1][0] - 10:.0f}" y="{prP[-1][1] - 22:.0f}" text-anchor="end" class="lt gold h" id="prl">PRICES</text>
      <text x="{erP[-1][0] - 10:.0f}" y="{erP[-1][1] + 48:.0f}" text-anchor="end" class="lt h" id="erl">EARNINGS</text>
    </svg>
    <div class="gaplabel h" id="gapl">THE GAP</div>
  </div>
  <div class="mult h" id="mult"><span class="m1">SPECULATION</span><span class="m2">× BORROWED MONEY</span><span class="m3">= RISK</span></div>
  <div class="gauge h" id="gauge">
    <div class="glabel">INVESTOR CONFIDENCE</div>
    <svg width="760" height="420" viewBox="-380 -380 760 420">
      <path d="M -330 0 A 330 330 0 0 1 -110 -311" class="arc a1"/>
      <path d="M -110 -311 A 330 330 0 0 1 110 -311" class="arc a2"/>
      <path d="M 110 -311 A 330 330 0 0 1 330 0" class="arc a3"/>
      <g id="needle" transform="rotate(62)"><polygon points="-12,0 0,-300 12,0" class="needle"/><circle r="26" class="needle"/></g>
      <text x="-330" y="40" class="gt" text-anchor="middle">LOW</text><text x="330" y="40" class="gt" text-anchor="middle">HIGH</text>
    </svg>
  </div>
  <div class="sells" id="sells">{"".join(sells)}</div>'''))

scenes.append(clip("crash", f'''
  {chap("crash")}
  <div class="cal h" id="cal1"><div class="calm">OCTOBER 1929</div><div class="cald">24</div><div class="calw">THURSDAY</div></div>
  <div class="cal h" id="cal2"><div class="calm">OCTOBER 1929</div><div class="cald">29</div><div class="calw">TUESDAY</div></div>
  <div class="blk h" id="blk1">BLACK THURSDAY</div>
  <div class="blk h" id="blk2">BLACK TUESDAY</div>
  <div class="tape h" id="tape"><div class="tapein" id="tapein">{html.escape(tape * 3)}</div></div>
  <div class="chart h" id="crashchart">
    <div class="clabel">DOW JONES, SEPT 1929 →</div>
    <div class="counter red"><span id="dowc">381.2</span></div>
    <svg width="{CW}" height="{CH + 60}" viewBox="-60 0 {CW + 60} {CH + 60}" style="margin-left:-60px">
      <g>{grid(CW, CH, [100, 200, 300, 400], 0, 420, [1930, 1931, 1932], 1929.6, 1932.6)}</g>
      <path d="{crash_d}" class="line red" id="crashline" style="stroke-dasharray:{crash_L};stroke-dashoffset:{crash_L}"/>
    </svg>
  </div>
  <div class="paper h" id="paper">
    <div class="mast">The Evening Ledger</div>
    <div class="pdate">NEW YORK, WEDNESDAY, OCTOBER 30, 1929 &nbsp;·&nbsp; TWO CENTS</div>
    <div class="head">STOCKS<br/>PLUNGE</div>
    <div class="sub">BILLIONS LOST AS PANIC SWEEPS WALL STREET</div>
    <div class="cols"><i></i><i></i><i></i></div>
  </div>
  <div class="telegram h" id="tele">
    <div class="tg-h">WESTERN TELEGRAPH &nbsp;·&nbsp; URGENT</div>
    <div class="tg-b" id="tgb">MARGIN CALL STOP<br/>DEPOSIT FUNDS IMMEDIATELY STOP<br/>OR YOUR SHARES WILL BE SOLD STOP</div>
  </div>
  <div class="chart h" id="avchart">
    <div class="clabel">DOW JONES, 1921 – 1932</div>
    <svg width="{CW}" height="{CH + 60}" viewBox="-60 0 {CW + 60} {CH + 60}" style="margin-left:-60px">
      <g>{grid(CW, CH, [100, 200, 300, 400], 0, 420, [1922, 1925, 1928, 1931], 1921.5, 1932.6)}</g>
      <path d="{full_up_d}" class="line" id="avup" style="stroke-dasharray:{full_up_L};stroke-dashoffset:{full_up_L}"/>
      <path d="{full_dn_d}" class="line red" id="avdn" style="stroke-dasharray:{full_dn_L};stroke-dashoffset:{full_dn_L}"/>
      <text x="{fdP[-1][0]:.0f}" y="{fdP[-1][1] - 30:.0f}" text-anchor="end" class="lt red h" id="avl">−89%</text>
    </svg>
  </div>'''))

city_html = "".join(f'<div class="city h" id="city{i}" style="left:{540 + x}px;top:{760 + y}px">{n}</div>' for i, (n, x, y) in enumerate(cities))
city_lines = "".join(f'<line x1="0" y1="0" x2="{x}" y2="{y}" class="cl" id="cl{i}" style="stroke-dasharray:{math.hypot(x, y):.0f};stroke-dashoffset:{math.hypot(x, y):.0f}"/>' for i, (n, x, y) in enumerate(cities))
scenes.append(clip("aftermath", f'''
  {chap("aftermath")}
  <div class="neq h" id="neq"><div>THE CRASH</div><div class="ne">≠</div><div>THE GREAT<br/>DEPRESSION</div></div>
  <div class="tiles" id="tiles">
    <div class="tile h" id="ti1"><b>BANK FAILURES</b><span>~9,000 U.S. banks failed, 1930–33</span></div>
    <div class="tile h" id="ti2"><b>COLLAPSING DEMAND</b><span>People and firms stopped spending</span></div>
    <div class="tile h" id="ti3"><b>FALLING PRODUCTION</b><span>Industrial output fell by nearly half</span></div>
    <div class="tile h" id="ti4"><b>POLICY MISTAKES</b><span>Tight money, trade barriers</span></div>
  </div>
  <div class="bigstat h" id="bigstat"><div class="bsn"><span id="unv">3</span>%</div><div class="bsl">U.S. UNEMPLOYMENT BY 1933</div></div>
  <div class="bl h" id="bl">{breadline()}</div>
  <div class="world h" id="world">
    <svg width="1080" height="1100" viewBox="-540 -760 1080 1100" class="wsvg">{city_lines}
      <circle r="60" class="ripple" id="rp1"/><circle r="60" class="ripple" id="rp2"/><circle r="18" class="ny"/></svg>
    <div class="nyl">NEW YORK</div>
    {city_html}
  </div>'''))

scenes.append(clip("lesson", f'''
  {chap("lesson")}
  <div class="lt-title h" id="lt">A timeless truth</div>
  <div class="rules" id="rules">
    <div class="rule h" id="ru1">Speculation <em>replaces</em> fundamentals</div>
    <div class="rule h" id="ru2">Debt <em>magnifies</em> risk</div>
    <div class="rule h" id="ru3">Confidence <em>turns into</em> panic</div>
    <div class="rule res h" id="ru4">Boom → Disaster</div>
  </div>
  <div class="money h" id="money">Markets don’t just run on money.</div>
  <div class="runon h" id="runon">They run on</div>
  <div class="trust h" id="trust"><div class="tr-top">TRUST</div><div class="tr-bot">TRUST</div></div>
  <div class="end h" id="endc"><div class="e1">The Wall Street Crash</div><div class="e2">1929</div></div>'''))

CSS = open(f"{ROOT}/tools/style.css").read()

JS = f"""
const T = {json.dumps(T_)};
const SC = {json.dumps(SC)};
const tl = gsap.timeline({{ paused: true }});
const E = 'power3.out';
function inn(s, t, v = {{}}, d = 0.7) {{ tl.fromTo(s, Object.assign({{ opacity: 0, y: 40 }}, v.from || {{}}), Object.assign({{ opacity: 1, y: 0, x: 0, scale: 1, duration: d, ease: E }}, v.to || {{}}), t); }}
function out(s, t, d = 0.45, v = {{}}) {{ tl.fromTo(s, {{ opacity: 1 }}, Object.assign({{ opacity: 0, duration: d, ease: 'power2.in', immediateRender: false }}, v), t); }}
function draw(s, t, d, ease = 'power1.inOut') {{ tl.to(s, {{ strokeDashoffset: 0, duration: d, ease }}, t); }}
function count(id, a, b, t, d, dec = 1, ease = 'power1.inOut') {{
  const o = {{ v: a }}; const el = document.getElementById(id);
  tl.fromTo(o, {{ v: a }}, {{ v: b, duration: d, ease, onUpdate: () => {{ el.textContent = o.v.toFixed(dec); }} }}, t);
}}
function capIn(s, t) {{ tl.fromTo(s, {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.28, ease: 'power2.out' }}, t); }}
function capOut(s, t) {{ tl.fromTo(s, {{ opacity: 1 }}, {{ opacity: 0, duration: 0.14, ease: 'none', immediateRender: false }}, t); }}

// scene cross-fades
for (const [k, [s, d]] of Object.entries(SC)) {{
  if (s > 0) tl.fromTo('#sc-' + k, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: 'none' }}, s);
  const chap = document.getElementById('chap-' + k);
  if (chap) {{ tl.fromTo(chap, {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.7, ease: E }}, s + 0.2); }}
}}

// grain + flicker (whole video)
tl.fromTo('#grain', {{ x: 0, y: 0 }}, {{ x: -400, y: -330, duration: {DUR}, ease: 'steps({int(DUR * 12)})' }}, 0);
tl.fromTo('#flicker', {{ opacity: 0.05 }}, {{ opacity: 0.12, duration: 0.09, ease: 'steps(1)', repeat: {int(DUR / 0.09) - 2}, yoyo: true }}, 0);

// ---------------- HOOK
tl.fromTo('#skywrap', {{ scale: 1.0, y: 40 }}, {{ scale: 1.14, y: -30, duration: SC.hook[1], ease: 'none' }}, 0);
tl.fromTo('.sun', {{ y: 0, opacity: 0.85 }}, {{ y: 120, opacity: 0.5, duration: SC.hook[1], ease: 'none' }}, 0);
tl.fromTo('#octtype .tc', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.01, stagger: 0.09 }}, 0.15);
tl.to('#octtype', {{ y: -120, scale: 0.62, duration: 0.8, ease: E }}, T.title - 0.1);
inn('#t1a', T.title, {{ from: {{ y: 60 }} }}, 0.9);
inn('#t1b', T.title + 0.35, {{ from: {{ scale: 1.25, y: 0 }} }}, 0.9);
inn('#t1c', T.title + 0.7, {{}}, 0.9);
tl.fromTo('#t1r', {{ opacity: 0, scaleX: 0 }}, {{ opacity: 1, scaleX: 1, duration: 0.9, ease: E }}, T.title + 1.0);
tl.to('#title1', {{ y: -260, scale: 0.72, duration: 1.0, ease: 'power2.inOut' }}, T.panic1);
tl.to('#octtype', {{ opacity: 0, duration: 0.5 }}, T.panic1);
inn('#tr1', T.greed, {{ from: {{ x: -80, y: 0 }} }});
inn('#tr2', T.easy, {{ from: {{ x: 80, y: 0 }} }});
inn('#tr3', T.belief, {{ from: {{ y: 50 }} }});

// ---------------- BOOM
draw('#boomline', T.boom + 0.3, T.many - T.boom - 0.6);
tl.fromTo('#boomarea', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8, ease: 'none' }}, T.many - 0.4);
count('dowv', 63.9, 381.2, T.boom + 0.3, T.many - T.boom - 0.6);
inn('#boomdot', T.many - 0.35, {{ from: {{ scale: 0, y: 0 }} }}, 0.4);
inn('#ch1', T.biz); inn('#ch2', T.spend); inn('#ch3', T.inv);
out('.chips', T.many - 0.3);
tl.to('#boomchart', {{ opacity: 0.05, duration: 0.6 }}, T.many);
inn('#margin', T.many + 0.1);
tl.fromTo('#mcash', {{ width: 0 }}, {{ width: 96, duration: 0.8, ease: E }}, T.many + 0.5);
tl.fromTo('#mloan', {{ width: 0 }}, {{ width: 724, duration: 1.4, ease: E }}, T.many + 1.3);
out('#margin', T.loop - 0.35);
inn('#loop', T.loop, {{ from: {{ scale: 0.85, y: 0 }} }});
tl.fromTo('#ring', {{ rotation: 0 }}, {{ rotation: 360, duration: T.unstop - T.loop + 1, ease: 'none' }}, T.loop);
inn('#nd1', T.loop + 0.2, {{ from: {{ scale: 0.6, y: 0 }} }}, 0.5);
inn('#nd2', T.rising + 0.6, {{ from: {{ scale: 0.6, y: 0 }} }}, 0.5);
inn('#nd3', T.more + 0.5, {{ from: {{ scale: 0.6, y: 0 }} }}, 0.5);
out('#loop', T.unstop - 0.3);
tl.to('#boomchart', {{ opacity: 1, duration: 0.6 }}, T.unstop - 0.3);
tl.fromTo('#stamp', {{ opacity: 0, scale: 2.2, rotation: -14 }}, {{ opacity: 1, scale: 1, rotation: -8, duration: 0.35, ease: 'power4.in' }}, T.unstopW - 0.1);

// ---------------- WARNING
draw('#prline', T.warn + 0.2, 2.6); draw('#erline', T.warn + 0.4, 2.6);
inn('#prl', T.warn + 2.4); inn('#erl', T.warn + 2.6);
tl.fromTo('#gap', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8 }}, T.detached + 0.3);
inn('#gapl', T.detached + 0.8, {{ from: {{ scale: 0.7, y: 0 }} }});
tl.to('#warnchart', {{ opacity: 0, y: -40, duration: 0.5 }}, T.spec - 0.3);
inn('#mult', T.spec);
tl.fromTo('#mult .m2', {{ opacity: 0, x: 60 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: E }}, T.borrowed);
tl.fromTo('#mult .m3', {{ opacity: 0, scale: 1.6 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: 'power4.in' }}, T.borrowed + 1.3);
out('#mult', T.conf - 0.3);
inn('#gauge', T.conf);
tl.fromTo('#needle', {{ rotation: 62 }}, {{ rotation: -64, duration: T.selling - T.conf - 0.3, ease: 'power2.in' }}, T.conf + 0.4);
out('#gauge', T.selling - 0.1, 0.3);
gsap.utils.toArray('.sell').forEach((el, i) => {{
  const t = i < 8 ? T.selling + i * 0.18 : T.everyone + (i - 8) * 0.045;
  tl.fromTo(el, {{ opacity: 0, scale: 2 }}, {{ opacity: 1, scale: 1, duration: 0.18, ease: 'power4.in' }}, t);
}});

// ---------------- CRASH
tl.fromTo('#cal1', {{ opacity: 0, rotationX: -90 }}, {{ opacity: 1, rotationX: 0, duration: 0.7, ease: E }}, T.crash + 0.1);
inn('#blk1', T.thursday, {{ from: {{ scale: 1.3, y: 0 }} }}, 0.4);
tl.to('#cal1', {{ rotationX: 90, opacity: 0, duration: 0.45, ease: 'power2.in' }}, T.five);
out('#blk1', T.five, 0.3);
tl.fromTo('#cal2', {{ opacity: 0, rotationX: -90 }}, {{ opacity: 1, rotationX: 0, duration: 0.6, ease: E }}, T.five + 0.45);
inn('#blk2', T.tuesday, {{ from: {{ scale: 1.3, y: 0 }} }}, 0.4);
out('#cal2', T.rushed - 0.3); out('#blk2', T.rushed - 0.3);
inn('#tape', T.rushed - 0.2, {{ from: {{ y: 0 }} }}, 0.4);
tl.fromTo('#tapein', {{ x: 0 }}, {{ x: -2400, duration: T.fortunes - T.rushed + 1, ease: 'none' }}, T.rushed - 0.2);
inn('#crashchart', T.rushed);
draw('#crashline', T.collapsed - 0.4, 2.6, 'power2.in');
count('dowc', 381.2, 198.7, T.collapsed - 0.4, 2.6, 1, 'power2.in');
tl.fromTo('#crashchart', {{ x: -8 }}, {{ x: 8, duration: 0.05, repeat: 15, yoyo: true, ease: 'none', immediateRender: false }}, T.collapsed + 1.4);
out('#crashchart', T.fortunes - 0.25, 0.3); out('#tape', T.fortunes - 0.25, 0.3);
tl.fromTo('#paper', {{ opacity: 0, scale: 2.4, rotation: 12 }}, {{ opacity: 1, scale: 1, rotation: -3, duration: 0.55, ease: 'power4.in' }}, T.fortunes - 0.1);
tl.to('#paper', {{ scale: 1.08, duration: T.those - T.fortunes, ease: 'none' }}, T.fortunes + 0.45);
out('#paper', T.those - 0.3);
inn('#tele', T.those);
tl.fromTo('#tgb', {{ clipPath: 'inset(0 100% 100% 0)' }}, {{ clipPath: 'inset(0 0% 0% 0)', duration: 2.6, ease: 'steps(40)' }}, T.those + 0.6);
out('#tele', T.spiral - 0.3);
inn('#avchart', T.spiral);
draw('#avup', T.spiral + 0.1, 1.6, 'power1.in');
draw('#avdn', T.spiral + 1.7, 1.8, 'power2.in');
inn('#avl', T.avalanche + 0.2, {{ from: {{ scale: 1.5, y: 0 }} }}, 0.4);

// ---------------- AFTERMATH
inn('#neq', T.after + 0.1);
tl.fromTo('#neq .ne', {{ scale: 0 }}, {{ scale: 1, duration: 0.5, ease: 'back.out(3)' }}, T.after + 1.4);
out('#neq', T.bank - 0.3);
inn('#ti1', T.bank, {{ from: {{ x: -60, y: 0 }} }}); inn('#ti2', T.demand, {{ from: {{ x: 60, y: 0 }} }});
inn('#ti3', T.prod, {{ from: {{ x: -60, y: 0 }} }}); inn('#ti4', T.policy, {{ from: {{ x: 60, y: 0 }} }});
out('#tiles', T.shut - 0.3);
inn('#bigstat', T.shut);
count('unv', 3, 25, T.unemp - 0.2, 1.4, 0, 'power2.out');
tl.to('#bigstat', {{ y: -200, scale: 0.7, duration: 0.8, ease: 'power2.inOut' }}, T.families - 0.2);
inn('#bl', T.families, {{ from: {{ y: 80 }} }}, 0.9);
tl.fromTo('#bl svg', {{ x: 60 }}, {{ x: -40, duration: T.spread - T.families + 0.5, ease: 'none' }}, T.families);
out('#bigstat', T.spread - 0.3); out('#bl', T.spread - 0.3);
inn('#world', T.spread, {{ from: {{ y: 0 }} }});
tl.fromTo('#rp1', {{ attr: {{ r: 20 }}, opacity: 0.9 }}, {{ attr: {{ r: 520 }}, opacity: 0, duration: 2.4, repeat: 1, ease: 'power1.out' }}, T.spread + 0.2);
tl.fromTo('#rp2', {{ attr: {{ r: 20 }}, opacity: 0.9 }}, {{ attr: {{ r: 520 }}, opacity: 0, duration: 2.4, repeat: 1, ease: 'power1.out' }}, T.spread + 1.4);
{''.join(f"draw('#cl{i}', T.spread + 0.5 + {i * 0.42:.2f}, 0.6); inn('#city{i}', T.spread + 0.9 + {i * 0.42:.2f}, {{ from: {{ scale: 0.6, y: 0 }} }}, 0.4);" for i in range(len(cities)))}

// ---------------- LESSON
inn('#lt', T.lesson + 0.2);
tl.to('#lt', {{ y: -120, scale: 0.75, opacity: 0.55, duration: 0.8, ease: 'power2.inOut' }}, T.when - 0.4);
inn('#ru1', T.when, {{ from: {{ x: -70, y: 0 }} }});
inn('#ru2', T.debt, {{ from: {{ x: -70, y: 0 }} }});
inn('#ru3', T.confP, {{ from: {{ x: -70, y: 0 }} }});
tl.fromTo('#ru4', {{ opacity: 0, scale: 1.5 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: 'power4.in' }}, T.boomD + 0.3);
out('#lt', T.because - 0.3); out('#rules', T.because - 0.3);
inn('#money', T.because);
tl.to('#money', {{ opacity: 0.45, duration: 0.5 }}, T.trust);
inn('#runon', T.trust);
tl.fromTo('#trust', {{ opacity: 0, scale: 1.35 }}, {{ opacity: 1, scale: 1, duration: 0.9, ease: E }}, T.trustW - 0.15);
tl.to('#trust .tr-top', {{ x: -40, y: -26, rotation: -4, duration: 2.2, ease: 'power2.in' }}, T.once + 0.6);
tl.to('#trust .tr-bot', {{ x: 50, y: 40, rotation: 3, duration: 2.2, ease: 'power2.in' }}, T.once + 0.6);
tl.to('#trust', {{ opacity: 0, duration: 1.2, ease: 'power1.in' }}, T.once + 1.8);
out('#money', T.once + 1.6, 0.8); out('#runon', T.once + 1.6, 0.8);
inn('#endc', T.once + 2.8, {{ from: {{ y: 30 }} }}, 1.0);

// captions
{"".join(cap_js)}

window.__timelines = window.__timelines || {{}};
window.__timelines['main'] = tl;
"""

page = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<title>The Wall Street Crash of 1929</title>
<script src="assets/gsap.min.js"></script>
<link rel="stylesheet" href="assets/fonts.css" />
<style>
{CSS}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
  <div class="bg"></div>
{chr(10).join(scenes)}
  <div class="caps">{"".join(cap_html)}</div>
  <div class="vignette"></div>
  <div class="grainwrap"><div id="grain"></div></div>
  <div id="flicker"></div>
  <audio id="vo" src="assets/voiceover.mp3" data-start="0" data-duration="{ADUR}" data-track-index="2" data-volume="1"></audio>
</div>
<script>
{JS}
</script>
</body>
</html>
"""
open(f"{ROOT}/video/index.html", "w").write(page)
print("scenes", SC)
print("captions", len(chunks))
