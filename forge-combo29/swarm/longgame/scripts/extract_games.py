#!/usr/bin/env python3
"""Build the replay corpus from the repo's PGN files at the audit commit 6b98f217.

Selection is deterministic: PGN files in sorted path order, round-robin across files,
first N accepted games per file, games kept only if python-chess validates every move
from the game's own start position.

NOTE ON THE START POSITION. Every one of the 5,689 games in the repo's PGN files carries
[SetUp "1"] + [FEN ...] -- they are all mid-game book starts, so there is no
`position startpos` game in the corpus. The replay therefore sends
`position fen <start> moves <prefix>`, which is also what a GUI reading these files sends.
Consequence for the drawn-root bail: the pre-start history is invisible to the engine, so
bail counts from this corpus are a lower bound against a from-move-1 startpos replay.
"""
import io, json, shutil, subprocess, sys, os
import chess, chess.pgn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import require

REPO = "/agent/repos/dwqww"
COMMIT = "6b98f217"
OUT = sys.argv[1] if len(sys.argv) > 1 else "evidence/games.json"
WANT = 200
PER_FILE_CAP = 16
MIN_PLIES, MAX_PLIES = 20, 400


# Resolved once, so the child process is named by an absolute path and no shell is involved.
# Every argv below is a fixed literal or a path taken from `git ls-tree`, never a value from
# outside this repository, and `shell=True` is never used.
GIT = shutil.which("git")
require(GIT is not None, "git not found on PATH")


def pgn_paths():
    out = subprocess.run([GIT, "-C", REPO, "ls-tree", "-r", "--name-only", COMMIT],
                         capture_output=True, text=True, check=True).stdout.split("\n")
    return sorted(p for p in out if p.endswith(".pgn"))


def pgn_text(path):
    # `path` comes from pgn_paths() above, i.e. from this repo's own tree listing.
    require(path.endswith(".pgn") and ".." not in path and not path.startswith("/"),
            f"refusing unexpected path from git ls-tree: {path!r}")
    return subprocess.run([GIT, "-C", REPO, "show", f"{COMMIT}:{path}"],
                          capture_output=True, text=True, check=True).stdout


def main():
    files = pgn_paths()
    accepted, rejected = [], {"illegal": 0, "too_short": 0, "too_long": 0, "bad_fen": 0}
    per_file = {p: 0 for p in files}
    queues = {}
    for path in files:
        games = []
        stream = io.StringIO(pgn_text(path))
        while True:
            g = chess.pgn.read_game(stream)
            if g is None:
                break
            games.append(g)
        queues[path] = games

    idx = {p: 0 for p in files}
    while len(accepted) < WANT:
        progressed = False
        for path in files:
            if len(accepted) >= WANT or per_file[path] >= PER_FILE_CAP:
                continue
            games = queues[path]
            while idx[path] < len(games):
                g = games[idx[path]]
                idx[path] += 1
                progressed = True
                try:
                    board = g.board()
                    start_fen = board.fen()
                except Exception:
                    rejected["bad_fen"] += 1
                    continue
                moves, ok = [], True
                for mv in g.mainline_moves():
                    if not board.is_legal(mv):
                        ok = False
                        break
                    moves.append(mv.uci())
                    board.push(mv)
                if not ok:
                    rejected["illegal"] += 1
                    continue
                if len(moves) < MIN_PLIES:
                    rejected["too_short"] += 1
                    continue
                if len(moves) > MAX_PLIES:
                    rejected["too_long"] += 1
                    continue
                h = g.headers
                accepted.append({
                    "id": f"g{len(accepted):03d}",
                    "file": path,
                    "white": h.get("White", ""), "black": h.get("Black", ""),
                    "result": h.get("Result", ""), "timecontrol": h.get("TimeControl", ""),
                    "event": h.get("Event", ""),
                    "start_fen": start_fen,
                    "plies": len(moves),
                    "final_fen": board.fen(),
                    "moves": moves,
                })
                per_file[path] += 1
                break
        if not progressed:
            break

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"commit": COMMIT, "files": files, "rejected": rejected,
                   "per_file": per_file, "games": accepted}, f)
    plies = sum(g["plies"] for g in accepted)
    print(f"accepted {len(accepted)} games, {plies} game plies, {plies - len(accepted)} queryable prefixes")
    print("rejected:", rejected)
    print("per file:", {os.path.basename(k): v for k, v in per_file.items() if v})


if __name__ == "__main__":
    main()
