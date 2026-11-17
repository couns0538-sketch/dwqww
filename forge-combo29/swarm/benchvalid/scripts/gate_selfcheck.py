#!/usr/bin/env python3
"""Every gate check must be shown to fire on a planted fault (brief rule 3).

For each check in gate.py, this plants one specific source change that MUST make that
check fail and the others pass, then runs the whole gate. A check that stays green on
its own fault is a check that cannot fail, and it is reported as BROKEN.

G1 pins        : change a search constant (already proven by sensitivity.py; re-run here)
G2 drawn root  : make the bail unconditional on every root with insufficient material
G3 book        : OwnBook default false
G4 clock       : Move Overhead default 10 -> 4000 ms (the search eats its own clock)
G5 threads     : pin the searcher to one worker regardless of the option
G6 order       : clear the hash before every UCI search, which is exactly what removes
                 the order dependence the check documents
G7 leaf        : move the fifty-move leaf rule one ply
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import sensitivity as S  # noqa: E402
import gate as G  # noqa: E402


def sub(path, old, new, n=1):
    t = path.read_text()
    if t.count(old) != n:
        raise SystemExit(f"{old[:60]!r} appears {t.count(old)}x in {path.name}, expected {n}")
    path.write_text(t.replace(old, new))


def p_g1(root):
    sub(root / "forge-combo29/src/search.cpp", "int LmrQuietBase = 85;", "int LmrQuietBase = 125;")


def p_g2(root):
    sub(root / "forge-combo29/src/search.cpp",
        "if (!root_candidates.empty()) result.best_move = root_candidates.front();",
        "if (!root_candidates.empty()) result.best_move = root_candidates.front();\n"
        "        result.nodes = 0;  // plant: report the bail as unsearched")


def p_g3(root):
    sub(root / "forge-combo29/src/uci.cpp",
        "bool own_book = forge::book::embedded_available();", "bool own_book = false;")


def p_g4(root):
    sub(root / "forge-combo29/src/uci.cpp", "int move_overhead_ms = 10;", "int move_overhead_ms = 4000;")


def p_g5(root):
    sub(root / "forge-combo29/include/forge/search.hpp",
        "explicit Searcher(std::size_t hash_mb = 32, int threads = 1);",
        "explicit Searcher(std::size_t hash_mb = 32, int threads = 1);  // audit plant below")
    p = root / "forge-combo29/src/search.cpp"
    t = p.read_text()
    old = "void Searcher::set_threads(int threads) {"
    if old not in t:
        raise SystemExit("set_threads not found")
    p.write_text(t.replace(old, "void Searcher::set_threads(int threads) {\n    (void)threads; threads = 1;  // plant"))


def p_g6(root):
    # Make a UCI search start from a cleared table, the way bench does. G6 asserts the
    # base's order dependence, so removing it must fail the check.
    p = root / "forge-combo29/src/uci.cpp"
    t = p.read_text()
    old = "                const forge::Board search_board = board;"
    if t.count(old) != 1:
        raise SystemExit("search dispatch anchor not found")
    p.write_text(t.replace(old, "                searcher.clear();  // plant: bench-like clear\n" + old))


def p_g7(root):
    p = root / "forge-combo29/src/search.cpp"
    t = p.read_text()
    m = re.search(r"halfmove_clock\(\) >= (\d+)", t)
    if not m:
        raise SystemExit("halfmove rule not found")
    p.write_text(t.replace(m.group(0), f"halfmove_clock() >= {int(m.group(1)) - 1}", 1))


PLANTS = {
    "G1": ("LmrQuietBase 85 -> 125", p_g1),
    "G2": ("drawn root reports nodes = 0", p_g2),
    "G3": ("OwnBook default false", p_g3),
    "G4": ("Move Overhead default 4000 ms", p_g4),
    "G5": ("set_threads forces 1", p_g5),
    "G6": ("a UCI search clears the table first", p_g6),
    "G7": ("fifty-move leaf rule one ply early", p_g7),
}


def main() -> None:
    only = sys.argv[1:] or None
    base = G.gate(str(S.BUILD))
    results = []
    for cid, (desc, fn) in PLANTS.items():
        if only and cid not in only:
            continue
        root = S.fresh("plant_" + cid)
        fn(root)
        try:
            exe = S.build(root, "plant_" + cid)
        except Exception as exc:
            msg = getattr(exc, "stderr", b"")
            msg = msg.decode()[-600:] if isinstance(msg, bytes) else str(exc)[-600:]
            results.append({"check": cid, "plant": desc, "error": "build failed", "tail": msg})
            print(f"{cid}: BUILD FAILED"); continue
        r = G.gate(str(exe))
        by_id = {c["id"]: c for c in r["checks"]}
        # Collateral is measured against the BASE's pass set, not against
        # "everything that is red". G2 is red on the base by design (the bail),
        # so counting it as collateral on every plant would hide a real
        # regression and, worse, would let a broken check look explained.
        base_failing = {c["id"] for c in base["checks"] if not c["pass"]}
        fired = [c for c in r["checks"] if not c["pass"] and c["id"] not in base_failing]
        results.append({"check": cid, "plant": desc,
                        "target_failed": not by_id[cid]["pass"],
                        "also_failed": [c["id"] for c in fired if c["id"] != cid],
                        "passing_checks": [c["id"] for c in r["checks"] if c["pass"]],
                        "detail": by_id[cid]["detail"],
                        "base_failing": sorted(base_failing),
                        "verdict": "fired-cleanly" if (not by_id[cid]["pass"] and
                                                       not [c for c in fired if c["id"] != cid])
                        else ("fired-with-collateral" if not by_id[cid]["pass"] else "BROKEN-does-not-fire")})
        print(f"{cid}: target_failed={results[-1]['target_failed']} "
              f"also_failed={results[-1]['also_failed']} -> {results[-1]['verdict']}", flush=True)
    print(json.dumps({"base_all_pass": base["all_pass"], "results": results}, indent=2, default=str))


if __name__ == "__main__":
    main()
