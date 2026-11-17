"""Soak 6: ASan + UBSan leak check on a mixed workload, with LeakSanitizer at exit.

Detectability is established outside this file and recorded in the same evidence folder:
 - `nm -C build-asan/forge | grep -c __asan_` = 35, `__ubsan_` = 15  (evidence/sanitizer_meta.txt)
 - a planted heap over-read through THIS runner reports 4 sanitizer lines and rc 23
   (evidence/sanitizer_proof.json: clean 0 / planted_untriggered 0 / planted_triggered 4)
 - a 1,234-byte leak in a toy program is reported by LSan in this container
   (evidence/lsan_control.txt)

So `sanitizer_lines = 0` here is a measurement, not an absence of instrument.

The workload mixes the four things a match runner does, because a leak that only the
MultiPV path or only `ucinewgame` can reach would be missed by a plain-search run:
plain depth-6 searches, MultiPV-3 searches, `ucinewgame`, `Clear Hash`. It ends with
`quit` so LSan runs at exit.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

PATTERNS = ("ERROR: AddressSanitizer", "runtime error:", "SUMMARY: AddressSanitizer",
            "LeakSanitizer", "Direct leak", "Indirect leak")


def drain(eng):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--searches", type=int, default=120)
    ap.add_argument("--hash", type=int, default=16)
    args = ap.parse_args()

    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=1:abort_on_error=0:exitcode=23"
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:halt_on_error=0"
    fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:30]

    eng = Engine(args.exe, env=env, options={"Hash": args.hash, "Threads": 1})
    rows = []
    for i in range(args.searches):
        fen = fens[i % len(fens)]
        eng.position_fen(fen)
        r = eng.go("go depth 6")
        rows.append({"i": i, "kind": "plain", "nodes": r["nodes"], "best": r["bestmove"]})
        if i % 7 == 6:
            eng.newgame()
            rows.append({"i": i, "kind": "ucinewgame"})
        if i % 11 == 10:
            eng.setoption("Clear Hash", "")
            rows.append({"i": i, "kind": "clearhash"})
        if i % 5 == 4:
            eng.setoption("MultiPV", 3)
            eng.position_fen(fen)
            r2 = eng.go("go depth 5")
            eng.setoption("MultiPV", 1)
            rows.append({"i": i, "kind": "multipv3", "nodes": r2["nodes"],
                         "best": r2["bestmove"]})
    state = eng.quit()
    err = drain(eng)
    lines = [l for l in err.splitlines() if any(p in l for p in PATTERNS)]
    zero_node = sum(1 for r in rows if "nodes" in r and r["nodes"] in (0, None))
    res = {"searches": args.searches, "exit": state, "rc": eng.proc.returncode,
           "sanitizer_lines": len(lines),
           "first": lines[0][:200] if lines else None,
           "zero_node_rows": zero_node, "stderr_bytes": len(err),
           "kinds": {k: sum(1 for r in rows if r["kind"] == k)
                     for k in ("plain", "multipv3", "ucinewgame", "clearhash")}}
    print(json.dumps(res))
    with open(args.out + ".json", "w") as f:
        json.dump({"summary": res, "rows": rows,
                   "sanitizer_lines": lines[:40]}, f, indent=1)
    if err:
        with open(args.out + ".stderr.txt", "w") as f:
            f.write(err)


if __name__ == "__main__":
    main()
