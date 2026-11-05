# T12 SPRT model: script and raw output (mirror of the session scratch files, for verification)

Run: python -I -B sprt_plan.py (numpy 1.26.4, venv C:/Users/Administrator/grok-pc/nnue/.venv), Idle, 1 thread,
input C:/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.csv (read-only). Own code; Brownian approximation of
the fastchess/fishtest GSPRT, Gaussian steps of m pairs, 20k walks per row, seeds 1 (table) and 7 (truncated rule).

## sprt_plan.py
```python
"""T12 planning numbers: Forge gate profile per book, bound fit per gate, Brownian SPRT model (MC)."""
import csv, math, sys
import numpy as np
CSV = 'C:/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.csv'
K = math.sqrt(2) * math.log(10) / 800          # t per nElo (per pair)
B = math.log(19)                                # fastchess bounds +-2.944
RATE = 497.0                                    # gate games/h (conc 4, Threads 2, 10+0.1)
rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))

def pstats(p):
    n = sum(p); x = [0, .25, .5, .75, 1]
    a = sum(xi * c for xi, c in zip(x, p)) / n
    v = sum(xi * xi * c for xi, c in zip(x, p)) / n - a * a
    return n, a, v

print('== A. book profiles (rows with |Elo|>3 and >=1000 games)')
for book, sel in (('UHO', lambda r: r['tag'].lower().startswith('uho')),
                  ('8moves/other', lambda r: not r['tag'].lower().startswith('uho'))):
    rat, sds, dr, vr = [], [], [], []
    for r in rows:
        if not sel(r) or not r['ptnml'].strip():
            continue
        p = [int(z) for z in r['ptnml'].split()]
        n, a, v = pstats(p)
        g = int(r['games']); w, l, d = int(r['w']), int(r['l']), int(r['d'])
        if g < 1000 or v <= 0:
            continue
        s = (w + 0.5 * d) / g
        vg = (w * 1 + d * 0.25) / g - s * s          # per-game (trinomial) variance
        sds.append(math.sqrt(v)); dr.append(d / g); vr.append(v / (vg / 2))
        elo, nelo = float(r['elo']), float(r['nelo'])
        if abs(elo) > 3:
            rat.append(nelo / elo)
    print(f'{book}: gates {len(sds)}  nElo/Elo median {np.median(rat):.3f} (n={len(rat)}, range {min(rat):.2f}..{max(rat):.2f})'
          f'  pair sd median {np.median(sds):.4f}  draw ratio median {np.median(dr):.3f}'
          f'  pent/trin variance ratio median {np.median(vr):.3f} (range {min(vr):.3f}..{max(vr):.3f})')

print('\n== B. unit check: LLR_brownian = pairs*dt*(t_hat - t_mid) vs printed LLR, bounds [0,10] nElo')
errs = []
for r in rows:
    if not r['ptnml'].strip() or 'NON-REG' in r['verdict'].upper():
        continue
    p = [int(z) for z in r['ptnml'].split()]
    n, a, v = pstats(p)
    if v <= 0:
        continue
    th = (a - 0.5) / math.sqrt(v); dt = 10 * K
    llr = n * dt * (th - dt / 2)
    pr = float(r['llr'])
    if abs(pr) < 2.9:                                    # caps only (no MLE-iteration clipping at stops)
        errs.append(llr - pr)
print(f'capped gates: n={len(errs)}  mean diff {np.mean(errs):+.3f}  max |diff| {np.max(np.abs(errs)):.3f}  '
      f'share |diff|<0.15: {np.mean(np.abs(np.array(errs))<0.15):.2f}')
decided = [r for r in rows if r['ptnml'].strip() and abs(float(r['llr'])) >= 2.9]
caps = [r for r in rows if r['ptnml'].strip() and abs(float(r['llr'])) < 2.9]
print(f'gates with ptnml: {len(decided)+len(caps)}  decided {len(decided)}  capped {len(caps)}')
cn = np.array([float(r['nelo']) for r in caps]); cg = np.array([int(r['games']) for r in caps])
print(f'capped: games median {np.median(cg):.0f}  nElo quantiles 10/50/90 % {np.percentile(cn,10):+.1f} {np.median(cn):+.1f} {np.percentile(cn,90):+.1f}'
      f'  |nElo|<=10: {np.mean(np.abs(cn)<=10):.2f}')

def mc(n0, n1, true, reps=20000, cap_pairs=None, seed=1):
    rng = np.random.default_rng(seed)
    dt = (n1 - n0) * K; t0, t1 = n0 * K, n1 * K; t = true * K
    d = dt * (t - (t0 + t1) / 2)
    m = max(1, int(round((0.12 / dt) ** 2)))
    llr = np.zeros(reps); stop = np.full(reps, -1, dtype=np.int64); res = np.zeros(reps, dtype=np.int8)
    alive = np.ones(reps, bool); k = 0
    maxp = cap_pairs if cap_pairs else int(60 * (B * B) / (dt * dt)) + 10 * m
    while alive.any() and k * m < maxp:
        k += 1
        idx = np.nonzero(alive)[0]
        llr[idx] += rng.normal(m * d, math.sqrt(m) * dt, idx.size)
        up = idx[llr[idx] >= B]; dn = idx[llr[idx] <= -B]
        stop[up] = k * m; res[up] = 1; stop[dn] = k * m; res[dn] = -1
        alive[up] = False; alive[dn] = False
    return stop, res, llr, alive

print('\n== C. planning table (Brownian GSPRT model, alpha=beta=0.05, 20k reps, pairs -> games x2, hours at 497 g/h)')
print('bounds nElo | true nElo | P(H1) | mean games | median | p90 | P(decided by 3000 g) | by 6000 | by 12000 | mean h | p90 h')
for (n0, n1) in ((0, 5), (0, 10), (0, 15), (0, 20), (-10, 0), (-5, 0), (-1.75, 0.25), (0, 2)):
    for true in (n0, (n0 + n1) / 2, n1, n1 + (n1 - n0) / 2):
        stop, res, llr, alive = mc(n0, n1, true)
        g = 2 * stop.astype(float)
        ok = ~alive
        ph1 = np.mean(res == 1)
        q = lambda c: np.mean(ok & (g <= c))
        mean = g[ok].mean(); med = np.median(g[ok]); p90 = np.percentile(g[ok], 90)
        print(f'[{n0:g},{n1:g}] | {true:+.2f} | {ph1:.3f} | {mean:,.0f} | {med:,.0f} | {p90:,.0f} | {q(3000):.2f} | {q(6000):.2f} | {q(12000):.2f} | {mean/RATE:.1f} | {p90/RATE:.1f}')

print('\n== D. truncated SPRT: at the cap decide by sign(LLR) (H1 if LLR>0); error rates')
print('bounds | cap games | true nElo | P(accept H1 incl. cap-sign) | P(stopped by SPRT before cap)')
for (n0, n1) in ((0, 5), (0, 10), (0, 20)):
    for cap in (3000, 6000, 12000):
        for true in (n0, (n0 + n1) / 2, n1):
            stop, res, llr, alive = mc(n0, n1, true, cap_pairs=cap // 2, seed=7)
            acc = np.mean((res == 1) | (alive & (llr > 0)))
            print(f'[{n0:g},{n1:g}] | {cap} | {true:+.1f} | {acc:.3f} | {np.mean(~alive):.2f}')
```

