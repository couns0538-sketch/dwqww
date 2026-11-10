"""R9: small-multiple SVG of an SPSA run (read only on the run): one panel per parameter, x = game pairs, y = the
move from the start value in units of c_end; the grey band is +-2 sigma of the null-gradient spread up to that point
(the spread the run would show with no true gradient, see r9_spsa_report.py), so a trajectory that leaves the band
moved by more than noise. Light and dark colours come from CSS variables inside the SVG (prefers-color-scheme).
usage: python -I -B r9_spsa_svg.py <run_dir> <out.svg> [--title TEXT]"""
import json
import math
import sys
from pathlib import Path

run_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
title = sys.argv[sys.argv.index("--title") + 1] if "--title" in sys.argv else f"SPSA run {run_dir.name}"
cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
recs = [json.loads(x) for x in (run_dir / "iterations.jsonl").read_text(encoding="ascii").splitlines()
        if x.strip().startswith("{")]
params = cfg["params"]
W = sum(r["W"] for r in recs)
L = sum(r["L"] for r in recs)
G = W + L + sum(r["D"] for r in recs)
v = (W + L) / G - ((W - L) / G) ** 2 if G else 0.0
cols = 4 if len(params) > 2 else len(params)
rows = math.ceil(len(params) / cols)
pw, ph, gap, top = 230, 150, 18, 46
width, height = cols * pw + (cols + 1) * gap, top + rows * (ph + gap) + 24
xmax = max(r["k_after"] for r in recs) if recs else 1


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
         f'font-family="system-ui, -apple-system, Segoe UI, sans-serif">',
         "<style>svg{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:#2a78d6;--band:#52514e;--grid:#d9d8d3}"
         "@media (prefers-color-scheme: dark){svg{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--line:#3987e5;"
         "--band:#c3c2b7;--grid:#3a3a37}}"
         "text{fill:var(--ink)}.sub{fill:var(--ink2)}</style>",
         f'<rect width="{width}" height="{height}" fill="var(--surface)"/>',
         f'<text x="{gap}" y="22" font-size="15" font-weight="600">{esc(title)}</text>',
         f'<text x="{gap}" y="38" font-size="11" class="sub">move from the start in c_end units vs game pairs; '
         f'grey band = +-2 sigma of the no-gradient spread; {len(recs)} batches, {xmax} pairs, +{W} -{L} ={G - W - L}</text>']
for i, p in enumerate(params):
    n, c_end = p["name"], p["c_end"]
    start = recs[0]["theta_before"][n] if recs else p["start"]
    xs, ys, bands = [0], [0.0], [0.0]
    s2 = 0.0
    for r in recs:
        s2 += r["a_over_c"][i] ** 2 * 2 * r["pairs"] * v
        xs.append(r["k_after"])
        ys.append((r["theta_after"][n] - start) / c_end)
        bands.append(2 * math.sqrt(s2) / c_end)
    span = max(1.0, max(abs(y) for y in ys), max(bands)) * 1.15
    ox, oy = gap + (i % cols) * (pw + gap), top + (i // cols) * (ph + gap)
    px0, px1, py0, py1 = ox + 34, ox + pw - 8, oy + 34, oy + ph - 18
    X = lambda x: px0 + (px1 - px0) * x / xmax
    Y = lambda y: (py0 + py1) / 2 - (py1 - py0) / 2 * y / span
    end = ys[-1] * c_end + start
    z = ys[-1] / (bands[-1] / 2) if bands[-1] > 0 else 0.0
    parts.append(f'<text x="{ox}" y="{oy + 12}" font-size="12" font-weight="600">{esc(n)}</text>')
    parts.append(f'<text x="{ox}" y="{oy + 26}" font-size="10.5" class="sub">{start:g} -> {end:.1f} '
                 f'(c_end {c_end:g}, z {z:+.1f})</text>')
    band = " ".join(f"{X(x):.1f},{Y(b):.1f}" for x, b in zip(xs, bands))
    band += " " + " ".join(f"{X(x):.1f},{Y(-b):.1f}" for x, b in reversed(list(zip(xs, bands))))
    parts.append(f'<polygon points="{band}" fill="var(--band)" fill-opacity="0.16"/>')
    parts.append(f'<line x1="{px0}" x2="{px1}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="var(--grid)" stroke-width="1"/>')
    line = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in zip(xs, ys))
    parts.append(f'<polyline points="{line}" fill="none" stroke="var(--line)" stroke-width="2" stroke-linejoin="round" '
                 f'stroke-linecap="round"><title>{esc(n)}: {start:g} -> {end:.2f}</title></polyline>')
    tick = f"{span / 1.15:.1f}"
    for yv, lab in ((span / 1.15, "+" + tick), (0, "0"), (-span / 1.15, "-" + tick)):
        parts.append(f'<text x="{px0 - 4}" y="{Y(yv) + 3.5:.1f}" font-size="9.5" class="sub" text-anchor="end">{lab}</text>')
    parts.append(f'<text x="{px0}" y="{py1 + 13}" font-size="9.5" class="sub">0</text>')
    parts.append(f'<text x="{px1}" y="{py1 + 13}" font-size="9.5" class="sub" text-anchor="end">{xmax} pairs</text>')
parts.append("</svg>")
out.write_bytes(("\n".join(parts) + "\n").encode("utf-8"))
print(f"wrote {out} ({len(params)} panels, {len(recs)} batches)")
