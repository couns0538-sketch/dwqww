#!/usr/bin/env python3
"""check_instrument.py -- is the printed histogram consistent with the printed counts?

An instrument whose own arithmetic does not close is not evidence. This checks, on
the raw text of one search:
  1. sum(mag histogram) == applied          (every reduction lands in exactly one bin)
  2. sum(cap_mag histogram) == cap_gate     (same, for the gate's nodes)
  3. cap_clamp <= cap_gate                  (a clamp needs a gate)
  4. research <= applied                    (a re-search follows a reduced search)
  5. rmean == sum(r*count)/sum(count), recomputed from the histogram
  6. the per-root blocks sum to the iteration block

It also runs a NEGATIVE control: a deliberately corrupted copy of the input must be
reported as inconsistent. A check that cannot fail proves nothing (findings §6).

Usage: check_instrument.py RAWFILE [RAWFILE...]
"""
import re
import sys

RE = re.compile(r"^info string (lmr|lmrsum) depth (\d+) root (\S+) applied (\d+)")


def parse_block(line):
    kv = {}
    for key in ("applied", "research", "rej", "cap_gate", "cap_clamp"):
        m = re.search(rf"\b{key} (\d+)", line)
        if m:
            kv[key] = int(m.group(1))
    m = re.search(r"\brmean (-|[\d.]+)", line)
    if m and m.group(1) != "-":
        kv["rmean"] = float(m.group(1))
    m = re.search(r"\bmag((?: r-?\d+=\d+)+)", line)
    kv["mag"] = {int(t.split("=")[0][1:]): int(t.split("=")[1]) for t in m.group(1).split()} if m else {}
    m = re.search(r"\bcap_mag((?: r-?\d+=\d+)+)", line)
    kv["cap_mag"] = {int(t.split("=")[0][1:]): int(t.split("=")[1]) for t in m.group(1).split()} if m else {}
    m = re.search(r"\[([^\]]*)\]", line)
    if m:
        toks = m.group(1).split()
        for j in range(0, len(toks) - 1, 2):
            kv[f"guard_{toks[j]}"] = int(toks[j + 1])
    return kv


def check(lines, label):
    """Return a list of failure strings."""
    fails = []
    blocks = []
    for line in lines:
        m = RE.match(line)
        if m:
            blocks.append((m.group(1), int(m.group(2)), m.group(3), parse_block(line)))
    if not blocks:
        return [f"{label}: NO LMR BLOCKS FOUND — the check examined nothing"]

    checked = 0
    for kind, depth, root, kv in blocks:
        if kind != "lmr":
            continue
        checked += 1
        applied = kv.get("applied", 0)
        mag = kv.get("mag", {})
        if sum(mag.values()) != applied:
            fails.append(f"{label} d{depth} {root}: mag sums to {sum(mag.values())}, applied says {applied}")
        if applied and sum(mag.values()):
            recomputed = sum(r * c for r, c in mag.items()) / sum(mag.values())
            if abs(recomputed - kv.get("rmean", -1)) > 0.0051:
                fails.append(f"{label} d{depth} {root}: rmean says {kv['rmean']}, histogram implies {recomputed:.4f}")
        gate = kv.get("cap_gate", 0)
        capmag = kv.get("cap_mag", {})
        if gate and sum(capmag.values()) != gate:
            fails.append(f"{label} d{depth} {root}: cap_mag sums to {sum(capmag.values())}, cap_gate says {gate}")
        if kv.get("cap_clamp", 0) > gate:
            fails.append(f"{label} d{depth} {root}: cap_clamp {kv['cap_clamp']} > cap_gate {gate}")
        if kv.get("research", 0) > applied:
            fails.append(f"{label} d{depth} {root}: research {kv['research']} > applied {applied}")

    by_depth = {}
    for kind, depth, root, kv in blocks:
        if kind != "lmr":
            continue
        by_depth.setdefault(depth, {"all": None, "roots": []})
        if root == "all":
            by_depth[depth]["all"] = kv
        else:
            by_depth[depth]["roots"].append(kv)
    for depth, d in by_depth.items():
        if d["all"] is None or not d["roots"]:
            continue
        tot_applied = sum(r.get("applied", 0) for r in d["roots"])
        tot_gate = sum(r.get("cap_gate", 0) for r in d["roots"])
        if tot_applied != d["all"].get("applied", 0):
            fails.append(f"{label} d{depth}: per-root applied sums to {tot_applied}, "
                         f"iteration says {d['all'].get('applied', 0)}")
        if tot_gate != d["all"].get("cap_gate", 0):
            fails.append(f"{label} d{depth}: per-root cap_gate sums to {tot_gate}, "
                         f"iteration says {d['all'].get('cap_gate', 0)}")

    print(f"{label}: examined {checked} per-depth blocks, {len(by_depth)} depths, {len(fails)} failures")
    return fails


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: check_instrument.py RAWFILE [RAWFILE...]")
    all_fails = []
    for path in sys.argv[1:]:
        lines = open(path).read().splitlines()
        all_fails += check(lines, path)

    if all_fails:
        print()
        for f in all_fails[:20]:
            print("  FAIL", f)
        if len(all_fails) > 20:
            print(f"  ... and {len(all_fails) - 20} more")

    # negative control: pick the first input that actually HAS a populated bin, so the
    # control is exercised rather than skipped (a skipped control proves nothing).
    path = None
    for cand in sys.argv[1:]:
        if re.search(r"\bmag r1=\d+", open(cand).read()):
            path = cand
            break
    if path is None:
        print("NEGATIVE CONTROL FAILED: no input carries a populated r1 bin — control not exercised")
        return 1
    lines = open(path).read().splitlines()
    corrupted = []
    done = False
    for line in lines:
        if not done and re.search(r"\bmag r1=(\d+)", line):
            line = re.sub(r"\bmag r1=(\d+)", lambda m: f"mag r1={int(m.group(1)) + 1}", line, count=1)
            done = True
        corrupted.append(line)
    if not done:
        print("NEGATIVE CONTROL: no mag r1 bin to corrupt — control not exercised")
        return 1
    ctl = check(corrupted, "NEGATIVE-CONTROL(histogram inflated by 1)")
    if not ctl:
        print("NEGATIVE CONTROL FAILED: the corrupted input was accepted — the check cannot fail")
        return 1
    print("NEGATIVE CONTROL PASSED: the corrupted input was rejected")

    if all_fails:
        print()
        for f in all_fails[:20]:
            print("  FAIL", f)
        if len(all_fails) > 20:
            print(f"  ... and {len(all_fails) - 20} more")
        return 1
    print("ALL CONSISTENT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