## sprt_plan.py output (2026-11-04 22:59 PC clock)
```text
== A. book profiles (rows with |Elo|>3 and >=1000 games)
UHO: gates 10  nElo/Elo median 1.910 (n=6, range 1.87..1.95)  pair sd median 0.1846  draw ratio median 0.561  pent/trin variance ratio median 0.618 (range 0.589..0.656)
8moves/other: gates 84  nElo/Elo median 2.101 (n=63, range 1.90..2.40)  pair sd median 0.1671  draw ratio median 0.754  pent/trin variance ratio median 0.900 (range 0.512..0.995)

== B. unit check: LLR_brownian = pairs*dt*(t_hat - t_mid) vs printed LLR, bounds [0,10] nElo
capped gates: n=85  mean diff -0.049  max |diff| 2.491  share |diff|<0.15: 0.96
gates with ptnml: 110  decided 25  capped 85
capped: games median 1500  nElo quantiles 10/50/90 % -12.9 +6.6 +17.8  |nElo|<=10: 0.52

== C. planning table (Brownian GSPRT model, alpha=beta=0.05, 20k reps, pairs -> games x2, hours at 497 g/h)
bounds nElo | true nElo | P(H1) | mean games | median | p90 | P(decided by 3000 g) | by 6000 | by 12000 | mean h | p90 h
[0,5] | +0.00 | 0.051 | 26,439 | 21,350 | 50,960 | 0.00 | 0.03 | 0.21 | 53.2 | 102.5
[0,5] | +2.50 | 0.507 | 44,030 | 33,600 | 90,650 | 0.00 | 0.01 | 0.11 | 88.6 | 182.4
[0,5] | +5.00 | 0.955 | 26,237 | 20,860 | 50,750 | 0.00 | 0.03 | 0.22 | 52.8 | 102.1
[0,5] | +7.50 | 0.998 | 14,408 | 12,460 | 24,850 | 0.00 | 0.08 | 0.47 | 29.0 | 50.0
[0,10] | +0.00 | 0.049 | 6,639 | 5,310 | 12,762 | 0.20 | 0.57 | 0.88 | 13.4 | 25.7
[0,10] | +5.00 | 0.507 | 11,061 | 8,388 | 22,734 | 0.11 | 0.35 | 0.66 | 22.3 | 45.7
[0,10] | +10.00 | 0.956 | 6,578 | 5,256 | 12,654 | 0.21 | 0.57 | 0.88 | 13.2 | 25.5
[0,10] | +15.00 | 0.997 | 3,594 | 3,114 | 6,228 | 0.47 | 0.89 | 1.00 | 7.2 | 12.5
[0,15] | +0.00 | 0.049 | 2,951 | 2,360 | 5,672 | 0.64 | 0.91 | 1.00 | 5.9 | 11.4
[0,15] | +7.50 | 0.507 | 4,916 | 3,728 | 10,104 | 0.40 | 0.72 | 0.94 | 9.9 | 20.3
[0,15] | +15.00 | 0.956 | 2,924 | 2,336 | 5,624 | 0.64 | 0.92 | 1.00 | 5.9 | 11.3
[0,15] | +22.50 | 0.997 | 1,597 | 1,384 | 2,768 | 0.92 | 1.00 | 1.00 | 3.2 | 5.6
[0,20] | +0.00 | 0.050 | 1,654 | 1,336 | 3,164 | 0.88 | 0.99 | 1.00 | 3.3 | 6.4
[0,20] | +10.00 | 0.505 | 2,715 | 2,052 | 5,636 | 0.68 | 0.92 | 0.99 | 5.5 | 11.3
[0,20] | +20.00 | 0.954 | 1,636 | 1,304 | 3,148 | 0.89 | 0.99 | 1.00 | 3.3 | 6.3
[0,20] | +30.00 | 0.998 | 897 | 776 | 1,556 | 1.00 | 1.00 | 1.00 | 1.8 | 3.1
[-10,0] | -10.00 | 0.049 | 6,639 | 5,310 | 12,762 | 0.20 | 0.57 | 0.88 | 13.4 | 25.7
[-10,0] | -5.00 | 0.507 | 11,061 | 8,388 | 22,734 | 0.11 | 0.35 | 0.66 | 22.3 | 45.7
[-10,0] | +0.00 | 0.956 | 6,578 | 5,256 | 12,654 | 0.21 | 0.57 | 0.88 | 13.2 | 25.5
[-10,0] | +5.00 | 0.997 | 3,594 | 3,114 | 6,228 | 0.47 | 0.89 | 1.00 | 7.2 | 12.5
[-5,0] | -5.00 | 0.051 | 26,439 | 21,350 | 50,960 | 0.00 | 0.03 | 0.21 | 53.2 | 102.5
[-5,0] | -2.50 | 0.507 | 44,030 | 33,600 | 90,650 | 0.00 | 0.01 | 0.11 | 88.6 | 182.4
[-5,0] | +0.00 | 0.955 | 26,237 | 20,860 | 50,750 | 0.00 | 0.03 | 0.22 | 52.8 | 102.1
[-5,0] | +2.50 | 0.998 | 14,408 | 12,460 | 24,850 | 0.00 | 0.08 | 0.47 | 29.0 | 50.0
[-1.75,0.25] | -1.75 | 0.048 | 166,484 | 134,106 | 322,505 | 0.00 | 0.00 | 0.00 | 335.0 | 648.9
[-1.75,0.25] | -0.75 | 0.506 | 273,985 | 207,452 | 567,238 | 0.00 | 0.00 | 0.00 | 551.3 | 1141.3
[-1.75,0.25] | +0.25 | 0.956 | 164,507 | 131,068 | 317,688 | 0.00 | 0.00 | 0.00 | 331.0 | 639.2
[-1.75,0.25] | +1.25 | 0.997 | 89,856 | 77,686 | 154,504 | 0.00 | 0.00 | 0.00 | 180.8 | 310.9
[0,2] | +0.00 | 0.048 | 166,484 | 134,106 | 322,505 | 0.00 | 0.00 | 0.00 | 335.0 | 648.9
[0,2] | +1.00 | 0.506 | 273,985 | 207,452 | 567,238 | 0.00 | 0.00 | 0.00 | 551.3 | 1141.3
[0,2] | +2.00 | 0.956 | 164,507 | 131,068 | 317,688 | 0.00 | 0.00 | 0.00 | 331.0 | 639.2
[0,2] | +3.00 | 0.997 | 89,856 | 77,686 | 154,504 | 0.00 | 0.00 | 0.00 | 180.8 | 310.9

== D. truncated SPRT: at the cap decide by sign(LLR) (H1 if LLR>0); error rates
bounds | cap games | true nElo | P(accept H1 incl. cap-sign) | P(stopped by SPRT before cap)
[0,5] | 3000 | +0.0 | 0.345 | 0.00
[0,5] | 3000 | +2.5 | 0.500 | 0.00
[0,5] | 3000 | +5.0 | 0.655 | 0.00
[0,5] | 6000 | +0.0 | 0.284 | 0.03
[0,5] | 6000 | +2.5 | 0.499 | 0.01
[0,5] | 6000 | +5.0 | 0.709 | 0.03
[0,5] | 12000 | +0.0 | 0.214 | 0.21
[0,5] | 12000 | +2.5 | 0.497 | 0.11
[0,5] | 12000 | +5.0 | 0.783 | 0.21
[0,10] | 3000 | +0.0 | 0.217 | 0.22
[0,10] | 3000 | +5.0 | 0.499 | 0.11
[0,10] | 3000 | +10.0 | 0.782 | 0.21
[0,10] | 6000 | +0.0 | 0.134 | 0.57
[0,10] | 6000 | +5.0 | 0.500 | 0.35
[0,10] | 6000 | +10.0 | 0.864 | 0.57
[0,10] | 12000 | +0.0 | 0.072 | 0.89
[0,10] | 12000 | +5.0 | 0.500 | 0.67
[0,10] | 12000 | +10.0 | 0.928 | 0.88
[0,20] | 3000 | +0.0 | 0.070 | 0.88
[0,20] | 3000 | +10.0 | 0.498 | 0.67
[0,20] | 3000 | +20.0 | 0.928 | 0.88
[0,20] | 6000 | +0.0 | 0.049 | 0.99
[0,20] | 6000 | +10.0 | 0.496 | 0.91
[0,20] | 6000 | +20.0 | 0.950 | 0.99
[0,20] | 12000 | +0.0 | 0.047 | 1.00
[0,20] | 12000 | +10.0 | 0.496 | 0.99
[0,20] | 12000 | +20.0 | 0.952 | 1.00
```

