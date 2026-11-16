import sys, math

# Queue 4 stats + THE POOLS (this is a pool item). Per match: identities,
# W-L-D, n5, Elo + pair interval, openings-slice check. Pools: every
# candidate at each node count over ALL its looks so far (queue items AND
# jobs 23-27), each named; plus the pool without the first look where that
# look was the reason for the repeats (the best-of problem, named).

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
    elo = -400 * math.log10(1 / sc - 1) if 0 < sc < 1 else 0.0
    d = 400 / (math.log(10) * sc * (1 - sc)) if 0 < sc < 1 else 0.0
    half = 1.959964 * d * se
    wm = endings.get("White mates", 0); bm = endings.get("Black mates", 0)
    fen = rows[0][5]; line = open("/tmp/evid/openings_queue4.epd").readlines()[first_opening_line - 1].strip()
    key = lambda s: " ".join(s.split()[:4])
    print(f"== {m}: games in the list = {games_in_list}, complete pairs = {P}; "
          f"openings slice: first game's FEN == line {first_opening_line}: {key(fen) == key(line)}")
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
    elo = -400 * math.log10(1 / sc - 1) if 0 < sc < 1 else 0.0
    d = 400 / (math.log(10) * sc * (1 - sc)) if 0 < sc < 1 else 0.0
    half = 1.959964 * d * se
    print(f"== POOL {tag}: pairs={P} n5={n} (sums to {sum(n)}) "
          f"Elo={elo:+.2f} 95%[{elo-half:+.2f},{elo+half:+.2f}]")

# n5 vectors from the committed gamelists of earlier jobs
M49 = [79, 207, 386, 208, 120]   # job 22: V@2k first look (the picked-best one)
M54 = [50, 231, 436, 228, 55]    # job 23: V@20k first look
M59 = [40, 239, 415, 251, 55]    # job 24: V@20k second look
M24 = [44, 205, 428, 261, 62]    # job 18: P@20k first look under S14

res = {}
slices = {"M116": 1, "M117": 1001, "M118": 2001, "M119": 3001, "M120": 4001}
for m in sys.argv[1:]:
    res[m] = load(m, slices[m])

pool("V@20000 ALL FIVE looks (M54+M59+M73+M74+M101+M116 = 6 looks)",
     [M54, M59, [53, 241, 440, 226, 40], [45, 230, 427, 254, 44],
      [55, 240, 398, 260, 47], res["M116"][0]])
pool("V@2000 ALL SEVEN looks (M49+M51+M52+M55+M56+M107+M117)",
     [M49, [98, 211, 397, 204, 90], [106, 206, 358, 213, 117],
      [84, 197, 373, 232, 114], [98, 204, 392, 204, 102],
      [107, 216, 383, 189, 105], res["M117"][0]])
pool("V@2000 WITHOUT the picked-best first look (M51+M52+M55+M56+M107+M117)",
     [[98, 211, 397, 204, 90], [106, 206, 358, 213, 117],
      [84, 197, 373, 232, 114], [98, 204, 392, 204, 102],
      [107, 216, 383, 189, 105], res["M117"][0]])
pool("T1@20000 ALL FOUR looks (M70+M71+M103+M118)",
     [[46, 252, 404, 261, 37], [45, 241, 420, 248, 46],
      [58, 247, 405, 250, 40], res["M118"][0]])
pool("P@20000 ALL FOUR looks (M24+M32+M105+M119)",
     [M24, [47, 238, 405, 251, 59], [37, 252, 400, 254, 57], res["M119"][0]])
pool("P@20000 WITHOUT its first look (M32+M105+M119)",
     [[47, 238, 405, 251, 59], [37, 252, 400, 254, 57], res["M119"][0]])
pool("N0@2000 (M120 alone; the mirrored null)", [res["M120"][0]])
