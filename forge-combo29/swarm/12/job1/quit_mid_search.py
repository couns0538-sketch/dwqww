#!/usr/bin/env python3
"""quit_mid_search.py EXE OUTDIR — does the quit-mid-search path touch freed memory?

The path seat 19 reports: send `go depth 12` and then `quit` at once. The engine stops the
search and prints a `bestmove` with 0 nodes and no `info` line. Seat 19's question to seat 12
is whether that print reads anything the stop already freed.

Two things are measured separately:

(A) WHERE THE MOVE COMES FROM. For each position the harness records the engine's own legal
    move order (`go perft 1`, whose first line is root_candidates.front()) and the bestmove
    that the interrupted search prints. If they are equal for every position, the move is the
    first entry of the root list and not a value read out of freed storage.

(B) WHETHER ANY SANITIZER NOTICES. Same runner, ASan+UBSan exe, N repeats per position, plus
    the planted-fault control through the SAME function (`run_case`) so a zero means the
    runner can see a fault when there is one.

Every case is a fresh process; the .meta file beside the output records the exe, its sha256,
its `id name`, the exact option lines sent, and the nm counts the brief requires.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SAN = re.compile(r"ERROR: (AddressSanitizer|LeakSanitizer)|SUMMARY: (Address|Undefined|Leak)Sanitizer|"
                 r"runtime error: ")

POSITIONS = [
    ("startpos", "position startpos"),
    ("kiwipete", "position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("endgame3", "position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ("middlegame", "position fen r2q1r1k/2p1bppp/p1np1n2/1p2P3/4P3/1NN1B3/PPP2PPP/R2Q1RK1 w - - 0 10"),
    ("mateset", "position fen 6k1/5ppp/8/8/8/8/8/R5NK w - - 0 1"),
]


def run_case(exe, script, timeout_s=60):
    """One fresh process; write the whole script, read everything until the process ends."""
    t0 = time.monotonic()
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1,
                         env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0",
                              "UBSAN_OPTIONS": "print_stacktrace=1"})
    try:
        out, _ = p.communicate(script, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
    san = [ln for ln in out.splitlines() if SAN.search(ln)]
    return {"wall_s": round(time.monotonic() - t0, 3), "rc": p.returncode,
            "out": out, "san": san}


def legal_order(exe, position_line):
    """The engine's own legal move order: first line of `go perft 1`."""
    r = run_case(exe, f"uci\n{position_line}\nisready\ngo perft 1\nisready\nquit\n")
    moves = [ln.split(":")[0] for ln in r["out"].splitlines()
             if re.match(r"^[a-h][1-8][a-h][1-8][qrbn]?: \d+$", ln)]
    return moves, r


def main():
    exe, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    repeats = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    # ---- the .meta the brief requires
    meta = outdir / "quit_mid_search.meta"
    sha = subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0]
    uci_out = run_case(exe, "uci\nquit\n")["out"]
    id_name = next((ln for ln in uci_out.splitlines() if ln.startswith("id name")), "?")
    nm = {}
    for sym in ("__asan_", "__ubsan_", "__tsan_"):
        nm[sym] = subprocess.run(f"nm -C {exe} | grep -c {sym}", shell=True,
                                 capture_output=True, text=True).stdout.strip()
    meta.write_text(
        f"exe: {exe}\nsha256: {sha}\n{id_name}\n"
        f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"nm_asan: {nm['__asan_']}\nnm_ubsan: {nm['__ubsan_']}\nnm_tsan: {nm['__tsan_']}\n"
        "options_sent: none (no setoption line in any case; the engine default Hash 32, Threads 1)\n"
        f"runner: {Path(__file__).name}, {repeats} repeats per position\n"
        "env: ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1\n")
    print(meta.read_text())

    # ---- (A) is the printed move the first entry of the engine's own root list?
    print(f"{'position':12} {'perft-order[0]':15} {'quit-mid-search bm':18} {'nodes':>6} {'info lines':>10} {'equal':5} {'san':>3}")
    rows = []
    for name, posline in POSITIONS:
        order, perft_run = legal_order(exe, posline)
        res = run_case(exe, f"uci\n{posline}\nisready\ngo depth 12\nquit\n")
        bm = next((ln.split()[1] for ln in res["out"].splitlines() if ln.startswith("bestmove")), None)
        infos = [ln for ln in res["out"].splitlines() if ln.startswith("info depth")]
        nodes = None
        if infos:
            m = re.search(r" nodes (\d+)", infos[-1])
            nodes = int(m.group(1)) if m else None
        row = {"position": name, "perft_first": order[0] if order else None,
               "bestmove": bm, "nodes": nodes, "info_lines": len(infos),
               "equal": (bool(order) and order[0] == bm), "sanitizer_lines": res["san"],
               "rc": res["rc"], "wall_s": res["wall_s"],
               "legal_moves": len(order),
               "bm_in_legal_list": (bm in order) if bm else None}
        rows.append(row)
        print(f"{name:12} {str(row['perft_first']):15} {str(bm):18} {str(nodes):>6} {len(infos):>10} "
              f"{str(row['equal']):5} {len(res['san']):>3}")

    # ---- (B) repeats for sanitizer lines, plus the planted-fault control
    print(f"\n{repeats} repeats per position under the same runner:")
    san_total = 0
    for name, posline in POSITIONS:
        hits = 0
        for _ in range(repeats):
            res = run_case(exe, f"uci\n{posline}\nisready\ngo depth 12\nquit\n")
            if res["san"]:
                hits += 1
                for ln in res["san"][:3]:
                    print(f"  SAN {name}: {ln}")
        san_total += hits
        print(f"  {name:12} runs with a sanitizer line: {hits}/{repeats}")
    print(f"total runs with a sanitizer line: {san_total}")

    control = None
    if len(sys.argv) > 4:
        ctl_exe = sys.argv[4]
        ctl = run_case(ctl_exe, "uci\nisready\nplantedasan\nisready\nplantedubsan\nisready\nquit\n")
        control = {"exe": ctl_exe, "sanitizer_lines": ctl["san"][:6], "rc": ctl["rc"]}
        print(f"\nplanted-fault control through the SAME runner ({ctl_exe}):")
        for ln in ctl["san"][:4]:
            print(f"  SAN {ln}")
        print(f"  control lines counted: {len(ctl['san'])}")

    (outdir / "quit_mid_search.json").write_text(json.dumps(
        {"rows": rows, "repeats": repeats, "sanitizer_runs": san_total, "control": control},
        indent=1) + "\n")
    print(f"\nraw written to {outdir/'quit_mid_search.json'}")


if __name__ == "__main__":
    main()
