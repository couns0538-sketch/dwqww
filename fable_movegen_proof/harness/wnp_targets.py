"""wnp_targets.py - positions in which WITNESS_NOPIN's shortcut decides the answer (job 3, standard library only).

has_legal_move() returns a bool that is true almost everywhere, so random playouts say little about the
shortcut. Its answer can only become wrong where the witness (a quiet pawn push) is illegal AND no other move is
legal: a stalemate whose pawn pushes all belong to pinned pawns. This tool constructs such stalemates
systematically: for every king square and every pawn square on the king's rank or on one of its diagonals
(a pin along the file leaves the push legal, so it cannot be decisive), with a rook, bishop or queen behind the
pawn, it searches for black pieces that take the king's flight squares without giving check. The independent
oracle confirms each position (not in check, no legal move, the push is generated). Every position is also
mirrored to the other colour.

  build            writes suite\\wnp_targets.tsv
  run TAG...       all fields of every target on the auxiliary probes, each tag against the lock
  scan NAME A-B    how many positions of fuzz chunks A..B are decisive in this sense

The positions are constructed and statically valid; whether a legal game reaches each of them is not
established. They are reported on their own and never counted in the fuzz total or as legal edge entries.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess_oracle as oracle  # noqa: E402
import fuzz  # noqa: E402
import mg_compare  # noqa: E402
import mg_format  # noqa: E402
import pinguard3  # noqa: E402

TARGETS = os.path.join(fuzz.PACK, "suite", "wnp_targets.tsv")
SEED = 20261110
DIRS = {"rank": [(1, 0), (-1, 0)], "diagonal": [(1, 1), (-1, -1)], "anti-diagonal": [(1, -1), (-1, 1)]}


def on(f, r):
    return 0 <= f <= 7 and 0 <= r <= 7


def attacked_by_black(b, s, without=None):
    """Is square s attacked by black, optionally with one square emptied (the king that steps away)?"""
    if without is None:
        return bool(oracle.attackers(b, s, "b"))
    keep = b[without]
    b[without] = "."
    hit = bool(oracle.attackers(b, s, "b"))
    b[without] = keep
    return hit


def construct(rng, k, p, s, pinner, tries=60):
    """A stalemate with white king on k, white pawn on p pinned by `pinner` on s, or None."""
    kf, kr = k & 7, k >> 3
    line = {k, p, s}
    df = (s & 7) - kf
    dr = (s >> 3) - kr
    step = (0 if df == 0 else df // abs(df)) + 8 * (0 if dr == 0 else dr // abs(dr))
    q = k + step
    while q != s:
        line.add(q)
        q += step
    flights = [(kf + a) + 8 * (kr + c) for a, c in oracle.KING if on(kf + a, kr + c) and (kf + a) + 8 * (kr + c) != p]
    for _ in range(tries):
        b = ["."] * 64
        b[k], b[p], b[s] = "K", "P", pinner
        free = [x for x in range(64) if x not in line and x != p + 8]
        # the black king: away from the white king and from the pawn's attack squares
        spots = [x for x in free if max(abs((x & 7) - kf), abs((x >> 3) - kr)) >= 3 and x not in (p + 7, p + 9)]
        if not spots:
            return None
        bk = rng.choice(spots)
        b[bk] = "k"
        ok = True
        for _round in range(7):
            open_flights = [f for f in flights if b[f] == "." and not attacked_by_black(b, f, without=k)]
            open_flights += [f for f in flights if b[f] not in (".", "k") and b[f].islower() and not attacked_by_black(b, f, without=k)]
            if not open_flights:
                break
            f = rng.choice(open_flights)
            options = []
            for piece in "qrnbq":
                for x in rng.sample(free, min(len(free), 24)):
                    if b[x] != "." or x in flights:
                        continue
                    b[x] = piece
                    if x in oracle.attackers(b, f, "b") or attacked_by_black(b, f, without=k):
                        if not oracle.attackers(b, k, "b"):
                            options.append((x, piece))
                    b[x] = "."
                if options:
                    break
            if not options:
                ok = False
                break
            x, piece = rng.choice(options)
            b[x] = piece
        if not ok or oracle.attackers(b, k, "b"):
            continue
        pos = oracle.Pos()
        pos.b, pos.side, pos.castle, pos.ep, pos.half, pos.full = b, "w", "", -1, 0, 1
        if oracle.static_problem(pos) or oracle.legal(pos):
            continue
        if not any(m[0] == p and m[1] == p + 8 for m in oracle.pseudo(pos)):
            continue
        if sum(1 for c in b if c == "q") > 8:
            continue
        return oracle.fen(pos)
    return None


def build():
    rng = random.Random(SEED)
    rows, tried, seen = [], 0, set()
    for k in range(64):
        kf, kr = k & 7, k >> 3
        for kind, dirs in DIRS.items():
            for df, dr in dirs:
                for d in range(1, 8):
                    pf, pr = kf + d * df, kr + d * dr
                    if not on(pf, pr) or not 1 <= pr <= 5:
                        continue                                   # ranks 2 to 6: the push is a plain one, not a promotion
                    p = pf + 8 * pr
                    behind = [(pf + e * df) + 8 * (pr + e * dr) for e in range(1, 8) if on(pf + e * df, pr + e * dr)]
                    behind = [x for x in behind if x != p + 8]          # the push square stays empty
                    if not behind:
                        continue
                    for pinner in ("r", "q") if kind == "rank" else ("b", "q"):
                        tried += 1
                        f = construct(rng, k, p, rng.choice(behind), pinner)
                        if f and f not in seen:
                            seen.add(f)
                            rows.append((f, "white", oracle.name(k), oracle.name(p), kind, pinner))
                            m = oracle.colour_mirror(f)
                            seen.add(m)
                            rows.append((m, "black", oracle.name(k ^ 56), oracle.name(p ^ 56), kind, pinner))
    bad = []
    for f, colour, *_ in rows:                                    # every row once more, from its FEN text
        ok, failed = oracle.check_predicate(f, "stalemate")
        pos = oracle.parse_fen(f)
        push = any(pos.b[m[0]].upper() == "P" and abs(m[1] - m[0]) == 8 and not m[2] for m in oracle.pseudo(pos))
        if not ok or not push or oracle.static_problem(pos):
            bad.append(f)
    pairs = {(r[1], r[2], r[3]) for r in rows}
    print(f"geometries tried {tried}; targets {len(rows)} ({len(rows) // 2} per colour); distinct king/pawn pairs per colour {len(pairs) // 2}; "
          f"by line: " + ", ".join(f"{kind} {sum(1 for r in rows if r[4] == kind)}" for kind in DIRS) + f"; failed the final oracle check: {len(bad)}")
    if bad or not rows:
        print("BUILD FAILED")
        return 3
    os.makedirs(os.path.dirname(TARGETS), exist_ok=True)
    with open(TARGETS, "w", encoding="ascii", newline="\n") as f:
        f.write("id\tfen\tside_to_move\tking\tpinned_pawn\tpin_line\tpinner\tprovenance\n")
        for i, (fen_text, colour, king, pawn, kind, pinner) in enumerate(rows):
            f.write(f"wnp_{i:04d}\t{fen_text}\t{colour}\t{king}\t{pawn}\t{kind}\t{pinner}\tconstructed by wnp_targets.py, seed {SEED}; oracle: stalemate with a generated pawn push\n")
    print(f"written {TARGETS} sha256 {fuzz.sha256_file(TARGETS)}")
    return 0


def load():
    return [ln.split("\t") for ln in open(TARGETS, "r", encoding="ascii").read().splitlines()[1:] if ln]


def run(tags):
    pinguard3.ensure()
    rows = load()
    path = "".join(f"P {i} X0 0 {r[1]}\nM\n" for i, r in enumerate(rows)).encode("ascii")
    ref, err, code = fuzz.run_probe([fuzz.probe("LOCK"), "run"], path)
    check = mg_compare.compare(ref, ref, expect_tag="LOCK", allow_error_records=True)
    recs = [mg_format.decode(ref[o:o + n]) for o, n in mg_format.frames(ref)[1:-1]]
    rejected = sum(1 for d in recs if d["kind"] != 0)
    decisive = sum(1 for d in recs if d["kind"] == 0 and not d["legal"] and d["checkers_main"] == 0 and d["has_before"] == 0 and d["has_after"] == 0 and d["all"])
    print(f"{fuzz.now()} lock probe: {len(recs)} targets, rejected by set_fen {rejected}, has_legal_move false with a generated move list "
          f"(decisive) {decisive}; reference {check.status}", flush=True)
    rdir = os.path.join(fuzz.OUT, "runs", "wnp_targets")
    os.makedirs(rdir, exist_ok=True)
    code_all = 0
    for tag in tags:
        tr, cerr, ccode = fuzz.run_probe([fuzz.probe(tag), "run"], path)
        res = mg_compare.compare(ref, tr, path.decode("ascii"), expect_tag=tag, allow_error_records=True)
        ok = code == 0 and ccode == 0 and check.status == "EQUAL" and res.status == "EQUAL" and rejected == 0 and decisive == len(rows)
        receipt = {"check": "wnp_targets", "tag": tag, "targets": len(rows), "decisive_for_the_lock": decisive, "rejected_by_set_fen": rejected,
                   "status": "MATCH" if ok else res.status, "positions_identical": res.positions, "detail": res.detail[:600],
                   "targets_sha256": fuzz.sha256_file(TARGETS), "probe_sha256": fuzz.sha256_file(fuzz.probe(tag)),
                   "lock_probe_sha256": fuzz.sha256_file(fuzz.probe("LOCK")), "exit": ccode, "when": fuzz.now(),
                   "meaning": "constructed stalemates in which every pawn push belongs to a pinned pawn: the only positions where the shortcut "
                              "of WITNESS_NOPIN could change the answer of has_legal_move; all fields compared, not only that one"}
        with open(os.path.join(rdir, tag + ".json"), "w", encoding="ascii", newline="\n") as f:
            json.dump(receipt, f, indent=1)
        print(f"{fuzz.now()} wnp targets {tag}: {receipt['status']} {res.positions}/{len(rows)}", flush=True)
        if not ok:
            code_all = 3
    return code_all


def scan(name, first, last):
    """Decisive positions inside fuzz chunks: stalemates in which a quiet pawn push is generated."""
    pinguard3.ensure()
    total = stalemates = decisive = 0
    for chunk in range(first, last + 1):
        path, _ = fuzz.gen_chunk(name, chunk)
        tr, _, _ = fuzz.run_probe([fuzz.probe("LOCK"), "run", "--null", "0"], path)
        playouts = mg_format.parse_path(path.decode("ascii"))
        for o, n in mg_format.frames(tr)[1:-1]:
            if tr[o + 6] != 0:
                continue
            total += 1
            d = mg_format.decode(tr[o:o + n])
            if d["legal"] or d["checkers_main"]:
                continue
            stalemates += 1
            seed, moves = playouts[d["playout"]]
            pos = oracle.parse_fen(seed)
            for mv in moves[:d["ply"]]:
                pos = oracle.make(pos, oracle.find(pos, mv, oracle.legal(pos)))
            if any(pos.b[m[0]].upper() == "P" and abs(m[1] - m[0]) == 8 and not m[2] and m[3] == "" and pos.b[m[1]] == "." for m in oracle.pseudo(pos)):
                decisive += 1
    out = {"check": "wnp_scan", "seeds": name, "chunks": f"{first}-{last}", "positions": total, "stalemates": stalemates,
           "stalemates_with_a_generated_pawn_push": decisive, "when": fuzz.now(),
           "meaning": "how many fuzz positions are decisive for WITNESS_NOPIN (has_legal_move is false although a pawn push is generated)"}
    rdir = os.path.join(fuzz.OUT, "runs", "wnp_targets")
    os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, f"SCAN_{name}_{first}_{last}.json"), "w", encoding="ascii", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out))
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if argv[1] == "build":
        return build()
    if argv[1] == "run":
        return run(argv[2:])
    if argv[1] == "scan":
        a, b = argv[3].split("-")
        return scan(argv[2], int(a), int(b))
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
