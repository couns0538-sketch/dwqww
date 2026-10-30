"""R8 equivalence test, Python side: the LIVE forge_selfplay.py's own play_game() (imported read-only, unchanged)
plays fixed openings, so its records can be compared line by line with forge_selfplay_fast's.

usage:
  python -I -B equivalence_ref.py gen <n> <seed> <openings.txt>      n openings of 8 uniformly random legal plies
  python -I -B equivalence_ref.py ref <engine.exe> <openings.txt> <out.txt> [--own-book false] [--cpus 8-9]
'ref' builds the live script's arguments with its own defaults (nodes 5000, opening plies 8, max ply 300,
adjudication 2000 cp x 4 plies, max score 3000), opens the engine with the live MeteredUCI protocol, configures
Threads 1, Hash 16 (and OwnBook, default false here as in the driver), and for each opening calls play_game() with a
stand-in RNG whose choice() returns the opening's next move. Every completed game's records are written as
"FEN | cp | result" (no de-duplication; compare with the driver's --no-dedup output)."""
import importlib.util
import random
import sys

import chess
import chess.engine

LIVE = r"C:\Users\Administrator\grok-pc\nnue\forge-nnue-tools\forge_selfplay.py"


def load_live():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("forge_selfplay_live", LIVE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FixedOpening:
    """rng.choice(list(board.legal_moves)) -> the next move of a fixed opening (must be legal)."""

    def __init__(self, moves):
        self.moves = list(moves)
        self.i = 0

    def choice(self, legal):
        m = chess.Move.from_uci(self.moves[self.i])
        self.i += 1
        if m not in legal:
            raise RuntimeError(f"opening move {m} not legal")
        return m


class NoStop:
    def is_set(self):
        return False


def gen(n, seed, path):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        b = chess.Board()
        ok = True
        for _ in range(8):
            if b.is_game_over(claim_draw=False):
                ok = False
                break
            b.push(rng.choice(list(b.legal_moves)))
        if ok and not b.is_game_over(claim_draw=False):
            out.append(" ".join(m.uci() for m in b.move_stack))
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {n} openings to {path}")


def ref(engine_exe, openings, out_path, own_book, cpus="8-9"):
    live = load_live()
    args = live.arguments(["--engine", engine_exe, "--workers", "1", "--cpus", cpus, "--nodes", "5000"])  # cpus: only checked by the live parser
    engine = chess.engine.SimpleEngine.popen(live.MeteredUCI, [args.engine], timeout=args.engine_timeout)
    engine.configure({"Threads": 1, "Hash": 16, "OwnBook": own_book})
    lines, games = [], 0
    for text in open(openings, encoding="ascii"):
        mv = text.split()
        if not mv:
            continue
        args.opening_plies = len(mv)
        done = live.play_game(engine, args, FixedOpening(mv), NoStop())
        if done is None:
            continue
        records, result = done
        games += 1
        lines += [f"{fen} | {int(cp)} | {result:.1f}" for fen, cp in records]
    engine.quit()
    with open(out_path, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    print(f"ref: {games} games, {len(lines)} records -> {out_path}")


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    else:
        ob = sys.argv[sys.argv.index("--own-book") + 1] == "true" if "--own-book" in sys.argv else False
        cpus = sys.argv[sys.argv.index("--cpus") + 1] if "--cpus" in sys.argv else "8-9"
        ref(sys.argv[2], sys.argv[3], sys.argv[4], ob, cpus)
