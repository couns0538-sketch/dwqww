"""Summarise the crew's gate verdict table FORGE_RESULTS.csv (read-only, standard library only).

Prints and writes: verdict classes, what kind of candidate each row tested, the base label by
recording date, every NOT CLEAN row, capped runs that came close, and options that were gated
more than once with their spread. Nothing here is an Elo claim; it is a reading aid for the table.

usage: gate_table_summary.py FORGE_RESULTS.csv OUT_MD
"""
import csv
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402


def cls(verdict: str) -> str:
    if "NOT CLEAN" in verdict:
        return "NOT_CLEAN"
    if "TRIAL-ONLY" in verdict:
        return "TRIAL_ONLY"
    if "NON-REGRESSION" in verdict:
        return "H1_NONREG"
    if verdict.startswith("H1"):
        return "H1"
    if "H0-early" in verdict:
        return "H0_EARLY"
    if verdict.startswith("H0"):
        return "H0"
    if verdict.startswith("Cap"):
        return "CAP"
    return "OTHER"


def kind(row) -> str:
    opts = row["cand_options"]
    if "EvalFile" in opts:
        return "net file"
    if opts:
        return "option line"
    return "exe only (net or build)"


def main():
    src, out = sys.argv[1], sys.argv[2]
    pinguard.ensure()
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    lines = [f"# Gate table summary ({len(rows)} rows of {os.path.basename(src)})", ""]

    c = Counter(cls(r["verdict"]) for r in rows)
    lines += ["## Verdict classes", "", "| class | rows |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in c.most_common()]

    kc = Counter((kind(r), cls(r["verdict"])) for r in rows)
    lines += ["", "## Candidate kind by class", "", "| kind | class | rows |", "|---|---|---|"]
    lines += [f"| {k[0]} | {k[1]} | {v} |" for k, v in sorted(kc.items())]

    bc = Counter((r["base"], r["recorded_pc"][:10]) for r in rows)
    lines += ["", "## Base label by recording date", "", "| base label | recorded | rows |", "|---|---|---|"]
    lines += [f"| {k[0]} | {k[1]} | {v} |" for k, v in sorted(bc.items(), key=lambda kv: kv[0][1])]

    lines += ["", "## NOT CLEAN rows", "", "| gate | games | time losses | Elo | LLR | recorded | options |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["clean"] != "CLEAN":
            lines.append(f"| {r['gate']} | {r['games']} | {r['time_losses']} | {r['elo']} | {r['llr']} | {r['recorded_pc']} | {r['cand_options'][:70]} |")

    lines += ["", "## Capped runs with LLR at or above 1.5", "", "| gate | games | Elo | nElo | LLR | candidate / options |", "|---|---|---|---|---|---|"]
    for r in rows:
        if cls(r["verdict"]) == "CAP" and float(r["llr"]) >= 1.5:
            lines.append(f"| {r['gate']} | {r['games']} | {r['elo']} | {r['nelo']} | {r['llr']} | {(r['cand_options'] or r['candidate'])[:80]} |")

    rep = defaultdict(list)
    for r in rows:
        rep[(r["cand_exe"], r["cand_options"])].append(r)
    lines += ["", "## Same exe and option line gated more than once", "", "| candidate | runs: gate (games, Elo, class) |", "|---|---|"]
    for (exe, opts), rs in rep.items():
        if len(rs) > 1:
            runs = "; ".join(f"{r['gate']} ({r['games']}, {r['elo']}, {cls(r['verdict'])})" for r in rs)
            lines.append(f"| {(opts or exe)[:70]} | {runs} |")

    total_games = sum(int(r["games"]) for r in rows)
    tl = sum(int(r["time_losses"] or 0) for r in rows)
    lines += ["", f"Total games in the table: {total_games}. Total time losses: {tl}.", ""]
    text = "\n".join(lines) + "\n"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
