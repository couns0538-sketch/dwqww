import sys, math

# Queue 2 stats: per match - identities, W-L-D, n5, Elo + pair interval,
# openings-slice check. Slices: M105 1-1000 (20k), M106 1001-2000, M107
# 2001-3000, M108 3001-4000, M109 4001-5000 (queue2 file), M110b 1-1000
# (queue2b file, fresh). The wrapped M110 run is VOID (superseded).

def load(m, first_opening_line, book):
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
    fen = rows[0][5]; line = open(book).readlines()[first_opening_line - 1].strip()
    key = lambda s: " ".join(s.split()[:4])
    print(f"== {m}: games in the list = {games_in_list}, complete pairs = {P}; "
          f"openings slice: first game's FEN == {book} line {first_opening_line}: {key(fen) == key(line)}")
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

which = sys.argv[1]
if which == "A":
    load("M105", 1, "/tmp/evid/openings_queue2.epd")
    load("M106", 1001, "/tmp/evid/openings_queue2.epd")
    load("M107", 2001, "/tmp/evid/openings_queue2.epd")
    load("M108", 3001, "/tmp/evid/openings_queue2.epd")
    load("M109", 4001, "/tmp/evid/openings_queue2.epd")
if which == "B":
    load("M110b", 1, "/tmp/evid/openings_queue2b.epd")
if which == "POOL":
    pool("P@20000 (M24+M32 job18 + M105 queue2)",
         [[44,205,428,261,62],[47,238,405,251,59],[37,252,400,254,57]])
    pool("P@2000 (M34+M36 job19 + M106 queue2)",
         [[56,131,346,264,203],[46,132,353,282,187],[42,142,304,298,214]])
    pool("V@2000 (M49+M51+M52+M55+M56 jobs22-24 + M107 queue2)",
         [[79,207,386,208,120],[98,211,397,204,90],[106,206,358,213,117],
          [84,197,373,232,114],[98,204,392,204,102],[107,216,383,189,105]])
    pool("C8@2000 (M53 job23 + M108 queue2)",
         [[92,231,358,199,120],[99,222,381,212,86]])
    pool("T1@2000 (M67+M68 job26 + M109 queue2)",
         [[111,214,373,194,108],[92,211,377,216,104],[98,205,364,214,119]])
    pool("T2@2000 (M69 job26 + M110b queue2; the wrapped M110 is VOID)",
         [[119,213,382,196,90],[108,208,360,214,110]])
