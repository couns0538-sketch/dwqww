#!/usr/bin/env python3
"""s46_profile_report.py (S46, opus 2026-10-27): tables for the report.
1) every fixture under the three rule profiles: voted (asserts), pc_896663b0 (log same/differs, asserts), pre_fix_F41CF92F;
2) every deliberately wrong rule (the mutation list of test_promote_sim.py) and the fixtures that catch it."""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_promote_sim as T  # noqa: E402  (loads the simulator and the fixtures)


def main():
    sim, fixes = T.sim, T.FIX
    print('| fixture | spec | voted: asserts | pc_896663b0: log vs voted / asserts | pre_fix_F41CF92F: asserts |')
    print('|---|---|---|---|---|')
    for fx in fixes:
        v = T.check(fx, sim.simulate(T.VOTED, fx))
        pl = sim.simulate(T.PC, fx)
        p = T.check(fx, pl)
        q = T.check(fx, sim.simulate(T.PRE, fx))
        same = T.body(pl) == T.body(sim.simulate(T.VOTED, fx))
        print(f"| {fx['name']} | {fx['spec_ref']} | {'PASS' if not v else 'FAIL'} | {'same' if same else 'DIFFERS'} / {'PASS' if not p else 'FAIL'} | "
              f"{'PASS' if not q else 'FAIL (' + q[:70] + ')'} |")
    print()
    print('| wrong rule (one at a time) | fixtures that fail |')
    print('|---|---|')
    allc = True
    for key, val in T.MUTATIONS:
        bad = sim.load_rules(os.path.join(T.CONF, 'rules_voted_20261026.json'), {key: val})
        failing = [fx['name'] for fx in fixes if T.check(fx, sim.simulate(bad, fx)) or T.body(sim.simulate(bad, fx)) != T.body(T.golden(fx['name']))]
        allc &= bool(failing)
        print(f"| {key} = {json.dumps(val)} | {len(failing)}: {', '.join(failing) if failing else 'NONE (not caught)'} |")
    print(f'\nall {len(T.MUTATIONS)} wrong rules caught: {allc}')
    return 0 if allc else 1


if __name__ == '__main__':
    sys.exit(main())
