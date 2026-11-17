"""Experiment G - ASan/UBSan over every resize path (coordinator item 3, last part).

A sanitizer run only means something if it drives the paths that could be wrong.
Each block below is a distinct lifecycle transition, and the script asserts the
engine is still ALIVE and still answers after each one, so a hang or an early
exit is reported rather than read as a clean run.

Paths driven:
  1. same-value resize on a cold table
  2. same-value resize on a warm table, repeatedly
  3. resize up, resize down, alternate 20x
  4. resize to the minimum (1 MB) and the maximum (2048 MB) and back
  5. resize DURING a search (the stop_search path)
  6. resize between `position` commands, and between `go` commands
  7. resize after ucinewgame, and before it
  8. resize with MultiPV > 1 (the alternate-table path from S3)
  9. every one of the above followed by a real search, so a corrupted table is
     read as well as written

The build is FORGE_PORTABLE=ON because ASan and the AVX-512 NNUE kernel do not
coexist usefully here, and the node counts are NOT comparable with the release
build's pins.  The claim this run supports is memory-safety only, and it is
stated that way: no ASan or UBSan diagnostic, no crash, no hang.

A deliberately broken control case is included at the end - the same harness
against a binary given a bad argument - purely to show the harness can report a
failure.  It is marked CONTROL and is expected to be the only red line.
"""

import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine

POS = "position fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"
POS2 = "position fen rnbqkb1r/pp1pn1pp/2p5/3P4/2P1pp2/4B2N/PP2PPPP/RN1QKB1R w KQkq - 0 1"

BLOCKS = []


def block(fn):
    BLOCKS.append(fn)
    return fn


@block
def same_value_cold(e, log):
    log("same-value resize, cold table")
    e.setoption("Hash", 32)
    e.setoption("Hash", 32)
    e.setoption("Hash", 32)
    r = e.search(POS, "go depth 10")
    assert r["ok"] and r["bestmove"], "no bestmove"


@block
def same_value_warm(e, log):
    log("same-value resize, 8 warm cycles")
    e.setoption("Hash", 32)
    e.newgame()
    for _ in range(8):
        e.search(POS, "go depth 10")
        e.setoption("Hash", 32)


@block
def up_down_cycles(e, log):
    log("16 <-> 256, 10 cycles")
    e.setoption("Hash", 16)
    e.newgame()
    for _ in range(10):
        e.setoption("Hash", 256)
        e.search(POS, "go depth 8")
        e.setoption("Hash", 16)
        e.search(POS2, "go depth 8")


@block
def extremes(e, log):
    log("1 MB and 2048 MB extremes")
    e.setoption("Hash", 1)
    e.newgame()
    r = e.search(POS, "go depth 8")
    assert r["ok"], "no bestmove at Hash 1"
    e.setoption("Hash", 2048)
    r = e.search(POS, "go depth 8")
    assert r["ok"], "no bestmove at Hash 2048"
    e.setoption("Hash", 16)
    r = e.search(POS, "go depth 8")
    assert r["ok"], "no bestmove after 2048 -> 16"


@block
def during_search(e, log):
    log("resize DURING a search")
    import time
    e.setoption("Hash", 16)
    e.newgame()
    for _ in range(5):
        e.send("position fen " + POS.split(" ", 2)[2])
        e.send("go infinite")
        time.sleep(0.12)
        # NOTE: use send(), not setoption() -- setoption() calls sync(), and the
        # `bestmove` that stop_search() produces arrives BEFORE `readyok`, so a
        # sync would swallow it.  That is a harness fact worth keeping: the
        # bestmove is emitted during the setoption, not after it.
        e.send("setoption name Hash value 64")
        lines, ok = e.lines_until("bestmove", timeout=60)
        assert ok, "no bestmove after mid-search resize"
        log("bestmove line: %s" % next((l for l in lines if l.startswith("bestmove")), "?"))
        e.send("isready")
        _sync, ok2 = e.lines_until("readyok", timeout=60)
        assert ok2, "no readyok after mid-search resize"
        e.setoption("Hash", 16)


@block
def between_positions(e, log):
    log("resize between position commands")
    e.setoption("Hash", 32)
    e.newgame()
    for _ in range(6):
        e.search(POS, "go depth 9")
        e.setoption("Hash", 48)
        e.search(POS2, "go depth 9")
        e.setoption("Hash", 32)


@block
def around_newgame(e, log):
    log("resize before and after ucinewgame")
    e.setoption("Hash", 128)
    e.newgame()
    e.setoption("Hash", 32)
    e.search(POS, "go depth 9")
    e.setoption("Hash", 32)
    e.newgame()
    e.setoption("Hash", 512)
    e.newgame()
    e.search(POS2, "go depth 9")


@block
def multipv_resize(e, log):
    log("resize with MultiPV > 1")
    e.setoption("Hash", 32)
    e.setoption("MultiPV", 3)
    e.newgame()
    e.search(POS, "go depth 8")
    e.setoption("Hash", 128)
    e.search(POS, "go depth 8")
    e.setoption("MultiPV", 1)
    e.setoption("Hash", 16)


