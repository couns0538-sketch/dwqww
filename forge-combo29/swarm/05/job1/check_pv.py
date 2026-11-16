#!/usr/bin/env python3
"""check_pv.py RAWFILE... writes rows.jsonl and prints the summary tables.
For each position block: take the LAST `info ... pv ...` line before bestmove.
Parse score (cp or mate) and the pv moves. Replay the pv with python-chess.
A pv move that python-chess refuses is ILLEGAL. Report mate-distance agreement.
"""
import json
import re
import sys

import chess

pv_re = re.compile(r"^info\b.*\bpv\b(.*)$")
score_cp_re = re.compile(r"\bscore cp (-?\d+)")
score_mate_re = re.compile(r"\bscore mate (-?\d+)")
depth_re = re.compile(r"\bdepth (\d+)")
nodes_re = re.compile(r"\bnodes (\d+)")


def parse_raw(path, tag):
    rows = []
    cur = None
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("### pos "):
                if cur:
                    rows.append(cur)
                parts = line.split(" ", 3)
                cur = {"set": tag, "pos": int(parts[2]), "fen": parts[3] if len(parts) > 3 else "",
                       "last_pv": None, "bestmove": None, "bad": [], "nlines": 0}
            elif cur is not None:
                if line.startswith("### end"):
                    continue
                if line.startswith("### HARNESS"):
                    cur["bad"].append(line)
                    continue
                cur["nlines"] += 1
                if line.startswith("bestmove"):
                    cur["bestmove"] = line
                m = pv_re.match(line)
                if m:
                    toks = m.group(1).split()
                    cur["last_pv"] = {"line": line, "moves": toks,
                                      "depth": int(depth_re.search(line).group(1)) if depth_re.search(line) else None,
                                      "nodes": int(nodes_re.search(line).group(1)) if nodes_re.search(line) else None}
        if cur:
            rows.append(cur)
    return rows


def analyse(row):
    fen = row["fen"]
    try:
        board = chess.Board(fen)
    except Exception as e:
        row["fen_error"] = str(e)
        return row
    row["py_valid"] = True
    lp = row["last_pv"]
    if not lp:
        row["verdict"] = "no_pv"
        return row
    ml = score_mate_re.search(lp["line"])
    cl = score_cp_re.search(lp["line"])
    lp["score"] = ("mate", int(ml.group(1))) if ml else (("cp", int(cl.group(1))) if cl else ("none", None))
    # replay
    b = board.copy()
    illegal_at = None
    plies = 0
    for mv in lp["moves"]:
        try:
            m = chess.Move.from_uci(mv)
        except Exception:
            illegal_at = (plies, mv, "unparsable uci")
            break
        if m not in b.legal_moves:
            illegal_at = (plies, mv, "not legal in position")
            break
        b.push(m)
        plies += 1
    lp["plies"] = plies
    lp["illegal"] = illegal_at
    lp["ends_checkmate"] = b.is_checkmate()
    lp["ends_stalemate"] = b.is_stalemate()
    kind, val = lp["score"]
    if kind == "mate":
        want = 2 * val - 1 if val > 0 else 2 * (-val)
        lp["mate_want_plies"] = want
        lp["mate_ok"] = bool(lp["ends_checkmate"] and plies == want)
        lp["mate_pv_too_short"] = bool(lp["ends_checkmate"] is False and plies < want)
    return row


def main():
    rows = []
    for spec in sys.argv[1:]:
        tag, path = spec.split("=", 1)
        rows += [analyse(r) for r in parse_raw(path, tag)]
    with open("out/rows.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    n = len(rows)
    with_best = sum(1 for r in rows if r["bestmove"])
    with_pv = sum(1 for r in rows if r["last_pv"])
    illegal = [r for r in rows if r["last_pv"] and r["last_pv"]["illegal"]]
    bad_harness = [r for r in rows if r["bad"]]
    print(f"TABLE A: positions={n} with_bestmove={with_best} with_pv={with_pv} "
          f"py_invalid_fen={sum(1 for r in rows if not r.get('py_valid'))} harness_stops={len(bad_harness)}")
    print(f"TABLE B (illegal pv moves): {len(illegal)}")
    for r in illegal[:20]:
        print(f"  {r['set']} pos {r['pos']} {r['fen']} -> {r['last_pv']['illegal']}")
    mates_pos = [r for r in rows if r["last_pv"] and r["last_pv"].get("score", ("",))[0] == "mate"
                 and r["last_pv"]["score"][1] > 0]
    mates_neg = [r for r in rows if r["last_pv"] and r["last_pv"].get("score", ("",))[0] == "mate"
                 and r["last_pv"]["score"][1] < 0]
    print(f"TABLE C: mate+ root scores={len(mates_pos)}  mate- root scores={len(mates_neg)}")
    for group, label in ((mates_pos, "mate+"), (mates_neg, "mate-")):
        for r in group:
            lp = r["last_pv"]
            print(f"  {label} {r['set']} pos {r['pos']} mate {lp['score'][1]} want {lp['mate_want_plies']} plies "
                  f"got {lp['plies']} endcheckmate={lp['ends_checkmate']} ok={lp['mate_ok']} "
                  f"tooshort={lp['mate_pv_too_short']} depth={lp['depth']}")
    if mates_pos:
        small = [r for r in mates_pos if r["last_pv"]["score"][1] <= 5]
        big = [r for r in mates_pos if r["last_pv"]["score"][1] >= 6]
        f_small = sum(1 for r in small if r["last_pv"]["mate_ok"])
        f_big = sum(1 for r in big if r["last_pv"]["mate_ok"])
        print(f"TABLE D: mate+ N<=5: {f_small}/{len(small)} exact;  mate+ N>=6: {f_big}/{len(big)} exact")
    if mates_neg:
        f_neg = sum(1 for r in mates_neg if r["last_pv"]["mate_ok"])
        print(f"TABLE E: mate-: {f_neg}/{len(mates_neg)} exact (mated after 2|N| plies)")


if __name__ == "__main__":
    main()
