import sys, math, re
import chess, chess.pgn

# Job 17 stats: per match - endings table (with identity mates = wins+losses),
# W-L-D, n5, Elo + 95% pair interval; and the IDENTICAL-PAIRS count (the two
# games of a pair move-for-move the same), with the identity identical <= n5[2].

def pgn_moves(path):
    games = {}
    with open(path) as f:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            key = (int(g.headers["Round"]), g.headers["White"] == "cand")
            games[key] = [m.uci() for m in g.mainline_moves()]
    return games

def stats(m):
    rows = [l.strip().split("|") for l in open(f"gamelist_{m}.txt")]
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
    wm = sum(v for k, v in endings.items() if k == "White mates")
    bm = sum(v for k, v in endings.items() if k == "Black mates")
    gm = pgn_moves(f"{m}.pgn")
    ident = 0
    for i in range(0, len(rows), 2):
        a, b = rows[i], rows[i + 1]
        rnd = (int(a[0]) + 1) // 2
        k1, k2 = (rnd, True), (rnd, False)
        if gm.get(k1) and gm.get(k2) and gm[k1] == gm[k2]:
            ident += 1
    print(f"== {m}: pairs={P} n5={n} (n5 sums to {sum(n)})")
    for k in sorted(endings):
        print(f"   ending {k}: {endings[k]}")
    print(f"   identity endings: white_mates+black_mates = {wm}+{bm} = {wm+bm}; wins+losses = {W}+{L} = {W+L}; equal: {wm+bm==W+L}")
    print(f"   W-L-D={W}-{L}-{D} Elo={elo:+.2f} 95%[{elo-half:+.2f},{elo+half:+.2f}] (one seed)")
    print(f"   identical-move pairs: {ident}; identity: identical ({ident}) <= n5 middle cell ({n[2]}): {ident <= n[2]}")

for m in sys.argv[1:]:
    stats(m)
