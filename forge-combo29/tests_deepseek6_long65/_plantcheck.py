import re, chess, sys
def check(rows_path, fens):

    bad_legal = []
    mate_mismatch = []
    mate_total = 0
    mate_ok = 0
    checkmate_nonmate = 0
    lengths = []
    unparsed = 0
    total = 0
    for line in open(rows_path):
        f = line.rstrip("\n").split("\t")
        if len(f) != 6 or f[0] == "pos":
            continue
        idx, nodes, bm, kind, val, pv = f
        idx = int(idx) - 1
        total += 1
        board = chess.Board(fens[idx])
        moves = pv.split() if pv else []
        if not moves:
            unparsed += 1
            continue
        lengths.append(len(moves))
        legal_until = 0
        for ply, mv in enumerate(moves, 1):
            try:
                m = chess.Move.from_uci(mv)
            except Exception:
                bad_legal.append((idx + 1, ply, mv, "unparseable"))
                legal_until = -1
                break
            if m not in board.legal_moves:
                bad_legal.append((idx + 1, ply, mv, "illegal"))
                legal_until = -1
                break
            board.push(m)
            legal_until = ply
        if legal_until < 0:
            continue
        ends_mate = board.is_checkmate()
        if kind == "mate":
            mate_total += 1
            n = int(val)
            want = (2 * n - 1) if n > 0 else (2 * abs(n))
            if ends_mate and len(moves) == want:
                mate_ok += 1
            else:
                mate_mismatch.append((idx + 1, n, want, len(moves), ends_mate))
        elif ends_mate:
            checkmate_nonmate += 1
    return dict(total=total, bad_legal=bad_legal, mate_total=mate_total, mate_ok=mate_ok,
                mate_mismatch=mate_mismatch, checkmate_nonmate=checkmate_nonmate,
                unparsed=unparsed, lengths=lengths)



fens=[l.strip() for l in open('SMOKE.fens') if l.strip()]
r=check('pv/SMOKE_plant.pvrows', fens)
print("PLANT via pvrows.py's own check():")
print("  searches:", r['total'], " fully legal:", len(r['lengths'])-len(r['bad_legal']))
print("  first illegal ply:", r['bad_legal'][:3])
