#!/usr/bin/env python3
"""runner.py -- MY OWN UCI sequence runner (written from the brief; not a copy of deepseek6's).

Differences from a naive runner, and why: a bestmove can only be attributed to a search
when the searches do not overlap. So after writing a BOUNDED `go` (depth/nodes/movetime/
softnodes with a valid value) the runner WAITS for that go's `bestmove` (BESTMOVE_WAIT
seconds; a go that produces none is counted `no_bestmove`, not a hang). A `go infinite` /
`go ponder` is not awaited: it is put on the pending list and its bestmove comes after
`stop` / `ponderhit` / `quit`. A bestmove is matched to the OLDEST pending go; if that
leaves a mismatch the sequence is counted `unpaired` and its bestmoves are NOT used for
the legality check. Invalid go lines ("go banana", "go depth -3") wait for nothing.

Every sequence runs in its own process. `isready` must be answered by `readyok` within
READY_TIMEOUT seconds, else the sequence is a HANG (process killed, sequence kept).
A non-zero exit is a crash. Sanitizer output on stderr is counted and kept.

usage: runner.py EXE SEQFILE OUTDIR [WORKERS]
"""
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import chess

READY_TIMEOUT = 20.0
BESTMOVE_WAIT = 12.0
EXIT_WAIT = 20.0
SAN_PAT = re.compile(r"AddressSanitizer|LeakSanitizer|ThreadSanitizer|runtime error|SUMMARY:")


def go_kind(line):
    """-> 'bounded' | 'open' | 'invalid' for a `go` line (UCI grammar subset)."""
    toks = line.split()[1:]
    i = 0
    seen_bounded = False
    seen_open = False
    while i < len(toks):
        t = toks[i]
        if t in ("depth", "nodes", "softnodes", "movetime", "movestogo", "wtime", "btime"):
            if i + 1 >= len(toks):
                return "invalid"
            try:
                v = int(toks[i + 1])
            except ValueError:
                return "invalid"
            if v < 0:
                return "invalid"
            if t in ("depth", "nodes", "softnodes", "movetime") and v > 0:
                seen_bounded = True
            i += 2
            continue
        if t in ("infinite", "ponder"):
            seen_open = True
            i += 1
            continue
        if t in ("winc", "binc"):
            if i + 1 >= len(toks) or not toks[i + 1].lstrip("-").isdigit():
                return "invalid"
            i += 2
            continue
        if t in ("searchmoves", "mate"):
            return "invalid"
        return "invalid"   # unknown token: the engine will not search
    if seen_bounded:
        return "bounded"
    if seen_open:
        return "open"
    return "invalid"


def parse_position(line, prev_board):
    toks = line.split()
    if len(toks) < 2:
        return prev_board
    if toks[1] == "startpos":
        board = chess.Board()
        rest = toks[2:]
    elif toks[1] == "fen":
        fields = toks[2:8]
        try:
            board = chess.Board(" ".join(fields))
        except ValueError:
            return prev_board
        rest = toks[8:]
    else:
        return prev_board
    if rest and rest[0] == "moves":
        for mv in rest[1:]:
            try:
                m = chess.Move.from_uci(mv)
            except ValueError:
                break
            if m not in board.legal_moves:
                break
            board.push(m)
    return board


