"""Play Job 29 start-position controls and test the published first-20 reference rows."""
import argparse
import asyncio
from contextlib import redirect_stderr, redirect_stdout
import csv
import hashlib
import json
import os
from pathlib import Path
import traceback

from game29 import BASE, GAME_COLS, PROFILES, chess, play, utc

HERE = Path(__file__).resolve().parent
RESULTS = Path(os.environ.get("JOB29_CONTROLS", HERE.parent / "controls"))
EXE = Path(os.environ.get("JOB29_NC_EXE", "/workspace/work/run23/job26work/P/build/forge"))
NC_SHA = "9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3"
K29 = [
    ("513827072a8e2e63", 87781, "1 4121 d2d4 / 2 2482 g7g6 / 3 5094 e2e4"),
    ("2c998001ce3d0422", 110606, "1 4121 d2d4 / 2 4815 e7e6 / 3 2218 b1c3"),
    ("c742bd472d34db18", 48366, "1 4121 d2d4 / 2 1420 d7d5 / 3 2811 c2c4"),
    ("b82c3404ac8ecb28", 48642, "1 1740 c2c4 / 2 3538 e7e5 / 3 2934 g2g3"),
]
C29 = ("9b811eee51b6b554", 60481, "1 4121 d2d4 / 2 2482 g7g6 / 3 3465 e2e4")
EQUAL_FIELDS = "ply color n depth score bestmove go soft_n info_nodes".split()


def read_rows(path):
    with path.open(newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def comparable(rows):
    return [tuple(row[key] for key in EQUAL_FIELDS) for row in rows]


async def run(stage, dest):
    with EXE.open("rb") as src:
        digest = hashlib.file_digest(src, "sha256").hexdigest()
    if digest != NC_SHA or chess.__version__ != "1.11.2":
        raise RuntimeError("binary SHA-256 or python-chess version differs")
    targets = K29 if stage == "K29" else [C29, C29]
    if stage == "C29":
        with (RESULTS / "K29/gate.json").open() as src:
            if not json.load(src)["passed"]:
                raise RuntimeError("K29 gate did not pass")
    inputs = dict(executable=str(EXE), sha256=digest, python_chess=chess.__version__,
                  settings=BASE, opening=chess.STARTING_FEN, profiles=PROFILES,
                  execution="Sequential games; two fresh processes each.")
    (dest / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    gate = dict(stage=stage, started_utc=utc(), checks=[], passed=True)
    semantic_games = []
    outcomes = []
    with (dest / "games.tsv").open("x", newline="", buffering=1) as games, (dest / "comparison.tsv").open("x", newline="", buffering=1) as comp:
        games_out = csv.writer(games, delimiter="\t", lineterminator="\n")
        games_out.writerow(GAME_COLS)
        out = csv.writer(comp, delimiter="\t", lineterminator="\n")
        out.writerow("pair color_game game kept_rows sha expected_sha sum_N expected_sum_N first_three reference_first_three check".split())
        for game, (ref_sha, ref_sum, ref_three) in enumerate(targets, 1):
            pair = (game + 1) // 2
            result = await play(EXE, stage, dest, game, pair, chess.STARTING_FEN)
            games_out.writerow(result)
            all_rows = read_rows(dest / f"g{game:04d}/searches.tsv")
            if stage == "C29":
                semantic_games.append(comparable(all_rows))
                game_result = dict(zip(GAME_COLS, result))
                outcomes.append({k: game_result[k] for k in ("result", "ending", "plies")})
            rows = all_rows[:20]
            lines = [f"{r['ply']} {r['n']} {r['bestmove']}" for r in rows]
            raw = "".join(line + "\n" for line in lines).encode("ascii")
            (dest / f"first20-g{game:04d}.txt").write_bytes(raw)
            sig = hashlib.sha256(raw).hexdigest()[:16]
            node_sum = sum(int(r["n"]) for r in rows)
            first_three = " / ".join(lines[:3])
            correct = (len(rows), sig, node_sum, first_three) == (20, ref_sha, ref_sum, ref_three)
            gate["checks"].append(dict(game=game, passed=correct, sha=sig, sum_n=node_sum))
            gate["passed"] &= correct
            out.writerow([pair, (game-1)%2 + 1, game, len(rows), sig, ref_sha, node_sum, ref_sum,
                          first_three, ref_three, "pass" if correct else "fail"])
            print(utc(), stage, game, sig, node_sum, correct, flush=True)
            if not correct:
                break
    if stage == "C29" and gate["passed"]:
        first, second = semantic_games
        refs = [r["sha"] for r in read_rows(RESULTS / "K29/comparison.tsv")]
        difference = next((i for i, (a, b) in enumerate(zip(first, second), 1) if a != b), None)
        if difference is None and len(first) != len(second):
            difference = min(len(first), len(second)) + 1
        gate.update(equivalent_fields=EQUAL_FIELDS, full_rows=[len(first),len(second)],
                    same_game_searches=(first == second), first_differing_ply=difference,
                    endings=outcomes, same_game_result=outcomes[0] == outcomes[1],
                    K29_reference_shas=refs, different_from_all_K29=(len(refs) == 4 and C29[0] not in refs))
        gate["passed"] &= gate["same_game_searches"] and gate["same_game_result"] and gate["different_from_all_K29"]
    gate["ended_utc"] = utc()
    (dest / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    return gate["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("K29", "C29"))
    stage = parser.parse_args().stage
    dest = RESULTS / stage
    dest.mkdir(parents=True, exist_ok=False)
    with (dest / "controller.log").open("x", buffering=1) as log, redirect_stdout(log), redirect_stderr(log):
        try:
            success = asyncio.run(run(stage, dest))
        except BaseException:
            traceback.print_exc()
            raise SystemExit(2)
    raise SystemExit(0 if success else 1)