@block
def quit_during_search(e, log):
    log("resize then immediate quit (destructor path)")
    import time
    e.setoption("Hash", 256)
    e.send("position fen " + POS.split(" ", 2)[2])
    e.send("go infinite")
    time.sleep(0.1)
    # quit with a search in flight exercises the destructor while a worker may
    # still be running; the stop_search in the `quit` branch is what protects it.
    e.setoption("Hash", 16)


def canary_check(script_dir):
    """Prove the detector reports a REAL ASan diagnostic, not just a dead binary.

    A missing-binary control only shows the harness can raise an exception.  The
    claim this seat makes is "no sanitizer diagnostic", which needs a case where
    a diagnostic certainly exists.  `asan_canary.cpp` is such a case: it answers
    `uci`/`isready` and then overflows on `setoption name Hash`.

    The canary is built here, with the same sanitizer flags, so the control is
    reproducible from the tree.
    """
    src = os.path.join(script_dir, "asan_canary.cpp")
    binpath = "/tmp/asan_canary"
    build = subprocess.run(
        ["g++", "-O1", "-g", "-fsanitize=address,undefined", "-o", binpath, src],
        capture_output=True, text=True,
    )
    if build.returncode != 0:
        return {"built": False, "stderr": build.stderr[:400], "detected": False}
    errfile = "/tmp/asan_canary.stderr"
    try:
        e = Engine(binpath, stderr_to_file=errfile)
        e.handshake()
        e.send("setoption name Hash value 32")
        e.drain(quiet_for=0.2)
        e.close()
    except Exception:  # noqa: BLE001 - the canary is expected to die
        pass
    try:
        with open(errfile, "r", errors="replace") as fh:
            text = fh.read()
    except OSError:
        text = ""
    detected = "AddressSanitizer" in text
    return {"built": True, "detected": detected, "head": text.splitlines()[:6]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="run one block by name")
    args = ap.parse_args()

    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=1:abort_on_error=0:detect_stack_use_after_return=1:allocator_may_return_null=1"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=0"

    results = []
    for fn in BLOCKS:
        if args.only and fn.__name__ != args.only:
            continue
        log_lines = []
        alive = True
        error = None
        errfile = args.out + ".%s.stderr" % fn.__name__
        try:
            e = Engine(args.engine, stderr_to_file=errfile)
            e.handshake()
            fn(e, lambda m: log_lines.append(m))
            # final liveness check: the engine still answers a real search
            r = e.search(POS2, "go depth 8", timeout=120)
            alive = bool(r["ok"] and r["bestmove"])
            e.close()
        except Exception as exc:  # noqa: BLE001 - report, do not crash the harness
            error = "%s: %s" % (type(exc).__name__, exc)
            alive = False
        diagnostics = []
        try:
            with open(errfile, "r", errors="replace") as fh:
                diagnostics = [l.rstrip() for l in fh if l.strip()]
        except OSError:
            pass
        clean = not any(("ERROR: AddressSanitizer" in l or "runtime error" in l or
                         "SUMMARY: " in l or "LeakSanitizer" in l) for l in diagnostics)
        results.append({
            "block": fn.__name__, "log": log_lines, "alive_at_end": alive,
            "error": error, "sanitizer_clean": clean,
            "diagnostic_lines": len(diagnostics),
            "diagnostics_head": diagnostics[:12],
        })
        print("%-22s alive=%-5s clean=%-5s %s" % (fn.__name__, alive, clean, error or ""), flush=True)

    # CONTROL 1: the harness must be able to report a failure.  Point it at a
    # non-existent binary; a harness that reports this as fine is broken.
    control_failed = False
    try:
        e = Engine("/nonexistent/forge")
        e.handshake()
        e.close()
    except Exception:
        control_failed = True
    print("CONTROL (bad binary detected) =", control_failed, flush=True)

    # CONTROL 2: the DETECTOR must fire on a real sanitizer report.
    canary = canary_check(os.path.dirname(os.path.abspath(__file__)))
    print("CONTROL (canary ASan report detected) =", canary.get("detected"), flush=True)
    for line in canary.get("head", [])[:4]:
        print("   canary |", line, flush=True)

    with open(args.out, "w") as fh:
        json.dump({"engine": args.engine, "blocks": results, "control_can_fail": control_failed,
                   "canary": canary}, fh, indent=2)
    ok = all(r["alive_at_end"] for r in results)
    clean = all(r["sanitizer_clean"] for r in results)
    print("\nall blocks alive:", ok, "| all blocks sanitizer-clean:", clean,
          "| control can fail:", control_failed, "| canary detected:", canary.get("detected"))
    # A sanitizer run that cannot report a failure is worthless, so the run is
    # only admissible when BOTH controls fired.
    admissible = ok and clean and control_failed and canary.get("detected")
    print("ADMISSIBLE:", admissible)
    raise SystemExit(0 if admissible else 1)


if __name__ == "__main__":
    main()
