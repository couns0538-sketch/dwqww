"""Read fresh_diff.py's stale output and answer the assignment's items 2 and 3."""
import json
import sys


def brief(rec, idx=-1):
    if rec.get("timeout"):
        return ("TIMEOUT", None, None, None)
    s = rec["runs"][0][idx]
    return (s["kind"], s["score"], s["bestmove"], rec["nodes"][0][idx])


def main():
    d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/stale_fresh.json"))
    names = sorted({k.split("|")[0] for k in d})
    print(f"{'board':11} {'coldA':>22} {'warmB':>22} {'coldB':>22} {'warmBB':>22}  verdict")
    changed = 0
    for n in names:
        cA, wB, cB, wBB = (d.get(f"{n}|{x}") for x in ("coldA", "warmAB", "coldB", "warmBB"))
        if any(r is None for r in (cA, wB, cB, wBB)):
            continue
        a = brief(cA)
        b = brief(wB)
        c = brief(cB)
        e = brief(wB)          # warmAB second search
        f = brief(wBB, 1)      # warmBB second search
        # Did the warm table change the score relative to a fresh search at B?
        stale_changed = (b[0], b[1]) != (c[0], c[1])
        same_clock_changed = (f[0], f[1]) != (c[0], c[1])
        if stale_changed:
            changed += 1
        verdict = []
        if stale_changed:
            verdict.append("WARM TABLE CHANGED SCORE vs cold")
        if same_clock_changed:
            verdict.append("(same-clock warm also changes it: not clock-specific)")
        print(f"{n:11} {str(a):>22} {str(b):>22} {str(c):>22} {str(f):>22}  {' '.join(verdict) or 'no change'}")
    print(f"\nboards where the 10->90 warm table changed the score vs a cold 90 search: {changed}")
    print("\nReproducibility (all runs identical, repeat=3):")
    for k in sorted(d):
        r = d[k]
        if r.get("timeout"):
            print(f"  {k:26} TIMEOUT")
            continue
        first = r["runs"][0]
        ok = all(x == first for x in r["runs"]) and len({tuple(x) for x in r["nodes"]}) == 1
        print(f"  {k:26} {'stable' if ok else 'UNSTABLE'}")


if __name__ == "__main__":
    main()
