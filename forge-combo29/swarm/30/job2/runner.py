#!/usr/bin/env python3
"""runner.py -- MY OWN UCI sequence runner (written from the brief; not a copy of deepseek6's).

Measured engine facts this runner relies on (each with its own command, see FACTS_job2.md):
  F1. The engine emits EXACTLY ONE `bestmove` line per `go` line -- also for "go banana",
      "go depth -3", a bare "go", "go depth 0", "go nodes 0", "go movetime 0".
      Verified in bulk: 83 sequences carried 191 bounded + 107 open + 53 invalid go lines
      and 351 bestmove lines (351 = 191+107+53); and by hand for each odd form.
  F2. `ucinewgame` RESETS the board to the start position (src/uci.cpp:257), so a
      `ucinewgame` after a `position` command throws that position away.
  F3. `go` sent while another search runs still yields one bestmove per go, in order, so
      the i-th bestmove belongs to the i-th go.
  F4. An illegal move inside `position ... moves` keeps the legal prefix (known; reproduced).

Attribution rule, therefore: the i-th `bestmove` is the answer to the i-th `go`. Nothing is
guessed: a sequence whose `bestmove` count differs from its `go` count is counted
`unpaired` and NONE of its bestmoves is used for the legality check.

The position of each `go` is tracked here with python-chess from the `position` /
`ucinewgame` lines themselves. A bounded `go` (a positive depth/nodes/softnodes/movetime)
is waited for, so the next line is not sent into a still-running search; an unbounded one
is not waited for.

Every sequence runs in its own process. `isready` must produce a `readyok` within
READY_TIMEOUT seconds, else HANG (process killed, sequence kept, reason ready_timeout).
A process that will not exit after `quit` is HANG (reason exit_timeout). A non-zero exit
is a crash. Sanitizer output on stderr is counted, first lines kept.

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
BESTMOVE_WAIT = 15.0
EXIT_WAIT = 20.0
SAN_PAT = re.compile(r"AddressSanitizer|LeakSanitizer|ThreadSanitizer|runtime error|SUMMARY:")


def is_bounded_go(line):
    """A `go` with a positive depth/nodes/softnodes/movetime value: it ends by itself."""
    toks = line.split()[1:]
    for i, t in enumerate(toks[:-1]):
        if t in ("depth", "nodes", "softnodes", "movetime"):
            v = toks[i + 1]
            if v.lstrip("-").isdigit() and int(v) > 0:
                return True
    return False


def parse_position(line, prev_board):
    toks = line.split()
    if len(toks) < 2:
        return prev_board
    if toks[1] == "startpos":
        board, rest = chess.Board(), toks[2:]
    elif toks[1] == "fen":
        try:
            board = chess.Board(" ".join(toks[2:8]))
        except ValueError:
            return prev_board      # engine refuses an unparsable FEN, keeps the old board
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
                break              # engine keeps the legal prefix (F4)
            board.push(m)
    return board


def judge(bm, bd):
    legal = {m.uci() for m in bd.legal_moves}
    if bm == "0000":
        return None if not legal else {"bestmove": bm, "fen": bd.fen(),
                                       "why": "0000 with legal moves"}
    if bm not in legal:
        return {"bestmove": bm, "fen": bd.fen(), "why": "not legal"}
    return None


def run_one(idx, lines, exe):
    rec = {"seq": idx, "crash": 0, "hangs": 0, "hang_reason": None, "san": [], "san_count": 0,
           "exit": None, "go": 0, "bounded": 0, "bestmoves": 0, "checked": 0,
           "illegal": [], "unpaired": 0, "no_bestmove": 0, "readyok": 0, "ready_sent": 0,
           "runner_error": None}
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1, env=env,
                         start_new_session=True)
    out_lines, err_lines = [], []
    olock = threading.Lock()

    def pump(stream, sink, lock=None):
        try:
            for l in stream:
                if lock is None:
                    sink.append(l.rstrip("\n"))
                else:
                    with lock:
                        sink.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, args=(p.stdout, out_lines, olock), daemon=True).start()
    threading.Thread(target=pump, args=(p.stderr, err_lines), daemon=True).start()

    def n_best():
        with olock:
            return sum(1 for l in out_lines if l.startswith("bestmove"))

    def best_list():
        with olock:
            return [l.split()[1] if len(l.split()) > 1 else ""
                    for l in out_lines if l.startswith("bestmove")]

    def wait_best(k, timeout):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if n_best() > k:
                return True
            if p.poll() is not None:
                return n_best() > k
            time.sleep(0.005)
        return n_best() > k

    def send(line):
        try:
            p.stdin.write(line + "\n")
            p.stdin.flush()
            return True
        except (BrokenPipeError, ValueError, OSError):
            return False

    board = chess.Board()
    go_boards = []
    pending_go = 0          # gos written whose bestmove has not been consumed yet
    try:
        for line in lines:
            s = line.strip()
            if s == "ucinewgame":
                board = chess.Board()          # F2
            if s.startswith("position"):
                board = parse_position(s, board)
            with olock:
                mark = len(out_lines)          # taken BEFORE the write: nothing missed
            k_before = n_best()
            if not send(line):
                break
            if s.startswith("go"):
                rec["go"] += 1
                go_boards.append(board.copy(stack=False))
                pending_go += 1
                if is_bounded_go(s):
                    rec["bounded"] += 1
                    if wait_best(k_before, BESTMOVE_WAIT):
                        pending_go -= 1
                    else:
                        rec["no_bestmove"] += 1
            elif s == "stop":
                if pending_go and wait_best(n_best(), BESTMOVE_WAIT):
                    pending_go -= 1
            elif s == "isready":
                rec["ready_sent"] += 1
                ok = False
                t0 = time.monotonic()
                while time.monotonic() - t0 < READY_TIMEOUT:
                    with olock:
                        if any(x.strip() == "readyok" for x in out_lines[mark:]):
                            ok = True
                            break
                    if p.poll() is not None:
                        break
                    time.sleep(0.005)
                if not ok:
                    rec["hangs"] += 1
                    rec["hang_reason"] = "ready_timeout"
                    break
                rec["readyok"] += 1
        # 19-F12: never close stdin while a search is live -- the engine then answers a
        # FABRICATED bestmove (a2a3, 0 nodes). So stop the search, wait for the real
        # bestmove, and only then quit.
        if p.poll() is None:
            if pending_go:
                k0 = n_best()
                send("ponderhit")   # a pending ponder search answers this, not stop
                wait_best(k0, 2.0)
                if n_best() == k0:
                    send("stop")
                    wait_best(k0, 2.0)
            send("quit")
        try:
            p.wait(timeout=EXIT_WAIT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                pass
            rec["hangs"] += 1
            rec["hang_reason"] = "exit_timeout"
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
    rec["san"], rec["san_count"] = san[:5], len(san)
    bests = best_list()
    rec["bestmoves"] = len(bests)
    if len(bests) == len(go_boards):
        for bm, bd in zip(bests, go_boards):
            rec["checked"] += 1
            bad = judge(bm, bd)
            if bad:
                rec["illegal"].append(bad)
    else:
        rec["unpaired"] = abs(len(bests) - len(go_boards))
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
            r = {"seq": i, "runner_error": repr(e)}
        r["lines"] = seqs[i]
        with lock:
            results.append(r)

    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, range(len(seqs))))
    wall = time.monotonic() - t0

    sums = ("crash", "hangs", "san_count", "no_bestmove", "unpaired", "checked",
            "go", "bounded", "bestmoves", "readyok", "ready_sent")
    agg = {"sequences": len(seqs), "wall_seconds": round(wall, 1), "workers": workers,
           "illegal_bestmoves": sum(len(r.get("illegal", [])) for r in results),
           "runner_errors": sum(1 for r in results if r.get("runner_error")),
           "hang_reasons": {}}
    for k in sums:
        agg[k] = sum(r.get(k, 0) for r in results)
    for r in results:
        if r.get("hang_reason"):
            agg["hang_reasons"][r["hang_reason"]] = agg["hang_reasons"].get(r["hang_reason"], 0) + 1

    with open(os.path.join(outdir, "records.jsonl"), "w") as f:
        for r in sorted(results, key=lambda x: x["seq"]):
            f.write(json.dumps({k: v for k, v in r.items() if k != "lines"}) + "\n")
    with open(os.path.join(outdir, "bad_sequences.txt"), "w") as f:
        for r in sorted(results, key=lambda x: x["seq"]):
            if r.get("crash") or r.get("hangs") or r.get("san_count") or r.get("illegal") \
                    or r.get("runner_error"):
                f.write("### seq %d: %s\n" % (r["seq"], json.dumps(
                    {k: r.get(k) for k in ("crash", "hangs", "hang_reason", "san", "exit",
                                           "illegal", "runner_error")})))
                f.write("\n".join(r["lines"]) + "\n\n")
    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(agg, f, indent=1)
    print(json.dumps(agg))


if __name__ == "__main__":
    main()
