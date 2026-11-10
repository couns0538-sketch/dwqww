"""Summarise a TSV written by etc_probe.exe (standard library only).

usage: summarize.py RESULTS.tsv OUT.md [POSITIONS.epd]

With POSITIONS.epd the summary also (a) drops positions whose board repeats an earlier line of that
file and (b) can group positions by material.

Vocabulary used in the output
  plain            the search as written (run "off")
  counting         the same tree; child table entries are looked up and only counted (runs "probe_*")
  cutoff taken     the mechanism is applied (runs "etc_*"); "_ns" = no table store at the node,
                   "_fh" = return beta instead of the child's bound
  placebo          the plain search with one history constant changed by 1 (run "off_p"): how far node
                   counts and best moves move under a change that is not a mechanism
  rule cutN        expected cut nodes with at least N plies left; allN = every non-PV node;
                   nohmN = cut nodes without a hash move
  eligible share   eligible nodes / all plain nodes
  hit rate         eligible nodes where some child entry already proves the cutoff
  first proof is the hash move   share of hits where the first proving child found (in move-generation
                   order) is the hash move; a lower bound on "the hash move also proves it"
  below-hit share  nodes the plain search spent below outermost hit nodes / all plain nodes. A first-order
                   estimate of the saving, NOT a ceiling: taking the cutoff also changes later table
                   contents, so the realised change can be larger or smaller
  lookup time      time of the counting run / time of the plain run - 1, on the identical tree
  node ratio       nodes with the cutoff taken / plain nodes. "sum" = ratio of totals; "geo" = geometric
                   mean over positions; "by position" = 95 % range treating positions as independent;
                   "by base" = 95 % range over base positions (a base and the positions generated from
                   it form one cluster), which is the honest one. It is centred on the mean of the base
                   means, which differs slightly from "geo" when bases have unequal numbers of positions.
                   All ranges use the normal factor 1.96. With few clusters a t factor would be wider:
                   by 6 to 15 % for 10 to 24 clusters, by about 3 % for 48
  best move differs  positions where the final best move is not the plain run's
  score moves by 50 or more   positions where the final score differs from the plain run's by at least
                   50 of the evaluation's units (about half a pawn)
  time ratio       wall time against the plain run. The machine is loaded and the runs are at Idle
                   priority: two runs of the identical tree have differed by tens of percent, so this
                   column is indicative only and no claim rests on it

Groups: for labels starting b/m/e + digit (the hand-made sets) "endgame" = labels e*, b4, b7 and their
continuations. For any other label "low material" = at most six knights, bishops, rooks and queens in all.
"""
import csv
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pinguard  # noqa: E402


def base_of(label: str) -> str:
    head, sep, tail = label.rpartition("_p")
    return head if sep and tail.isdigit() else label


def pieces(fen: str) -> int:
    return sum(1 for c in fen.split()[0] if c in "nbrqNBRQ")


def group_of(label: str, fen) -> str:
    base = base_of(label)
    if len(base) > 1 and base[0] in "bme" and base[1].isdigit():
        return "endgame" if base.startswith("e") or base in ("b4_rook_endgame", "b7_rook_up") else "middlegame"
    if fen is None:
        return "all"
    return "endgame" if pieces(fen) <= 6 else "middlegame"


def t(row) -> int:
    return int(row["us"]) if row.get("us") else int(row["ms"]) * 1000


def mean_range(values):
    n = len(values)
    mean = sum(values) / n
    if n < 2:
        return mean, mean, mean
    sd = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return mean, mean - half, mean + half


