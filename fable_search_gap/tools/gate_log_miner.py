"""Count game terminations in the surviving fastchess gate logs (read-only, standard library only).

For every *.log under ROOT that has "Finished game" lines it records, per gate:
  games, mates, draws by 3-fold repetition / fifty moves / insufficient material / stalemate,
  losses on time and other abnormal endings, split by which side (candidate or base) they hit,
  plus the time control, thread count, hash and book that fastchess printed.

The gate PGNs no longer exist, so this is the finest game-level view left. It cannot see scores or moves.

usage: gate_log_miner.py ROOT OUT_TSV
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

FIN = re.compile(r"Finished game (\d+) \((.+?) vs (.+?)\): (\S+) \{(.+?)\}")
RES = re.compile(r"Results of (.+?) vs (.+?) \((.+?)\):")
KINDS = ["mate", "rep3", "fifty", "insufficient", "stalemate", "time", "illegal", "disconnect", "adjudication", "other"]


def classify(reason: str) -> str:
    r = reason.lower()
    if "mates" in r:
        return "mate"
    if "3-fold" in r or "repetition" in r:
        return "rep3"
    if "fifty" in r:
        return "fifty"
    if "insufficient" in r:
        return "insufficient"
    if "stalemate" in r:
        return "stalemate"
    if "time" in r:
        return "time"
    if "illegal" in r:
        return "illegal"
    if "disconnect" in r or "stall" in r or "crash" in r:
        return "disconnect"
    if "adjudication" in r:
        return "adjudication"
    return "other"


def loser(white: str, black: str, result: str):
    if result == "1-0":
        return black
    if result == "0-1":
        return white
    return None


def main():
    root, out = sys.argv[1], sys.argv[2]
    print(pinguard.ensure(), flush=True)
    rows = []
    total = Counter()
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.endswith(".log"):
                continue
            path = os.path.join(dirpath, name)
            kinds = Counter()
            time_loser = Counter()
            other_reasons = Counter()
            games = 0
            setup = ""
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        m = FIN.search(line)
                        if m:
                            games += 1
                            white, black, result, reason = m.group(2), m.group(3), m.group(4), m.group(5)
                            kind = classify(reason)
                            kinds[kind] += 1
                            if kind == "time":
                                who = loser(white, black, result)
                                time_loser["cand" if who and who.startswith("cand") else "base" if who else "?"] += 1
                            if kind == "other":
                                other_reasons[reason] += 1
                            continue
                        m = RES.search(line)
                        if m:
                            setup = m.group(3)
            except OSError as exc:
                print(f"skip {path}: {exc}", flush=True)
                continue
            if games == 0:
                continue
            total.update(kinds)
            total["games"] += games
            rows.append([os.path.basename(dirpath), games] + [kinds[k] for k in KINDS] +
                        [time_loser["cand"], time_loser["base"], setup,
                         "; ".join(f"{k} x{v}" for k, v in other_reasons.most_common(3))])
    rows.sort(key=lambda r: r[0])
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("gate\tgames\t" + "\t".join(KINDS) + "\ttime_loss_cand\ttime_loss_base\tsetup\tother_reasons\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    g = total["games"]
    print(f"logs with games: {len(rows)}; games: {g}", flush=True)
    for k in KINDS:
        if total[k]:
            print(f"  {k:13s} {total[k]:7d}  {100.0 * total[k] / g:5.1f} %", flush=True)
    draws = total["rep3"] + total["fifty"] + total["insufficient"] + total["stalemate"]
    if draws:
        print(f"  draws {draws} = {100.0 * draws / g:.1f} % of games; 3-fold share of draws {100.0 * total['rep3'] / draws:.1f} %",
              flush=True)


if __name__ == "__main__":
    main()
