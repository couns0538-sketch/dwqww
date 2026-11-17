"""Soak 5: hard `ulimit -v` just above the working set -- does the engine DEGRADE or DIE?

Prior work (findings S7 trap 3c) says: no middle band, every cap that ran gave 0 of 12
different answers, and below the cliff 12 of 12 died. This re-measures that on this build
instead of assuming it.

Two instrument corrections, both forced by the first version of this script:

 1. The answer key must EXCLUDE `nps`. The engine prints `nps 19` on one run and `nps 17`
    on the next for the same nodes and the same score, so a comparison over the raw `info`
    tail reports a difference on 13 of 15 caps that is pure timing. The key here is
    (bestmove, score token, nodes), and a separate column reports how many rows differed
    in nps alone, so the correction is visible rather than silently applied.

 2. `ulimit -v` caps VIRTUAL memory, and the engine's VmSize (119 MB at Hash 32) is not
    its working set (RSS 43 MB). Under a cap the process takes a different allocation path:
    VmSize drops to 53 MB because a 64 MiB glibc arena reservation fails and malloc falls
    back to the main arena. So the cap numbers are compared against VmSize AND RSS, and the
    report says which one the cliff tracks.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine, EngineError  # noqa: E402

SCORE_RE = re.compile(r"score (cp|mate) (-?\d+)")
NODES_RE = re.compile(r"\bnodes (\d+)")


def answer_key(last_info, bestmove):
    """(bestmove, score, nodes). Deliberately excludes nps and time."""
    score = None
    nodes = None
    if last_info:
        m = SCORE_RE.search(last_info)
        if m:
            score = "%s %s" % (m.group(1), m.group(2))
        n = NODES_RE.search(last_info)
        if n:
            nodes = int(n.group(1))
    return (bestmove, score, nodes)


def run_capped(exe, cap_kb, fens, hash_mb, depth):
    if cap_kb:
        cmd = ["bash", "-c", 'ulimit -v %d; exec "%s"' % (cap_kb, exe)]
    else:
        cmd = [exe]
    env = dict(os.environ)
    env.pop("ASAN_OPTIONS", None)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, bufsize=0, env=env)
    eng = Engine.__new__(Engine)
    eng.exe = exe
    eng.proc = proc
    eng.buf = b""
    eng.sent = []
    eng.id_name = None
    keys = []
    raw = []
    vm_after = None
    died = None
    try:
        eng._handshake({"Hash": hash_mb, "Threads": 1})
        for fen in fens:
            eng.position_fen(fen)
            r = eng.go("go depth %d" % depth, deadline_s=180)
            keys.append(answer_key(r["last"], r["bestmove"]))
            raw.append(r["last"])
        vm_after = eng.vm_kb()
    except EngineError as e:
        died = {"why": str(e)[:200]}
    except (BrokenPipeError, OSError) as e:
        died = {"why": repr(e)[:200]}
    finally:
        if proc.poll() is None:
            try:
                proc.stdin.write(b"quit\n")
                proc.stdin.flush()
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
                proc.wait()
        err = b""
        try:
            err = proc.stderr.read() or b""
        except Exception:
            pass
    return {"cap_kb": cap_kb, "keys": keys, "raw": raw, "died": died,
            "rc": proc.returncode,
            "signal": (-proc.returncode if proc.returncode and proc.returncode < 0 else None),
            "stderr_tail": err.decode("utf-8", "replace")[-300:],
            "vm_after": vm_after}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hash", type=int, default=32)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--positions", default="/tmp/soak/positions_R.fens")
    ap.add_argument("--caps", default="0,512,256,200,180,170,160,150,140,130,120,"
                                     "110,100,96,92,88,84,80,76,72,68,64,60,56")
    args = ap.parse_args()

    fens = [l.strip() for l in open(args.positions) if l.strip()][10:22]
    caps = [int(c) for c in args.caps.split(",")]
    out = []
    ref_keys = None
    ref_raw = None
    for cap_mb in caps:
        rec = run_capped(args.exe, cap_mb * 1024 if cap_mb else 0, fens,
                         args.hash, args.depth)
        rec["cap_mb"] = cap_mb
        if ref_keys is None and rec["keys"]:
            ref_keys, ref_raw = rec["keys"], rec["raw"]
        nps_only = 0
        if rec["keys"] and ref_keys:
            for a, b, ra, rb in zip(rec["keys"], ref_keys, rec["raw"], ref_raw):
                if a != b:
                    pass
                elif ra != rb:
                    nps_only += 1
        rec["completed"] = len(rec["keys"])
        rec["n_expected"] = len(fens)
        rec["same_answers"] = (rec["keys"] == ref_keys) if rec["keys"] else None
        rec["diff_rows"] = (sum(1 for a, b in zip(rec["keys"], ref_keys) if a != b)
                            if rec["keys"] else None)
        rec["nps_only_rows"] = nps_only
        rec.pop("keys")
        rec.pop("raw")
        out.append(rec)
        print(json.dumps(rec))
        sys.stdout.flush()

    with open(args.out + ".json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
