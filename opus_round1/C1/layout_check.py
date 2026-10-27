#!/usr/bin/env python3
"""Code placement check for C1: every function (text symbol) present in both
executables, its address modulo 64 in A (reference) and B (candidate).

The tablebase code is [[gnu::cold]] and must land after all other code, so in
B every function outside that cold tail should keep its A address mod 64
(ideally the same address). Prints the address delta histogram and every
function whose placement mod 64 changed, the hot search/eval functions first.

usage: layout_check.py <exe_A> <exe_B> [nm]
"""
import collections
import subprocess
import sys

HOT = ("forge::Worker::search(", "forge::Worker::qsearch(", "forge::MovePicker::", "forge::Worker::static_evaluate(",
       "forge::TranspositionTable::probe(", "forge::TranspositionTable::store(", "forge::Worker::should_stop(",
       "forge::Worker::is_draw(", "forge::Worker::corrected_eval(", "forge::Worker::update_", "forge::Worker::quiet_history(",
       "forge::Worker::capture_history_value(", "forge::Worker::record_move(", "forge::nnue::", "forge::Board::",
       "forge::Evaluator::", "std::__introsort_loop<forge::MovePicker")


def symbols(exe, nm):
    out = subprocess.run([nm, "-C", "-n", exe], capture_output=True, text=True, check=True).stdout
    first = {}
    for line in out.splitlines():
        parts = line.split(" ", 2)
        if len(parts) < 3 or parts[1] not in ("T", "t"):
            continue
        name = parts[2]
        if name.startswith(".text") or name.startswith("__tcf_"):
            continue
        first.setdefault(name, int(parts[0], 16))
    return first


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    nm = sys.argv[3] if len(sys.argv) > 3 else "nm"
    a = symbols(sys.argv[1], nm)
    b = symbols(sys.argv[2], nm)
    # The cold tail (.text.unlikely, after all .text and the sorted COMDATs) starts at the first
    # tablebase function proper; template instantiations (COMDATs) stay in the comparison.
    cold_start = min((addr for name, addr in b.items()
                      if name.startswith("forge::syzygy::") or name.startswith("forge::Worker::probe_tablebase")),
                     default=None)
    common = [n for n in a if n in b]
    deltas = collections.Counter()
    moved = []
    for n in common:
        if cold_start is not None and b[n] >= cold_start:
            continue
        d = b[n] - a[n]
        deltas[d] += 1
        if a[n] % 64 != b[n] % 64:
            moved.append((not n.startswith(HOT), n, a[n] % 64, b[n] % 64, d))
    print("functions compared: %d (B cold tablebase tail starts at %s)" % (sum(deltas.values()), hex(cold_start) if cold_start else "-"))
    print("address delta histogram (delta: count):", ", ".join("%+d: %d" % kv for kv in sorted(deltas.items())))
    moved.sort()
    hot_moved = [m for m in moved if not m[0]]
    print("hot functions with a different address mod 64: %d" % len(hot_moved))
    print("all functions with a different address mod 64: %d" % len(moved))
    for _, n, ma, mb, d in moved[:80]:
        print("  %-3s %2d -> %2d  delta %+6d  %s" % ("HOT" if n.startswith(HOT) else "", ma, mb, d, n[:150]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
