#!/usr/bin/env python3
"""check_s12f1.py -- MY OWN check of seat 12's S-F1: `ucinewgame` silently resets the board.

Every case is one fresh process, and every `go` is WAITED FOR (seat 19's 19-F12: closing stdin
mid-search fabricates a bestmove). Assertions: if a case yields no bestmove or no perft total,
the script exits 3 rather than reporting a verdict (seat 19's measurement-integrity rule).

usage: check_s12f1.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

FEN = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"
START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
ENDPOS = "4k3/8/8/8/8/8/2P1P3/4K3 w - - 0 1"


def session(exe, lines, terminal="bestmove", timeout=120.0):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out, err = [], []
    lock = threading.Lock()

    def pump(stream, sink):
        try:
            for l in stream:
                with lock:
                    sink.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, args=(p.stdout, out), daemon=True).start()
    threading.Thread(target=pump, args=(p.stderr, err), daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pred, timeout=timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                hit = pred(list(out))
            if hit is not None and hit is not False:
                return hit
            if p.poll() is not None:
                break
            time.sleep(0.004)
        return None

    send("uci")
    wait(lambda o: "uciok" if any(x.strip() == "uciok" for x in o) else None, 30)
    send("isready")
    wait(lambda o: "readyok" if any(x.strip() == "readyok" for x in o) else None, 30)

    results = []
    for line in lines:
        with lock:
            mark = len(out)
        send(line)
        if line.startswith("go"):
            def pred(o, mark=mark):
                block = o[mark:]
                if any(x.startswith("bestmove") for x in block):
                    return block
                return None
            block = wait(pred)
            results.append((line, block or []))
        elif line == "isready":
            wait(lambda o, mark=mark: True if any(x.strip() == "readyok"
                                                  for x in o[mark:]) else None, 30)
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        pass
    return results


def first_best(block):
    for l in block:
        if l.startswith("bestmove"):
            p = l.split()
            return p[1] if len(p) > 1 else None
    return None


def perft_total(block):
    for l in block:
        if l.startswith("nodes "):
            return int(l.split()[1])
    return None


def case_arm(exe, use_ucinewgame, go="go depth 4"):
    lines = ["position fen " + FEN]
    if use_ucinewgame:
        lines.append("ucinewgame")
        lines.append("isready")
    lines.append(go)
    res = session(exe, lines)
    block = res[-1][1]
    return {"bestmove": first_best(block), "perft": perft_total(block)}


def case_perft(exe, use_ucinewgame):
    lines = ["position fen " + FEN]
    if use_ucinewgame:
        lines.append("ucinewgame")
        lines.append("isready")
    lines.append("go perft 1")
    res = session(exe, lines)
    return {"perft1": perft_total(res[-1][1])}


def case_history(exe, use_ucinewgame):
    lines = [
        "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",
    ]
    if use_ucinewgame:
        lines += ["ucinewgame", "isready"]
    lines.append("go depth 4")
    res = session(exe, lines)
    return {"bestmove": first_best(res[-1][1])}


def case_warmth(exe):
    """P3: does ucinewgame restore a cold tree?  Fresh process vs warm 2nd search vs ucinewgame 2nd."""
    fen = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"

    def nodes_of(block):
        infos = [x for x in block if x.startswith("info") and " pv" in x]
        if not infos:
            return None
        t = infos[-1].split()
        return int(t[t.index("nodes") + 1]) if "nodes" in t else None

    fresh = session(exe, ["position fen " + fen, "go depth 12"])
    warm = session(exe, ["position fen " + fen, "go depth 12", "go depth 12"])
    newg = session(exe, ["position fen " + fen, "go depth 12", "ucinewgame", "isready",
                         "position fen " + fen, "go depth 12"])
    return {
        "fresh_process_first_search": nodes_of(fresh[0][1]),
        "warm_second_search": nodes_of(warm[1][1]),
        "second_search_after_ucinewgame": nodes_of(newg[2][1]),
    }


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    out = {"exe": os.path.realpath(exe), "fen": FEN,
           "start_fen": START_FEN, "endpos": ENDPOS}
    out["A_no_ucinewgame"] = case_arm(exe, False)
    out["B_with_ucinewgame"] = case_arm(exe, True)
    out["C_perft_no_ucinewgame"] = case_perft(exe, False)
    out["D_perft_with_ucinewgame"] = case_perft(exe, True)
    out["E_history_no_ucinewgame"] = case_history(exe, False)
    out["F_history_with_ucinewgame"] = case_history(exe, True)
    out["G_warmth"] = case_warmth(exe)

    print(json.dumps(out, indent=1))

    missing = []
    for k in ("A_no_ucinewgame", "B_with_ucinewgame", "E_history_no_ucinewgame",
              "F_history_with_ucinewgame"):
        if not out[k].get("bestmove"):
            missing.append(k + ".bestmove")
    for k in ("C_perft_no_ucinewgame", "D_perft_with_ucinewgame"):
        if out[k].get("perft1") is None:
            missing.append(k + ".perft1")
    for k, v in out["G_warmth"].items():
        if v is None:
            missing.append("G_warmth." + k)
    if missing:
        print("FAIL: nothing parsed for: %s" % ", ".join(missing))
        print("(an empty result must not be able to pass as a confirmation)")
        raise SystemExit(3)

    with open(os.path.join(outdir, "results.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
