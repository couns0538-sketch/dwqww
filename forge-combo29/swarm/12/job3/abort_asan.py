#!/usr/bin/env python3
"""abort_asan.py EXE OUTFILE [--pc20] [--planted PLANTED_EXE] — the aborted-search fault on a
sanitizer build, with the two proofs a sanitizer zero requires.

Part 1 counts, over N fresh processes, how often an aborted search publishes a bestmove with no
`info depth` line (a fabricated answer), and records every sanitizer line.

Part 2 is the planted-fault proof, driven through the SAME case runner: a scratch copy of this
same engine with one heap over-read and one signed overflow behind commands the harness sends. If
Part 1 reports zero sanitizer lines, Part 2 must report at least one through the same code path,
or the zero is "not shown".
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

SAN = re.compile(r"ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: (Address|Undefined|Leak)Sanitizer|runtime error: ")

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
GO_FORMS = [("bounded", "go depth 12"), ("unbounded", "go infinite")]


def one_run(exe, opts, go, extra_cmds=()):
    """One fresh process; send opts, position, go, then quit at once. Returns the transcript."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1,
                         env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                              "UBSAN_OPTIONS": "print_stacktrace=1"})
    out = []
    q = queue.Queue()
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()
    try:
        p.stdin.write("uci\n")
        p.stdin.flush()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            ln = q.get(timeout=0.5)
            if ln is None:
                break
            out.append(ln)
            if ln == "uciok":
                break
        for n, v in opts:
            p.stdin.write(f"setoption name {n} value {v}\nisready\n")
            p.stdin.flush()
            while time.monotonic() < deadline:
                ln = q.get(timeout=0.5)
                if ln is None:
                    break
                out.append(ln)
                if ln == "readyok":
                    break
        for c in extra_cmds:
            p.stdin.write(c + "\n")
            p.stdin.flush()
        p.stdin.write(f"position fen {FEN}\nisready\n{go}\nquit\n")
        p.stdin.flush()
        p.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    end = time.monotonic() + 3
    while time.monotonic() < end:
        try:
            ln = q.get(timeout=0.1)
        except queue.Empty:
            if p.poll() is not None:
                break
            continue
        if ln is None:
            break
        out.append(ln)
    return out, p.returncode


def classify(lines):
    infos = [l for l in lines if l.startswith("info depth")]
    bms = [l for l in lines if l.startswith("bestmove")]
    return {
        "bestmove": bms[-1].split()[1] if bms else None,
        "info_depth_lines": len(infos),
        "fabricated": bool(bms) and not infos,
        "sanitizer_lines": [l for l in lines if SAN.search(l)][:6],
    }


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    opts = PC20 if "--pc20" in sys.argv else []
    label = "PC20" if opts else "none"
    reps = 25
    out = {"exe": exe, "settings": label, "threads": 1, "reps": reps, "parts": []}
    print(f"exe {exe}\nsettings {label}, Threads 1 (no Threads option sent), {reps} reps per form")

    total_san = 0
    for name, go in GO_FORMS:
        fab = 0
        san = 0
        moves = {}
        for _ in range(reps):
            lines, rc = one_run(exe, opts, go)
            c = classify(lines)
            fab += c["fabricated"]
            san += len(c["sanitizer_lines"])
            moves[c["bestmove"]] = moves.get(c["bestmove"], 0) + 1
        total_san += san
        print(f"  {name:10} ({go:12}) fabricated {fab}/{reps}  sanitizer lines {san}  moves {moves}")
        out["parts"].append({"form": name, "go": go, "fabricated": fab, "reps": reps,
                             "sanitizer_lines": san, "moves": moves})

    out["total_sanitizer_lines"] = total_san
    print(f"\ntotal sanitizer lines across both forms: {total_san}")

    if "--planted" in sys.argv:
        pexe = sys.argv[sys.argv.index("--planted") + 1]
        print(f"\nplanted-fault proof through the SAME run function: {pexe}")
        lines, rc = one_run(pexe, [], "go depth 1",
                            extra_cmds=("plantedasan", "isready", "plantedubsan", "isready"))
        hits = [l for l in lines if SAN.search(l)]
        print(f"  exit code {rc}; sanitizer lines counted: {len(hits)}")
        for h in hits[:4]:
            print(f"    {h}")
        out["planted"] = {"exe": pexe, "sanitizer_lines": hits[:6], "count": len(hits), "rc": rc}
        if total_san == 0 and len(hits) == 0:
            print("\nWARNING: zero elsewhere AND zero in the plant -> the zero is NOT SHOWN")

    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nraw -> {outfile}")


if __name__ == "__main__":
    main()
