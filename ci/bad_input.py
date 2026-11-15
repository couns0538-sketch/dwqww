"""Part C of the Fable/Opus checks: the engine must survive bad and unusual input, under AddressSanitizer + UBSan.
(Opus session, 2026-11-15; from Fable's job text HELPER_JOB2_glmflash.txt, part C.)

One engine process gets the inputs below one at a time. After each: isready, and readyok must come within 10 s.
After an input that starts a search, the search is stopped (stop, then bestmove within 60 s) so the next input
meets a quiet engine, except for the cases that are about overlapping commands. Then a health check: from the start
position, go depth 4 must show a real search (an info line with nodes above 0) and a legal move; if not, that is
a finding and a fresh engine takes over (so one broken state does not hide the later cases).
A finding is: AddressSanitizer, LeakSanitizer or UBSan output on stderr, a crash or an unexpected end of the
process, no readyok within 10 s, or a failed health check. The engine MAY end with "info string ERROR NNUE v3" and exit code 2 when told
to use a bad net file; that is recorded as "allowed exit", and a fresh engine continues.

    python bad_input.py <engine exe built with -fsanitize=address,undefined> <results dir>
Exit code: 0 = no finding; 1 = findings (summary.txt); 2 = the check itself failed.
"""
from __future__ import annotations

import json
import os
import sys
import time

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine, cut  # noqa: E402

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
SAN_MARKS = ("ERROR: AddressSanitizer", "ERROR: LeakSanitizer", "runtime error:", "SUMMARY: AddressSanitizer",
             "SUMMARY: UndefinedBehaviorSanitizer", "ThreadSanitizer")
OPTIONS = {"OwnBook": "false", "Threads": "1", "Hash": "16"}


def knight_shuffle(n: int) -> str:
    cycle = ["g1f3", "g8f6", "f3g1", "f6g8"]
    return " ".join(cycle[i % 4] for i in range(n))


