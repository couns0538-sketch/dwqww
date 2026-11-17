#!/usr/bin/env python3
"""Do the two patches compose? Measured, not assumed.

Trap 1 and trap 2 touch different parts of `uci.cpp` (`parse_limits` vs the book
gate), so they should be independent. "Should be" is not a result, so this checks
the combination directly:

  * apply both diffs to a clean tree at the base commit, build it
  * all 11 pins must match the lock
  * trap 2 must be fixed in the combined build (pre-emption 0)
  * trap 1 must be fixed in the combined build (opponent-clock-only answers)

Exit 1 if the combination is not at least as good as each patch alone.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

SCRIPTS = Path(__file__).parent
PATCH1 = SCRIPTS.parent / "patches/trap1-clock-gate-both-clocks.patch"
PATCH2 = SCRIPTS.parent / "patches/trap2-drawn-root-before-book.patch"
CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"
NOBOOK = "fen r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6"
START = "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def probe(binary: str, position: str, go: str, opts=(), window: float = 25.0) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        for n, v in opts:
            eng.setoption(n, v)
        eng.position_checked(position)
        t0 = time.monotonic()
        eng.send(f"go {go}")
        r = eng.read_until(lambda ln: ln.startswith("bestmove"), window)
        elapsed = time.monotonic() - t0
        answered = not r.timed_out
        lines = list(r.lines)
        if not answered:
            eng.send("stop")
            lines += eng.read_until(lambda ln: ln.startswith("bestmove"), 20.0).lines
        depth = [ln for ln in lines if ln.startswith("info depth")]
        score = None
        pv_empty = None
        if depth:
            m = re.search(r"score (cp|mate) (-?\d+)", depth[-1])
            score = (m.group(1), int(m.group(2))) if m else None
            t = depth[-1].split(" pv", 1)
            pv_empty = len(t) == 2 and t[1].strip() == ""
        return {"answered": answered, "elapsed": elapsed,
                "book": any("book move" in ln for ln in lines),
                "depth": len(depth), "score": score, "pv_empty": pv_empty}
    finally:
        eng.quit()


def build_combined(base_commit: str) -> str:
    """Check out the base commit, apply both patches, build. Returns binary path."""
    for p in (PATCH1, PATCH2):
        if not p.exists():
            print(f"missing patch {p}")
            sys.exit(1)
    wt = Path(tempfile.mkdtemp(prefix="sw65-both-"))
    repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                          text=True, cwd=SCRIPTS).stdout.strip()
    print(f"  worktree {wt}")
    subprocess.run(["git", "worktree", "add", "--detach", str(wt), base_commit],
                   check=True, capture_output=True, cwd=repo)
    for p in (PATCH1, PATCH2):
        subprocess.run(["git", "apply", str(p)], check=True, cwd=wt)
        print(f"  applied {p.name}")
    bdir = Path(tempfile.mkdtemp(prefix="sw65-both-build-"))
    env = {"LIBRARY_PATH": "/usr/lib/gcc/x86_64-linux-gnu/13"}
    import os
    full_env = {**os.environ, **env}
    subprocess.run(["cmake", "-S", str(wt / "forge-combo29"), "-B", str(bdir),
                    "-DCMAKE_BUILD_TYPE=Release", "-DFORGE_MARCH=native",
                    "-DCMAKE_CXX_COMPILER=/usr/bin/g++"],
                   check=True, capture_output=True, env=full_env)
    subprocess.run(["cmake", "--build", str(bdir), "-j4"], check=True,
                   capture_output=True, env=full_env)
    return str(bdir / "forge")


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "6b98f217"
    lock = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"composing trap 1 + trap 2 on {base}")
    binary = build_combined(base)
    print(f"  binary {binary}")
    print()

    print("1. pins on the combined build")
    r = subprocess.run([sys.executable, str(SCRIPTS / "q13_pins.py"), binary],
                       capture_output=True, text=True)
    tail = [ln for ln in r.stdout.splitlines() if ln.strip()][-1]
    print(f"    {tail}")
    check("combined build reproduces all 11 pins", r.returncode == 0, tail)
    print()

    for fen in (START[4:], NOBOOK[4:]):
        chess.Board(fen)

    print("2. trap 2 still fixed in the combined build")
    for label, pos in (("fifty-move + book entry",
                        "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1"),
                       ("repetition + book entry",
                        "startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8")):
        p = probe(binary, pos, CLOCK, [("OwnBook", "true"), ("Book Variety", "0")])
        ok = (not p["book"]) and p["depth"] > 0 and p["score"] == ("cp", 0) and p["pv_empty"] is True
        print(f"    {label}: book={p['book']} depth={p['depth']} score={p['score']} pv_empty={p['pv_empty']}")
        check(f"combined build reports the drawn root: {label}", ok, "bail answer")
    p = probe(binary, START, CLOCK, [("OwnBook", "true"), ("Book Variety", "0")])
    check("combined build still books an ordinary position", p["book"], f"book={p['book']}")
    print()

    print("3. trap 1 still fixed in the combined build")
    a = probe(binary, NOBOOK, "btime 10000 binc 100")
    print(f"    no-book position, only the opponent's clock: "
          f"answered={a['answered']} in {a['elapsed']:.2f}s")
    check("combined build is time-limited from the opponent's clock", a["answered"],
          f"{a['elapsed']:.2f}s")
    # The book fires from the opponent's clock too, which requires the trap-1 fix
    # to be feeding limits.time_ms and the trap-2 fix not to be blocking it.
    w = probe(binary, START, "btime 10000 binc 100")
    print(f"    book position, only btime: book={w['book']} bestmove_depth={w['depth']}")
    check("combined build books from the opponent's clock", w["book"], f"book={w['book']}")
    print()

    if lock:
        print("4. comparison point: lock on the same probes")
        a0 = probe(lock, NOBOOK, "btime 10000 binc 100")
        w0 = probe(lock, START, "btime 10000 binc 100")
        print(f"    lock no-book, only btime: answered={a0['answered']} in {a0['elapsed']:.2f}s")
        print(f"    lock book pos, only btime: book={w0['book']}")
        check("lock still shows the original defect (so the comparison is meaningful)",
              (not a0["answered"]) and (not w0["book"]), "unbounded and not booked")
        print()

    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("Both patches compose: pins identical, trap 1 fixed, trap 2 fixed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
