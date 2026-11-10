"""Generate the repository logo (assets/logo.svg).

Rounded-square 'pipeline' badge in the MedicagoXeniumSpatialViewer palette:
a tissue section with transcripts, where the left half shows default
nucleus-expansion cells and the right half the H&E-based resegmented cells.
Pure Python, fixed seed.

Usage: python3 assets/make_logo.py
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).parent
BG, EDGE, TISSUE, TEDGE, SOFT, WHITE = "#1A1A2E", "#F2A541", "#23233D", "#3B3B60", "#A9ABC8", "#FFFFFF"
GENES = ["#4C9BE8", "#F28C3A", "#45B87A", "#B57BE0"]
HE_BG, HE_LINE, HE_NUC = "#F3C6DD", "#9C4F86", "#5B2A63"
FONT = 'font-family="Helvetica, Arial, sans-serif"'
S = 240  # badge size


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
    res = []
    for i, (px, py) in enumerate(seeds):
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for j, (qx, qy) in enumerate(seeds):
            if i != j:
                poly = clip_halfplane(poly, 2 * (qx - px), 2 * (qy - py), qx * qx + qy * qy - px * px - py * py)
        res.append(poly)
    return res


def in_poly(x, y, poly):
    inside = False
    for i, (ax, ay) in enumerate(poly):
        bx, by = poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    return inside


def pts(poly):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in poly)


class Badge:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.b, self.defs = [], []

    def add(self, s):
        self.b.append(s)

    def g(self):
        r = self.rng
        return (r.random() + r.random() + r.random() - 1.5) / 1.5

    def frame(self):
        self.add(f'<rect x="6" y="6" width="{S - 12}" height="{S - 12}" rx="42" fill="{BG}" stroke="{EDGE}" stroke-width="7"/>')

    def name(self):
        self.add(f'<text x="{S / 2}" y="196" text-anchor="middle" {FONT} font-size="25" font-weight="bold" fill="{WHITE}">Relabel</text>')
        self.add(f'<text x="{S / 2}" y="218" text-anchor="middle" {FONT} font-size="13.5" letter-spacing="2.4" fill="{EDGE}">+ RESEGMENT</text>')

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}" role="img" '
                f'aria-label="Medicago Xenium Relabeling and Resegmentation logo">\n<defs>{"".join(self.defs)}</defs>\n'
                + "\n".join(self.b) + "\n</svg>\n")

    def cells_in_circle(self, cx, cy, r, n, min_d):
        seeds = []
        while len(seeds) < n:
            a, d = self.rng.random() * 6.283, math.sqrt(self.rng.random()) * (r + 6)
            p = (cx + d * math.cos(a), cy + d * math.sin(a))
            if all(math.hypot(p[0] - q[0], p[1] - q[1]) > min_d for q in seeds):
                seeds.append(p)
        return seeds, voronoi(seeds, (cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10))

    def dom(self, x, y, cx, cy, r):
        d = int(((x - cx) / r * 0.8 + (y - cy) / r * 0.4 + 1.1) / 2.2 * 4 + self.g() * 0.4)
        return max(0, min(3, d))


def logo():
    b = Badge(4)
    b.frame()
    cx, cy, r = 120, 92, 64
    b.defs.append(f'<clipPath id="tis"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    b.defs.append(f'<clipPath id="lh"><rect x="0" y="0" width="{cx}" height="{S}"/></clipPath>')
    b.defs.append(f'<clipPath id="rh"><rect x="{cx}" y="0" width="{S}" height="{S}"/></clipPath>')
    b.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{TISSUE}" stroke="{TEDGE}" stroke-width="1.5"/>')
    seeds, polys = b.cells_in_circle(cx, cy, r, 16, 22)
    # left: default circular expansion around nuclei (dashed, grey)
    g = ['<g clip-path="url(#tis)"><g clip-path="url(#lh)">']
    for sx, sy in seeds:
        g.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="11" fill="none" stroke="{SOFT}" stroke-width="1.3" stroke-dasharray="3 2.5"/>')
        g.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3.2" fill="#4C9BE8" opacity="0.8"/>')
    g.append('</g><g clip-path="url(#rh)">')
    # right: H&E-based segmentation, filled by cell type
    for (sx, sy), poly in zip(seeds, polys):
        col = GENES[b.dom(sx, sy, cx, cy, r)]
        g.append(f'<polygon points="{pts(poly)}" fill="{col}" fill-opacity="0.35" stroke="{EDGE}" stroke-width="1.5" stroke-linejoin="round"/>')
    g.append('</g>')
    for _ in range(170):  # transcripts everywhere
        a, d = b.rng.random() * 6.283, math.sqrt(b.rng.random()) * r
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.25" fill="{GENES[b.dom(x, y, cx, cy, r)]}"/>')
    g.append('</g>')
    b.add("".join(g))
    b.add(f'<line x1="{cx}" y1="{cy - r - 6}" x2="{cx}" y2="{cy + r + 6}" stroke="{EDGE}" stroke-width="2.2"/>')
    b.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{TEDGE}" stroke-width="1.5"/>')
    b.name()
    return b



if __name__ == "__main__":
    out = OUT / "logo.svg"
    out.write_text(logo().svg())
    print("wrote", out)
