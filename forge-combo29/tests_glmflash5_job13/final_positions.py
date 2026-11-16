import io, sys
import chess, chess.pgn

# Step 4: replay each game's PGN (final position), count pieces, attribute
# the pair's result to a piece-count class (<=5 / 6-12 / >=13).
# Also: which side had the extra material in decisive short-material endings.

def analyze(pgn_path, out_path):
    games = {}
    with open(pgn_path) as f:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            rnd = int(g.headers["Round"])
            board = g.board()
            for mv in g.mainline_moves():
                board.push(mv)
            pieces = chess.popcount(board.occupied)
            # extra material: candidate's material minus base's, in pawns (simple counts)
            def mat(color):
                s = 0
                for pt, w in [(chess.PAWN,1),(chess.KNIGHT,3),(chess.BISHOP,3),(chess.ROOK,5),(chess.QUEEN,9)]:
                    s += w * len(board.pieces(pt, color))
                return s
            wcand = g.headers["White"] == "cand"
            diff = (mat(chess.WHITE) - mat(chess.BLACK)) * (1 if wcand else -1)
            games[rnd] = (pieces, diff)
    rows = [l.strip().split("|") for l in open(out_path.replace(".finals.txt", ".txt"))]
    cls = {"<=5": [0,0.0], "6-12": [0,0.0], ">=13": [0,0.0]}
    extra_rows = []
    for i in range(0, len(rows), 2):
        a, b = rows[i], rows[i+1]
        rnd = (int(a[0]) + 1) // 2
        pieces, diff = games[rnd]
        k = "<=5" if pieces <= 5 else ("6-12" if pieces <= 12 else ">=13")
        s = 0.0
        for row in (a, b):
            white, result = row[1], row[3]
            if result == "1/2-1/2":
                s += 0.5
            elif (result == "1-0") == (white == "cand"):
                s += 1.0
        cls[k][0] += 1
        cls[k][1] += s
    lines = [f"match {out_path.split('_')[0]}: final-position classes (pairs, cand points):"]
    for k in ("<=5", "6-12", ">=13"):
        cnt, pts = cls[k]
        elo = ""
        if cnt >= 100 and cnt > 0:
            sc = pts / (2 * cnt)
            if 0 < sc < 1:
                elo = f" Elo={-400 * __import__('math').log10(1/sc - 1):+.1f}"
        lines.append(f"  {k}: pairs={cnt} cand_score={pts:.1f}{elo}")
    return "\n".join(lines), games

out = []
for m in ["M12", "M13", "M14"]:
    txt, games = analyze(f"{m}.pgn", f"gamelist_{m}.finals.txt")
    # write finals file: round|pieces|material diff
    with open(f"{m}_finals.txt", "w") as f:
        for rnd in sorted(games):
            p, d = games[rnd]
            f.write(f"{rnd}|{p}|{d}\n")
    out.append(txt)
    print(txt)
with open("job13_finals_summary.txt", "w") as f:
    f.write("\n".join(out) + "\n")
