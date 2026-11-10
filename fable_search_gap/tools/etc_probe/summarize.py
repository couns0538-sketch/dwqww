"""Summarise a TSV written by etc_probe.exe (standard library only).

For each eligibility rule and for three groups of positions (all, middlegame, endgame) it reports:

  control          PROBE node count == OFF node count (must hold: the counting does not change the tree)
  eligible share   eligible nodes as a share of all nodes
  hit rate         eligible nodes where a child table entry already proves the cutoff
  hash-move share  share of those hits where the proving child is the hash move (the plain search then
                   needs one extra node to find the same cutoff, so nothing real is saved)
  savable share    nodes the plain search spent below top-level hit nodes, as a share of all nodes:
                   a first-order upper bound on what taking the cutoff could save
  lookup cost      extra time of PROBE over OFF on the identical tree (the price of the lookups alone)
  first-order net  savable share minus lookup cost (positive = the rule can pay for itself to first order)
  realised         node and time ratio of the run that takes the cutoff versus OFF; this includes search
                   instability, so single positions swing widely

Rule names: cutN = expected cut nodes at depth >= N; allN = every non-PV node at depth >= N;
nohmN = expected cut nodes at depth >= N without a hash move.

usage: summarize.py RESULTS.tsv OUT.md
"""
import csv
import math
import sys
from collections import defaultdict


def group_of(label: str) -> str:
    base = label.rsplit("_p", 1)[0] if label.rsplit("_p", 1)[-1].isdigit() else label
    return "endgame" if base.startswith("e") or base in ("b4_rook_endgame", "b7_rook_up") else "middlegame"


def t(row) -> int:
    return int(row["us"]) if row.get("us") else int(row["ms"]) * 1000


def main():
    src, out = sys.argv[1], sys.argv[2]
    rows = defaultdict(dict)
    order = []
    with open(src, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows[r["label"]][r["run"]] = r
            if r["run"].startswith("probe_") and r["run"][6:] not in order:
                order.append(r["run"][6:])
    name = src.replace(chr(92), "/").split("/")[-1]
    lines = [f"# etc_probe summary ({name}, {len(rows)} positions)", "",
             "Replica search on unmodified lock board and evaluation sources. Not the lock's search. No Elo claim.", ""]
    aborted = [l for l, rr in rows.items() if any(int(x["aborted"]) for x in rr.values())]
    lines.append(f"Positions stopped by the node cap and left out: {len(aborted)} ({', '.join(aborted) or 'none'}).")
    lines.append("")
    if all("off_b" in rr for rr in rows.values()):
        sel = [l for l in rows if l not in aborted]
        same = sum(1 for l in sel if rows[l]["off_b"]["nodes"] == rows[l]["off"]["nodes"])
        ratio = sum(t(rows[l]["off_b"]) for l in sel) / sum(t(rows[l]["off"]) for l in sel)
        mid = [l for l in sel if group_of(l) == "middlegame"]
        end = [l for l in sel if group_of(l) == "endgame"]
        rm = sum(t(rows[l]["off_b"]) for l in mid) / max(sum(t(rows[l]["off"]) for l in mid), 1)
        re_ = sum(t(rows[l]["off_b"]) for l in end) / max(sum(t(rows[l]["off"]) for l in end), 1)
        lines.append(f"A/A control (the plain search run twice): identical node counts in {same}/{len(sel)} positions; "
                     f"time ratio second/first {ratio:.3f} overall, {rm:.3f} middlegame, {re_:.3f} endgame. "
                     "Time differences of this size are noise.")
        lines.append("")
    lines += ["## Cost and saving by rule", "",
              "| rule | group | positions | control ok | OFF nodes | eligible share | hit rate | hash-move share of hits | savable share | "
              "lookup cost | first-order net | plain search also failed high | realised node ratio (sum / geo mean [95 % range]) | realised time ratio |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for rule in order:
        for grp in ("all", "middlegame", "endgame"):
            sel = [l for l in rows if l not in aborted and (grp == "all" or group_of(l) == grp)]
            if not sel:
                continue
            off_n = sum(int(rows[l]["off"]["nodes"]) for l in sel)
            off_t = sum(t(rows[l]["off"]) for l in sel)
            pr = [rows[l][f"probe_{rule}"] for l in sel]
            control = sum(1 for l in sel if rows[l][f"probe_{rule}"]["nodes"] == rows[l]["off"]["nodes"])
            elig = sum(int(x["eligible"]) for x in pr)
            hits = sum(int(x["hits"]) for x in pr)
            hm = sum(int(x["hits_hash_move"]) for x in pr)
            top = sum(int(x["top_hits"]) for x in pr)
            sav = sum(int(x["savable_nodes"]) for x in pr)
            tfh = sum(int(x["top_hits_fail_high"]) for x in pr)
            cost = sum(t(x) for x in pr) / off_t - 1.0
            realised = "n/a"
            rtime = "n/a"
            if all(f"etc_{rule}" in rows[l] for l in sel):
                et = [rows[l][f"etc_{rule}"] for l in sel]
                logs = [math.log(int(rows[l][f"etc_{rule}"]["nodes"]) / int(rows[l]["off"]["nodes"])) for l in sel]
                mean = sum(logs) / len(logs)
                geo = math.exp(mean)
                half = 0.0
                if len(logs) > 1:
                    sd = math.sqrt(sum((x - mean) ** 2 for x in logs) / (len(logs) - 1))
                    half = 1.96 * sd / math.sqrt(len(logs))
                realised = (f"{sum(int(x['nodes']) for x in et) / off_n:.3f} / {geo:.3f} "
                            f"[{math.exp(mean - half):.3f}, {math.exp(mean + half):.3f}]")
                rtime = f"{sum(t(x) for x in et) / off_t:.3f}"
            lines.append(
                f"| {rule} | {grp} | {len(sel)} | {control}/{len(sel)} | {off_n} | {100 * elig / off_n:.2f} % | {100 * hits / max(elig, 1):.1f} % | "
                f"{100 * hm / max(hits, 1):.1f} % | {100 * sav / off_n:.2f} % | {100 * cost:+.1f} % | {100 * (sav / off_n - cost):+.1f} % | "
                f"{100 * tfh / max(top, 1):.1f} % | {realised} | {rtime} |")
    lines.append("")
    for rule in order:
        has_etc = all(f"etc_{rule}" in rr for rr in rows.values())
        lines += [f"## Per position, rule {rule}", "",
                  "| position | depth | OFF nodes | hit rate | savable share | realised node ratio | score OFF / with cutoff |", "|---|---|---|---|---|---|---|"]
        for l in rows:
            if l in aborted:
                continue
            o, p = rows[l]["off"], rows[l][f"probe_{rule}"]
            ratio = scores = "n/a"
            if has_etc:
                e = rows[l][f"etc_{rule}"]
                ratio = f"{int(e['nodes']) / int(o['nodes']):.3f}"
                scores = f"{o['score']} / {e['score']}"
            lines.append(f"| {l} | {o['depth']} | {o['nodes']} | {100 * int(p['hits']) / max(int(p['eligible']), 1):.1f} % | "
                         f"{100 * int(p['savable_nodes']) / int(o['nodes']):.2f} % | {ratio} | {scores} |")
        lines.append("")
    text = "\n".join(lines) + "\n"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("\n".join(lines[:9 + 3 * len(order)]))


if __name__ == "__main__":
    main()
