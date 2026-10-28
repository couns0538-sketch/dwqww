#!/usr/bin/env python3
"""Build tests/syzygy_reference.tsv: Syzygy answers from an independent
reference prober (python-chess, used as an external test oracle only; no code
of it is used in the engine) on the same table files the engine reads.

Positions: for every material with a WDL table in the folder, random legal
positions from `forge_syzygy_tests gen` (seeded by the material name), plus
en-passant positions for materials with pawns of both colours.
Per position: WDL, DTZ, and the DTZ of every root move counted from the root
(capture or pawn move: from the WDL after the move; mate: 1; otherwise the
child's DTZ plus one ply), the values rank_root_moves must reproduce.

usage: python -I make_reference.py <forge_syzygy_tests binary> <tablebase dir> <python-chess site dir> <out.tsv>
"""
import hashlib
import os
import subprocess
import sys

PER_MATERIAL = 10
EP_PER_MATERIAL = 3
PIECE_ORDER = "QRBNP"


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    binary, tb_dir, site, out_path = sys.argv[1:5]
    sys.path.insert(0, site)
    import chess
    import chess.syzygy

    tables = sorted(f[:-5] for f in os.listdir(tb_dir) if f.endswith(".rtbw"))
    tb = chess.syzygy.open_tablebase(tb_dir)

    def table_name(a, b):
        for name in (a + "v" + b, b + "v" + a):
            if name in tables:
                return name
        return None

    def side_name(s):
        return "K" + "".join(sorted(s, key=PIECE_ORDER.index))

    def needs(board):
        w = "".join(chess.piece_symbol(p.piece_type).upper() for p in board.piece_map().values()
                    if p.color == chess.WHITE and p.piece_type != chess.KING)
        b = "".join(chess.piece_symbol(p.piece_type).upper() for p in board.piece_map().values()
                    if p.color == chess.BLACK and p.piece_type != chess.KING)
        out = set()
        if len(w) + len(b) + 2 == 5:
            out.add(table_name(side_name(w), side_name(b)))
            for promo in "QRBN":
                if "P" in w:
                    out.add(table_name(side_name(w.replace("P", "", 1) + promo), side_name(b)))
                if "P" in b:
                    out.add(table_name(side_name(w), side_name(b.replace("P", "", 1) + promo)))
        out.discard(None)
        return sorted(out)

    def zeroing_dtz(wdl):
        return {2: 1, 1: 101, 0: 0, -1: -101, -2: -1}[wdl]

    rows = []
    for name in tables:
        seed = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
        jobs = [(PER_MATERIAL, [])]
        if "P" in name.split("v")[0] and "P" in name.split("v")[1]:
            jobs.append((EP_PER_MATERIAL, ["ep"]))
        for count, extra in jobs:
            out = subprocess.run([binary, "gen", name, str(count), str(seed)] + extra, capture_output=True, text=True,
                                 check=True).stdout
            for fen in out.split("\n"):
                fen = fen.strip()
                if not fen:
                    continue
                board = chess.Board(fen)
                wdl = tb.probe_wdl(board)
                dtz = tb.probe_dtz(board)
                moves = []
                for move in board.legal_moves:
                    zeroing = board.is_zeroing(move)
                    board.push(move)
                    if zeroing:
                        value = zeroing_dtz(-tb.probe_wdl(board))
                    elif board.is_checkmate():
                        value = 1
                    else:
                        d = -tb.probe_dtz(board)
                        value = d + (d > 0) - (d < 0)
                    board.pop()
                    moves.append("%s:%d" % (move.uci(), value))
                note = name + (" ep" if extra else "")
                need = needs(board)
                if need:
                    note += " needs: " + " ".join(need)
                rows.append((fen, wdl, dtz, " ".join(moves), note))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Syzygy answers of an independent reference prober (python-chess %s, test oracle only) on the\n" % chess.__version__)
        f.write("# Syzygy 3-4-5 files (tablebase.sesse.net mirror, checksum.md5 verified); built by opus_round1/C1/make_reference.py.\n")
        f.write("# fen\twdl\tdtz\troot moves (uci:dtz from the root)\tnote [needs: 5-piece tables]\n")
        for fen, wdl, dtz, moves, note in rows:
            f.write("%s\t%d\t%d\t%s\t%s\n" % (fen, wdl, dtz, moves or "-", note))
    print("rows", len(rows), "materials", len(tables))
    return 0


if __name__ == "__main__":
    sys.exit(main())
