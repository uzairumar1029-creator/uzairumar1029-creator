"""Shared design tokens + SVG helpers for the profile asset generators."""
import os
from xml.sax.saxutils import escape

BG, S1, S2, BR = "#070A0F", "#0D1118", "#111722", "#202A38"
TX, MU, DM = "#F3F7FA", "#8B98A8", "#536070"
CY, BL, VI, GR, WARN = "#6EE7FF", "#5B9CFF", "#8B7CFF", "#B8F7D4", "#FF6B8B"
SANS = "Inter,'SF Pro Display','Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SF Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

DEFS = f"""
<linearGradient id="gA" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{CY}"/><stop offset=".55" stop-color="{BL}"/><stop offset="1" stop-color="{VI}"/></linearGradient>
<linearGradient id="gAd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CY}"/><stop offset=".55" stop-color="{BL}"/><stop offset="1" stop-color="{VI}"/></linearGradient>
<linearGradient id="gFade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BL}" stop-opacity=".7"/><stop offset="1" stop-color="{BL}" stop-opacity="0"/></linearGradient>
<linearGradient id="gSurf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{S2}"/><stop offset="1" stop-color="{S1}"/></linearGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
"""

def e(s): return escape(str(s))

def T(x, y, s, size=14, fill=TX, fam=SANS, weight=400, anchor="start", ls=0, extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}" {extra}>{e(s)}</text>')

def svg(w, h, body, defs="", title=""):
    t = f"<title>{e(title)}</title>" if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{e(title)}">{t}<defs>{DEFS}{defs}</defs>{body}</svg>\n')

def frame(w, h, r=16, grad_border=True, fill="url(#gSurf)"):
    stroke = "url(#gA)" if grad_border else BR
    op = ".45" if grad_border else "1"
    return (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{r}" fill="{fill}"/>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{r}" fill="none" stroke="{stroke}" stroke-opacity="{op}"/>')

def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > n:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines

def write(path, s):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(s)