def main():
    pinguard.ensure()
    src, out = sys.argv[1], sys.argv[2]
    epd = sys.argv[3] if len(sys.argv) > 3 else None
    fens, dup = {}, set()
    if epd:
        seen = {}
        with open(epd, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [x.strip() for x in line.split(";")]
                board = " ".join(parts[0].split()[:4])
                fens[parts[2]] = parts[0]
                if board in seen:
                    dup.add(parts[2])
                else:
                    seen[board] = parts[2]
    rows = defaultdict(dict)
    probes, etcs = [], []
    with open(src, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows[r["label"]][r["run"]] = r
            if r["run"].startswith("probe_") and r["run"] not in probes:
                probes.append(r["run"])
            if (r["run"].startswith("etc_") or r["run"] == "off_p") and r["run"] not in etcs:
                etcs.append(r["run"])
    name = src.replace(chr(92), "/").split("/")[-1]
    aborted = {l for l, rr in rows.items() if any(int(x["aborted"]) for x in rr.values())}
    use = [l for l in rows if l not in aborted and l not in dup]
    groups = ["all"] + sorted({group_of(l, fens.get(l)) for l in use} - {"all"})
    sel_of = {g: [l for l in use if g == "all" or group_of(l, fens.get(l)) == g] for g in groups}
    bases = {l: base_of(l) for l in use}

    lines = [f"# etc_probe summary: {name}", "",
             "Replica search on unmodified lock board and evaluation sources. Not the lock's search. No Elo claim.",
             "Terms are defined at the top of `tools/etc_probe/summarize.py`.", "",
             f"Positions in the file: {len(rows)}. Left out: {len(aborted)} stopped by the node cap, "
             f"{len(dup - aborted)} with a board that repeats an earlier position. Used: {len(use)}, "
             f"from {len(set(bases.values()))} base positions.", ""]
    for g in groups[1:]:
        lines.append(f"- {g}: {len(sel_of[g])} positions from {len({bases[l] for l in sel_of[g]})} bases")
    lines.append("")
    if all("off_b" in rows[l] for l in use):
        same = sum(1 for l in use if rows[l]["off_b"]["nodes"] == rows[l]["off"]["nodes"])
        per = [t(rows[l]["off_b"]) / t(rows[l]["off"]) for l in use]
        m, _lo, _hi = mean_range(per)
        sd = math.sqrt(sum((x - m) ** 2 for x in per) / max(len(per) - 1, 1))
        tot = sum(t(rows[l]["off_b"]) for l in use) / sum(t(rows[l]["off"]) for l in use)
        lines += [f"Plain run repeated: identical node counts in {same}/{len(use)} positions; time ratio of the totals "
                  f"{tot:.4f}; per position the time ratio has standard deviation {100 * sd:.1f} %.", ""]

    if probes:
        lines += ["## Counting runs (identical tree)", "",
                  "| rule | group | positions | same nodes as plain | plain nodes | eligible share | hit rate | "
                  "first proof is the hash move | below-hit share | lookup time | plain search also failed high |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for run in probes:
            for g in groups:
                sel = [l for l in sel_of[g] if run in rows[l]]
                if not sel:
                    continue
                off_n = sum(int(rows[l]["off"]["nodes"]) for l in sel)
                off_t = sum(t(rows[l]["off"]) for l in sel)
                pr = [rows[l][run] for l in sel]
                control = sum(1 for l in sel if rows[l][run]["nodes"] == rows[l]["off"]["nodes"])
                elig = sum(int(x["eligible"]) for x in pr)
                hits = sum(int(x["hits"]) for x in pr)
                hm = sum(int(x["hits_hash_move"]) for x in pr)
                top = sum(int(x["top_hits"]) for x in pr)
                sav = sum(int(x["savable_nodes"]) for x in pr)
                tfh = sum(int(x["top_hits_fail_high"]) for x in pr)
                cost = sum(t(x) for x in pr) / off_t - 1.0
                lines.append(f"| {run[6:]} | {g} | {len(sel)} | {control}/{len(sel)} | {off_n} | {100 * elig / off_n:.2f} % | "
                             f"{100 * hits / max(elig, 1):.1f} % | {100 * hm / max(hits, 1):.1f} % | {100 * sav / off_n:.2f} % | "
                             f"{100 * cost:+.1f} % | {100 * tfh / max(top, 1):.1f} % |")
        lines.append("")

    if etcs:
        lines += ["## Runs that change the search (cutoff taken, variants, placebo)", "",
                  "| run | group | positions | node ratio sum | node ratio geo | 95 % range by position | 95 % range by base | "
                  "geo without the 2 smallest ratios | smallest / largest ratio | time ratio | best move differs | "
                  "score moves by 50 or more |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for run in etcs:
            for g in groups:
                sel = [l for l in sel_of[g] if run in rows[l]]
                if not sel:
                    continue
                off_n = sum(int(rows[l]["off"]["nodes"]) for l in sel)
                off_t = sum(t(rows[l]["off"]) for l in sel)
                ratios = {l: int(rows[l][run]["nodes"]) / int(rows[l]["off"]["nodes"]) for l in sel}
                logs = [math.log(v) for v in ratios.values()]
                m, lo, hi = mean_range(logs)
                by_base = defaultdict(list)
                for l in sel:
                    by_base[bases[l]].append(math.log(ratios[l]))
                _cm, clo, chi = mean_range([sum(v) / len(v) for v in by_base.values()])
                trimmed = sorted(logs)[2:] if len(logs) > 4 else logs
                diff = sum(1 for l in sel if rows[l][run]["best"] != rows[l]["off"]["best"])
                moved = sum(1 for l in sel if abs(int(rows[l][run]["score"]) - int(rows[l]["off"]["score"])) >= 50)
                lines.append(
                    f"| {run} | {g} | {len(sel)} | {sum(int(rows[l][run]['nodes']) for l in sel) / off_n:.3f} | {math.exp(m):.3f} | "
                    f"[{math.exp(lo):.3f}, {math.exp(hi):.3f}] | [{math.exp(clo):.3f}, {math.exp(chi):.3f}] | "
                    f"{math.exp(sum(trimmed) / len(trimmed)):.3f} | {min(ratios.values()):.3f} / {max(ratios.values()):.3f} | "
                    f"{sum(t(rows[l][run]) for l in sel) / off_t:.3f} | {diff}/{len(sel)} | {moved}/{len(sel)} |")
        lines.append("")
        lines += ["## Base positions against the positions generated from them", "",
                  "| run | bases: positions | bases: node ratio geo | generated: positions | generated: node ratio geo |",
                  "|---|---|---|---|---|"]
        for run in etcs:
            sel = [l for l in use if run in rows[l]]
            parts = []
            for want_base in (True, False):
                part = [math.log(int(rows[l][run]["nodes"]) / int(rows[l]["off"]["nodes"]))
                        for l in sel if (bases[l] == l) == want_base]
                parts.append((len(part), math.exp(sum(part) / len(part)) if part else float("nan")))
            lines.append(f"| {run} | {parts[0][0]} | {parts[0][1]:.3f} | {parts[1][0]} | {parts[1][1]:.3f} |")
        lines.append("")
        if "off_p" in etcs:
            lines += ["## Each run against the placebo, position by position", "",
                      "Node count of the run divided by the node count of the placebo run on the same position.", "",
                      "| run | group | positions | geo | 95 % range by base |",
                      "|---|---|---|---|---|"]
            for run in etcs:
                if run == "off_p":
                    continue
                for g in groups:
                    sel = [l for l in sel_of[g] if run in rows[l] and "off_p" in rows[l]]
                    if not sel:
                        continue
                    logs = []
                    by_base = defaultdict(list)
                    for l in sel:
                        v = math.log(int(rows[l][run]["nodes"]) / int(rows[l]["off_p"]["nodes"]))
                        logs.append(v)
                        by_base[bases[l]].append(v)
                    _cm, clo, chi = mean_range([sum(v) / len(v) for v in by_base.values()])
                    lines.append(f"| {run} | {g} | {len(sel)} | {math.exp(sum(logs) / len(logs)):.3f} | "
                                 f"[{math.exp(clo):.3f}, {math.exp(chi):.3f}] |")
            lines.append("")
    text = "\n".join(lines) + "\n"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