def run_one(idx, lines, exe):
    rec = {"seq": idx, "crash": 0, "hangs": 0, "san": [], "san_count": 0, "exit": None,
           "go_bounded": 0, "go_open": 0, "go_invalid": 0, "bestmoves": 0,
           "checked": 0, "illegal": [], "unpaired": 0, "no_bestmove": 0,
           "readyok": 0, "ready_sent": 0, "runner_error": None, "lines": lines}
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out_lines, err_lines = [], []
    olock = threading.Lock()

    def reader(stream, sink, lock=None):
        try:
            for l in stream:
                if lock:
                    with lock:
                        sink.append(l.rstrip("\n"))
                else:
                    sink.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=reader, args=(p.stdout, out_lines, olock), daemon=True).start()
    threading.Thread(target=reader, args=(p.stderr, err_lines), daemon=True).start()

    def bestmove_positions():
        with olock:
            return [i for i, l in enumerate(out_lines) if l.startswith("bestmove")]

    def count_bestmoves():
        return len(bestmove_positions())

    def wait_for(pred, timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if pred():
                return True
            if p.poll() is not None:
                return pred()
            time.sleep(0.005)
        return pred()

    board = chess.Board()
    pending = []        # boards of bounded/open gos whose bestmove has not been seen
    try:
        for line in lines:
            s = line.strip()
            if s.startswith("position"):
                board = parse_position(s, board)
            n_before = count_bestmoves()
            try:
                p.stdin.write(line + "\n")
                p.stdin.flush()
            except Exception:
                break
            if s.startswith("go"):
                kind = go_kind(s)
                if kind in ("bounded", "open"):
                    pending.append(board.copy(stack=False))
                    rec["go_bounded" if kind == "bounded" else "go_open"] += 1
                else:
                    rec["go_invalid"] += 1
                if kind == "bounded":
                    if wait_for(lambda: count_bestmoves() > n_before, BESTMOVE_WAIT):
                        idx_bm = bestmove_positions()[n_before]
                        bm = out_lines[idx_bm].split()[1] if len(out_lines[idx_bm].split()) > 1 else ""
                        if len(pending) != 1:
                            # an older search is still open: the bestmove cannot be
                            # attributed with certainty, so it is NOT used for the check
                            rec["unpaired"] += 1
                            pending.clear()
                        else:
                            bd = pending.pop(0)
                            rec["checked"] += 1
                            legal = {m.uci() for m in bd.legal_moves}
                            if bm == "0000":
                                if legal:
                                    rec["illegal"].append({"bestmove": bm, "fen": bd.fen(),
                                                           "why": "0000 with legal moves"})
                            elif bm not in legal:
                                rec["illegal"].append({"bestmove": bm, "fen": bd.fen(),
                                                       "why": "not legal"})
                    else:
                        rec["no_bestmove"] += 1
                        if pending:
                            pending.pop(0)
            elif s == "isready":
                rec["ready_sent"] += 1
                n_out = len(out_lines)
                ok = wait_for(lambda: any(x.strip() == "readyok" for x in out_lines[n_out:]),
                              READY_TIMEOUT)
                if not ok:
                    rec["hangs"] += 1
                    break
                rec["readyok"] += 1
        if p.poll() is None:
            try:
                p.stdin.write("quit\n")
                p.stdin.flush()
            except Exception:
                pass
        try:
            p.wait(timeout=EXIT_WAIT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                pass
            rec["hangs"] += 1
    except Exception as e:
        rec["runner_error"] = repr(e)
    finally:
        if p.poll() is None:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                pass
        time.sleep(0.02)

    rec["exit"] = p.returncode
    if p.returncode not in (0, -15, 15) and not rec["hangs"]:
        rec["crash"] = 1
    san = [l for l in err_lines if SAN_PAT.search(l)]
    rec["san"] = san[:5]
    rec["san_count"] = len(san)
    rec["bestmoves"] = count_bestmoves()
    rec["unpaired"] += abs(rec["bestmoves"] - (rec["go_bounded"] + rec["go_open"]))
    rec.pop("lines", None)
    return rec


def main():
    exe, seqfile, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    seqs, cur = [], None
    with open(seqfile) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("### seq "):
                cur = []
                seqs.append(cur)
            elif cur is not None:
                cur.append(line)
    os.makedirs(outdir, exist_ok=True)
    results, lock = [], threading.Lock()

    def work(i):
        try:
            r = run_one(i, seqs[i], exe)
        except Exception as e:
            r = {"seq": i, "runner_error": repr(e), "crash": 0, "hangs": 0,
                 "san": [], "san_count": 0, "illegal": [], "checked": 0, "unpaired": 0,
                 "no_bestmove": 0, "go_bounded": 0, "go_open": 0, "go_invalid": 0,
                 "bestmoves": 0, "exit": None, "readyok": 0, "ready_sent": 0}
        r["lines"] = seqs[i]
        with lock:
            results.append(r)

    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, range(len(seqs))))
    wall = time.monotonic() - t0

    keys = ("crash", "hangs", "san_count", "no_bestmove", "unpaired")
    agg = {"sequences": len(seqs), "wall_seconds": round(wall, 1), "workers": workers,
           "illegal_bestmoves": sum(len(r["illegal"]) for r in results),
           "bestmoves_checked": sum(r["checked"] for r in results),
           "go_bounded": sum(r["go_bounded"] for r in results),
           "go_open": sum(r["go_open"] for r in results),
           "go_invalid": sum(r["go_invalid"] for r in results),
           "bestmoves_seen": sum(r["bestmoves"] for r in results),
           "readyok": sum(r["readyok"] for r in results),
           "ready_sent": sum(r["ready_sent"] for r in results),
           "runner_errors": sum(1 for r in results if r.get("runner_error"))}
    for k in keys:
        agg[k] = sum(r.get(k, 0) for r in results)

    with open(os.path.join(outdir, "records.jsonl"), "w") as f:
        for r in sorted(results, key=lambda x: x["seq"]):
            r2 = {k: v for k, v in r.items() if k != "lines"}
            f.write(json.dumps(r2) + "\n")
    with open(os.path.join(outdir, "bad_sequences.txt"), "w") as f:
        for r in sorted(results, key=lambda x: x["seq"]):
            if r["crash"] or r["hangs"] or r["san_count"] or r["illegal"] or r.get("runner_error"):
                f.write("### seq %d: %s\n" % (r["seq"], json.dumps(
                    {k: r.get(k) for k in ("crash", "hangs", "san", "exit", "illegal",
                                           "runner_error")})))
                f.write("\n".join(r["lines"]) + "\n\n")
    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(agg, f, indent=1)
    print(json.dumps(agg))


if __name__ == "__main__":
    main()
