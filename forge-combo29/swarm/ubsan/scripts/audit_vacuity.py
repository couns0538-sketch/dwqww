#!/usr/bin/env python3
"""Non-vacuity audit of a workload.json.

A zero from a path that never executed is not a zero. For each phase this
checks the evidence that the phase's code actually ran:

  * pins     : the four node counts equal the honesty pins
  * perft    : `nodes N` lines present, and startpos perft 5 == 4,865,609
  * depth    : every probe reported an `info depth N` line with depth == N and
               nodes > 0 (a drawn-root bail would give 0 nodes / empty pv)
  * deep     : same at the deeper target
  * netoff   : evaluations ran with the second net, and `eval` printed hce lines
  * eval     : 240 `info string eval` lines with both components
  * mate     : `go mate` answered with a bestmove and a mate score where one exists
  * book     : at least one `info string book move` was produced
  * stress   : extreme-material positions evaluated and searched with nodes > 0
  * malformed: each malformed form produced a reply or a bounded stop
  * protocol : each protocol form was followed by a search that ran

Writes a JSON report; exit 1 if any phase has no evidence it executed.
"""
import json
import re
import sys

PINS = {"bench 11": 312866, "bench 13": 862329, "bench 16": 3024920}
PERFT5 = 4865609


def phase_probes(d, name):
    return d["phases"].get(name, {}).get("probes", [])


def audit(d):
    out = {}
    order = d.get("order", [])

    if "pins" in order:
        rows = {}
        for pr in phase_probes(d, "pins"):
            m = re.search(r"bench depth (\d+) nodes (\d+)", pr.get("cmd", "") + " " +
                          (pr.get("nodes") or ""))
            lab = pr.get("probe", "")
            if re.search(r"bench (\d+)", lab):
                src = pr.get("bench_line") or pr.get("node_line") or ""
                mm = re.search(r"nodes (\d+)", src)
                rows[lab] = int(mm.group(1)) if mm else None
        got = {k: v for k, v in rows.items() if "neton" in k}
        out["pins"] = {"values": rows,
                       "match": {k: rows.get(f"{k} neton") == v for k, v in PINS.items()},
                       "ran": all(rows.get(f"{k} neton") == v for k, v in PINS.items())}

    if "perft" in order:
        ps = phase_probes(d, "perft")
        p5 = [pr for pr in ps if pr.get("probe", "").startswith("perft 5")]
        n5 = None
        if p5:
            mm = re.search(r"nodes (\d+)", p5[0].get("node_line") or "")
            n5 = int(mm.group(1)) if mm else None
        n4 = [pr for pr in ps if pr.get("probe", "").startswith("perft4")]
        ok4 = sum(1 for pr in n4 if (pr.get("node_line") or "").startswith("nodes "))
        # A refused FEN silently searches the PREVIOUS board, so every number
        # after it describes a position nobody asked for. Any refusal in this
        # phase invalidates the phase, however clean its counts look.
        refused = [pr.get("probe") for pr in ps if pr.get("refused")]
        out["perft"] = {"perft5": n5, "perft5_match": n5 == PERFT5,
                        "perft4_probes": len(n4), "perft4_with_nodes": ok4,
                        "refused_fixtures": len(refused),
                        "refused_examples": refused[:5],
                        "ran": n5 == PERFT5 and ok4 == len(n4) and len(n4) > 0
                               and not refused}

    for ph in ("depth", "deep"):
        if ph not in order:
            continue
        ps = [pr for pr in phase_probes(d, ph) if pr.get("probe", "").startswith("depth")]
        with_nodes = [pr for pr in ps if (pr.get("last_nodes") or 0) > 0]
        zero = [pr["probe"] for pr in ps if pr.get("last_nodes") == 0]
        depths = sorted({pr.get("last_depth") for pr in ps if pr.get("last_depth")})
        out[ph] = {"probes": len(ps), "with_nodes_gt_0": len(with_nodes),
                   "zero_node_probes": len(zero), "zero_examples": zero[:5],
                   "depths_seen": depths,
                   "ran": len(ps) > 0 and len(with_nodes) == len(ps)}

    if "netoff" in order:
        ps = phase_probes(d, "netoff")
        searches = [pr for pr in ps if pr.get("probe", "").startswith("depth")]
        evals = [pr for pr in ps if pr.get("probe", "").startswith("eval")]
        out["netoff"] = {"searches": len(searches),
                         "searches_with_nodes": sum(1 for pr in searches
                                                    if (pr.get("last_nodes") or 0) > 0),
                         "eval_lines": sum(1 for pr in ps if pr.get("eval_line")),
                         "ran": len(searches) > 0 and
                                all((pr.get("last_nodes") or 0) > 0 for pr in searches)}

    if "eval" in order:
        ps = [pr for pr in phase_probes(d, "eval") if pr.get("probe", "").startswith("eval")]
        good = [pr for pr in ps if pr.get("eval_line") and
                "hce" in pr["eval_line"] and "nnue" in pr["eval_line"]]
        out["eval"] = {"probes": len(ps), "eval_lines_with_hce_and_nnue": len(good),
                       "ran": len(ps) > 0 and len(good) == len(ps)}

    if "mate" in order:
        ps = [pr for pr in phase_probes(d, "mate") if "go mate" in pr.get("probe", "")]
        answered = [pr for pr in ps if pr.get("bestmove")]
        out["mate"] = {"probes": len(ps), "answered": len(answered),
                       "ran": len(ps) > 0 and len(answered) == len(ps)}

    if "book" in order:
        ps = phase_probes(d, "book")
        books = [pr for pr in ps if pr.get("book_line")]
        out["book"] = {"probes": len(ps), "book_moves": len(books),
                       "examples": [pr["book_line"] for pr in books[:3]],
                       "ran": len(books) > 0}

    for ph in ("stress", "stress_netoff"):
        if ph not in order:
            continue
        ps = [pr for pr in phase_probes(d, ph) if pr.get("probe", "").startswith("depth")]
        with_nodes = [pr for pr in ps if (pr.get("last_nodes") or 0) > 0]
        evals = [pr for pr in phase_probes(d, ph) if pr.get("eval_line")]
        out[ph] = {"searches": len(ps), "with_nodes_gt_0": len(with_nodes),
                   "eval_lines": len(evals),
                   "ran": len(ps) > 0 and len(with_nodes) == len(ps)}

    if "malformed" in order:
        ps = [pr for pr in phase_probes(d, "malformed") if "malformed" in pr.get("probe", "")]
        replied = [pr for pr in ps if pr.get("bestmove") or pr.get("answered")]
        out["malformed"] = {"probes": len(ps), "replied_or_bounded": len(replied),
                            "ran": len(ps) > 0}

    if "protocol" in order:
        ps = [pr for pr in phase_probes(d, "protocol") if pr.get("probe", "").startswith("after")]
        with_nodes = [pr for pr in ps if (pr.get("last_nodes") or 0) > 0]
        out["protocol"] = {"probes": len(ps), "searches_with_nodes": len(with_nodes),
                           "ran": len(ps) > 0 and len(with_nodes) == len(ps)}

    return out


def main():
    d = json.load(open(sys.argv[1]))
    rep = audit(d)
    rep["_all_phases_non_vacuous"] = all(v.get("ran") for k, v in rep.items()
                                         if isinstance(v, dict))
    print(json.dumps(rep, indent=1))
    if len(sys.argv) > 2:
        json.dump(rep, open(sys.argv[2], "w"), indent=1)
    sys.exit(0 if rep["_all_phases_non_vacuous"] else 1)


if __name__ == "__main__":
    main()
