r"""work_counters.py - what each switch removes, counted exactly (no timing involved).

Every lock-recipe build has an instrumented first stage that runs the frozen workload (bench 11, 13, 16: the
same node counts in every build, because all builds are node-identical). Its profile holds an exact entry
counter per source function and a counter per source region. This tool reads those profiles for the control
rebuild of the lock source and for every switch-1 build and prints the counters the patches aim at.

Counters are work, not time: fewer calls of a cheap function may be worth less than they look, and a counter
says nothing about cache or layout effects. They are exact and repeatable, which timing on a shared CPU is not.

usage: work_counters.py OUT_DIR [MARKDOWN_OUT] [TSV_OUT]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402
import spd_counters  # noqa: E402

BUILDS = [("lock (control rebuild)", "c29ctl"), ("WITNESS_NOPIN", "wit_on"), ("EVADE_LEGAL", "evd_on"),
          ("PAWN_CAPMASK", "cap_on"), ("CHECKERS_KL", "chk_on"), ("KING_PAWN_CACHE", "kpc_on"),
          ("BUNDLE4", "bn4_on"), ("BUNDLE", "bun_on")]
# label, regex on the demangled name (all matches are summed), region index (None = entry count)
ROWS = [
    ("Searches entered (`Worker::search`), unchanged by design", r"^Worker::search\(Board&, SearchStack\*", None),
    ("Quiescence searches entered (`Worker::qsearch`), unchanged by design", r"^Worker::qsearch\(", None),
    ("`make_move` calls, unchanged by design", r"^Board::make_move\(", None),
    ("King-line builds (`refresh_king_lines`)", r"^Board::refresh_king_lines\(", None),
    ("`is_legal` calls", r"^Board::is_legal\(", None),
    ("Full king-attack tests (`square_attacked_with_occupancy`)", r"^Board::square_attacked_with_occupancy\(", None),
    ("`attackers_to` calls", r"^Board::attackers_to\(int, unsigned long long\)", None),
    ("Pawn-capture loop iterations (generator, region 7)", r"^Board::generate_pseudo_legal\(MoveList&, Board::GenMode\) const$", 7),
    ("Pawn captures emitted (generator, region 8), unchanged by design", r"^Board::generate_pseudo_legal\(MoveList&, Board::GenMode\) const$", 8),
    ("Shelter, storm and open-file terms added (`evaluate_king` lambda, both colours)",
     r"evaluate_king<false, \(Color\)[01]>\(.*\)::'lambda'\(int\)::operator\(\)\(int\) const$", None),
]


def profile_of(out: str, tag: str):
    d = os.path.join(out, "build", tag, "m2gen")
    if not os.path.isdir(d):
        return None
    files = [f for f in os.listdir(d) if f.endswith(".profdata")]
    return os.path.join(d, files[0]) if len(files) == 1 else None


def table(out: str):
    """(markdown lines, tsv lines)."""
    cols = []
    for label, tag in BUILDS:
        p = profile_of(out, tag)
        cols.append((label, tag, spd_counters.load(p) if p else None))
    md = ["| Counter over the frozen workload (bench 11, 13, 16) | " + " | ".join(c[0] for c in cols) + " |",
          "|---|" + "---|" * len(cols)]
    tsv = ["counter\t" + "\t".join(c[1] for c in cols)]
    for label, rx, region in ROWS:
        r = re.compile(rx)
        cells, raw = [], []
        base = None
        for _label, _tag, funcs in cols:
            if funcs is None:
                cells.append("not built")
                raw.append("")
                continue
            hits = [f for f in funcs if r.search(f["name"])]
            if not hits or (region is not None and any(len(f["counts"]) <= region for f in hits)):
                cells.append("counter not found")
                raw.append("")
                continue
            v = sum(f["entry"] if region is None else f["counts"][region] for f in hits)
            raw.append(str(v))
            if base is None:
                base = v
                cells.append(f"{v:,}")
            elif v == base:
                cells.append("same")
            else:
                cells.append(f"{v:,} ({100.0 * (v - base) / base:+.1f} %)" if base else f"{v:,}")
        md.append(f"| {label} | " + " | ".join(cells) + " |")
        tsv.append(label.replace("`", "") + "\t" + "\t".join(raw))
    return md, tsv


def main() -> int:
    out = sys.argv[1]
    print(pinguard.ensure(), flush=True)
    md, tsv = table(out)
    text = "\n".join(md) + "\n"
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(tsv) + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
