"""R10: run a FORGE_HALFKA_VERIFY build (every lazily built HalfKA row is compared with a full refresh inside the search;
a mismatch aborts) through bench and multi-threaded searches with a net loaded.
usage: python -I -B verify_search.py <verify.exe> <net.nnue> [--threads 3] [--depth 13]"""
import subprocess
import sys

exe, net = sys.argv[1], sys.argv[2]
threads = int(sys.argv[sys.argv.index("--threads") + 1]) if "--threads" in sys.argv else 3
depth = int(sys.argv[sys.argv.index("--depth") + 1]) if "--depth" in sys.argv else 13
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)


def send(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def until(prefix):
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("engine ended early (verify abort?)")
        if line.startswith(prefix):
            return line.strip()


send("uci")
until("uciok")
send(f"setoption name EvalFileHalfKA value {net}")
send("isready")
until("readyok")
print(until("info string bench") if not send("bench 13") else "", flush=True)
send(f"setoption name Threads value {threads}")
for moves in ("", "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6", "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4", "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4"):
    send("ucinewgame")
    send("position startpos" + (f" moves {moves}" if moves else ""))
    send(f"go depth {depth}")
    print(f"threads {threads} {moves or 'startpos'}: {until('bestmove')}", flush=True)
send("quit")
_, err = p.communicate(timeout=120)
print(err.strip())
print("VERIFY OK" if p.returncode == 0 and "lazily built rows equal" in err and "FAILED" not in err else f"VERIFY FAILED rc={p.returncode}")
