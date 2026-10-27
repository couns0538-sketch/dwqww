#!/usr/bin/env python3
"""Rebuild positions50.fen: 8 bench FENs + 14 WAC300 + 14 ECM + 14 forge-10000 openings (deterministic picks).
usage: make_positions50.py <lock_archive_dir> <forge_src_dir> <out.fen>"""
import sys, re, os
pkg, w, out = sys.argv[1:4]
bench = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
 "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
 "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
 "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
 "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
 "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
 "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
 "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"]
def epd(path):
    rows = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line: continue
        f = line.split()
        m = re.search(r'id "?([^";]+)', line)
        rows.append((" ".join(f[:4]) + " 0 1", m.group(1) if m else f"{os.path.basename(path)}:{n}"))
    return rows
wac = epd(pkg + "/4_tests/suites/wac300.epd")
ecm = epd(pkg + "/4_tests/suites/ecm_gcp.epd")
opn = epd(w + "/tools/openings/forge-10000.epd")
pick = lambda rows, n, offset=0: [rows[offset + (i * (len(rows) - offset)) // n] for i in range(n)]
sel = [(f, "bench.%d" % i) for i, f in enumerate(bench)] + pick(wac, 14, 7) + pick(ecm, 14) + pick(opn, 14)
assert len(sel) == 50 and len({f for f, _ in sel}) == 50, "positions must be unique"
with open(out, "w", newline="\n") as fh:
    for fen, ident in sel: fh.write(f"{fen} ; {ident}\n")
print("wrote", len(sel), "positions to", out)
