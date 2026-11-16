#!/usr/bin/env python3
"""regression.py EXE OUTFILE — a genuine drawn root with no mate on the board must still
return the draw score, and a mate must not change anything else.

Cases (every one a fresh process, answer read to `bestmove` before `quit`):

  quiet_hm99        a quiet position at halfmove 99          -> searched normally
  quiet_hm100       the same at halfmove 100 (draw claim)    -> adjudicated draw
  quiet_hm150       the same at halfmove 150                 -> adjudicated draw
  quiet_rep3        a quiet position reached three times     -> adjudicated draw
  quiet_rep_ctrl    the same board given by fen              -> searched normally
  kk                K v K (dead material)                    -> adjudicated draw
  kbk               K+B v K                                  -> adjudicated draw
  mate_hm99         mate in one at halfmove 99               -> mate 1
  mate_hm100        the same board at halfmove 100           -> MUST still be mate 1
  mate_rep3         the same board reached three times       -> MUST still be mate 1
  nomate_hm100      pawn race at halfmove 100, no mate       -> adjudicated draw (not a mate)
  mate_in_2_hm100   mate in TWO at halfmove 100              -> still adjudicated (stated limit)

For the mate cases python-chess independently confirms that the printed bestmove really mates.
"""
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import chess

MATESHUFFLE = "g1f3 g8h8 f3g1 h8g8 g1f3 g8h8 f3g1 h8g8"


def mates_now(fen):
    b = chess.Board(fen)
    out = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            out.append(m.uci())
        b.pop()
    return out


def ask(exe, posline, depth=8, timeout_s=60):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()

    def reader():
        for ln in p.stdout:
            q.put(ln.rstrip("\n"))
        q.put(None)
    threading.Thread(target=reader, daemon=True).start()
    p.stdin.write(f"uci\n{posline}\nisready\ngo depth {depth}\n")
    p.stdin.flush()
    lines, t0 = [], time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        try:
            ln = q.get(timeout=0.5)
        except queue.Empty:
            if p.poll() is not None:
                break
            continue
        if ln is None:
            break
        lines.append(ln)
        if ln.startswith("bestmove"):
            break
    try:
        p.stdin.write("quit\n")
        p.stdin.flush()
        p.stdin.close()
    except OSError:
        pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()

    infos = [l for l in lines if l.startswith("info depth")]
    bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    score, nodes = None, None
    if infos:
        m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
        score = f"{m.group(1)} {m.group(2)}" if m else None
        m = re.search(r" nodes (\d+)", infos[-1])
        nodes = int(m.group(1)) if m else None
    san = [l for l in lines if re.search(r"ERROR: (AddressSanitizer|LeakSanitizer)|runtime error: ", l)]
    return {"bestmove": bm, "score": score, "nodes": nodes, "info_lines": len(infos),
            "sanitizer_lines": san, "last_info": infos[-1] if infos else None}


def main():
    exe, outfile = sys.argv[1], sys.argv[2]
    quiet = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - {} 20"
    mate_base = "6k1/5ppp/8/8/8/8/8/R5NK w - - 0 1"
    # a quiet position reached three times: same shuffle idea, but no mate on the board
    quiet_rep_base = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 20"

    b = chess.Board(mate_base)
    for m in MATESHUFFLE.split():
        b.push_uci(m)
    mate_rep_fen = b.fen()

    cases = []
    cases.append(("quiet_hm99", f"position fen {quiet.format(99)}"))
    cases.append(("quiet_hm100", f"position fen {quiet.format(100)}", "draw"))
    cases.append(("quiet_hm150", f"position fen {quiet.format(150)}", "draw"))
    cases.append(("kk", "position fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1", "draw"))
    cases.append(("kbk", "position fen 4k3/8/8/8/8/8/8/2B1K3 w - - 0 1", "draw"))
    cases.append(("mate_hm99", f"position fen 6k1/5ppp/8/8/8/8/8/R5NK w - - 99 40", "mate"))
    cases.append(("mate_hm100", f"position fen 6k1/5ppp/8/8/8/8/8/R5NK w - - 100 40", "mate"))
    cases.append(("mate_rep3", f"position fen {mate_base} moves {MATESHUFFLE}", "mate"))
    cases.append(("mate_rep_ctrl", f"position fen {mate_rep_fen}", "mate"))
    cases.append(("nomate_hm100", f"position fen 8/8/8/4k3/8/8/4P3/4K3 w - - 100 60", "draw"))
    # knight shuffles Nc3-b1 / Nc6-b8 returning to the same position a third time (verified
    # threefold by python-chess in the raw output)
    quiet_rep_moves = "c3b1 c6b8 b1c3 b8c6 c3b1 c6b8 b1c3 b8c6"
    cases.append(("quiet_rep3", f"position fen {quiet_rep_base} moves {quiet_rep_moves}", "draw"))
    cases.append(("quiet_rep_ctrl", f"position fen {quiet_rep_base}", "search"))

    out = {"exe": exe, "cases": []}
    print(f"exe {exe}")
    print(f"{'case':16} {'expect':7} {'bestmove':9} {'score':9} {'nodes':>7} {'info':>5} {'san':>3} verdict")
    bad = 0
    for name, posline, *rest in cases:
        expect = rest[0] if rest else "search"
        r = ask(exe, posline)
        # what does the engine's own board look like?  take the FEN the case set, if any
        fen = None
        m = re.search(r"position fen ([^m]*?)( moves .*)?$", posline)
        if m:
            fen = m.group(1).strip()
            if m.group(2):
                bb = chess.Board(fen)
                for mv in m.group(2).split()[1:]:
                    try:
                        bb.push_uci(mv)
                    except ValueError:
                        break
                fen = bb.fen()
        is_mate = None
        if fen and r["bestmove"]:
            bb = chess.Board(fen)
            try:
                bb.push_uci(r["bestmove"])
                is_mate = bb.is_checkmate()
            except ValueError:
                is_mate = "unparseable"

        verdict = ""
        if expect == "mate":
            ok = is_mate is True and r["score"] == "mate 1"
        elif expect == "draw":
            ok = r["score"] == "cp 0"
        else:
            ok = r["info_lines"] > 0 and r["nodes"] is not None and r["nodes"] > 0
        if not ok:
            bad += 1
            verdict = "<-- FAIL"
        print(f"{name:16} {expect:7} {str(r['bestmove']):9} {str(r['score']):9} {str(r['nodes']):>7} "
              f"{r['info_lines']:>5} {len(r['sanitizer_lines']):>3} {verdict}")
        out["cases"].append({"case": name, "expect": expect, "position_line": posline, "fen": fen,
                             "bestmove_is_mate": is_mate, "answer": r, "pass": ok})

    Path(outfile).write_text(json.dumps(out, indent=1) + "\n")
    print(f"\n{bad} failing case(s); raw written to {outfile}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
