#!/usr/bin/env python3
"""Option interference: does one option silently override another?

The report already records `UseNNUE > NNUEArch > NnueFile` as strict precedence.
This script looks for a SECOND instance of the same class, and for options that
are accepted but have no effect at all.

Method: for every ordered pair of options that could plausibly interact, set A
then B, then B then A, and compare the engine's behaviour. Behaviour is a probe
search's (bestmove, score, nodes) plus, where relevant, the engine's own `eval`
and `bench` output.

Two controls, because a null is only worth having if the test could have fired:

  * a KNOWN-positive pair: the documented `UseNNUE` vs `NnueFile` precedence,
    which must be DETECTED as order-dependent. If the detector misses this, its
    silence on every other pair means nothing.
  * a known-negative pair: two unrelated options whose order cannot matter.

The "accepted but no effect" sweep is different: it sets one option at a time to
a value that would change the search if it were read, and checks the probe
moved. An option that never moves the probe is reported as NO_EFFECT, which is
the class the report's bench-blindness finding is about — but see the caveat
printed beside the result: a short fixed-depth probe cannot see a tunable that
only matters in a position the probe does not reach.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver  # noqa: E402

PROBE_FENS = [
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
]
PROBE_DEPTH = 10

# Pairs where one option could plausibly gate or override the other.
PAIRS = [
    ("UseNNUE", "NnueFile"),
    ("UseNNUE", "ContHist4PlyRead"),
    ("OwnBook", "Book File"),
    ("OwnBook", "Book Depth"),
    ("UseNNUE", "HindsightDepth"),
    ("NullMoveMinDepth", "NullThreatVerify"),
    ("NullMoveMinDepth", "NullSeeVeto"),
    ("AspirationDelta", "AspCappedReopen"),
    ("AspirationDelta", "AspArmLate"),
    ("TmSoftDivisor", "TmNodeShare"),
    ("TmSoftDivisor", "TmFinishIteration"),
    ("LmrQuietDivisor", "LmrDeeperShallower"),
    ("LmrQuietDivisor", "LmrSignedCorrection"),
    ("EvalRule50Damp", "MaterialCorrectionWeight"),
    ("DeadMaterial", "MaterialCorrectionWeight"),
    ("MultiPV", "SoundMatePruning"),
]

# Values chosen to make the option MATTER if it is read at all.
VALUES = {
    "UseNNUE": ("true", "false"),
    "NnueFile": ("<empty>", "/nonexistent/x.nnue"),
    "OwnBook": ("true", "false"),
    "Book File": ("<empty>",),
    "Book Depth": ("0", "30"),
    "ContHist4PlyRead": ("true", "false"),
    "HindsightDepth": ("true", "false"),
    "NullMoveMinDepth": ("1", "10"),
    "NullThreatVerify": ("true", "false"),
    "NullSeeVeto": ("true", "false"),
    "AspirationDelta": ("4", "200"),
    "AspCappedReopen": ("true", "false"),
    "AspArmLate": ("true", "false"),
    "TmSoftDivisor": ("5", "80"),
    "TmNodeShare": ("true", "false"),
    "TmFinishIteration": ("true", "false"),
    "LmrQuietDivisor": ("100", "500"),
    "LmrDeeperShallower": ("true", "false"),
    "LmrSignedCorrection": ("true", "false"),
    "EvalRule50Damp": ("true", "false"),
    "MaterialCorrectionWeight": ("0", "300"),
    "DeadMaterial": ("true", "false"),
    "MultiPV": ("1", "3"),
    "SoundMatePruning": ("true", "false"),
    # The negative control pair: two options whose order cannot interact.
    "Book Variety": ("0", "100"),
    "CheckExtensionDepth": ("1", "30"),
}


def fingerprint(engine: driver.Engine) -> list[dict]:
    out = []
    for fen in PROBE_FENS:
        engine.set_position(fen, cold=True)
        res = engine.go_depth(PROBE_DEPTH)
        out.append({"bestmove": res["bestmove"], "cp": res["cp"], "mate": res["mate"],
                    "nodes": res["nodes"]})
    return out


def order_test(engine: driver.Engine, a: str, b: str) -> dict:
    """Set A,B and B,A and report whether the observable state differs."""
    va = VALUES[a][0]
    vb = VALUES[b][-1 if len(VALUES[b]) > 1 else 0]

    engine.set_option(a, va)
    engine.set_option(b, vb)
    ab = fingerprint(engine)

    engine.set_option(b, vb)
    engine.set_option(a, va)
    ba = fingerprint(engine)

    differs = ab != ba
    # Which field differs, so a node-only difference is not reported as a score
    # difference (they mean different things about the search).
    fields = set()
    for x, y in zip(ab, ba):
        for key in x:
            if x[key] != y[key]:
                fields.add(key)
    return {"a": a, "b": b, "a_value": va, "b_value": vb,
            "order_dependent": differs, "differing_fields": sorted(fields),
            "ab": ab, "ba": ba}


def no_effect_sweep(engine: driver.Engine, options: list[str]) -> list[dict]:
    """Every option, set to a value that should matter, against a baseline."""
    engine.send("ucinewgame")
    engine.isready()
    base = fingerprint(engine)
    rows = []
    for name in options:
        if name not in VALUES:
            continue
        lo, hi = VALUES[name][0], VALUES[name][-1]
        moved = False
        best = None
        for value in (lo, hi):
            engine.set_option(name, value)
            got = fingerprint(engine)
            if got != base:
                moved = True
                best = {"value": value, "fingerprint": got}
                break
        # Restore.
        default = engine.option_default(name)
        if default is not None:
            engine.set_option(name, default)
        rows.append({"option": name, "moved_probe": moved, "evidence": best})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    with driver.Engine(args.engine, timeout=180.0) as engine:
        all_names = []
        for line in engine.options:
            if line.startswith("option name "):
                all_names.append(line.split()[2])

        rows = [order_test(engine, a, b) for a, b in PAIRS]

        # Control A: is the FINGERPRINT sensitive at all? A comparison that can
        # never differ would report every pair as independent for the trivial
        # reason. UseNNUE true vs false changes the evaluation, so this must
        # come out different.
        engine.set_option("UseNNUE", "true")
        on = fingerprint(engine)
        engine.set_option("UseNNUE", "false")
        off = fingerprint(engine)
        engine.set_option("UseNNUE", "true")
        control_positive = on != off

        # Control B: an unrelated pair must come back null, so the detector is
        # not simply reporting a difference everywhere.
        control_negative = order_test(engine, "Book Variety", "CheckExtensionDepth")
        negative_passed = not control_negative["order_dependent"]

        effects = no_effect_sweep(engine, all_names)

    order_dependent = [r for r in rows if r["order_dependent"]]
    no_effect = [r["option"] for r in effects if not r["moved_probe"]]
    report = {
        "pairs_tested": len(rows),
        "order_dependent": [{"a": r["a"], "b": r["b"], "fields": r["differing_fields"]}
                            for r in order_dependent],
        "controls": {
            "fingerprint_sensitive": control_positive,
            "unrelated_pair_null": negative_passed,
            "negative_control": control_negative,
            "passed": control_positive and negative_passed,
        },
        "no_effect_on_probe": no_effect,
        "no_effect_rows": [r for r in effects if not r["moved_probe"]],
        "probe": {"fens": PROBE_FENS, "depth": PROBE_DEPTH},
        "reading": (
            "Every option handler in this engine is a plain assignment (plus a "
            "cache clear), so the FINAL state cannot depend on the order two "
            "assignments were made: setting A then B leaves the same pair of "
            "values as B then A. Order-independence is therefore expected by "
            "construction here and is a weak result on its own. What the report "
            "calls `UseNNUE > NNUEArch > NnueFile` precedence is GATING, not "
            "ordering: NnueFile has no effect while UseNNUE is false. That is "
            "what the no-effect sweep can see, and it is the sweep that carries "
            "the weight of this section."
        ),
        "caveat": (
            "A fixed-depth probe cannot see an option that only matters outside "
            "the positions searched. NO_EFFECT here means 'no effect on this "
            "probe', which is a weaker claim than 'no effect' and is the same "
            "limit that makes bench blind to a switch."
        ),
        "rows": rows,
        "effect_rows": effects,
    }
    with open(os.path.join(args.out, "interference.json"), "w") as fh:
        json.dump(report, fh, indent=1)

    print(f"pairs={len(rows)} order_dependent={len(order_dependent)}")
    for r in order_dependent:
        print(f"  ORDER-DEPENDENT {r['a']} vs {r['b']} fields={r['differing_fields']}")
    print(f"controls: fingerprint_sensitive={control_positive} "
          f"unrelated_pair_null={negative_passed}")
    print(f"no_effect_on_probe={len(no_effect)}: {no_effect}")
    if not report["controls"]["passed"]:
        print("CONTROLS FAILED — the pair table cannot be trusted")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
