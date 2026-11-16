#!/usr/bin/env python3
"""check_s01f5.py -- MY OWN reproduction of seat 01's S-F5 (halfmove >= 100 hides a mate in 1).

Written from the finding's sentence and its FEN list. One fresh engine process per case,
fully synchronised: `position fen` -> `isready`/`readyok` -> `go depth 6` -> WAIT for this
search's `bestmove` -> `quit`. The waiting is the point: my first version of this check
piped `quit` straight after `go` and the engine aborted every search, which looked like a
"missed mate at every counter" - a harness fault, caught by the hm-0 row disagreeing with
seat 01's own hm-0 row. That bug is recorded in the report, not hidden.

usage: check_s01f5.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

GO = "go depth 6"
TIMEOUT = 60.0
MATE1 = "6k1/5ppp/8/8/8/8/5PPP/R5K1"
QUIET = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R"
COUNTERS = [0, 97, 98, 99, 100, 101, 150]


def mate_in_one(fen):
    b = chess.Board(fen)
    out = []
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate():
            out.append(mv.uci())
        b.pop()
    return out


def run_case(exe, fen, go=GO):
    rec = {"fen": fen, "go": go, "score": None, "bestmove": None, "nodes": None,
           "info_lines": 0, "refused": None, "raw": []}
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out = []
    lock = threading.Lock()

    def pump():
        for l in p.stdout:
            with lock:
                out.append(l.rstrip("\n"))

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait_for(pred, timeout=TIMEOUT):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                if pred():
                    return True
            if p.poll() is not None:
                with lock:
                    return pred()
            time.sleep(0.003)
        return False

    send("uci")
    wait_for(lambda: any(x.strip() == "uciok" for x in out))
    send("isready")
    wait_for(lambda: any(x.strip() == "readyok" for x in out))
    n_before = None
    with lock:
        n_before = len(out)
    send("position fen " + fen)
    send("isready")
    wait_for(lambda: any(x.strip() == "readyok" for x in out[n_before:]))
    with lock:
        refused = [x for x in out[n_before:] if "invalid FEN" in x]
    rec["refused"] = refused
    with lock:
        start = len(out)
    send(go)
    got = wait_for(lambda: any(x.startswith("bestmove") for x in out[start:]))
    with lock:
        block = out[start:]
    rec["raw"] = block
    if got:
        for l in block:
            if l.startswith("bestmove"):
                parts = l.split()
                rec["bestmove"] = parts[1] if len(parts) > 1 else ""
        infos = [l for l in block if l.startswith("info") and " pv" in l]
        rec["info_lines"] = len(infos)
        if infos:
            toks = infos[-1].split()
            if "score" in toks:
                i = toks.index("score")
                rec["score"] = " ".join(toks[i + 1:i + 3])
            if "nodes" in toks:
                rec["nodes"] = toks[toks.index("nodes") + 1]
    send("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(p.pid), 9)
    rec["exit"] = p.returncode
    return rec


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    meta = {
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "exe": os.path.realpath(exe),
        "id_name": None, "asan_syms": 0, "ubsan_syms": 0,
        "options_sent": ["uci", "isready", "position fen <FEN>", "isready", GO, "quit"],
        "env_sanitizer_vars": [k for k in os.environ
                               if k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS",
                                        "LSAN_OPTIONS")],
    }
    u = subprocess.run([exe], input="uci\nisready\nquit\n", capture_output=True, text=True)
    for l in u.stdout.splitlines():
        if l.startswith("id name"):
            meta["id_name"] = l
    nm = subprocess.run(["nm", "-C", exe], capture_output=True, text=True).stdout
    meta["asan_syms"] = nm.count("__asan_")
    meta["ubsan_syms"] = nm.count("__ubsan_")
    h = subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0]
    meta["sha256"] = h
    with open(os.path.join(outdir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)

    rows = []
    for hm in COUNTERS:
        fen = "%s w - - %d 1" % (MATE1, hm)
        r = run_case(exe, fen)
        r["case"] = "mate1_hm%d" % hm
        r["python_chess_mate_in_1"] = mate_in_one(fen)
        rows.append(r)
        print("%-12s score=%-12s bestmove=%-6s nodes=%-5s mates=%s" % (
            r["case"], r["score"], r["bestmove"], r["nodes"], r["python_chess_mate_in_1"]))
    for hm in (0, 99, 100):
        fen = "%s w KQkq - %d 1" % (QUIET, hm)
        r = run_case(exe, fen)
        r["case"] = "quiet_hm%d" % hm
        r["python_chess_mate_in_1"] = mate_in_one(fen)
        rows.append(r)
        print("%-12s score=%-12s bestmove=%-6s nodes=%-5s mates=%s" % (
            r["case"], r["score"], r["bestmove"], r["nodes"], r["python_chess_mate_in_1"]))

    # controls: the same board with the rook removed (no mate in 1 exists)
    for hm in (0, 99, 100):
        fen = "6k1/5ppp/8/8/8/8/5PPP/6K1 w - - %d 1" % hm
        r = run_case(exe, fen)
        r["case"] = "norook_hm%d" % hm
        r["python_chess_mate_in_1"] = mate_in_one(fen)
        rows.append(r)
        print("%-12s score=%-12s bestmove=%-6s nodes=%-5s mates=%s" % (
            r["case"], r["score"], r["bestmove"], r["nodes"], r["python_chess_mate_in_1"]))

    # P5: whose move it is must not matter to root_drawn -- black to move, mate in 1 for BLACK
    for hm in (99, 100):
        fen = "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - %d 1" % hm
        r = run_case(exe, fen)
        r["case"] = "black_mate1_hm%d" % hm
        r["python_chess_mate_in_1"] = mate_in_one(fen)
        rows.append(r)
        print("%-12s score=%-12s bestmove=%-6s nodes=%-5s mates=%s" % (
            r["case"], r["score"], r["bestmove"], r["nodes"], r["python_chess_mate_in_1"]))

    with open(os.path.join(outdir, "results.json"), "w") as f:
        json.dump(rows, f, indent=1)
    with open(os.path.join(outdir, "table.tsv"), "w") as f:
        f.write("case\tfen\tscore\tbestmove\tnodes\tinfo_lines\tpy_mate_in_1\n")
        for r in rows:
            f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                r["case"], r["fen"], r["score"], r["bestmove"], r["nodes"],
                r["info_lines"], ",".join(r["python_chess_mate_in_1"]) or "-"))
    print(json.dumps({"rows": len(rows), "meta": meta["sha256"]}))


if __name__ == "__main__":
    main()
