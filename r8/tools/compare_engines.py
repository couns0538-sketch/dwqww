"""R8: do two Forge exes search identically? (bench nodes + fixed-node game searches with the TT carried over)
usage: python -I -B compare_engines.py <exe_a> <exe_b> [--games 20] [--nodes 5000] [--seed 1]
For each exe: `bench 10` and `bench 13` node counts; then <games> games of the live self-play shape (Threads 1,
Hash 16, OwnBook false, ucinewgame, 8 random opening plies from python-chess, then `go nodes N` per move with the
growing `position startpos moves ...` history, at most 60 searched plies per game). Every search's bestmove and final
score/nodes line must be equal between the two exes. Exit 0 when everything matches."""
import random
import re
import subprocess
import sys

import chess

a, b = sys.argv[1], sys.argv[2]
games = int(sys.argv[sys.argv.index("--games") + 1]) if "--games" in sys.argv else 20
nodes = int(sys.argv[sys.argv.index("--nodes") + 1]) if "--nodes" in sys.argv else 5000
seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 1


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.send("uci")
        self.until(r"^uciok")
        for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
            self.send("setoption name " + o)
        self.send("isready")
        self.until(r"^readyok")

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, pat):
        rx = re.compile(pat)
        lines = []
        for line in self.p.stdout:
            line = line.rstrip("\n")
            lines.append(line)
            if rx.search(line):
                return lines
        raise SystemExit("engine exited")

    def bench(self, d):
        return self.until_bench(d)

    def until_bench(self, d):
        self.send(f"bench {d}")
        lines = self.until(rf"bench depth {d} nodes (\d+)")
        return int(re.search(rf"bench depth {d} nodes (\d+)", lines[-1]).group(1))

    def search(self, moves):
        self.send("position startpos" + (" moves " + " ".join(moves) if moves else ""))
        self.send(f"go nodes {nodes}")
        lines = self.until(r"^bestmove")
        infos = [l for l in lines if l.startswith("info") and " score " in l]
        last = infos[-1] if infos else ""
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        nd = re.search(r" nodes (\d+)", last)
        return lines[-1].split()[1], (sc.group(1) + " " + sc.group(2)) if sc else None, int(nd.group(1)) if nd else None

    def quit(self):
        self.send("quit")
        self.p.wait(timeout=30)


ea, eb = Engine(a), Engine(b)
ok = True
for d in (10, 13):
    na, nb = ea.bench(d), eb.bench(d)
    print(f"bench {d}: {na} vs {nb} {'OK' if na == nb else 'DIFF'}", flush=True)
    ok &= na == nb
rng = random.Random(seed)
searches = 0
for g in range(games):
    board = chess.Board()
    for _ in range(8):
        legal = list(board.legal_moves)
        if not legal:
            break
        board.push(rng.choice(legal))
    if board.is_game_over():
        continue
    ea.send("ucinewgame")
    eb.send("ucinewgame")
    moves = [m.uci() for m in board.move_stack]
    for ply in range(60):
        if board.is_game_over(claim_draw=False) or board.is_repetition(3) or board.is_fifty_moves():
            break
        ra, rb = ea.search(moves), eb.search(moves)
        searches += 1
        if ra != rb:
            print(f"game {g} ply {len(moves)}: {ra} vs {rb} DIFF", flush=True)
            ok = False
            break
        board.push(chess.Move.from_uci(ra[0]))
        moves.append(ra[0])
print(f"{searches} fixed-node searches compared ({games} games, nodes {nodes})")
ea.quit()
eb.quit()
print("IDENTICAL" if ok else "DIFFERENT")
sys.exit(0 if ok else 1)
