#!/usr/bin/env python3
"""ESCAPE PROTOCOL — turns a real GitHub contribution graph into a self-playing SVG game.

Data   : GraphQL API when a token is present, otherwise the public contributions page.
Engine : a small deterministic simulation (player vs. monster) played on the real grid.
Output : assets/escape-protocol.svg  (SMIL animation, no JavaScript, plays inside a README <img>)

The simulation is seeded from the contribution data itself, so the file only changes when
your contributions change (no noisy daily commits).
"""
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from common import BG, S1, S2, BR, TX, MU, DM, CY, BL, VI, WARN, MONO, e  # noqa: E402

USER = os.environ.get("GH_USER") or "uzairumar1029-creator"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(__file__), "..", "assets", "escape-protocol.svg"))
UA = {"User-Agent": "escape-protocol-generator"}


# --------------------------------------------------------------------------- data
def http(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def from_graphql():
    q = ("query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{weeks{"
         "contributionDays{date contributionCount contributionLevel}}}}}}")
    raw = http("https://api.github.com/graphql",
               json.dumps({"query": q, "variables": {"l": USER}}).encode(),
               {"Authorization": "bearer " + TOKEN, "Content-Type": "application/json"})
    lv = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    weeks = json.loads(raw)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(d["date"], d["contributionCount"], lv[d["contributionLevel"]])
            for w in weeks for d in w["contributionDays"]]


def from_html():
    h = http(f"https://github.com/users/{USER}/contributions")
    counts = {}
    for m in re.finditer(r'for="([^"]+)"[^>]*>\s*(\d+|No) contribution', h):
        counts[m.group(1)] = 0 if m.group(2) == "No" else int(m.group(2))
    days = []
    for m in re.finditer(r"<td\b[^>]*ContributionCalendar-day[^>]*>", h):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(0)))
        if "data-date" not in a:
            continue
        lvl = int(a.get("data-level", 0))
        days.append((a["data-date"], counts.get(a.get("id"), 1 if lvl else 0), lvl))
    return days


def get_days():
    errors = []
    if TOKEN:
        try:
            d = from_graphql()
            if d:
                return sorted(d)
        except Exception as ex:  # noqa: BLE001
            errors.append(f"graphql: {ex}")
    try:
        d = from_html()
        if d:
            return sorted(d)
    except Exception as ex:  # noqa: BLE001
        errors.append(f"html: {ex}")
    raise RuntimeError("; ".join(errors) or "no contribution data")


# --------------------------------------------------------------------------- simulation
ROWS = 7
VAL = {0: 0, 1: 1, 2: 2, 3: 4, 4: 8}      # contribution level -> energy
ATTACK_COST, MONSTER_HP, ENERGY_CAP, INTEGRITY = 2, 4, 12, 3
PRE = 14                                   # intro ticks (init + threat detection)
MAX_TICKS = 230


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def sgn(v):
    return (v > 0) - (v < 0)


def step(p, target, m, w, ncols):
    best = None
    for dc in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if dc == 0 and dr == 0:
                continue
            q = (p[0] + dc, p[1] + dr)
            if not (0 <= q[0] < ncols and 0 <= q[1] < ROWS) or (m and q == m):
                continue
            s = math.hypot(q[0] - target[0], q[1] - target[1])
            if m and w:
                s -= w * min(cheb(q, m), 6)
            if best is None or s < best[0] - 1e-9:
                best = (s, q)
    return best[1] if best else p


