"""Proof-of-need for the sanitizer runner, and the clean-build leak run.

Three cases, so the claim is about the RUNNER and not about one code path:
  clean   + no planted command -> expect 0 lines   (negative control)
  planted + no planted command -> expect 0 lines   (the planted INPUT is the variable)
  planted + planted command    -> expect >=1 line  (the detector fires)

Two defects in the first version of this file, both of them findings S7 traps, and both
fixed here rather than worked around:

 1. It fed the engine through `printf | exe`. EOF reaching a running search fabricates a
    `bestmove a2a3` with zero `info depth` lines (trap 3a), so the first version's clean and
    planted_untriggered rows recorded `a2a3` -- not the engine's answer. Every case now goes
    through the same non-blocking UCI reader the soak uses and asserts an `info depth` line.

 2. An ASan abort closes stdout, so the runner cannot wait for an in-band `planted` line.
    The sanitizer's output is on STDERR by construction; the runner therefore scans stderr
    after the process is gone. Waiting for a stdout line that an aborting process will never
    print is the "test that cannot fire" shape.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine, EngineError  # noqa: E402

CASES = [
    ("clean", "/tmp/soak/build-asan/forge", False),
    ("planted_untriggered", "/tmp/soak/build-planted/forge", False),
    ("planted_triggered", "/tmp/soak/build-planted/forge", True),
]

PATTERNS = ("ERROR: AddressSanitizer", "runtime error:", "SUMMARY: AddressSanitizer",
            "LeakSanitizer")


def drain(eng):
    """Read whatever is on stderr without blocking."""
    os.set_blocking(eng.proc.stderr.fileno(), False)
    out = b""
    try:
        while True:
            chunk = eng.proc.stderr.read(65536)
            if not chunk:
                break
            out += chunk
    except Exception:
        pass
    return out.decode("utf-8", "replace")


def run_case(exe, trigger):
    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0:exitcode=23"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=0"
    eng = Engine(exe, env=env, options={"Hash": 16, "Threads": 1})
    seen = {"info_depth": 0, "bestmoves": [], "aborted": None}
    try:
        eng.position_startpos_moves(["e2e4", "e7e5"])
        r = eng.go("go depth 6")
        seen["info_depth"] += r["n_depth_lines"]
        seen["bestmoves"].append(r["bestmove"])
        if trigger:
            eng.write("soakplant")
            try:
                eng.read_until(lambda ls: any("planted" in l for l in ls), 20, "planted")
            except EngineError as e:
                seen["aborted"] = str(e)[:80]
        if not seen["aborted"]:
            eng.position_startpos_moves(["d2d4", "d7d5"])
            r2 = eng.go("go depth 6")
            seen["info_depth"] += r2["n_depth_lines"]
            seen["bestmoves"].append(r2["bestmove"])
        eng.quit()
    except (EngineError, BrokenPipeError, OSError) as e:
        seen["aborted"] = (seen["aborted"] or repr(e)[:120])
    if eng.proc.poll() is None:
        eng.proc.kill()
        eng.proc.wait()
    err = drain(eng)
    lines = [l for l in err.splitlines() if any(p in l for p in PATTERNS)]
    seen.update({"rc": eng.proc.returncode, "sanitizer_lines": len(lines),
                 "first": lines[0][:150] if lines else None,
                 "stderr_bytes": len(err)})
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/soak/ev/sanitizer_proof.json")
    args = ap.parse_args()
    out = {}
    for name, exe, trig in CASES:
        out[name] = run_case(exe, trig)
        print(json.dumps({name: out[name]}))
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
