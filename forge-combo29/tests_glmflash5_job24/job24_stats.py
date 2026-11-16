import sys, math, re

# Job 24 stats: per match - identities, W-L-D, n5, Elo + pair interval;
# three pools by one command; each match's openings slice printed.

def load(m, first_opening_line):
    rows = [l.strip().split("|") for l in open(f"gamelist_{m}.txt")]
    games_in_list = len(rows)
    if games_in_list % 2 == 1:
        rows = rows[:-1]
    n = [0, 0, 0, 0, 0]; W = L = D = 0
    endings = {}
    for i in range(0, len(rows), 2):
        a, b = rows[i], rows[i + 1]; s = 0.0
        for row in (a, b):
            white, result, how = row[1], row[3], row[4]
            endings[how] = endings.get(how, 0) + 1
            if result == "1/2-1/2": s += 0.5; D += 1
            elif (result == "1-0") == (white == "cand"): s += 1.0; W += 1
            else: L += 1
        n[int(round(s * 2))] += 1
    P = sum(n); X = sum(i / 2 * ni for i, ni in enumerate(n)); sc = X / (2 * P)
    Vp = sum(ni * (i / 2 - 2 * sc) ** 2 for i, ni in enumerate(n)) / (P - 1)
    se = math.sqrt(Vp / (4 * P))
    elo = -400 * math.log10(1 / sc - 1); d = 400 / (math.log(10) * sc * (1 - sc))
    half = 1.959964 * d * se
    wm = endings.get("White mates", 0); bm = endings.get("Black mates", 0)
    fen = rows[0][5]; line = open("/tmp/evid/openings_job24.epd").readlines()[first_opening_line - 1].strip()
    key = lambda s: " ".join(s.split()[:4])
    ok = key(fen) == key(line)
    print(f"== {m}: games in the list = {games_in_list}, complete pairs = {P}; "
          f"openings slice: first game's FEN == line {first_opening_line}: {ok}")
    for k in sorted(endings):
        print(f"   ending {k}: {endings[k]}")
    print(f"   identity endings: white_mates+black_mates = {wm}+{bm} = {wm+bm}; "
          f"wins+losses = {W}+{L} = {W+L}; equal: {wm+bm == W+L}")
    print(f"   identity n5: {sum(n)} = pairs {P}; identity results: {W}+{L}+{D} = {2*P}: "
          f"{sum(n) == P and W+L+D == 2*P}")
    print(f"   W-L-D={W}-{L}-{D} Elo={elo:+.2f} 95%[{elo-half:+.2f},{elo+half:+.2f}] (one seed)")
    return n, elo, half

def pool(tag, pairs):
    n = [0, 0, 0, 0, 0]
    for p in pairs:
        n = [a + b for a, b in zip(n, p)]
    P = sum(n); X = sum(i / 2 * ni for i, ni in enumerate(n)); sc = X / (2 * P)
    Vp = sum(ni * (i / 2 - 2 * sc) ** 2 for i, ni in enumerate(n)) / (P - 1)
    se = math.sqrt(Vp / (4 * P))
    elo = -400 * math.log10(1 / sc - 1); d = 400 / (math.log(10) * sc * (1 - sc))
    half = 1.959964 * d * se
    print(f"== POOL {tag}: pairs={P} n5={n} (sums to {sum(n)}) "
          f"Elo={elo:+.2f} 95%[{elo-half:+.2f},{elo+half:+.2f}]")

res = {}
slices = {"M55": 1, "M56": 1001, "M57": 2001, "M58": 3001, "M59": 4001, "M60": 5001}
for m in sys.argv[1:]:
    res[m] = load(m, slices[m])
pool("variant@2000 (M49+M51+M52+M55+M56)",
     [[79,207,386,208,120],[98,211,397,204,90],[106,206,358,213,117],
      res["M55"][0], res["M56"][0]])
pool("CED8alone@2000 (M53+M57+M58)",
     [[92,231,358,199,120], res["M57"][0], res["M58"][0]])
pool("variant@20000 (M54+M59)",
     [[50,231,436,228,55], res["M59"][0]])