## outliers.py (capped gates whose LLR does not fit [0,10])
```python
import csv, math
K = math.sqrt(2) * math.log(10) / 800
rows = list(csv.DictReader(open('C:/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.csv', encoding='utf-8-sig')))
for r in rows:
    if not r['ptnml'].strip(): continue
    p = [int(z) for z in r['ptnml'].split()]; n = sum(p); x = [0, .25, .5, .75, 1]
    a = sum(xi*c for xi, c in zip(x, p))/n; v = sum(xi*xi*c for xi, c in zip(x, p))/n - a*a
    if v <= 0: continue
    th = (a-0.5)/math.sqrt(v); pr = float(r['llr'])
    best = min(((w0, w1) for w0, w1 in ((0,5),(0,10),(0,15),(0,20),(-10,0),(-5,0),(-3,1),(0,3))),
               key=lambda b: abs(n*(b[1]-b[0])*K*(th-(b[0]+b[1])*K/2)-pr))
    l10 = n*10*K*(th-5*K)
    if abs(l10-pr) > 0.15 and abs(pr) < 2.9:
        print(r['gate'], r['tag'][:44], r['games'], r['nelo'], pr, f'llr[0,10]={l10:.2f}', 'best fit', best, r['verdict'][:40])
```
```text
101 gate101_speedmp2_vs_h256e12 1500 -14.93 -0.69 llr[0,10]=-2.48 best fit (-3, 1) Cap with no decision (LLR -0.69 inside (
R5D-MF gateR5D_matefix_t2_nonreg_vs_a3base 3000 -9.89 -1.21 llr[0,10]=-3.70 best fit (-10, 0) Cap with no decision (LLR -1.21 inside (
R7-PFE gateR7_prefetchearly_fixed1000_vs_r7off 1000 7.83 0.06 llr[0,10]=0.23 best fit (0, 15) Cap with no decision (LLR 0.06 inside (-
```
