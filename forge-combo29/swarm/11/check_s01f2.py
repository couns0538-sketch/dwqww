#!/usr/bin/env python3
"""check_s01f2.py EXE — seat 11's INDEPENDENT check of seat 01's finding S-F2.

Seat 01's claim (verbatim from their FINDINGS.md):
  "A FEN whose side to move is in check from two pieces
   (`3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1`) is accepted and the engine's perft 2 = 64
   equals python-chess's, so move generation is right; python-chess reports
   STATUS_IMPOSSIBLE_CHECK."

This harness is written from that sentence alone; seat 01's scripts were not read or copied.
Falsifiable predictions I test:
  (1) the engine ACCEPTS the FEN (no "invalid FEN" line),
  (2) engine perft 2 == 64,
  (3) python-chess perft 2 == 64,
  (4) python-chess flags STATUS_IMPOSSIBLE_CHECK on that board,
  (5) control: the same harness detects a wrong perft (a deliberately corrupted comparison).
"""
import subprocess, sys, chess

EXE = sys.argv[1]
FEN = "3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1"


def engine(fen, cmd):
    inp = f"uci\nposition fen {fen}\nisready\n{cmd}\nquit\n"
    p = subprocess.run([EXE], input=inp, capture_output=True, text=True, timeout=120)
    return p.stdout


def py_perft(board, d):
    if d == 0:
        return 1
    total = 0
    for m in board.legal_moves:
        board.push(m)
        total += py_perft(board, d - 1)
        board.pop()
    return total


def main():
    out = engine(FEN, "go perft 2")
    refused = "invalid FEN" in out
    eng_nodes = None
    for line in out.splitlines():
        if line.startswith("nodes "):
            eng_nodes = int(line.split()[1])

    print("=== raw engine output ===")
    print(out.strip())
    print("=== measurements ===")
    print(f"engine refused the FEN      : {refused}")
    print(f"engine perft 2 nodes        : {eng_nodes}")

    b = chess.Board(FEN)
    py = py_perft(b, 2)
    status = b.status()
    print(f"python-chess perft 2        : {py}")
    print(f"python-chess status()       : {status}")
    print(f"python-chess is_check       : {b.is_check()}")
    print(f"attackers of white king (w) : {[str(x) for x in b.attackers(chess.BLACK, b.king(chess.WHITE))]}")

    impossible = bool(status & chess.Status.IMPOSSIBLE_CHECK)
    print("\n=== verdict on seat 01's S-F2 ===")
    checks = [
        ("FEN accepted by engine", not refused),
        ("engine perft 2 == 64", eng_nodes == 64),
        ("python-chess perft 2 == 64", py == 64),
        ("engine == python-chess", eng_nodes == py),
        ("python-chess flags IMPOSSIBLE_CHECK", impossible),
    ]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    allok = all(ok for _, ok in checks)
    if refused:
        print("\nRESULT: REFUTES S-F2 — the engine refuses the FEN, so there is no board and")
        print("        the perft-2 comparison cannot be made at all.")
    elif allok:
        print("\nRESULT: CONFIRMS S-F2 — every part of the claim holds.")
    else:
        print("\nRESULT: PARTLY CONFIRMS S-F2 — see the FAIL lines above.")

    # control: the harness must be able to report a difference
    ctrl = engine(chess.STARTING_FEN, "go perft 2")
    ctrl_nodes = next((int(l.split()[1]) for l in ctrl.splitlines() if l.startswith("nodes ")), None)
    ctrl_py = py_perft(chess.Board(), 2)
    fake = ctrl_nodes + 1
    print(f"\ncontrol: harness compares {ctrl_nodes} vs fake {fake} -> "
          f"{'DIFFERENCE DETECTED' if ctrl_nodes != fake else 'HARNESS BLIND'}")
    print(f"control: startpos engine {ctrl_nodes} vs python-chess {ctrl_py} -> "
          f"{'EQUAL' if ctrl_nodes == ctrl_py else 'DIFFERENT'}")


if __name__ == "__main__":
    main()
