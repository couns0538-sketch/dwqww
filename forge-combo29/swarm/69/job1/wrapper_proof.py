"""Proof that the environment wrappers actually bite (a wrapper that is silently
ignored would make every "0 differing" row above vacuous).

W1  `taskset -c 0` / `-c 2` must place the process on that core
    (/proc/self/status Cpus_allowed_list).
W2  `nice -n 19` must show Nice: 19.
W3  `ulimit -v 65536` must make a large allocation FAIL. Hash 512 needs >=512 MB,
    so the engine must die or answer with an error under the cap and succeed without
    it. Two directions, so the check cannot pass by accident.
W4  `ulimit -s 8192` must be visible in the process's own limit listing.
W5  A deliberately-too-small cap (ulimit -v 4096, 4 MB) must kill the engine
    outright -- proving the cap is enforced and not just recorded.
"""

import subprocess
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
results = []


def record(name, ok, detail):
    results.append((name, ok, detail))
    print("%-58s %s  %s" % (name, "OK" if ok else "FAILED", detail))


def probe(argv):
    """Run a complete argv (its last element is the shell script or command)."""
    out = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    return out.stdout.strip(), out.returncode


def main():
    print("exe:", BASE_EXE)

    # W1: affinity
    for core in ("0", "2"):
        out, _ = probe(["taskset", "-c", core, "bash", "-c",
                        "grep Cpus_allowed_list /proc/self/status"])
        ok = out.split(":")[-1].strip() == core
        record("W1 taskset -c %s pins the process" % core, ok, out)

    # A control with no wrapper, so "core 0" is a real restriction and not the default.
    out, _ = probe(["bash", "-c", "grep Cpus_allowed_list /proc/self/status"])
    record("W1 control: no wrapper lists all cores", out.split(":")[-1].strip() != "0", out)

    # W2: nice. This container's /proc/<pid>/status has no Nice field, so ask ps
    # about the process itself (`$$`), not about the parent.
    out, _ = probe(["nice", "-n", "19", "bash", "-c", 'ps -o nice= -p $$'])
    out_plain, _ = probe(["bash", "-c", 'ps -o nice= -p $$'])
    record("W2 nice -n 19 changes the child's nice value",
           out.strip() == "19" and out_plain.strip() == "0",
           "nice=%r vs unwrapped=%r" % (out.strip(), out_plain.strip()))

    # W4: stack limit visible
    out, _ = probe(["bash", "-c", 'ulimit -s 8192; exec bash -c "ulimit -s"'])
    record("W4 ulimit -s 8192 is visible to the child", out.strip() == "8192", out)

    # W3 + W5: the memory cap must break a real allocation.
    def hash_search(prefix, mb):
        engine = ucih.Engine(BASE_EXE, prefix=prefix, timeout=120)
        try:
            engine.uci()
            engine.setoption("Hash", mb)
            engine.position_startpos()
            return engine.go("go depth 4")
        finally:
            try:
                engine.close()
            except Exception:  # noqa: BLE001
                pass

    big_ref = hash_search(None, 512)
    record("W3 Hash 512 succeeds with no cap (control)",
           big_ref["bestmove"] is not None, "bestmove %s" % big_ref["bestmove"])

    cap = ["bash", "-c", 'ulimit -v 65536; exec "$0"']
    try:
        big_capped = hash_search(cap, 512)
        died = big_capped["bestmove"] is None
        detail = "bestmove %s" % big_capped["bestmove"]
    except Exception as exc:  # noqa: BLE001 - a crash is the expected outcome
        died = True
        detail = "%s: %s" % (type(exc).__name__, str(exc)[:60])
    record("W3 Hash 512 FAILS under ulimit -v 65536", died, detail)

    # The cap used in the matrix holds a 16 MB Hash fine -- so its 0/40 is meaningful.
    try:
        small = hash_search(cap, 16)
        ok = small["bestmove"] is not None
        detail = "bestmove %s nodes %s" % (small["bestmove"], small["nodes"])
    except Exception as exc:  # noqa: BLE001
        ok = False
        detail = "%s: %s" % (type(exc).__name__, str(exc)[:60])
    record("W3 Hash 16 fits under ulimit -v 65536", ok, detail)

    tiny = ["bash", "-c", 'ulimit -v 4096; exec "$0"']
    try:
        engine = ucih.Engine(BASE_EXE, prefix=tiny, timeout=60)
        try:
            engine.uci()
            engine.position_startpos()
            r = engine.go("go depth 4")
            survived = r["bestmove"] is not None
        finally:
            try:
                engine.close()
            except Exception:  # noqa: BLE001
                pass
        detail = "survived, bestmove %s" % r["bestmove"]
    except Exception as exc:  # noqa: BLE001
        survived = False
        detail = "%s: %s" % (type(exc).__name__, str(exc)[:60])
    record("W5 ulimit -v 4096 kills the engine (cap is enforced)", not survived, detail)

    bad = [n for n, ok, _ in results if not ok]
    print("\n%d checks, %d failed" % (len(results), len(bad)))
    for n in bad:
        print("  FAILED:", n)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
