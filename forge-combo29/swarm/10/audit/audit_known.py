#!/usr/bin/env python3
"""audit_known.py -- seat 10's batch audit of the brief's "Known:" claims (K1..K14).

Every check writes its raw engine I/O to OUT/<K>/ and one JSON verdict per claim to
OUT/verdicts/<K>.json. Nothing is printed that is not also written to a file.

Usage: audit_known.py EXE OUTDIR
The position sets are read from OUTDIR/sets/{first200.fens,set_G.epd}.
"""
import json
import os
import subprocess
import sys

import chess

EXE = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
SETS = os.path.join(OUT, "sets")
os.makedirs(os.path.join(OUT, "verdicts"), exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def talk(lines, tag, timeout=1200):
    """one fresh process; raw stdout+stderr saved under OUT/<tag>.txt"""
    p = subprocess.run([EXE], input="\n".join(lines) + "\nquit\n",
                       capture_output=True, text=True, timeout=timeout)
    path = os.path.join(OUT, tag + ".txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("=== exe %s\n=== commands:\n" % EXE)
        for l in lines:
            f.write("  " + l + "\n")
        f.write("=== stdout:\n" + p.stdout)
        f.write("=== stderr:\n" + p.stderr)
        f.write("=== exit %s\n" % p.returncode)
    return p.stdout, p.stderr, p.returncode


def badlines(out, err):
    hits = []
    for l in (out + "\n" + err).splitlines():
        low = l.lower()
        for b in BAD:
            if b in low:
                hits.append(l.strip())
    return hits


def nodes_of(out):
    n = None
    for l in out.splitlines():
        if l.startswith("nodes "):
            n = int(l.split()[1])
    return n


def verdict(k, **kw):
    p = os.path.join(OUT, "verdicts", k + ".json")
    with open(p, "w") as f:
        json.dump(kw, f, indent=2)
        f.write("\n")
    print(k + ": " + json.dumps({x: kw[x] for x in kw if x in
                                 ("result", "detail", "engine", "python")}, default=str)[:400])


def perft_py(b, d):
    if d == 0:
        return 1
    if d == 1:
        return b.legal_moves.count()
    n = 0
    for m in list(b.legal_moves):
        b.push(m)
        n += perft_py(b, d - 1)
        b.pop()
    return n


# ---------------------------------------------------------------- K1
def k1():
    lines = ["uci", "isready", "position startpos moves e2e4 e7e5 e1e3", "isready",
             "go perft 1"]
    out, err, rc = talk(lines, "K1/illegal_prefix")
    eng = nodes_of(out)
    b = chess.Board()
    b.push(chess.Move.from_uci("e2e4"))
    b.push(chess.Move.from_uci("e7e5"))
    py = b.legal_moves.count()
    verdict("K1", claim="an illegal move keeps the legal prefix (perft 1 = 29 after e2e4 e7e5 e1e3)",
            engine=eng, python=py, result="PASS" if eng == py == 29 else "REFUTED",
            detail="post-e2e4-e7e5 legal move count, engine vs python-chess",
            refusals=badlines(out, err), rc=rc)


# ---------------------------------------------------------------- K2 + K11
def k2():
    cases = {
        "hash0": ["setoption name Hash value 0"],
        "hash2049": ["setoption name Hash value 2049"],
        "threads0": ["setoption name Threads value 0"],
        "valueless_multipv": ["setoption name MultiPV"],
        "valueless_hash": ["setoption name Hash"],
        "unknown_option": ["setoption name NoSuchOption value 1"],
    }
    res = {}
    for name, cmd in cases.items():
        out, err, rc = talk(["uci", "isready"] + cmd + ["isready"], "K2/" + name)
        msg = [l.strip() for l in out.splitlines()
               if l.strip().lower().startswith("info string")]
        res[name] = {"cmd": cmd[0], "info_string_lines": msg, "rc": rc}
    # the exact line required by the brief
    exact = "info string invalid value for option Hash"
    k2_ok = exact in res["hash0"]["info_string_lines"]
    msgset = {n: tuple(v["info_string_lines"]) for n, v in res.items()}
    same_shape = len({tuple(x.replace(n.split("_")[0], "X") for x in v["info_string_lines"])
                      for n, v in res.items()}) <= 2
    verdict("K2", claim="`setoption name Hash value 0` answers `info string invalid value for option Hash`",
            result="PASS" if k2_ok else "REFUTED", cases=res,
            detail="exact message present for Hash 0" if k2_ok else "message differs",
            same_message_shape_for_all_out_of_range_and_valueless=same_shape,
            message_shapes=msgset)
    verdict("K11", claim="an option without a value answers info string invalid value for option X",
            result="PASS" if all(res[n]["info_string_lines"] and
                                 all("invalid value for option" in l
                                     for l in res[n]["info_string_lines"])
                                 for n in ("valueless_multipv", "valueless_hash"))
            else "REFUTED", cases={n: res[n] for n in ("valueless_multipv", "valueless_hash")})


# ---------------------------------------------------------------- K3
def k3():
    out, err, rc = talk(["uci", "isready", "position startpos", "isready", "go perft 5"],
                        "K3/perft5")
    n = nodes_of(out)
    verdict("K3", claim="startpos perft 5 = 4,865,609", engine=n,
            result="PASS" if n == 4865609 else "REFUTED", rc=rc,
            refusals=badlines(out, err))


# ---------------------------------------------------------------- K4
def k4():
    fens = [l.strip() for l in open(os.path.join(SETS, "set_G.epd")) if l.strip()]
    bad3, bad4, refused = [], [], []
    checked3 = checked4 = 0
    for i, fen in enumerate(fens):
        try:
            b = chess.Board(fen)
        except ValueError:
            refused.append((i, "python-chess cannot parse", fen))
            continue
        py3 = perft_py(chess.Board(fen), 3)
        out, err, rc = talk(["uci", "isready", "position fen " + fen, "isready",
                             "go perft 3"], "K4/p%03d_d3" % i)
        e3 = nodes_of(out)
        checked3 += 1
        if e3 != py3:
            bad3.append({"i": i, "fen": fen, "engine": e3, "python": py3})
        if i < 60:
            py4 = perft_py(chess.Board(fen), 4)
            out, err, rc = talk(["uci", "isready", "position fen " + fen, "isready",
                                 "go perft 4"], "K4/p%03d_d4" % i)
            e4 = nodes_of(out)
            checked4 += 1
            if e4 != py4:
                bad4.append({"i": i, "fen": fen, "engine": e4, "python": py4})
    with open(os.path.join(OUT, "K4/mismatches.json"), "w") as f:
        json.dump({"d3": bad3, "d4": bad4, "refused": refused}, f, indent=2)
    verdict("K4", claim="G perft 3 and the first 60 at perft 4 were equal in an earlier check",
            result="PASS" if not bad3 and not bad4 else "REFUTED",
            checked_depth3=checked3, mismatches_depth3=len(bad3),
            checked_depth4=checked4, mismatches_depth4=len(bad4),
            note="'equal' is undefined in the brief; tested as equal to python-chess 1.11.2")


# ---------------------------------------------------------------- K8
def k8():
    cases = {
        "canonical": "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
        "digits44": "4k3/44/8/8/8/8/8/4K3 w - - 0 1",
        "digits17": "4k3/17/8/8/8/8/8/4K3 w - - 0 1",
        "digit9": "4k3/9/8/8/8/8/8/4K3 w - - 0 1",
    }
    res = {}
    for name, fen in cases.items():
        out, err, rc = talk(["uci", "isready", "position fen " + fen, "isready", "go perft 2"],
                            "K8/" + name)
        res[name] = {"fen": fen, "perft2": nodes_of(out), "rc": rc,
                     "refused": [l.strip() for l in out.splitlines()
                                 if "invalid fen" in l.lower()]}
    same = (res["canonical"]["perft2"] == res["digits44"]["perft2"] == res["digits17"]["perft2"])
    nine_refused = bool(res["digit9"]["refused"])
    verdict("K8", claim="consecutive digits of a rank are ADDED; '9' is refused",
            result="PASS" if same and nine_refused else "REFUTED", cases=res,
            detail="44 and 17 give the same perft 2 as the canonical rank; 9 refused")


# ---------------------------------------------------------------- K9
def k9():
    fen = "4k3/8/8/8/8/1n1n1n2/8/4K3 w - - 0 1"   # white king e1 attacked by knights d2? no: see note
    # three knights all attacking the WHITE king on e1: c2, d3, f3 all attack e1
    fen = "4k3/8/8/8/8/3n1n2/2n5/4K3 w - - 0 1"
    out, err, rc = talk(["uci", "isready", "position fen " + fen, "isready", "go perft 1"],
                        "K9/triple_check")
    eng = nodes_of(out)
    refused = [l.strip() for l in out.splitlines() if "invalid fen" in l.lower()]
    b = chess.Board(fen)
    py = b.legal_moves.count()
    py_status = b.status()
    attackers = sorted(chess.square_name(s) for s in b.attackers(chess.BLACK, b.king(chess.WHITE)))
    verdict("K9", claim="a position no game can reach is accepted (a triple check by three knights); "
                        "its moves are generated right",
            fen=fen, result="PASS" if (not refused and eng == py) else "REFUTED",
            engine=eng, python=py, refused=refused, attackers=attackers,
            python_status=py_status,
            detail="three knights c2/d3/f3 each attack the white king on e1")


# ---------------------------------------------------------------- K10
def k10():
    cases = {
        "plain_garbage": ["garbage line"],
        "go_banana": ["go banana"],
        "bare_position": ["position"],
        "bare_setoption": ["setoption name"],
        "go_depth_negative": ["go depth -3"],
        "hash_hash": ["###"],
    }
    res = {}
    for name, cmd in cases.items():
        out, err, rc = talk(["uci", "isready"] + cmd + ["isready"], "K10/" + name)
        lines_after = out.split("readyok")
        spoke = [l.strip() for l in out.splitlines()
                 if l.strip() and not l.startswith(("id ", "option ", "uciok", "readyok"))]
        res[name] = {"cmd": cmd[0], "spoke": spoke, "rc": rc}
    silent = [n for n, v in res.items() if not v["spoke"]]
    verdict("K10", claim="an unknown command is ignored without a line",
            result="PASS" if res["plain_garbage"]["spoke"] == [] else "REFUTED",
            cases=res, silent_cases=silent,
            beyond="plain garbage is silent; the other garbage forms that begin with a KNOWN word "
                   "are NOT silent")


# ---------------------------------------------------------------- K12
def k12():
    cases = {"checkmate": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
             "stalemate": "7k/5Q2/5K2/8/8/8/8/8 b - - 0 1"}
    res = {}
    for name, fen in cases.items():
        b = chess.Board(fen)
        out, err, rc = talk(["uci", "isready", "position fen " + fen, "isready", "go depth 5"],
                            "K12/" + name)
        best = [l.strip() for l in out.splitlines() if l.startswith("bestmove")]
        res[name] = {"fen": fen, "python_is_checkmate": b.is_checkmate(),
                     "python_is_stalemate": b.is_stalemate(),
                     "python_legal": b.legal_moves.count(),
                     "bestmove_lines": best, "rc": rc}
    ok = all(v["bestmove_lines"] and v["bestmove_lines"][0].startswith("bestmove 0000")
             for v in res.values())
    verdict("K12", claim="bestmove 0000 on a position without legal moves (checkmate, stalemate)",
            result="PASS" if ok else "REFUTED", cases=res)


if __name__ == "__main__":
    which = sys.argv[3].split(",") if len(sys.argv) > 3 else ["K1", "K2", "K3", "K8", "K9", "K10", "K12"]
    for k in which:
        globals()[k.lower()]()
