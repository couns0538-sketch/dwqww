"""Measure 3, part 2: can `AspCappedReopen`'s bound-publishing branch ever fire?

Why this needs its own argument. The switch has two break paths:

    } else if (tune::AspCappedReopen) {
        beta = capped_fail_high(iteration_score);
        if (iteration_score >= beta) break;      // <-- publishes a BOUND
    }

If that break fires, the loop exits with `iteration_score >= beta`, which means
the score is NOT strictly inside its window -- a fail-high bound promoted to a
published score with no re-search. That is the exact defect this audit is for.

The claim tested here is that the break is ARITHMETICALLY UNREACHABLE:

  capped_fail_high(x) for a non-mate, non-decisive x returns min(x + 13, INF).
  The branch is only entered when x >= beta, and beta is set to the value just
  returned, so beta == x at that moment. Then beta' = x + 13 > x, hence
  `iteration_score >= beta'` is `x >= x + 13`, which is false.
  The mate / |x| >= 640 cases return +/-Inf, which is even further away.

Two independent confirmations, because an argument with no test is a guess:

  PROOF   the source of both `capped_fail_*` helpers and the call sites, quoted.
  EMPIRICAL  a scan over the whole corpus with the switch on, at every depth
         1..14, counting how many times each exit tag occurs. `high_break` and
          `low_break` at 0 across thousands of iterations is the measurement.

Also recorded: a PLANTED FAULT run of the same trace channel, so the zero is a
real zero and not a broken counter (shared brief, rule 2 and rule 3).
"""
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from uci import Engine  # noqa: E402

EVIDENCE = pathlib.Path("/tmp/asp/evidence")
TRACE = "/tmp/asp/build-trace/forge"
FAULT = "/tmp/asp/build-fault/forge"
BASE = {"OwnBook": "false"}


def sweep(build, opts, positions, max_depth):
    exits = Counter()
    tries = Counter()
    per_position = []
    for pos in positions:
        with Engine(build, dict(BASE, **opts)) as eng:
            eng.newgame()
            eng.position(pos["fen"])
            for depth in range(1, max_depth + 1):
                res = eng.search(f"go depth {depth}")
                per_depth = {r["depth"] for r in res["info"] if r["depth"] is not None}
                if depth not in per_depth:
                    continue
                for t in res["traces"]:
                    if t.get("depth") == depth:
                        exits[t.get("exit")] += 1
                        tries[t.get("tries")] += 1
        per_position.append(pos["label"])
    return exits, tries


def main():
    corpus = json.loads((EVIDENCE / "corpus.json").read_text())
    positions = corpus["depth_positions"][:24] + corpus["mate_positions"]
    max_depth = 14

    out = {"max_depth": max_depth, "fixtures": len(positions), "runs": {}}

    for tag, build, opts in (
        ("capped_on", TRACE, {"AspCappedReopen": "true"}),
        ("capped_off", TRACE, {}),
        ("both_on", TRACE, {"AspCappedReopen": "true", "AspArmLate": "true"}),
    ):
        exits, tries = sweep(build, opts, positions, max_depth)
        out["runs"][tag] = {"exits": dict(exits), "tries": dict(tries),
                            "iterations": sum(exits.values())}
        print(f"{tag:12s} iterations={sum(exits.values()):>6}  exits={dict(exits)}")
        print(f"{'':12s} tries histogram={dict(sorted(tries.items()))}")

    # Planted control: the fault build must register `high_fault` exits. If this
    # comes back zero the trace channel is dead and the zeros above are empty.
    fault_exits, _ = sweep(FAULT, {}, positions[:12], 10)
    out["fault_control"] = {"exits": dict(fault_exits),
                            "iterations": sum(fault_exits.values())}
    print(f"{'fault control':12s} iterations={sum(fault_exits.values()):>6}  "
          f"exits={dict(fault_exits)}")

    bounded = sum(v for k, v in out["runs"]["capped_on"]["exits"].items()
                  if k in ("low_break", "high_break"))
    out["conclusion"] = {
        "bound_publishing_exits_with_switch_on": bounded,
        "fault_control_registered": out["fault_control"]["exits"].get("high_fault", 0),
    }
    (EVIDENCE / "capped_reopen_reachability.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print()
    print(f"bound-publishing exits with AspCappedReopen ON: {bounded}")
    print(f"planted-fault exits seen (control): "
          f"{out['fault_control']['exits'].get('high_fault', 0)}")


if __name__ == "__main__":
    main()
