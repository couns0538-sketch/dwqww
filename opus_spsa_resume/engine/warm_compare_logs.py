"""warm_compare_logs.py - offline re-comparison of the transcripts saved by warm_identity_0xF000.py, for a candidate
that advertises extra UCI options (the gate build adds RazorTune and QsTune). No engine is started.

usage: python -I -B warm_compare_logs.py <warm out dir> [--allow-extra "<exact option line>" ...] [--json <out.json>]

The comparison uses the tool's own normalisation (`norm`, imported from warm_identity_0xF000.py): nps and time are
removed from info and bench lines, and id lines are dropped. From the candidate transcript it then removes exactly
the allowed extra lines. Each must occur exactly once in the candidate and never in the reference, and must sit
between the `> uci` line and `uciok`. Everything else must be identical line by line. That includes every
`go nodes` search, the state-change cycle and the final `bench 13`, which must equal the pin 862329 on both.
Exit 0 = identical apart from the allowed lines, 3 = a difference, 1 = error."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from warm_identity_0xF000 import norm  # noqa: E402  (QA's normalisation, unchanged in the derived copy)

PIN = "862329"


def load(p):
    return Path(p).read_text(encoding="utf-8").splitlines()


def main(argv):
    a = argv[1:]
    allow, jout = [], None
    while "--allow-extra" in a:
        i = a.index("--allow-extra")
        allow.append(a[i + 1])
        del a[i:i + 2]
    if "--json" in a:
        i = a.index("--json")
        jout = a[i + 1]
        del a[i:i + 2]
    if len(a) != 1:
        print(__doc__)
        return 1
    d = Path(a[0])
    r, c = norm(load(d / "ref.log")), norm(load(d / "cand.log"))
    res = {"dir": str(d), "ref_lines": len(r), "cand_lines": len(c), "allowed_extra": allow, "removed": []}
    for line in allow:
        if r.count(line) != 0 or c.count(line) != 1:
            res["error"] = f"allowed line must occur once in the candidate and never in the reference: {line!r}"
            print(json.dumps(res, indent=1))
            return 1
        i = c.index(line)
        u0 = max(k for k in range(i) if c[k] == "> uci")
        u1 = next(k for k in range(i, len(c)) if c[k] == "uciok")
        if not u0 < i < u1:
            res["error"] = f"allowed line outside the uci reply: {line!r}"
            print(json.dumps(res, indent=1))
            return 1
        res["removed"].append({"line": line, "cand_index": i})
        del c[i]
    diff = next((i for i, (x, y) in enumerate(zip(r, c)) if x != y), None)
    if diff is None and len(r) != len(c):
        diff = min(len(r), len(c))
    benches = [s for s in r if "bench depth 13" in s], [s for s in c if "bench depth 13" in s]
    bench_ok = bool(benches[0]) and bool(benches[1]) and all(f"nodes {PIN}" in s for s in benches[0][-1:] + benches[1][-1:])
    res.update({"searches": sum(1 for s in r if s.startswith("bestmove")),
                "setoption_lines": sum(1 for s in r if s.startswith("> setoption name")),
                "first_difference": None if diff is None else {
                    "line": diff, "ref": r[diff] if diff < len(r) else "<end>",
                    "cand": c[diff] if diff < len(c) else "<end>"},
                "final_bench13": [benches[0][-1:], benches[1][-1:]], "bench13_pin_both": bench_ok})
    res["identical_apart_from_allowed"] = diff is None and bench_ok
    text = json.dumps(res, indent=1)
    if jout:
        Path(jout).write_text(text + "\n", encoding="ascii")
    print(text)
    return 0 if res["identical_apart_from_allowed"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
