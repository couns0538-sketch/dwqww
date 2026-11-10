"""R9 equivalence (saved-results replay, no games): feed R9's own saved run records (tests/fixtures/r9, byte-exact
copies of opus-r9-spsa 73eb280a opus_r9/runs/<run>/{config.json,iterations.jsonl}) through space.py and require
exactly R9's perturbations and theta trajectory.
  * bounds_mode r9_clamp: every batch's delta, plus, minus and theta_after must equal R9's record bit for bit.
  * bounds_mode inner (this pack's default): each batch starts from R9's recorded theta, and must equal R9 exactly
    unless that same batch shrank, projected or capped its perturbation, projected its update, or had a coordinate
    without information (E-006). A mismatch in any other batch fails.
usage: python -I -B test_r9_equivalence.py   (exit 0 = PASS)"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "spsa"))
from space import Space  # noqa: E402

FIX = HERE / "fixtures" / "r9"


def load(run):
    cfg = json.loads((FIX / f"{run}_config.json").read_text(encoding="utf-8"))
    recs = [json.loads(x) for x in (FIX / f"{run}_iterations.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return cfg, recs


def check(run, mode):
    cfg, recs = load(run)
    cfg = dict(cfg, bounds_mode=mode)
    sp = Space(cfg)
    names = sp.names
    mism, allowed = [], set()
    theta = [float(recs[0]["theta_before"][n]) for n in names]
    for r in recs:
        if [r["theta_before"][n] for n in names] != theta:
            mism.append((r["batch"], "theta_before"))
            theta = [float(r["theta_before"][n]) for n in names]
        plan = sp.plan(theta, r["k_before"])
        up = sp.update(plan, r["W"], r["L"], r["pairs"])
        # inner mode differs from R9 by design only in a batch that shrinks the whole perturbation (s < 1), moves
        # theta inward or caps a coordinate (R9 clamps plus and minus independently), projects the update, or has a
        # coordinate whose rounded plus equals its minus (E-006: no update)
        if plan["theta_moved"] or any(plan["capped"]) or plan["s"] < 1.0 or up["projected"] or 0 in plan["eff"]:
            allowed.add(r["batch"])
        if plan["delta"] != r["delta"]:
            mism.append((r["batch"], "delta"))
        if plan["plus"] != r["plus"] or plan["minus"] != r["minus"]:
            mism.append((r["batch"], "plus/minus"))
        if up["k_after"] != r["k_after"]:
            mism.append((r["batch"], "k_after"))
        want = [r["theta_after"][n] for n in names]
        if up["theta_after"] != want:
            mism.append((r["batch"], "theta_after"))
        theta = want
    return len(recs), mism, allowed


def main():
    ok = True
    for run in ("stc1", "sanity3"):
        for mode in ("r9_clamp", "inner"):
            n, mism, allowed = check(run, mode)
            stray = [m for m in mism if m[0] not in allowed]
            good = not mism if mode == "r9_clamp" else not stray
            ok &= good
            print(f"{'PASS' if good else 'FAIL'} R9 {run} replay, bounds_mode {mode}: {n} batches, "
                  f"{len(mism)} mismatches{'' if not mism else ' first ' + str(mism[:3])}"
                  + ("" if mode == "r9_clamp" else
                     f", batches that differ from R9 by design (shrink/projection/cap/E-006) {len(allowed)}, "
                     f"mismatches outside them {len(stray)}"))
    print("R9 EQUIVALENCE OK" if ok else "R9 EQUIVALENCE FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
