"""Generate the README workflow figure (assets/workflow.svg).

Two stages: Xenium Ranger relabeling with a corrected gene panel, then
import of H&E-derived cell masks (resegmentation). Same palette as
MedicagoXeniumSpatialViewer. Pure Python, fixed seed, no 10x logos.

Usage: python3 assets/make_workflow.py
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).parent
NAVY, AMBER, INK, MUTED = "#1A1A2E", "#F2A541", "#1F2133", "#5E6178"
LINE, PAPER, WHITE = "#E2E4EC", "#F7F8FB", "#FFFFFF"
GLASS, TISSUE, TEDGE, SOFT = "#24243E", "#23233D", "#3B3B60", "#A9ABC8"
CARD = "#2A2A48"
GENES = ["#4C9BE8", "#F28C3A", "#45B87A", "#B57BE0"]
HE_BG, HE_LINE, HE_NUC = "#F3C6DD", "#9C4F86", "#5B2A63"
CHECK = "#45B87A"
SANS = 'font-family="Inter, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"'
MONO = 'font-family="SFMono-Regular, Menlo, Consolas, monospace"'


def clip_halfplane(poly, a, b, c):
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if fp * fq < 0:
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def voronoi(seeds, box):
    x0, y0, x1, y1 = box
    cells = []
    for i, (px, py) in enumerate(seeds):
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for j, (qx, qy) in enumerate(seeds):
            if i != j:
                poly = clip_halfplane(poly, 2 * (qx - px), 2 * (qy - py), qx * qx + qy * qy - px * px - py * py)
        cells.append(poly)
    return cells


class Fig:
    def __init__(self, w, h, seed=11):
        self.w, self.h, self.b = w, h, []
        self.rng = random.Random(seed)
        self.nclip = 0

    def add(self, x):
        self.b.append(x)

    def g(self):
        r = self.rng
        return (r.random() + r.random() + r.random() - 1.5) / 1.5

    def svg(self):
        markers = "".join(
            f'<marker id="ah-{n}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
            f'orient="auto-start-reverse"><path d="M1.5 1.5L8 5L1.5 8.5" fill="none" stroke="{c}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></marker>'
            for n, c in [("amber", AMBER), ("soft", SOFT), ("muted", "#9A9CB4")])
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" role="img" aria-label="Relabeling and resegmentation workflow">\n'
                f'<defs>{markers}</defs>\n' + "\n".join(self.b) + "\n</svg>\n")

    # primitives
    def T(self, x, y, t, size=14, w=400, fill=INK, anchor="middle", font=SANS, ls=None):
        t = str(t).replace("&", "&amp;")
        extra = f' letter-spacing="{ls}"' if ls else ""
        self.add(f'<text x="{x}" y="{y}" {font} font-size="{size}" font-weight="{w}" fill="{fill}" '
                 f'text-anchor="{anchor}"{extra}>{t}</text>')

    def R(self, x, y, w, h, rx=8, fill=WHITE, stroke=None, sw=1, dash=None):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{s}{d}/>')

    def C(self, cx, cy, r, fill, stroke=None, sw=1, op=None):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        o = f' opacity="{op}"' if op is not None else ""
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"{s}{o}/>')

    def L(self, x1, y1, x2, y2, stroke=AMBER, sw=2, marker=None, dash=None):
        m = f' marker-end="url(#ah-{marker})"' if marker else ""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linecap="round"{m}{d}/>')

    def P(self, d, stroke=AMBER, sw=2, marker=None, dash=None, fill="none"):
        m = f' marker-end="url(#ah-{marker})"' if marker else ""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" '
                 f'stroke-linejoin="round"{m}{da}/>')

    def clip_circle(self, cx, cy, r):
        self.nclip += 1
        cid = f"c{self.nclip}"
        self.add(f'<clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
        return cid

    def clip_rect(self, x, y, w, h, rx):
        self.nclip += 1
        cid = f"c{self.nclip}"
        self.add(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath>')
        return cid

    def plus(self, cx, cy, col=SOFT):
        self.L(cx - 7, cy, cx + 7, cy, col, 2.5)
        self.L(cx, cy - 7, cx, cy + 7, col, 2.5)

    def check(self, cx, cy):
        self.C(cx, cy, 10, CHECK, NAVY, 2)
        self.P(f"M{cx - 4.5},{cy} l3.5,3.5 l6,-7", WHITE, 2.4)

    # icons
    def transcripts(self, cx, cy, r, n=140, rr=1.3):
        cid = self.clip_circle(cx, cy, r)
        self.C(cx, cy, r, TISSUE, TEDGE, 1.2)
        g = [f'<g clip-path="url(#{cid})">']
        for _ in range(n):
            a, d = self.rng.random() * 6.283, math.sqrt(self.rng.random()) * r
            x, y = cx + d * math.cos(a), cy + d * math.sin(a)
            dom = int(((x - cx) / r * 0.8 + (y - cy) / r * 0.4 + 1.1) / 2.2 * 4 + self.g() * 0.4)
            g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr}" fill="{GENES[max(0, min(3, dom))]}"/>')
        self.add("".join(g) + "</g>")

    def cells(self, cx, cy, r, n=14, fill=True):
        cid = self.clip_circle(cx, cy, r)
        self.C(cx, cy, r, TISSUE, TEDGE, 1.2)
        seeds = []
        while len(seeds) < n:
            a, d = self.rng.random() * 6.283, math.sqrt(self.rng.random()) * (r + 4)
            p = (cx + d * math.cos(a), cy + d * math.sin(a))
            if all(math.hypot(p[0] - q[0], p[1] - q[1]) > r * 0.32 for q in seeds):
                seeds.append(p)
        polys = voronoi(seeds, (cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6))
        g = [f'<g clip-path="url(#{cid})">']
        for (sx, sy), poly in zip(seeds, polys):
            dom = int(((sx - cx) / r * 0.8 + (sy - cy) / r * 0.4 + 1.1) / 2.2 * 4)
            col = GENES[max(0, min(3, dom))]
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)
            f = f'fill="{col}" fill-opacity="0.55"' if fill else 'fill="none"'
            g.append(f'<polygon points="{pts}" {f} stroke="#C9CBE6" stroke-width="1"/>')
        self.add("".join(g) + "</g>")

    def folder(self, cx, cy, w, h, stroke=SOFT, fill=CARD):
        x, y = cx - w / 2, cy - h / 2
        self.P(f"M{x},{y + 8} q0,-8 8,-8 h{w * 0.3} l8,8 h{w * 0.7 - 24} q8,0 8,8 v{h - 8} q0,8 -8,8 h{-w + 16} "
               f"q-8,0 -8,-8 z", stroke, 1.5, fill=fill)

    def bundle(self, cx, cy, kind="transcripts", done=False, stroke=SOFT, fill=CARD):
        self.folder(cx, cy, 92, 74, stroke, fill)
        if kind == "transcripts":
            self.transcripts(cx, cy + 4, 25)
        else:
            self.cells(cx, cy + 4, 25)
        if done:
            self.check(cx + 40, cy - 30)

    def doc(self, cx, cy, label="JSON", fill="#F4F1EA", text=NAVY, accent=AMBER):
        w, h = 58, 72
        x, y = cx - w / 2, cy - h / 2
        self.P(f"M{x},{y} h{w - 16} l16,16 v{h - 16} h{-w} z", "#C9C3B4", 1.2, fill=fill)
        self.P(f"M{x + w - 16},{y} v16 h16", "#C9C3B4", 1.2)
        self.T(cx, cy + 4, "{ }", 20, 700, accent, font=MONO)
        self.R(cx - 22, cy + 14, 44, 14, 3, NAVY)
        self.T(cx, cy + 25, label, 9.5, 700, WHITE, font=MONO)

    def terminal(self, cx, cy, sub, w=150, h=84, bg="#0F0F1F", stroke=AMBER):
        x, y = cx - w / 2, cy - h / 2
        self.R(x, y, w, h, 9, bg, stroke, 2)
        for i, c in enumerate(["#EE6A5F", "#F5BD4F", "#61C454"]):
            self.C(x + 13 + i * 11, y + 12, 3.3, c)
        self.T(x + 12, y + 42, "$ xeniumranger", 12, 600, "#D9DBEE", "start", MONO)
        self.T(x + 24, y + 62, sub, 12, 700, AMBER, "start", MONO)
        tw = len(sub) * 12 * 0.61
        self.R(x + 26 + tw, y + 52, 7, 13, 1, AMBER)

    def nuclei(self, cx, cy, r=30):
        cid = self.clip_circle(cx, cy, r)
        self.C(cx, cy, r, "#101528", TEDGE, 1.2)
        g = [f'<g clip-path="url(#{cid})">']
        for _ in range(16):
            a, d = self.rng.random() * 6.283, math.sqrt(self.rng.random()) * r
            g.append(f'<ellipse cx="{cx + d * math.cos(a):.1f}" cy="{cy + d * math.sin(a):.1f}" '
                     f'rx="{3 + self.rng.random() * 2:.1f}" ry="{2.5 + self.rng.random() * 1.5:.1f}" '
                     f'fill="#4C9BE8" opacity="0.9"/>')
        self.add("".join(g) + "</g>")

    def he_mask(self, cx, cy, w=70, h=60):
        x, y = cx - w / 2, cy - h / 2
        cid = self.clip_rect(x, y, w, h, 6)
        self.R(x, y, w, h, 6, HE_BG, "#C98AB0", 1.2)
        seeds = [(x + self.rng.random() * w, y + self.rng.random() * h) for _ in range(12)]
        polys = voronoi(seeds, (x - 4, y - 4, x + w + 4, y + h + 4))
        g = [f'<g clip-path="url(#{cid})">']
        for (sx, sy), poly in zip(seeds, polys):
            pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in poly)
            g.append(f'<polygon points="{pts}" fill="none" stroke="{HE_LINE}" stroke-width="1.3"/>')
            g.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="2.6" fill="{HE_NUC}"/>')
        self.add("".join(g) + "</g>")

    def matrix(self, cx, cy, s=58, stroke=SOFT, fill=CARD, text="#D9DBEE"):
        x, y = cx - s / 2, cy - s / 2
        self.R(x, y, s, s, 6, fill, stroke, 1.2)
        vals = [["a", "b", "tx"], ["c", "d", "ty"], ["0", "0", "1"]]
        for i in range(3):
            for j in range(3):
                self.T(x + s * (j + 0.5) / 3, y + s * (i + 0.5) / 3 + 4, vals[i][j], 10, 600,
                       AMBER if vals[i][j] in ("tx", "ty") else text, font=MONO)
        self.P(f"M{x + 6},{y + 5} h-3 v{s - 10} h3", text, 1.2)
        self.P(f"M{x + s - 6},{y + 5} h3 v{s - 10} h-3", text, 1.2)


def label(f, x, y, title, sub, tcol=WHITE, scol=SOFT, mono_sub=False):
    f.T(x, y, title, 13.5, 600, tcol)
    if sub:
        f.T(x, y + 17, sub, 11, 400, scol, font=MONO if mono_sub else SANS)


def v_a():
    f = Fig(1000, 520, seed=3)
    f.R(0, 0, 1000, 520, 18, NAVY)
    f.T(40, 44, "1 · RELABELING", 12, 700, AMBER, "start", ls="1.5")
    f.T(40, 290, "2 · RESEGMENTATION WITH H&E CELL MASKS", 12, 700, AMBER, "start", ls="1.5")
    y1 = 125
    f.bundle(110, y1)
    label(f, 110, y1 + 70, "Raw Xenium bundle", "one per sample")
    f.L(165, y1, 255, y1, AMBER, 2, "amber")
    f.doc(300, y1)
    label(f, 300, y1 + 70, "Corrected gene panel", "panel.json (subset)")
    f.L(338, y1, 420, y1, AMBER, 2, "amber")
    f.terminal(500, y1, "relabel")
    label(f, 500, y1 + 70, "Relabel transcripts", "no re-imaging needed")
    f.L(580, y1, 660, y1, AMBER, 2, "amber")
    f.bundle(720, y1, done=True)
    label(f, 720, y1 + 70, "Relabeled bundle", "outs/ + per-sample log")
    f.P(f"M720,{y1 + 98} V250 H110 V318", SOFT, 1.5, "soft", dash="5 5")
    y2 = 375
    f.bundle(110, y2)
    label(f, 110, y2 + 70, "Relabeled bundle", "from step 1")
    f.plus(185, y2)
    f.nuclei(250, y2)
    label(f, 250, y2 + 70, "Nuclei", "cells.zarr.zip", mono_sub=True)
    f.plus(315, y2)
    f.he_mask(385, y2)
    label(f, 385, y2 + 70, "H&E cell mask", "TIFF")
    f.plus(455, y2)
    f.matrix(520, y2)
    label(f, 520, y2 + 70, "H&E → Xenium", "matrix.csv", mono_sub=True)
    f.L(565, y2, 630, y2, AMBER, 2, "amber")
    f.terminal(715, y2, "import-segmentation", w=165)
    label(f, 715, y2 + 70, "Import cell masks", "--expansion-distance=0", mono_sub=True)
    f.L(803, y2, 845, y2, AMBER, 2, "amber")
    f.bundle(905, y2, kind="cells", done=True)
    label(f, 905, y2 + 70, "Resegmented output", "H&E-based cells")
    return f


if __name__ == "__main__":
    out = OUT / "workflow.svg"
    out.write_text(v_a().svg())
    print("wrote", out)
