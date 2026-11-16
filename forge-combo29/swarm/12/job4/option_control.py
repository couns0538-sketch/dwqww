#!/usr/bin/env python3
"""option_control.py EXE — prove the option harness can fail.

A "0 cases fired" result is worth nothing unless the same checking code catches a known-bad
response. This drives three plants through the harness's own `STOPLINE`/legality logic:

  1. a genuinely unknown option  -> the engine's OWN `info string unknown option X` must be seen
  2. an out-of-range spin value  -> the engine's OWN `info string invalid value` must be seen
  3. a fake engine that always answers an ILLEGAL bestmove (`bestmove e2e5` to every `go`)
     -> the harness's legality check must mark it illegal

Plants 1 and 2 use the real engine's own refusal lines, so they prove the regexes match what the
engine actually prints (that is the failure seat 19 hit: a parser looking for a line the engine
never prints). Plant 3 is a throwaway Python "engine" written here, so the legality check has
something genuinely wrong to catch.
"""
import subprocess
import sys
import tempfile
import os
import stat

STOPLINE = __import__("re").compile(r"unknown option|invalid value|invalid FEN|illegal move")


def ask(exe, lines):
    p = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True,
                       timeout=120, env={"PATH": "/usr/bin:/bin", "ASAN_OPTIONS": "detect_leaks=0"})
    return p.stdout.splitlines()


def main():
    exe = sys.argv[1]
    ok = 0
    total = 3

    # 1. unknown option must produce a line our regex matches
    out = ask(exe, ["uci", "setoption name NoSuchOptionHere value 1", "isready", "quit"])
    hits = [l for l in out if STOPLINE.search(l)]
    print(f"plant 1 unknown option   : {len(hits)} stop line(s); first: {hits[0] if hits else '(none)'}")
    ok += bool(hits)

    # 2. out-of-range spin must produce invalid value
    out = ask(exe, ["uci", "setoption name Hash value 0", "isready", "quit"])
    hits = [l for l in out if STOPLINE.search(l)]
    print(f"plant 2 Hash 0           : {len(hits)} stop line(s); first: {hits[0] if hits else '(none)'}")
    ok += bool(hits)

    # 3. a fake engine answering an illegal move
    script = '''#!/usr/bin/env python3
import sys
for line in sys.stdin:
    w = line.split()
    if not w: continue
    if w[0] == "uci":
        print("id name Fake"); print("option name Hash type spin default 32 min 1 max 2048")
        print("uciok", flush=True)
    elif w[0] == "isready":
        print("readyok", flush=True)
    elif w[0] == "go":
        print("bestmove e2e5", flush=True)
'''
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w") as f:
        f.write(script)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    out = ask(sys.executable, [path]) if False else subprocess.run(
        [sys.executable, path], input="uci\nisready\ngo depth 6\nquit\n",
        capture_output=True, text=True, timeout=60).stdout.splitlines()
    bms = [l.split()[1] for l in out if l.startswith("bestmove")]
    import chess
    board = chess.Board("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
    illegal = bool(bms) and chess.Move.from_uci(bms[0]) not in board.legal_moves
    print(f"plant 3 fake engine      : bestmove {bms[0] if bms else '(none)'} -> illegal in position: {illegal}")
    ok += illegal
    os.unlink(path)

    print(f"\nplants detected {ok}/{total}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