def cases(text_file: str) -> list[tuple[str, list[str]]]:
    """(kind, lines to send) pairs. A case may send several lines (for example a position and then a go)."""
    c: list[tuple[str, list[str]]] = []
    add = lambda kind, *lines: c.append((kind, list(lines)))  # noqa: E731
    # unknown commands, empty lines, odd spacing and case
    for s in ["", " ", "\t", "foo", "hello world", "uci2", "isready now", "go2", "positionx startpos",
              "setoptionname Hash value 16", "   position startpos", "POSITION startpos", "Go depth 2",
              "position", "position startpos fen", "position fen", "moves e2e4", "debug on", "debug off",
              "register later", "ucinewgame now", "stop now"]:
        add("unknown or odd command", s)
    add("long line", "x" * 100000)
    add("long line", "position startpos moves " + "e2e4 " * 20000)
    add("long line", "setoption name " + "H" * 50000 + " value 1")
    # position fen with bad parts
    full = START + " w KQkq - 0 1"
    for fen in [START, START + " w", START + " w KQkq", START + " w KQkq -", START + " w KQkq - 0",
                full + " extra fields here",
                "rnbqkbnr/ppppxppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "rnbqkbnrp/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "9/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP w KQkq - 0 1",
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR/8 w KQkq - 0 1",
                "8/8/8/8/8/8/8/8 w - - 0 1",
                "4k3/8/8/8/8/8/8/3KK3 w - - 0 1",
                "4k3/8/8/8/8/8/8/8 w - - 0 1",
                START + " x KQkq - 0 1", START + " W KQkq - 0 1",
                START + " w KQkq e9 0 1", START + " w KQkq z3 0 1", START + " w KQkq e4 0 1",
                START + " w XYZ - 0 1", START + " w KQkqKQkq - 0 1",
                START + " w KQkq - -5 1", START + " w KQkq - 0 -1",
                START + " w KQkq - 99999999999999999999 1", START + " w KQkq - 0 4294967296",
                "rnbqkbnP/pppppppp/8/8/8/8/PPPPPPP1/RNBQKBNR w KQkq - 0 1",
                "4k3/8/8/8/8/8/4R3/4K3 w - - 0 1",
                "4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1",
                "4k3/8/8/8/8/8/8/4K3 w - e3 0 1",
                "k7/8/8/8/8/8/8/7K w - - 0 1"]:
        add("position fen", f"position fen {fen}", "go depth 3")
    # position startpos with bad moves
    for mv in ["e2e5", "e2-e4", "E2E4", "e2e4e5", "zz", "e2e4 e7e5 e1e3", "e7e5", "0000", "e2e4 0000 e7e5",
               "e1g1", "a1a1", "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 e1g1 f8c5 g1h1 h1h2"]:
        add("position startpos moves", f"position startpos moves {mv}", "go depth 3")
    add("position startpos moves", "position startpos moves", "go depth 3")
    add("promotion without piece letter", "position fen 8/P7/8/8/8/8/8/k6K w - - 0 1 moves a7a8", "go depth 3")
    add("promotion to a king", "position fen 8/P7/8/8/8/8/8/k6K w - - 0 1 moves a7a8k", "go depth 3")
    add("promotion to a pawn", "position fen 8/P7/8/8/8/8/8/k6K w - - 0 1 moves a7a8p", "go depth 3")
    add("600 legal moves", "position startpos moves " + knight_shuffle(600), "go depth 3")
    add("1200 legal moves", "position startpos moves " + knight_shuffle(1200), "go depth 3")
    # setoption
    for name, value in [("Foo", "3"), ("Hash", ""), ("Hash", "0"), ("Hash", "4096"), ("Hash", "abc"),
                        ("Hash", "-16"), ("Hash", "16.5"), ("Threads", "0"), ("Threads", "300"),
                        ("Threads", "two"), ("MultiPV", "0"), ("MultiPV", "99"), ("MultiPV", ""),
                        ("Move Overhead", "-1"), ("Move Overhead", "99999"), ("Ponder", "maybe"),
                        ("NNUEArch", "2"), ("UseNNUE", "perhaps"), ("Book Depth", "-3"),
                        ("Book Variety", "1000"), ("DrawJitter", "-1"), ("NonPawnCorrection", "yes"),
                        ("LmrQuietBase", "-999999"), ("LmrQuietBase", "999999999")]:
        add("setoption", f"setoption name {name} value {value}".rstrip(), "position startpos", "go depth 3")
    for s in ["setoption", "setoption name", "setoption value 3", "setoption name Hash value 16 extra words",
              "setoption name  Hash  value  16", "setoption name hash value 16", "setoption name Threads"]:
        add("setoption form", s)
    add("book file that does not exist", "setoption name Book File value /nonexistent/forge_ci_book.bin",
        "setoption name OwnBook value true", "go depth 3")
    add("book option back", "setoption name OwnBook value false")
    add("old net file that does not exist", "setoption name NnueFile value /nonexistent/forge_ci.nnue", "go depth 3")
    add("v3 net file that does not exist", "setoption name NNUEArchFile value /nonexistent/forge_ci_missing.fnn3",
        "setoption name NNUEArch value true", "go depth 3")
    add("v3 net file that is a text file", f"setoption name NNUEArchFile value {text_file}",
        "setoption name NNUEArch value true", "go depth 3")
    add("v3 net switched off again", "setoption name NNUEArch value false", "go depth 3")
    # go with odd limits
    for g in ["go depth 0", "go depth -1", "go nodes 0", "go movetime 0", "go movetime -5", "go depth abc",
              "go wtime -1000 btime -1000", "go wtime 0 btime 0", "go wtime 100", "go mate 1", "go mate -1",
              "go mate 0", "go searchmoves e2e4 depth 3", "go searchmoves z9z9 depth 3", "go searchmoves",
              "go movestogo 0 wtime 1000 btime 1000", "go winc -50 binc -50 wtime 1000 btime 1000",
              "go depth 3 nodes 1", "go nodes 99999999999999999999", "go perft 0", "go perft -1", "go perft 11",
              "go perft abc", "go"]:
        add("go", "position startpos", g)
    add("go in a checkmate", "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1", "go depth 5")
    add("go in a stalemate", "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "go depth 5")
    add("go in a checkmate, no limit", "position fen 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1", "go")
    add("go in a stalemate, perft", "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "go perft 3")
    add("stop without a search", "stop")
    add("ponderhit without ponder", "ponderhit")
    add("go ponder without the Ponder option", "position startpos moves e2e4", "go ponder wtime 10000 btime 10000")
    add("ucinewgame", "ucinewgame")
    add("ucinewgame twice", "ucinewgame", "ucinewgame")
    add("uci again", "uci")
    add("overlap: go depth 12, at once position and go", "position startpos", "go depth 12",
        "position startpos moves e2e4", "go depth 5")
    add("overlap: go infinite then stop after 1 s", "position startpos", "go infinite", "#sleep 1", "stop")
    add("overlap: two go in a row", "position startpos", "go infinite", "go depth 4")
    add("overlap: setoption during a search", "position startpos", "go infinite", "setoption name Hash value 32",
        "#sleep 0.3", "stop")
    add("overlap: ucinewgame during a search", "position startpos", "go infinite", "ucinewgame", "#sleep 0.3", "stop")
    add("bench with odd values", "bench -1")
    add("bench with odd values", "bench abc")
    add("bench with odd values", "bench 0")
    return c


def new_stderr(path: str, offset: int) -> tuple[str, int]:
    try:
        with open(path, "rb") as fh:
            fh.seek(offset)
            data = fh.read()
        return data.decode("utf-8", "replace"), offset + len(data)
    except OSError:
        return "", offset


def main() -> int:
    exe, res = sys.argv[1], sys.argv[2]
    os.makedirs(res, exist_ok=True)
    errpath = os.path.join(res, "engine_stderr.txt")
    rows: list[dict] = []
    findings: list[str] = []
    allowed_exits = 0
    starts = 0
    transcripts: list[str] = []

    def start() -> Engine:
        nonlocal starts
        starts += 1
        transcripts.append(f"===== engine start {starts}")
        e = Engine(exe, errpath)
        if not e.start_uci(OPTIONS):
            findings.append(f"engine start {starts}: no uciok/readyok")
        return e

    eng = start()
    offset = os.path.getsize(errpath) if os.path.exists(errpath) else 0
    all_cases = cases(os.path.abspath(__file__))
    t_all = time.time()
    for i, (kind, lines) in enumerate(all_cases, 1):
        row = {"n": i, "kind": kind, "input": [cut(x, 160) for x in lines]}
        t = time.time()
        for ln in lines:
            if ln.startswith("#sleep "):
                time.sleep(float(ln.split()[1]))
            else:
                eng.send(ln)
        t_ready = time.time()
        eng.send("isready")
        ok, got_lines = eng.wait_for("readyok", 10.0)
        row["readyok"] = ok
        row["seconds_to_readyok"] = round(time.time() - t_ready, 3)
        # A started search must answer with bestmove. A short one has usually answered already (its bestmove came
        # before readyok); a long one is stopped now so that the next case meets a quiet engine.
        n_go = sum(1 for x in lines if x.split()[:1] == ["go"] and "perft" not in x)
        seen = [x for x in got_lines if x.startswith("bestmove")]
        if ok and n_go and len(seen) < n_go:
            eng.send("stop")
            got, out = eng.wait_for("bestmove", 30.0)
            if got:
                seen.append(out[-1])
            elif not seen and eng.alive():
                findings.append(f"case {i} ({kind}): no bestmove at all within 30 s after stop")
        if n_go:
            row["bestmove"] = seen[-1] if seen else ("none" if eng.alive() else "engine gone")
        if not ok and eng.alive():
            try:                                      # an engine that is ending gets 3 s to be gone
                eng.p.wait(timeout=3)
            except Exception:  # noqa: BLE001
                pass
        printed = [x for x in eng.transcript[-12:] if " << " in x]
        row["engine_printed_last"] = [cut(x.split(" << ", 1)[1], 160) for x in printed[-4:]]
        # 1. sanitizer output of this case (read before any restart)
        text, offset = new_stderr(errpath, offset)
        san = [m for m in SAN_MARKS if m in text]
        if san:
            row["sanitizer"] = san
            findings.append(f"case {i} ({kind}): sanitizer output {san}; input {cut(' | '.join(lines), 200)}")
        # 2. the engine ended: allowed only for a bad net file (exit code 2 with "ERROR NNUE v3")
        if not eng.alive():
            rc = eng.p.returncode
            allowed = (rc == 2 and any("ERROR NNUE v3" in x for x in eng.transcript[-40:]))
            row["exit_code"] = rc
            row["exit"] = "allowed (bad net file, exit code 2)" if allowed else "UNEXPECTED"
            if allowed:
                allowed_exits += 1
            else:
                findings.append(f"case {i} ({kind}): the engine ended with exit code {rc}; input {cut(' | '.join(lines), 200)}")
            eng.close()
            transcripts.extend(eng.transcript)
            eng = start()
            text, offset = new_stderr(errpath, offset)
        elif not ok:
            findings.append(f"case {i} ({kind}): no readyok within 10 s; input {cut(' | '.join(lines), 200)}")
        # 3. health check: the engine must still search the start position normally after this input
        if eng.alive():
            eng.send("position startpos")
            eng.send("go depth 4")
            hc_ok, hc = eng.wait_for("bestmove", 30.0)
            searched = any(x.startswith("info depth") and " nodes " in x and " nodes 0 " not in x for x in hc)
            try:
                legal = bool(hc_ok and chess.Move.from_uci(hc[-1].split()[1]) in chess.Board().legal_moves)
            except (ValueError, IndexError):
                legal = False
            row["health_check"] = "ok" if (searched and legal) else f"FAILED ({cut(' / '.join(hc[-2:]), 160)})"
            if not (searched and legal):
                findings.append(f"case {i} ({kind}): afterwards the engine did not search the start position "
                                f"normally ({cut(' / '.join(hc[-2:]), 160)}); input {cut(' | '.join(lines), 200)}")
                text, offset = new_stderr(errpath, offset)
                if any(m in text for m in SAN_MARKS):
                    findings.append(f"case {i} ({kind}): sanitizer output during the health check")
                eng.close()
                transcripts.extend(eng.transcript)
                eng = start()
                text, offset = new_stderr(errpath, offset)
        row["seconds"] = round(time.time() - t, 3)
        rows.append(row)
    rc, secs = eng.quit(30.0)
    text, offset = new_stderr(errpath, offset)
    tail_san = [m for m in SAN_MARKS if m in text]
    if tail_san:
        findings.append(f"at the final quit: sanitizer output {tail_san}")
    if rc not in (0,):
        findings.append(f"the final quit gave exit code {rc}")
    summary = [f"Part C: {len(all_cases)} inputs in {len(set(k for k, _ in all_cases))} kinds, one engine process "
               f"(restarted {starts - 1} times), {(time.time() - t_all) / 60:.1f} minutes",
               f"readyok within 10 s: {sum(1 for r in rows if r.get('readyok'))} of {len(rows)} inputs; the others "
               f"ended the engine ({sum(1 for r in rows if 'exit' in r)}) or are listed below; slowest "
               f"{max(r['seconds_to_readyok'] for r in rows):.2f} s",
               f"health check (start position, go depth 4, real search and a legal move) passed after "
               f"{sum(1 for r in rows if r.get('health_check') == 'ok')} of {len(rows)} inputs",
               f"allowed exits (bad net file, exit code 2 with 'ERROR NNUE v3'): {allowed_exits}",
               f"final quit: exit code {rc} after {secs:.1f} s; stderr bytes in all: {os.path.getsize(errpath)}",
               "", "FINDINGS: " + ("none" if not findings else str(len(findings)))]
    summary += ["  " + f for f in findings]
    with open(os.path.join(res, "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(summary) + "\n")
    with open(os.path.join(res, "cases.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
    transcripts.extend(eng.transcript)
    with open(os.path.join(res, "transcript.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(transcripts) + "\n")
    print("\n".join(summary))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