def simulate(cells, ncols, seed):
    rnd = random.Random(seed)
    remaining = {c: lv for c, lv in cells.items() if lv > 0}
    recs, collects = [], []
    tot = sum(VAL[v] for v in remaining.values()) or 1
    cm = sum(c[0] * VAL[v] for c, v in remaining.items()) / tot if remaining else ncols / 2
    to_right = cm >= (ncols - 1) / 2
    pstart = (max(2, min(ncols - 3, round(cm + (-ncols * 0.12 if to_right else ncols * 0.12)))), 3)
    S = dict(p=pstart, m=None, flee=0, energy=2, hp=MONSTER_HP, integ=INTEGRITY, stun=0, over=0,
             pst="idle", mst="hidden", face=1, mface=-1, pop=0.0, mop=0.0,
             combat_until=-1, first_collect=None, end=None, combo=[])

    def push(label=None, **kw):
        S.update(kw)
        recs.append(dict(p=S["p"], m=S["m"] or (ncols - 1, 3), pst=S["pst"], mst=S["mst"],
                         face=S["face"], mface=S["mface"], energy=S["energy"], hp=S["hp"],
                         over=S["over"] > 0, pop=S["pop"], mop=S["mop"], label=label))

    # --- intro: system initialising, monster appears, threat detected
    spawn = (0 if to_right else ncols - 1, rnd.randrange(ROWS))
    drift = 1 if to_right else -1
    for t in range(PRE):
        pop = [0.0, 0.5, 1.0][t] if t < 3 else 1.0
        if t == 5:
            S["m"] = spawn
        if t == 5:
            S.update(mst="searching", mop=0.3)
        elif t == 6:
            S.update(mop=1.0)
        if S["m"] and t > 5 and t % 2 == 0:
            S["m"] = (S["m"][0] + drift, S["m"][1])
        push("INIT" if t < 5 else "THREAT", pop=pop, pst="idle")
    S["mst"] = "chasing"

    mode, t = "collect", PRE
    exit_cell = None
    while t < MAX_TICKS and S["end"] is None:
        p, m = S["p"], S["m"]
        dm = cheb(p, m)
        if S["over"] > 0:
            S["over"] -= 1
        label = None
        pst = "moving"
        collected = None
        if t >= MAX_TICKS - 30 and mode != "escape":
            mode = "escape"

        if mode == "escape":
            if exit_cell is None:
                n = ncols - 1
                a = abs(0 - m[0]) - 0.35 * abs(0 - p[0])
                b = abs(n - m[0]) - 0.35 * abs(n - p[0])
                exit_cell = (0 if a > b else n, p[1])
            S["p"] = step(p, exit_cell, m, 1.1, ncols)
            pst = "escaping"
            label = "ESCAPE"
            if S["p"][0] == exit_cell[0]:
                S["end"] = "escape"
        elif dm <= 1:
            away = (sgn(m[0] - p[0]) or rnd.choice([-1, 1]), sgn(m[1] - p[1]))
            if S["energy"] >= ATTACK_COST:
                dmg = 2 if S["over"] > 0 else 1
                S["hp"] = max(0, S["hp"] - dmg)
                S["energy"] -= ATTACK_COST
                S["over"] = 0
                pst = "attacking"
                S["face"] = sgn(m[0] - p[0]) or S["face"]
                S["m"] = (max(0, min(ncols - 1, m[0] + 2 * away[0])), max(0, min(ROWS - 1, m[1] + 2 * away[1])))
                S["stun"] = 2
                S["mst"] = "damaged"
                S["combat_until"] = t + 3
                if S["hp"] == 0:
                    S["mst"], S["end"] = "defeated", "win"
            else:
                S["integ"] -= 1
                pst = "damaged"
                S["p"] = (max(0, min(ncols - 1, p[0] - 2 * away[0])), max(0, min(ROWS - 1, p[1] - 2 * away[1])))
                S["stun"] = 1
                S["flee"] = 4
                S["mst"] = "damaged"
                S["combat_until"] = t + 3
                if S["integ"] <= 0:
                    mode = "escape"
        else:
            ready = S["energy"] >= ATTACK_COST
            moved = None
            if S["flee"] > 0:
                S["flee"] -= 1
                far = (0 if abs(0 - m[0]) > abs(ncols - 1 - m[0]) else ncols - 1, p[1])
                moved = step(p, far, m, 1.4, ncols)
            elif ready and (dm <= 3 or not remaining):
                moved = step(p, m, m, 0, ncols)
            elif remaining:
                best, tgt = -1, None
                for c, lv in remaining.items():
                    sc = VAL[lv] / (cheb(p, c) + 3)
                    if S["energy"] < ATTACK_COST and cheb(c, m) <= 3:
                        sc *= 0.3
                    if sc > best:
                        best, tgt = sc, c
                moved = step(p, tgt, m, 0.9 if S["energy"] < ATTACK_COST else 0, ncols)
            else:
                mode = "escape"
            if moved:
                S["face"] = sgn(moved[0] - p[0]) or S["face"]
                S["p"] = moved
                if moved in remaining:
                    lv = remaining.pop(moved)
                    S["energy"] = min(ENERGY_CAP, S["energy"] + VAL[lv])
                    pst = "collecting"
                    S["combo"] = [x for x in S["combo"] if t - x <= 5] + [t]
                    if lv == 4 or len(S["combo"]) >= 3:
                        S["over"] = 40
                    if S["first_collect"] is None:
                        S["first_collect"] = t
                    collected = (len(recs), moved, lv)

        # monster turn
        if S["end"] != "win":
            alive_state = "enraged" if S["hp"] <= 2 else "chasing"
            if S["stun"] > 0:
                S["stun"] -= 1
                S["mst"] = "damaged" if S["stun"] > 0 or pst in ("attacking", "damaged") else alive_state
            else:
                S["mst"] = alive_state
                if cheb(S["m"], S["p"]) > 1 and not (t % 5 == 4 and S["mst"] != "enraged"):
                    S["m"] = step(S["m"], S["p"], None, 0, ncols)
            S["mface"] = sgn(S["p"][0] - S["m"][0]) or S["mface"]

        # label
        if S["end"]:
            label = "SECURED" if S["end"] == "win" else label
        elif t <= S["combat_until"] or pst == "attacking":
            label = "COMBAT"
        elif label is None:
            if S["over"] > 0:
                label = "OVERCHARGE"
            elif S["first_collect"] is not None and t - S["first_collect"] < 8:
                label = "POWER"
            else:
                label = "PURSUIT"
        push(label, pst=pst)
        if collected:
            collects.append(collected)
        t += 1

    # --- finale
    if S["end"] == "win":
        for i, op in enumerate([1, 1, .8, .5, .25, 0, 0]):
            S["pst"] = "idle"
            push("SECURED", pst="idle", mop=op)
        S["mst"] = "defeated"
    else:
        S["mst"] = "searching"
        for op in (.7, .4, .15, 0):
            push("SECURED", pst="escaping", pop=op, mst="searching")
    for _ in range(3):
        push("SECURED", pst="idle")
    return recs, collects, S["end"]


