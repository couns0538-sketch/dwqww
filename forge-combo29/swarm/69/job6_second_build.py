"""JOB 6: the closest available proxy for "a different machine" — a different BUILD.

I cannot run a second machine, so the nearest honest substitute is to build the SAME
source a second time, in a different directory, and ask whether a fixed-budget answer
survives it. This catches:

  * anything derived from a pointer value, an address, or allocation order (which
    differs between builds through ASLR and through layout);
  * anything that depends on an uninitialised value the compiler happened to zero;
  * timestamps, build paths or `__DATE__` leaking into the search;
  * ASLR itself, which a fresh process already exercises.

It does NOT catch a genuinely different CPU (different ISA path, different cache
latency) or a different compiler. Those are stated as untested, not as passed.

Build B is the same source with `-g` added, in a new directory, so the binary differs
in size and layout while the code is identical.
"""

import json
import os
import subprocess
import sys

import ucih

SRC = os.path.expanduser("~/builds/base/forge-combo29")
BUILD_A = "/home/ubuntu/builds/base-build/forge"
BUILD_B = "/home/ubuntu/builds/base-build-b/forge"
BUILD_B_DIR = "/home/ubuntu/builds/base-build-b"

BUDGETS = ["go nodes 50000", "go depth 12"]
OPTIONS = [("Threads", 1), ("Hash", 16)]


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def cell(exe, fen, budget):
    engine = ucih.Engine(exe, timeout=600)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_fen(fen)
        return key(engine.go(budget))
    finally:
        engine.close()


def build_b():
    if os.path.exists(BUILD_B):
        return "already built"
    os.makedirs(BUILD_B_DIR, exist_ok=True)
    cfg = subprocess.run(
        ["cmake", "-S", SRC, "-B", BUILD_B_DIR, "-DCMAKE_BUILD_TYPE=Release",
         "-DCMAKE_CXX_COMPILER=g++", "-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -g"],
        capture_output=True, text=True, timeout=600)
    if cfg.returncode != 0:
        return "CONFIGURE FAILED: " + cfg.stderr[-400:]
    bld = subprocess.run(["cmake", "--build", BUILD_B_DIR, "-j4"],
                         capture_output=True, text=True, timeout=1800)
    if bld.returncode != 0:
        return "BUILD FAILED: " + bld.stderr[-400:]
    return "built"


def sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=== JOB 6: second build of identical source as a proxy for a second machine ===")
    status = build_b()
    print("build B:", status)
    if not os.path.exists(BUILD_B):
        print("no second binary; stopping")
        return 1

    print("build A sha256 %s  (%d bytes)" % (sha(BUILD_A)[:16], os.path.getsize(BUILD_A)))
    print("build B sha256 %s  (%d bytes)" % (sha(BUILD_B)[:16], os.path.getsize(BUILD_B)))
    identical_binary = sha(BUILD_A) == sha(BUILD_B)
    print("binaries are byte-identical:", identical_binary, "(expected False: -g changes layout)")

    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:40]

    report = {"binary_identical": identical_binary, "n": len(fens)}
    for budget in BUDGETS:
        a = [cell(BUILD_A, f, budget) for f in fens]
        b = [cell(BUILD_B, f, budget) for f in fens]
        diff = [i for i in range(len(fens)) if a[i] != b[i]]
        report[budget] = {"n": len(fens), "n_differing": len(diff), "differing": diff,
                          "sample_a": [list(c) for c in a[:5]],
                          "sample_b": [list(c) for c in b[:5]]}
        print("  %-16s  differ %d / %d %s" % (budget, len(diff), len(fens), diff[:5]))

    # Pins on build B, so it is a build we are entitled to use at all.
    print("\n-- honesty pins on build B --")
    pins = {}
    for depth, expected in ((11, 312866), (13, 862329), (16, 3024920)):
        out = subprocess.run(["bash", "-c",
                              "printf 'bench %d\\nquit\\n' | '%s'" % (depth, BUILD_B)],
                             capture_output=True, text=True, timeout=600).stdout
        nodes = None
        for line in out.splitlines():
            if line.startswith("info string bench"):
                nodes = int(line.split("nodes")[1].split()[0])
        pins[depth] = {"nodes": nodes, "expected": expected, "ok": nodes == expected}
        print("  bench %-2d nodes %-8s expected %-8d %s"
              % (depth, nodes, expected, "OK" if nodes == expected else "MISMATCH"))
    report["pins"] = pins

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job6/second_build.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
