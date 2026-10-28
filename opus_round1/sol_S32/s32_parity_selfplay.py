"""S32: game-level parity of datagen v2 (in-engine) with forge_selfplay.py (python-chess over UCI).

For every game in a datagen run (<prefix>.games + <prefix>_NNN.txt, written with --text), the game is played again
by forge_selfplay.py's own play_game() driving an engine over UCI (Threads 1, Hash 16, as its worker() sets up),
with the random opening forced to datagen's opening moves. Compared per game: every searched move, every recorded
(FEN, score) pair, and White's result. Read-only on its inputs; prints and writes one JSON report.

  python -I -B s32_parity_selfplay.py --selfplay <copy of forge_selfplay.py> --engine <exe> --prefix <datagen prefix>
                                      --out report.json [--max-games N]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import threading
import time
from pathlib import Path

import chess
import chess.engine


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("forge_selfplay_copy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ForcedOpening:
    """Stands in for random.Random: choice() returns datagen's opening move (and checks it is legal)."""

    def __init__(self, moves: list[str]):
        self.moves, self.index = moves, 0

    def choice(self, legal):
        want = self.moves[self.index]
        self.index += 1
        for move in legal:
            if move.uci() == want:
                return move
        raise AssertionError(f"opening move {want} is not legal here")


class RecordingEngine:
    """Passes play() through to the SimpleEngine and records the moves it returns."""

    def __init__(self, engine):
        self.engine, self.moves = engine, []

    @property
    def protocol(self):
        return self.engine.protocol

    def play(self, *args, **kwargs):
        reply = self.engine.play(*args, **kwargs)
        self.moves.append(reply.move.uci())
        return reply


def read_run(prefix: Path):
    config, games = {}, []
    for line in Path(str(prefix) + ".games").read_text(encoding="ascii").splitlines():
        if line.startswith("# ") and "=" in line:
            key, _, value = line[2:].partition("=")
            config[key] = value
        elif line and not line.startswith("#"):
            f = line.split("\t")
            games.append({"game": int(f[0]), "result": f[3], "termination": f[4], "records": int(f[5]),
                          "opening": f[6].split(), "moves": f[7].split()})
    text = []
    for shard in sorted(prefix.parent.glob(prefix.name + "_[0-9][0-9][0-9].txt")):
        text += shard.read_text(encoding="ascii").splitlines()
    return config, games, text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selfplay", type=Path, required=True)
    ap.add_argument("--engine", type=Path, required=True)
    ap.add_argument("--prefix", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-games", type=int, default=0)
    a = ap.parse_args(argv)
    if a.out.exists():
        ap.error("--out must be a new file")
    selfplay = load_module(a.selfplay)
    config, games, text = read_run(a.prefix)
    if config.get("mode") != "selfplay" or int(config["draw_plies"]) != 0 or config["openings"] != "startpos":
        raise SystemExit("parity needs a startpos self-play run without draw adjudication (forge_selfplay.py has neither)")
    kind, _, value = config["budget"].partition(" ")
    args = argparse.Namespace(opening_plies=int(config["random_plies"]), max_ply=int(config["max_ply"]),
                              depth=int(value) if kind == "depth" else None, nodes=int(value) if kind == "nodes" else None,
                              max_score=int(config["max_score"]), adjudicate_cp=int(config["win_cp"]),
                              adjudicate_plies=int(config["win_plies"]))
    if int(config["hash_mb"]) != 16:
        raise SystemExit("forge_selfplay.py always uses Hash 16")
    if a.max_games:
        games = games[:a.max_games]
    result_value = {"1-0": 1.0, "1/2-1/2": 0.5, "0-1": 0.0}
    engine = chess.engine.SimpleEngine.popen(selfplay.MeteredUCI, [str(a.engine)], timeout=60)
    rows, offset, start = [], 0, time.perf_counter()
    try:
        engine.configure({"Threads": 1, "Hash": 16})
        for game in games:
            mine = [line.split(" | ") for line in text[offset:offset + game["records"]]]
            offset += game["records"]
            recorder = RecordingEngine(engine)
            out = selfplay.play_game(recorder, args, ForcedOpening(game["opening"]), threading.Event())
            if out is None:
                rows.append({"game": game["game"], "identical": False, "why": "forge_selfplay discarded the game"})
                continue
            records, result = out
            theirs = [(fen, int(cp)) for fen, cp in records]
            ours = [(fen, int(cp)) for fen, cp, _ in mine]
            same_moves = recorder.moves == game["moves"]
            same_records = theirs == ours
            same_result = result == result_value[game["result"]] and all(float(r) == result for _, _, r in mine)
            row = {"game": game["game"], "plies": len(game["moves"]), "records": len(ours), "termination": game["termination"],
                   "identical": same_moves and same_records and same_result,
                   "same_moves": same_moves, "same_records": same_records, "same_result": same_result}
            if not row["identical"]:
                first = next((i for i, (x, y) in enumerate(zip(recorder.moves, game["moves"])) if x != y), None)
                row["first_move_mismatch"] = first
                row["records_python"], row["records_datagen"] = len(theirs), len(ours)
            rows.append(row)
    finally:
        engine.quit()
    report = {"tool": "s32_parity_selfplay", "engine": str(a.engine), "prefix": str(a.prefix), "config": config,
              "games": len(rows), "identical": sum(r["identical"] for r in rows),
              "plies": sum(r.get("plies", 0) for r in rows), "records": sum(r.get("records", 0) for r in rows),
              "elapsed_s": round(time.perf_counter() - start, 2), "rows": rows}
    report["pass"] = report["games"] > 0 and report["identical"] == report["games"]
    a.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("rows", "config")}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