# --------------------------------------------------------------------------- svg
PITCH, CELL, X0, Y0 = 17, 14, 40, 62
LVL_FILL = {0: "#121a26", 1: "#164a5c", 2: "#1f7a94", 3: "#3bb7d6", 4: "#6EE7FF"}
LABELS = {"INIT": "SYSTEM INITIALIZING", "THREAT": "THREAT DETECTED", "POWER": "POWER ACQUIRED",
          "PURSUIT": "PURSUIT", "OVERCHARGE": "OVERCHARGE", "COMBAT": "COMBAT",
          "ESCAPE": "ESCAPE PROTOCOL", "SECURED": "SYSTEM SECURED"}


def cx(c): return X0 + c * PITCH + CELL / 2
def cy(r): return Y0 + r * PITCH + CELL / 2


def build_svg(days):
    first = dt.date.fromisoformat(days[0][0])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    grid = {}
    for d, cnt, lv in days:
        dd = dt.date.fromisoformat(d)
        grid[((dd - start).days // 7, (dd.weekday() + 1) % 7)] = (dd, cnt, lv)
    ncols = max(c for c, _ in grid) + 1
    levels = {k: v[2] for k, v in grid.items()}
    total = sum(v[1] for v in grid.values())
    cores = sum(1 for v in levels.values() if v == 4)

    # longest real streak
    streak = run = 0
    prev = None
    for d, cnt, _ in days:
        dd = dt.date.fromisoformat(d)
        run = run + 1 if cnt > 0 and prev is not None and (dd - prev).days == 1 and run else (1 if cnt > 0 else 0)
        prev = dd
        streak = max(streak, run)

    seed = int(hashlib.sha256(json.dumps(sorted((k, v) for k, v in levels.items() if v)).encode()).hexdigest()[:8], 16)
    recs, collects, outcome = simulate(levels, ncols, seed)

    N = len(recs)
    dt_ = min(0.26, 32.0 / N)
    outro = 2.6
    T = round(N * dt_ + outro, 3)
    W = X0 + ncols * PITCH + 24
    H = 252

    def kt(i): return f"{min(1.0, i * dt_ / T):.5f}"
    dur = f'dur="{T}s" repeatCount="indefinite"'

    def anim_lin(attr, vals, extra=""):
        keys = ";".join(kt(i) for i in range(len(vals)))
        v = ";".join(str(x) for x in vals)
        return f'<animate attributeName="{attr}" calcMode="linear" {dur} keyTimes="{keys};1" values="{v};{vals[-1]}" {extra}/>'

    def anim_flag(attr, series, extra=""):
        pts = []
        for i, v in enumerate(series):
            if not pts or pts[-1][1] != v:
                pts.append((i, v))
        keys = ";".join(kt(i) for i, _ in pts)
        vals = ";".join(str(v) for _, v in pts)
        return (f'<animate attributeName="{attr}" calcMode="discrete" {dur} '
                f'keyTimes="{keys};1" values="{vals};{pts[-1][1]}" {extra}/>')

    def anim_move(pos, key=None):
        vals = ";".join(f"{cx(c):.1f} {cy(r):.1f}" for c, r in pos)
        keys = ";".join(kt(i) for i in range(len(pos)))
        return (f'<animateTransform attributeName="transform" type="translate" calcMode="linear" {dur} '
                f'keyTimes="{keys};1" values="{vals};{cx(*pos[-1]):.1f} {cy(pos[-1][1]):.1f}"/>'
                if False else
                f'<animateTransform attributeName="transform" type="translate" calcMode="linear" {dur} '
                f'keyTimes="{keys};1" values="{vals};{cx(pos[-1][0]):.1f} {cy(pos[-1][1]):.1f}"/>')

    def anim_flip(series):
        vals = [f"{s} 1" for s in series]
        pts = []
        for i, v in enumerate(vals):
            if not pts or pts[-1][1] != v:
                pts.append((i, v))
        return (f'<animateTransform attributeName="transform" type="scale" calcMode="discrete" {dur} '
                f'keyTimes="{";".join(kt(i) for i, _ in pts)};1" values="{";".join(v for _, v in pts)};{pts[-1][1]}"/>')

    P = [r["p"] for r in recs]
    M = [r["m"] for r in recs]

    # ---------- field
    out = []
    # month labels
    last_m, last_c = None, -9
    for c in range(ncols):
        d0 = start + dt.timedelta(days=7 * c)
        if d0.month != last_m and c - last_c >= 3:
            out.append(f'<text x="{X0 + c * PITCH}" y="{Y0 - 9}" font-family="{MONO}" font-size="9" fill="{DM}">{d0.strftime("%b").upper()}</text>')
            last_c = c
        last_m = d0.month
    for r, name in ((1, "MON"), (3, "WED"), (5, "FRI")):
        out.append(f'<text x="{X0 - 8}" y="{cy(r) + 3}" font-family="{MONO}" font-size="8" fill="{DM}" text-anchor="end">{name}</text>')

    # power zone (densest 3x3 of real contributions)
    best, zone = 0, None
    for c in range(max(1, ncols - 2)):
        for r in range(ROWS - 2):
            s = sum(grid[(c + i, r + j)][1] for i in range(3) for j in range(3) if (c + i, r + j) in grid)
            if s > best:
                best, zone = s, (c, r)
    fade_start = round(N * dt_ + 1.8, 3)
    sweep = PRE * dt_ * 0.55

    cell_svg = []
    collected_at = {cell: i for i, cell, lv in collects}
    for (c, r), (dd, cnt, lv) in sorted(grid.items()):
        x, y = X0 + c * PITCH, Y0 + r * PITCH
        base = LVL_FILL[lv]
        tip = f'<title>{cnt} contribution{"s" if cnt != 1 else ""} on {dd.isoformat()}</title>'
        a = ""
        if (c, r) in collected_at:
            tc = collected_at[(c, r)] * dt_
            k = [0, tc, tc + 0.12, tc + 0.5, N * dt_ + 1.6, T]
            keys = ";".join(f"{min(1, v / T):.5f}" for v in k)
            a = (f'<animate attributeName="fill" calcMode="linear" {dur} keyTimes="{keys}" '
                 f'values="{base};{base};#FFFFFF;{LVL_FILL[0]};{LVL_FILL[0]};{base}"/>')
        deco = ""
        if lv >= 3:
            deco = (f'<rect x="{x + 4}" y="{y + 4}" width="{CELL - 8}" height="{CELL - 8}" rx="1" '
                    f'fill="none" stroke="#04202a" stroke-width="1" opacity=".55"/>')
        cell_svg.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{base}">{tip}{a}</rect>{deco}')
    zone_svg = ""
    if zone:
        zx, zy = X0 + zone[0] * PITCH - 4, Y0 + zone[1] * PITCH - 4
        zw = 3 * PITCH + 5 - 3
        zone_svg = (f'<g stroke="{VI}" stroke-width="1.2" fill="none" opacity=".75" stroke-linecap="round">'
                    f'<path d="M{zx} {zy + 7}V{zy}H{zx + 7}M{zx + zw - 7} {zy}H{zx + zw}V{zy + 7}'
                    f'M{zx + zw} {zy + zw - 7}V{zy + zw}H{zx + zw - 7}M{zx + 7} {zy + zw}H{zx}V{zy + zw - 7}"/>'
                    f'<animate attributeName="opacity" values=".35;.9;.35" dur="3.2s" repeatCount="indefinite"/></g>'
                    f'<text x="{zx}" y="{zy - 3}" font-family="{MONO}" font-size="8" fill="{VI}" opacity=".85">POWER ZONE</text>')

    # pickup bursts
    fx = []
    for i, cell, lv in collects:
        tc = i * dt_
        keys = ";".join(f"{min(1, v / T):.5f}" for v in (0, tc, tc + 0.45, T))
        col = VI if lv == 4 else CY
        fx.append(f'<circle cx="{cx(cell[0]):.1f}" cy="{cy(cell[1]):.1f}" r="3" fill="none" stroke="{col}" stroke-width="1.2" opacity="0">'
                  f'<animate attributeName="r" {dur} keyTimes="{keys}" values="3;3;{12 if lv >= 3 else 9};{12 if lv >= 3 else 9}"/>'
                  f'<animate attributeName="opacity" {dur} keyTimes="{keys}" values="0;.95;0;0"/></circle>')
        if lv >= 2:
            k2 = ";".join(f"{min(1, v / T):.5f}" for v in (0, tc, tc + 0.9, T))
            fx.append(f'<text x="{cx(cell[0]):.1f}" y="{cy(cell[1]) - 8:.1f}" font-family="{MONO}" font-size="9" font-weight="700" fill="{col}" text-anchor="middle" opacity="0">+{VAL[lv]}'
                      f'<animate attributeName="opacity" {dur} keyTimes="{k2}" values="0;1;0;0"/>'
                      f'<animateTransform attributeName="transform" type="translate" {dur} keyTimes="{k2}" values="0 0;0 0;0 -9;0 -9"/></text>')

    # ---------- player sprite (faces right)
    pst = [r["pst"] for r in recs]
    fl = lambda name: [1 if s == name else 0 for s in pst]  # noqa: E731
    player = f"""
<g>{anim_move(P)}
 <g>{anim_flip([r['face'] for r in recs])}
  <g>{anim_lin('opacity', [r['pop'] for r in recs])}
   <g opacity="0">{anim_flag('opacity', [1 if s == 'moving' else 0 for s in pst])}<path d="M-5 0L-15 -2.6 -11.5 0 -15 2.6Z" fill="{CY}" opacity=".45"/></g>
   <g opacity="0">{anim_flag('opacity', fl('escaping'))}<path d="M-6 -4H-17M-6 0H-20M-6 4H-17" stroke="{CY}" stroke-width="1.2" stroke-linecap="round" opacity=".85"/></g>
   <circle r="10" fill="{VI}" fill-opacity=".14" stroke="{VI}" stroke-width="1.1" stroke-dasharray="3 2.5" opacity="0">{anim_flag('opacity', [1 if r['over'] else 0 for r in recs])}<animateTransform attributeName="transform" type="rotate" values="0;360" dur="3s" repeatCount="indefinite"/></circle>
   <circle r="9" fill="{CY}" fill-opacity=".16" stroke="{CY}" stroke-width=".9" opacity="0">{anim_flag('opacity', fl('collecting'))}</circle>
   <path d="M-1.5 4.8L-2.7 8.4M1.5 4.8L2.9 8.4" stroke="{CY}" stroke-width="1.3" stroke-linecap="round"/>
   <path d="M-3.3 -.6L-6.6 1.8-3.3 3.6Z" fill="{BL}"/>
   <rect x="-3.7" y="-1.4" width="7.4" height="7" rx="2.6" fill="{S1}" stroke="{CY}" stroke-width="1"/>
   <circle cy="2.2" r="3.2" fill="{CY}" opacity=".3"><animate attributeName="r" values="2.6;3.6;2.6" dur="1.4s" repeatCount="indefinite"/></circle>
   <circle cy="2.2" r="1.4" fill="#fff"/>
   <path d="M-1 -7.4L-2.2 -9.6" stroke="{CY}" stroke-width=".9" stroke-linecap="round"/><circle cx="-2.3" cy="-9.8" r=".9" fill="{CY}"/>
   <circle cy="-3.7" r="3.7" fill="#EAFBFF" stroke="{CY}" stroke-width=".8"/>
   <path d="M.2 -5.1H4.1Q4.9 -3.7 4.1 -2.3H.2Q-.5 -3.7 .2 -5.1Z" fill="{S1}"/><rect x="1.6" y="-4.2" width="2" height=".9" rx=".4" fill="{CY}"/>
   <circle r="8" fill="{WARN}" fill-opacity=".5" opacity="0">{anim_flag('opacity', fl('damaged'))}</circle>
   <path d="M3 -10A12 12 0 0 1 3 10A8.5 8.5 0 0 0 3 -10Z" fill="#fff" stroke="{CY}" stroke-width=".8" opacity="0">{anim_flag('opacity', fl('attacking'))}</path>
  </g>
 </g>
</g>"""

    # ---------- monster sprite (faces right)
    mst = [r["mst"] for r in recs]
    core_col = {"hidden": DM, "searching": "#6a5fd6", "chasing": VI, "enraged": WARN, "damaged": "#FFFFFF", "defeated": BR}
    mfl = lambda name: [1 if s == name else 0 for s in mst]  # noqa: E731
    det = next((i for i, r in enumerate(recs) if r["label"] == "THREAT" and i >= 9), 9)
    defeat_i = next((i for i, s in enumerate(mst) if s == "defeated"), None)
    shards = ""
    if defeat_i is not None:
        td = defeat_i * dt_
        k = ";".join(f"{min(1, v / T):.5f}" for v in (0, td, td + 0.9, T))
        for dx, dy in ((-11, -9), (12, -7), (0, 12), (-9, 9), (10, 8)):
            shards += (f'<path d="M0 0l{dx * .18:.1f} {dy * .18:.1f}" stroke="{VI}" stroke-width="1.4" stroke-linecap="round" opacity="0">'
                       f'<animate attributeName="opacity" {dur} keyTimes="{k}" values="0;1;0;0"/>'
                       f'<animateTransform attributeName="transform" type="translate" {dur} keyTimes="{k}" values="0 0;0 0;{dx} {dy};{dx} {dy}"/></path>')
    alert_k = ";".join(f"{min(1, v / T):.5f}" for v in (0, det * dt_, det * dt_ + 0.15, (det + 5) * dt_, (det + 5) * dt_ + 0.01, T))
    monster = f"""
<g>{anim_move(M)}
 <g>{anim_flip([r['mface'] for r in recs])}
  <g>{anim_lin('opacity', [r['mop'] for r in recs])}
   <circle r="11" fill="none" stroke="{WARN}" stroke-width=".9" stroke-dasharray="2 2.5" opacity="0">{anim_flag('opacity', mfl('enraged'))}<animateTransform attributeName="transform" type="rotate" values="360;0" dur="2.4s" repeatCount="indefinite"/></circle>
   <g stroke="{VI}" stroke-width="1" fill="none" stroke-linecap="round">
    <path d="M-3 3Q-6 6.5 -7.8 9"/><path d="M0 4.2Q0 7.4 -1 9.4"/><path d="M3 3Q6 6.5 7.8 9"/><path d="M-4.4 .4Q-8.4 1 -9.4 4.4"/><path d="M4.4 .4Q8.4 1 9.4 4.4"/>
   </g>
   <path d="M-5.4 -3L-6.4 -8.2-2.8 -5.2-1.2 -9.8 1 -5.2 3.2 -8.8 4.8 -3Z" fill="{BG}" stroke="{VI}" stroke-width=".9" stroke-linejoin="round"/>
   <ellipse cy=".6" rx="6.4" ry="4.9" fill="#04060A" stroke="{VI}" stroke-width="1.1"/>
   <path d="M5.2 1.2L8.8 -.6M5.2 2.6L8.8 3.8" stroke="{VI}" stroke-width="1" stroke-linecap="round"/>
   <circle cx="-.6" cy=".9" r="3.6" fill="{VI}" opacity=".28" filter="url(#glow)"/>
   <circle cx="-.6" cy=".9" r="2.1" fill="{VI}">{anim_flag('fill', [core_col[s] for s in mst])}<animate attributeName="r" values="1.8;2.4;1.8" dur="1.1s" repeatCount="indefinite"/></circle>
   <path d="M1.6 -2.1L5 -1.1 2 -.1Z" fill="{WARN}"/><path d="M1.2 -.2L3.6 .5 1.4 1Z" fill="{WARN}" opacity=".7"/>
   <ellipse cy=".6" rx="7" ry="5.4" fill="#fff" opacity="0">{anim_flag('opacity', [.8 if s == 'damaged' else 0 for s in mst])}</ellipse>
   {shards}
  </g>
  <text y="-12" x="0" font-family="{MONO}" font-size="10" font-weight="700" fill="{WARN}" text-anchor="middle" opacity="0">!<animate attributeName="opacity" {dur} keyTimes="{alert_k}" values="0;1;1;1;0;0"/></text>
 </g>
</g>"""

    # ---------- HUD
    pw = [round(110 * min(1, r["energy"] / ENERGY_CAP), 1) for r in recs]
    th = []
    for r in recs:
        if r["mst"] in ("hidden", "defeated"):
            th.append(0)
            continue
        prox = max(0, min(1, 1 - (cheb(r["p"], r["m"]) - 1) / 14))
        th.append(round(110 * (0.35 * r["hp"] / MONSTER_HP + 0.65 * prox), 1))
    labels = [r["label"] or "PURSUIT" for r in recs]
    label_svg = ""
    for key, text in LABELS.items():
        series = [1 if l == key else 0 for l in labels]
        if not any(series):
            continue
        label_svg += (f'<text x="{W - 24}" y="30" font-family="{MONO}" font-size="11" letter-spacing="2.4" fill="{CY}" text-anchor="end" opacity="0">'
                      f'{text}{anim_flag("opacity", series)}</text>')
    hy = H - 28
    hud = f"""
<mask id="seg" maskUnits="userSpaceOnUse" x="0" y="0" width="110" height="6">{''.join(f'<rect x="{i * 10}" y="0" width="8" height="6" rx="1" fill="#fff"/>' for i in range(11))}</mask>
<text x="{X0}" y="{hy + 6}" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{DM}">POWER</text>
<g transform="translate({X0 + 54} {hy})" mask="url(#seg)"><rect width="110" height="6" fill="{BR}"/><rect height="6" fill="url(#gPow)" width="0">{anim_lin('width', pw)}</rect></g>
<text x="{X0 + 196}" y="{hy + 6}" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{DM}">THREAT</text>
<g transform="translate({X0 + 256} {hy})" mask="url(#seg)"><rect width="110" height="6" fill="{BR}"/><rect height="6" fill="url(#gThr)" width="0">{anim_lin('width', th)}</rect></g>
<text x="{X0 + 398}" y="{hy + 6}" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{DM}">STREAK <tspan fill="{MU}">×{streak}</tspan></text>
<text x="{X0 + 478}" y="{hy + 6}" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{DM}">CORE <tspan fill="{MU}">{cores:02d}</tspan></text>
<text x="{X0 + 566}" y="{hy + 6}" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{DM}">LAST YEAR <tspan fill="{MU}">{total}</tspan></text>"""
    legend = f'<text x="{W - 24 - 5 * 15 - 36}" y="{hy + 6}" font-family="{MONO}" font-size="9" fill="{DM}" text-anchor="end">LOW</text>'
    for i in range(5):
        legend += f'<rect x="{W - 24 - 5 * 15 - 30 + i * 15}" y="{hy - 1}" width="11" height="11" rx="3" fill="{LVL_FILL[i]}"/>'
    legend += f'<text x="{W - 24 + 2}" y="{hy + 6}" font-family="{MONO}" font-size="9" fill="{DM}" text-anchor="end">CORE</text>'

    defs = f"""
<linearGradient id="gPow" x1="0" x2="1"><stop offset="0" stop-color="{CY}"/><stop offset="1" stop-color="{BL}"/></linearGradient>
<linearGradient id="gThr" x1="0" x2="1"><stop offset="0" stop-color="{VI}"/><stop offset="1" stop-color="{WARN}"/></linearGradient>
<linearGradient id="gLine" x1="0" x2="1"><stop offset="0" stop-color="{CY}"/><stop offset=".5" stop-color="{BL}"/><stop offset="1" stop-color="{VI}"/></linearGradient>
<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="2.2"/></filter>
<clipPath id="reveal"><rect x="0" y="{Y0 - 14}" height="{ROWS * PITCH + 20}" width="0">
<animate attributeName="width" {dur} calcMode="linear" keyTimes="0;{sweep / T:.5f};1" values="0;{W};{W}"/></rect></clipPath>"""

    fade = f'<animate attributeName="opacity" {dur} keyTimes="0;{fade_start / T:.5f};{min(1, (fade_start + 0.6) / T):.5f};1" values="1;1;0;0"/>'
    body = f"""
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{BG}" stroke="{BR}"/>
<rect x="1" y="1" width="{W - 2}" height="46" rx="13" fill="{S1}" opacity=".55"/>
<circle cx="26" cy="26" r="3.4" fill="{CY}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>
<text x="40" y="30" font-family="{MONO}" font-size="12" letter-spacing="3.4" fill="{TX}" font-weight="600">ESCAPE PROTOCOL</text>
<g>{label_svg}{fade}</g>
<g>{''.join(out)}
<g clip-path="url(#reveal)">{''.join(cell_svg)}{zone_svg}</g>
<rect y="{Y0 - 6}" width="1.6" height="{ROWS * PITCH + 4}" fill="{CY}" opacity="0"><animate attributeName="x" {dur} keyTimes="0;{sweep / T:.5f};1" values="{X0};{W - 20};{W - 20}"/><animate attributeName="opacity" {dur} keyTimes="0;{max(0.0001, sweep / T - 0.001):.5f};{sweep / T:.5f};1" values=".95;.95;0;0"/></rect>
{''.join(fx)}
{monster}
{player}
{fade}</g>
<line x1="24" x2="{W - 24}" y1="{H - 42}" y2="{H - 42}" stroke="url(#gLine)" stroke-opacity=".35"/>
{hud}{legend}"""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-label="ESCAPE PROTOCOL: an autonomous mini-game generated from {e(USER)}\'s real GitHub contribution graph">'
           f'<title>ESCAPE PROTOCOL — generated from the real contribution graph</title><defs>{defs}{hud.split("<text")[0]}</defs>{body.replace(hud.split("<text")[0], "")}</svg>\n')
    stats = dict(ticks=N, seconds=T, cells=len([1 for v in levels.values() if v]), collected=len(collects),
                 outcome=outcome, streak=streak, cores=cores, total=total, cols=ncols)
    return svg, stats


def main():
    try:
        days = get_days()
    except Exception as ex:  # noqa: BLE001
        print(f"[escape-protocol] could not fetch contributions: {ex}", file=sys.stderr)
        if os.path.exists(OUT):
            print("[escape-protocol] keeping existing asset", file=sys.stderr)
            return 0
        return 1
    svg, stats = build_svg(days)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if old != svg:
        open(OUT, "w", encoding="utf-8").write(svg)
    print("[escape-protocol]", json.dumps(stats), f"{len(svg) / 1024:.1f} KB", "updated" if old != svg else "unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
