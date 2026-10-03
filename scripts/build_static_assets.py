#!/usr/bin/env python3
"""Builds the hand-designed SVGs (hero, cards, buttons, panels, socials, footer).
Edit the copy/data below and re-run:  python3 scripts/build_static_assets.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import *  # noqa: F401,F403

A = os.path.join(os.path.dirname(__file__), "..", "assets")


def out(name, s):
    write(os.path.join(A, name), s)


def brackets(w, h, m=14, l=14, col=BR):
    return (f'<path d="M{m} {m + l}V{m}H{m + l}M{w - m - l} {m}H{w - m}V{m + l}M{w - m} {h - m - l}V{h - m}H{w - m - l}'
            f'M{m + l} {h - m}H{m}V{h - m - l}" fill="none" stroke="{col}" stroke-width="1"/>')


# ------------------------------------------------------------------ hero
def hero():
    w, h, cx_, cy_ = 880, 380, 690, 192
    d = f'<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#101824" stroke-width="1"/></pattern>'
    d += f'<radialGradient id="rg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{BL}" stop-opacity=".30"/><stop offset=".5" stop-color="{VI}" stop-opacity=".10"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>'
    d += f'<radialGradient id="core" cx=".4" cy=".35" r=".8"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="{CY}"/><stop offset=".65" stop-color="{BL}"/><stop offset="1" stop-color="{VI}"/></radialGradient>'
    d += f'<linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity=".0"/></linearGradient>'
    b = f'<rect width="{w}" height="{h}" rx="18" fill="{BG}"/><rect width="{w}" height="{h}" rx="18" fill="url(#grid)"/>'
    b += f'<circle cx="{cx_}" cy="{cy_}" r="250" fill="url(#rg)"/>'
    for r, dash in ((38, ""), (80, "2 6"), (126, ""), (174, "1 7")):
        b += f'<circle cx="{cx_}" cy="{cy_}" r="{r}" fill="none" stroke="{BR}" stroke-width="1" stroke-dasharray="{dash}"/>'
    b += f'<ellipse cx="{cx_}" cy="{cy_}" rx="196" ry="62" fill="none" stroke="url(#gA)" stroke-width="1" opacity=".75" transform="rotate(-24 {cx_} {cy_})"/>'
    b += f'<ellipse cx="{cx_}" cy="{cy_}" rx="150" ry="46" fill="none" stroke="{BR}" stroke-width="1" transform="rotate(34 {cx_} {cy_})"/>'
    # tick marks on outer ring
    for i in range(72):
        a = math.radians(i * 5)
        r1, r2 = 178, 184 if i % 6 else 190
        b += f'<line x1="{cx_ + r1 * math.cos(a):.1f}" y1="{cy_ + r1 * math.sin(a):.1f}" x2="{cx_ + r2 * math.cos(a):.1f}" y2="{cy_ + r2 * math.sin(a):.1f}" stroke="{BR}" stroke-width="1"/>'
    # orbiting data points
    pts = ""
    for r, a, col, rad in ((80, 20, CY, 3), (126, 150, VI, 3.4), (174, 255, BL, 3), (126, 300, CY, 2.4), (80, 200, GR, 2.4), (174, 100, VI, 2.4)):
        x, y = cx_ + r * math.cos(math.radians(a)), cy_ + r * math.sin(math.radians(a))
        pts += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{col}"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{rad + 4}" fill="none" stroke="{col}" stroke-opacity=".35"/>'
    b += f'<g>{pts}<animateTransform attributeName="transform" type="rotate" from="0 {cx_} {cy_}" to="360 {cx_} {cy_}" dur="140s" repeatCount="indefinite"/></g>'
    # core
    b += f'<circle cx="{cx_}" cy="{cy_}" r="30" fill="{CY}" opacity=".18" filter="url(#glow)"/>'
    b += f'<circle cx="{cx_}" cy="{cy_}" r="30" fill="none" stroke="{CY}" stroke-opacity=".5"><animate attributeName="r" values="30;42;30" dur="5s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".5;0;.5" dur="5s" repeatCount="indefinite"/></circle>'
    b += f'<circle cx="{cx_}" cy="{cy_}" r="18" fill="url(#core)"/><circle cx="{cx_}" cy="{cy_}" r="6" fill="#fff" opacity=".9"/>'
    b += f'<path d="M{cx_ - 60} {cy_}H{cx_ - 26}M{cx_ + 26} {cy_}H{cx_ + 60}M{cx_} {cy_ - 60}V{cy_ - 26}M{cx_} {cy_ + 26}V{cy_ + 60}" stroke="{CY}" stroke-opacity=".5"/>'
    # tiny technical labels
    for x, y, s, anc in ((cx_ + 96, cy_ - 74, "P2P", "start"), (cx_ - 150, cy_ - 108, "AI", "end"), (cx_ + 150, cy_ + 112, "RUST", "start"),
                         (cx_ - 98, cy_ + 112, "MESH", "end"), (cx_ + 8, cy_ + 76, "CORE", "start")):
        b += T(x, y, s, 9.5, DM, MONO, 400, anc, 1.8)
    b += brackets(w, h, 16, 16, BR)
    # text
    b += T(56, 64, "// UZAIR.UMAR / PROFILE", 11, DM, MONO, 400, "start", 2)
    b += T(54, 176, "UZAIR UMAR", 64, TX, SANS, 700, "start", -1.5)
    b += T(56, 216, "SOFTWARE ENGINEER", 16, CY, MONO, 600, "start", 4.5)
    b += T(56, 241, "SYSTEMS BUILDER · RESEARCHER", 13, MU, MONO, 400, "start", 3)
    b += f'<rect x="56" y="262" width="260" height="1.5" rx=".75" fill="url(#gA)"/>'
    b += T(56, 296, "Building software at the intersection of", 17.5, MU)
    b += T(56, 320, "systems, AI and distributed computing.", 17.5, TX)
    b += f'<circle cx="60" cy="350" r="3" fill="{GR}"><animate attributeName="opacity" values="1;.3;1" dur="2.6s" repeatCount="indefinite"/></circle>'
    b += T(72, 354, "STATUS  BUILDING", 10.5, DM, MONO, 400, "start", 2.4)
    b += f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="none" stroke="{BR}"/>'
    out("hero-system.svg", svg(w, h, b, d, "Uzair Umar — Software Engineer, Systems Builder, Researcher"))


# ------------------------------------------------------------------ section dividers
def sections():
    for key, label in (("about", "ABOUT"), ("projects", "FEATURED PROJECTS"), ("game", "ESCAPE PROTOCOL"),
                       ("engineering", "ENGINEERING"), ("research", "RESEARCH"), ("process", "BUILD PROCESS"),
                       ("contact", "CONTACT")):
        w, h = 880, 44
        tw = len(label) * 11.4 + 24
        b = f'<circle cx="4" cy="22" r="3" fill="{CY}"/>'
        b += T(18, 26, label, 12, TX, MONO, 600, "start", 4)
        b += f'<rect x="{tw + 24}" y="21.25" width="{w - tw - 24}" height="1.5" fill="url(#gFade)"/>'
        out(f"section-{key}.svg", svg(w, h, b, "", label))


# ------------------------------------------------------------------ about panel
def about():
    w, h = 640, 258
    rows = (("BUILDING", "systems worth understanding", CY), ("EXPLORING", "AI · distributed systems · Linux · research", BL),
            ("LEARNING", "Rust · Go · deeper systems engineering", VI), ("PRINCIPLE", "specification before implementation", GR))
    b = frame(w, h, 16)
    b += f'<circle cx="30" cy="34" r="3.5" fill="{GR}"><animate attributeName="opacity" values="1;.3;1" dur="2.6s" repeatCount="indefinite"/></circle>'
    b += T(44, 38, "CURRENT MODE", 12, TX, MONO, 600, "start", 3.4)
    b += T(w - 28, 38, "SYS.ACTIVE", 10.5, DM, MONO, 400, "end", 2)
    b += f'<line x1="28" x2="{w - 28}" y1="58" y2="58" stroke="{BR}"/>'
    for i, (k, v, col) in enumerate(rows):
        y = 94 + i * 44
        b += f'<rect x="28" y="{y - 14}" width="3" height="22" rx="1.5" fill="{col}"/>'
        b += T(46, y + 2, k, 12, col, MONO, 600, "start", 3)
        b += T(168, y + 3, v, 16, TX if i < 3 else MU)
    out("about-panel.svg", svg(w, h, b, "", "Current mode: building, exploring, learning, principle"))


# ------------------------------------------------------------------ project cards
def motif_chat():
    pts = ((286, 98), (376, 74), (350, 134))
    s = ""
    for a, b_ in ((0, 1), (1, 2), (2, 0)):
        s += f'<line x1="{pts[a][0]}" y1="{pts[a][1]}" x2="{pts[b_][0]}" y2="{pts[b_][1]}" stroke="{BL}" stroke-opacity=".5" stroke-dasharray="3 4"/>'
    s += f'<circle cx="332" cy="102" r="52" fill="none" stroke="{BR}" stroke-dasharray="1 5"/>'
    for (x, y), c in zip(pts, (CY, BL, VI)):
        s += f'<circle cx="{x}" cy="{y}" r="9" fill="{c}" opacity=".16"/><circle cx="{x}" cy="{y}" r="4.5" fill="{S1}" stroke="{c}" stroke-width="1.5"/>'
    path = f"M{pts[0][0]} {pts[0][1]}L{pts[1][0]} {pts[1][1]}L{pts[2][0]} {pts[2][1]}L{pts[0][0]} {pts[0][1]}"
    s += f'<circle r="2.6" fill="#fff"><animateMotion dur="7s" repeatCount="indefinite" path="{path}"/></circle>'
    s += f'<circle r="5" fill="{CY}" opacity=".35" filter="url(#glow)"><animateMotion dur="7s" repeatCount="indefinite" path="{path}"/></circle>'
    return s


def motif_mesh():
    c = (334, 102)
    ring = [(c[0] + 40 * math.cos(math.radians(a)), c[1] + 40 * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    s = ""
    for i, (x, y) in enumerate(ring):
        n = ring[(i + 1) % 6]
        s += f'<line x1="{c[0]}" y1="{c[1]}" x2="{x:.1f}" y2="{y:.1f}" stroke="{BL}" stroke-opacity=".4"/>'
        s += f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{n[0]:.1f}" y2="{n[1]:.1f}" stroke="{BR}"/>'
    cols = (CY, BL, VI, CY, GR, BL)
    for (x, y), col in zip(ring, cols):
        s += f'<rect x="{x - 4.5:.1f}" y="{y - 4.5:.1f}" width="9" height="9" rx="2.5" fill="{S1}" stroke="{col}" stroke-width="1.4"/>'
    s += f'<circle cx="{c[0]}" cy="{c[1]}" r="12" fill="{CY}" opacity=".18" filter="url(#glow)"/><rect x="{c[0] - 7}" y="{c[1] - 7}" width="14" height="14" rx="3.5" fill="url(#gAd)"/>'
    s += f'<circle cx="{c[0]}" cy="{c[1]}" r="14" fill="none" stroke="{CY}"><animate attributeName="r" values="14;28;14" dur="4.5s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".6;0;.6" dur="4.5s" repeatCount="indefinite"/></circle>'
    return s


def project_card(fname, num, name, desc, tags, chip, status, motif, title):
    w, h = 420, 262
    d = f'<radialGradient id="cg" cx=".85" cy=".1" r=".7"><stop offset="0" stop-color="{BL}" stop-opacity=".22"/><stop offset="1" stop-color="{BL}" stop-opacity="0"/></radialGradient>'
    b = frame(w, h, 18) + f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17" fill="url(#cg)"/>'
    b += T(28, 44, num, 13, DM, MONO, 400, "start", 2)
    cw = len(chip) * 8.6 + 22
    b += f'<rect x="{w - 28 - cw}" y="27" width="{cw}" height="24" rx="12" fill="none" stroke="{BR}"/>'
    b += T(w - 28 - cw / 2, 43, chip, 10.5, MU, MONO, 400, "middle", 1.8)
    b += motif
    b += T(28, 122, name, 31, TX, SANS, 700, "start", 1)
    b += f'<rect x="28" y="136" width="46" height="2" rx="1" fill="url(#gA)"/>'
    for i, ln in enumerate(wrap(desc, 38)):
        b += T(28, 168 + i * 22, ln, 15.5, MU)
    b += T(28, 214, tags, 10.5, CY, MONO, 400, "start", 1.4)
    b += f'<line x1="28" x2="{w - 28}" y1="228" y2="228" stroke="{BR}"/>'
    b += f'<circle cx="32" cy="245" r="3" fill="{GR}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>'
    b += T(44, 249, status, 10.5, TX, MONO, 600, "start", 2.4)
    b += T(w - 28, 249, "SOON", 10.5, DM, MONO, 400, "end", 2.4)
    out(fname, svg(w, h, b, d, title))


def mall_card():
    w, h = 700, 180
    d = f'<radialGradient id="cg" cx=".92" cy=".5" r=".6"><stop offset="0" stop-color="{VI}" stop-opacity=".18"/><stop offset="1" stop-color="{VI}" stop-opacity="0"/></radialGradient>'
    b = frame(w, h, 18) + f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17" fill="url(#cg)"/>'
    b += T(28, 44, "03", 13, DM, MONO, 400, "start", 2)
    b += f'<rect x="{w - 28 - 92}" y="27" width="92" height="24" rx="12" fill="none" stroke="{BR}"/>'
    b += f'<circle cx="{w - 28 - 76}" cy="39" r="3" fill="{GR}"/>' + T(w - 28 - 40, 43, "PUBLIC", 10.5, MU, MONO, 400, "middle", 1.8)
    b += T(28, 90, "MALL MANAGEMENT SYSTEM", 29, TX, SANS, 700, "start", 1)
    b += f'<rect x="28" y="102" width="46" height="2" rx="1" fill="url(#gA)"/>'
    b += T(28, 130, "Python terminal app with JSON data, four user roles and modular architecture.", 15.5, MU)
    b += T(28, 160, "PYTHON · JSON · ROLE-BASED · MODULAR", 10.5, CY, MONO, 400, "start", 1.4)
    b += f'<rect x="{w - 28 - 176}" y="138" width="176" height="28" rx="14" fill="none" stroke="url(#gA)" stroke-opacity=".8"/>'
    b += T(w - 28 - 88, 156, "VIEW REPOSITORY ↗", 11, TX, MONO, 600, "middle", 1.4)
    out("project-card-mall.svg", svg(w, h, b, d, "Mall Management System — public Python project"))


# ------------------------------------------------------------------ buttons
def button(fname, label, accent):
    w, h = 420, 64
    b = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="url(#gSurf)"/>'
    b += f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="url(#gA)" stroke-opacity=".6"/>'
    b += f'<rect x="1" y="1" width="6" height="{h - 2}" rx="3" fill="{accent}" opacity=".9"/>'
    b += T(28, 38, label, 13.5, TX, MONO, 600, "start", 2.4)
    b += f'<circle cx="{w - 34}" cy="32" r="14" fill="none" stroke="{accent}" stroke-opacity=".7"/>'
    b += f'<path d="M{w - 40} 32H{w - 28}M{w - 33} 27L{w - 28} 32L{w - 33} 37" fill="none" stroke="{accent}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
    out(fname, svg(w, h, b, "", label))


# ------------------------------------------------------------------ engineering map
def engineering():
    w, pw_ = 640, 312
    groups = (
        ("LANGUAGES", CY, (("Python", 1), ("C#", 1), ("SQL / T-SQL", 1), ("JavaScript", 1), ("Rust", 0), ("Go", 0))),
        ("APPLICATIONS", BL, (("React", 1), ("Vite", 1), ("FastAPI", 1), ("REST APIs", 1), ("Databases", 1), ("Git", 1), ("GitHub", 1))),
        ("SYSTEMS", VI, (("Linux", 0), ("Networking", 1), ("P2P", 1), ("Distributed Systems", 0), ("Software Architecture", 1), ("SOLID", 1))),
        ("AI / RESEARCH", GR, (("AI / ML", 0), ("Computer Vision", 0), ("Linear Algebra", 0), ("Systems Research", 0))),
    )
    ph = 236
    h = 2 * ph + 16 + 44
    b = ""
    for gi, (title, col, items) in enumerate(groups):
        x, y = (gi % 2) * (pw_ + 16), (gi // 2) * (ph + 16)
        b += f'<g transform="translate({x} {y})">' + frame(pw_, ph, 16, False)
        b += f'<rect x="1" y="1" width="{pw_ - 2}" height="3" rx="1.5" fill="{col}" opacity=".7"/>'
        b += T(24, 38, title, 12, TX, MONO, 600, "start", 3)
        b += T(pw_ - 24, 38, f"{sum(1 for _, a in items if a)}/{len(items)}", 10.5, DM, MONO, 400, "end", 1.5)
        b += f'<line x1="24" x2="{pw_ - 24}" y1="54" y2="54" stroke="{BR}"/>'
        n = len(items)
        b += f'<line x1="34" x2="34" y1="80" y2="{80 + (n - 1) * 24}" stroke="{col}" stroke-opacity=".3"/>'
        for i, (name, active) in enumerate(items):
            yy = 80 + i * 24
            if active:
                b += f'<circle cx="34" cy="{yy}" r="4.5" fill="{col}"/>'
                b += T(52, yy + 5, name, 15, TX)
            else:
                b += f'<circle cx="34" cy="{yy}" r="4.5" fill="{S1}" stroke="{col}" stroke-width="1.4" stroke-dasharray="2 1.6"/>'
                b += T(52, yy + 5, name, 15, MU)
                b += T(pw_ - 24, yy + 4, "EXPLORING", 9.5, col, MONO, 400, "end", 1.6)
        b += "</g>"
    ly = 2 * ph + 16 + 28
    b += f'<circle cx="8" cy="{ly - 4}" r="4.5" fill="{CY}"/>' + T(22, ly, "IN ACTIVE USE", 10.5, MU, MONO, 400, "start", 2)
    b += f'<circle cx="168" cy="{ly - 4}" r="4.5" fill="{S1}" stroke="{CY}" stroke-width="1.4" stroke-dasharray="2 1.6"/>' + T(182, ly, "EXPLORING / DEEPENING", 10.5, MU, MONO, 400, "start", 2)
    out("engineering-stack.svg", svg(2 * pw_ + 16, h, b, "", "Engineering system map: languages, applications, systems, AI and research"))


# ------------------------------------------------------------------ research
def research():
    w, h = 640, 270
    topics = ("Artificial Intelligence", "Computer Vision", "Linear Algebra", "Distributed Computing", "Systems Research", "Mathematical & computational experiments")
    cols = (CY, BL, VI, CY, BL, GR)
    b = frame(w, h, 16)
    b += T(28, 40, "OPEN QUESTIONS", 12, TX, MONO, 600, "start", 3.4)
    b += f'<line x1="28" x2="{w - 28}" y1="58" y2="58" stroke="{BR}"/>'
    for i, (t, c) in enumerate(zip(topics, cols)):
        x, y = 28 + (i % 2) * 300, 96 + (i // 2) * 44
        b += f'<circle cx="{x + 5}" cy="{y - 5}" r="9" fill="none" stroke="{c}" stroke-opacity=".5"/><circle cx="{x + 5}" cy="{y - 5}" r="3" fill="{c}"/>'
        b += T(x + 26, y, t if i < 5 else "Mathematical experiments", 15.5, TX)
    b += f'<line x1="28" x2="{w - 28}" y1="{h - 52}" y2="{h - 52}" stroke="{BR}"/>'
    b += T(28, h - 24, "Curiosity-led: small experiments to see how things behave.", 14, MU)
    out("research-map.svg", svg(w, h, b, "", "Research and exploration topics"))


# ------------------------------------------------------------------ build process
def process():
    w = 640
    steps = (("SPECIFY", "Define the problem.", CY), ("MODEL", "Understand entities, data, boundaries and failure modes.", CY),
             ("ARCHITECT", "Decide how components communicate.", BL), ("IMPLEMENT", "Build explicit responsibilities and maintainable boundaries.", BL),
             ("TEST", "Try to break assumptions.", VI), ("ITERATE", "Keep what survives.", VI))
    rowh = 64
    h = 40 + len(steps) * rowh
    b = f'<line x1="30" x2="30" y1="30" y2="{h - 34}" stroke="url(#gSurf)"/>'
    b += f'<linearGradient id="vl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CY}"/><stop offset=".6" stop-color="{BL}"/><stop offset="1" stop-color="{VI}"/></linearGradient>'
    b += f'<rect x="29" y="30" width="2" height="{h - 64}" fill="url(#vl)" opacity=".55"/>'
    for i, (k, v, c) in enumerate(steps):
        y = 36 + i * rowh
        b += f'<circle cx="30" cy="{y + 14}" r="17" fill="{BG}" stroke="{c}" stroke-width="1.4"/>'
        b += T(30, y + 19, f"{i + 1:02d}", 12.5, c, MONO, 600, "middle", 1)
        b += T(66, y + 12, k, 15, TX, MONO, 600, "start", 3)
        b += T(66, y + 34, v, 15, MU)
    out("build-process.svg", svg(w, h, b, "", "Build process: specify, model, architect, implement, test, iterate"))


# ------------------------------------------------------------------ social pills
def socials():
    for key, label, col in (("github", "GITHUB", CY), ("linkedin", "LINKEDIN", BL), ("instagram", "INSTAGRAM", VI),
                            ("facebook", "FACEBOOK", BL), ("fiverr", "FIVERR", GR), ("email", "EMAIL", CY)):
        w, h = 132, 46
        b = f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="23" fill="url(#gSurf)" stroke="{BR}"/>'
        b += f'<circle cx="24" cy="23" r="4" fill="{col}"/><circle cx="24" cy="23" r="8" fill="none" stroke="{col}" stroke-opacity=".4"/>'
        b += T(42, 27, label, 11, TX, MONO, 600, "start", 1.8)
        out(f"social-{key}.svg", svg(w, h, b, "", label))


# ------------------------------------------------------------------ footer + empty state
def footer():
    w, h = 880, 120
    b = f'<rect x="0" y="30" width="{w}" height="1.5" fill="url(#gA)" opacity=".5"/>'
    b += T(w / 2, 72, "BUILD · BREAK · UNDERSTAND · REBUILD", 14, TX, MONO, 600, "middle", 5)
    b += T(w / 2, 100, "Designed and engineered by Uzair Umar.", 13.5, DM, SANS, 400, "middle", .4)
    out("footer-system.svg", svg(w, h, b, "", "Build, break, understand, rebuild — designed and engineered by Uzair Umar"))


def empty_hosted():
    w, h = 640, 230
    b = frame(w, h, 18, False) + brackets(w, h, 18, 14, BR)
    b += f'<rect x="{w / 2 - 48}" y="44" width="96" height="64" rx="8" fill="none" stroke="{BR}" stroke-dasharray="4 4"/>'
    b += f'<path d="M{w / 2 - 48} 62H{w / 2 + 48}" stroke="{BR}"/><circle cx="{w / 2 - 38}" cy="53" r="2" fill="{DM}"/><circle cx="{w / 2 - 30}" cy="53" r="2" fill="{DM}"/><circle cx="{w / 2 - 22}" cy="53" r="2" fill="{DM}"/>'
    b += f'<circle cx="{w / 2}" cy="86" r="6" fill="none" stroke="{CY}" stroke-opacity=".6"><animate attributeName="r" values="4;10;4" dur="3.2s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".7;0;.7" dur="3.2s" repeatCount="indefinite"/></circle>'
    b += f'<circle cx="{w / 2}" cy="86" r="2.6" fill="{CY}"/>'
    b += T(w / 2, 152, "No hosted projects yet.", 22, TX, SANS, 600, "middle")
    b += T(w / 2, 180, "Live projects will appear here as soon as they are deployed.", 14.5, MU, SANS, 400, "middle")
    b += T(w / 2, 204, "STATUS  EMPTY", 10, DM, MONO, 400, "middle", 2.4)
    out("hosted-empty.svg", svg(w, h, b, "", "No hosted projects yet"))


def main():
    hero(); sections(); about()
    project_card("project-card-sudochat.svg", "01", "SUDOCHAT", "Privacy-first, peer-to-peer communication infrastructure.",
                 "P2P · NETWORKING · SECURITY · ARCHITECTURE", "BUILD", "BUILDING", motif_chat(), "SudoChat — privacy-first communication platform (building)")
    project_card("project-card-sudomesh.svg", "02", "SUDOMESH", "Coordinates CPU, RAM, GPU and storage across a distributed mesh.",
                 "RUST · DISTRIBUTED SYSTEMS · NETWORKING", "ENGINEERING", "ENGINEERING", motif_mesh(), "SudoMesh — distributed resource mesh (engineering)")
    mall_card()
    button("button-projects.svg", "EXPLORE MORE PROJECTS", CY)
    button("button-hosted.svg", "EXPLORE HOSTED PROJECTS", VI)
    engineering(); research(); process(); socials(); footer(); empty_hosted()
    print("static assets written")


if __name__ == "__main__":
    main()
