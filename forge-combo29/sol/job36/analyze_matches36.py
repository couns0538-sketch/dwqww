#!/usr/bin/env python3
"""Read completed fastchess PGNs, transcripts and sidecars for Job 36."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import io
import json
from math import log10, sqrt
from pathlib import Path
import re

import chess.pgn


SCHEDULE = {"K26": (7360, 20), "Q1": (7361, 600), "Q2": (7362, 400)}
ARMS = ("A", "B")
RESULT_POINTS = {"1-0": 2, "1/2-1/2": 1, "0-1": 0}
START = re.compile(r"^Started game (\d+) of (\d+) \(([AB]) vs ([AB])\)$", re.M)
FINISH = re.compile(r"^Finished game (\d+) \(([AB]) vs ([AB])\): (1-0|0-1|1/2-1/2) \{([^\n]*)\}$", re.M)
NATIVE_TIMEOUTS = re.compile(r"^Player: ([AB])\n  Timeouts: (\d+)\b", re.M)
TIMEOUT_REASON = re.compile(r"(White|Black) loses on time \((\d+)ms overrun\)")
PGN_RECORD = re.compile(r'(?m)(?=^\[Event ")')
RESULT_END = re.compile(r"(?:^|\s)(1-0|0-1|1/2-1/2)\s*\Z")
MOVE_TIME = re.compile(r"^[^/\s]*/\d+ (\d+\.\d{3})s, tl=(-?\d+\.\d{3})s(?:,|$)")
INITIAL_MS, INC_MS = 6060, 60
NORMAL_95 = 1.959963984540054


@dataclass(frozen=True)
class FinishedGame:
    white: str
    black: str
    result: str
    reason: str

    def timeout(self):
        return TIMEOUT_REASON.fullmatch(self.reason)


@dataclass(frozen=True)
class ScoredGame:
    white: str
    fen: str
    points: int
    moves: tuple


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_bytes(path, expected_bytes, expected_sha):
    content = path.read_bytes()
    require(len(content) == expected_bytes and sha256(content).hexdigest() == expected_sha,
            f"{path}: length or SHA-256 differs from sidecar")
    return content


def pgn_bytes(raw, match, meta):
    source = raw / f"{match}.pgn"
    parts_path = raw / f"{match}.pgn.manifest.json"
    if parts_path.is_file():
        parts = json.loads(parts_path.read_bytes())
        require(parts["parts"], f"{parts_path}: empty manifest")
        chunks = []
        for part in parts["parts"]:
            name = part["file"]
            require(Path(name).name == name and name.startswith(f"{match}.part") and name.endswith(".pgn"),
                    f"{parts_path}: invalid part filename {name}")
            chunks.append(file_bytes(raw / name, part["bytes"], part["sha256"]))
        content = b"".join(chunks)
    elif source.is_file():
        return file_bytes(source, meta["pgn_bytes"], meta["pgn_sha256"])
    else:
        require(meta["status"] == "interrupted" and "pgn_sha256" not in meta, f"{source}: missing")
        return b""
    require(len(content) == meta["pgn_bytes"] and sha256(content).hexdigest() == meta["pgn_sha256"],
            f"{parts_path}: concatenated PGN differs from sidecar")
    return content


def finish_readback(transcript, requested):
    starts = {}
    for game, schedule, white, black in START.findall(transcript):
        game = int(game)
        expected = ARMS if game % 2 else ARMS[::-1]
        require(1 <= game <= requested and int(schedule) == requested and (white, black) == expected
                and game not in starts, f"Transcript: invalid or repeated start for game {game}")
        starts[game] = (white, black)
    ends = {}
    for game, white, black, result, reason in FINISH.findall(transcript):
        game = int(game)
        require(game not in ends and starts.get(game) == (white, black),
                f"Transcript: unmatched or repeated finish for game {game}")
        require("loses on time" not in reason or TIMEOUT_REASON.fullmatch(reason),
                f"Transcript: unrecognized timeout detail for game {game}")
        ends[game] = FinishedGame(white, black, result, reason)
    native = dict.fromkeys(ARMS, 0)
    footer = NATIVE_TIMEOUTS.findall(transcript)
    require(len({arm for arm, _ in footer}) == len(footer), "Transcript: repeated native timeout footer")
    native.update({arm: int(count) for arm, count in footer})
    return starts, ends, native if footer else None


def time_flag(finish, game_id, round_id, clocks, late, board):
    color, overrun = finish.timeout().groups()
    overrun = int(overrun)
    arm = finish.white if color == "White" else finish.black
    require(finish.result == ("0-1" if color == "White" else "1-0"),
            f"Game {game_id}: timeout loser and result disagree")
    if late:
        require(late["arm"] == arm and late["elapsed_ms"] - late["clock_before_ms"] == overrun,
                f"Game {game_id}: timeout loss and late PGN move disagree")
        move = late
        evidence = "Late legal move and elapsed time recorded in PGN"
    else:
        require(board.turn == (color == "White"), f"Game {game_id}: timeout is not on the loser's turn")
        clock = clocks[arm]
        require(overrun > 0 or clock <= 0, f"Game {game_id}: zero-overrun timeout with positive prior clock")
        move = {"arm": arm, "move_number": board.fullmove_number, "move_san": None, "move_uci": None,
                "elapsed_ms": clock + overrun if overrun else None, "clock_before_ms": clock}
        evidence = ("No bestmove in PGN; elapsed reconstructed from prior clock and fastchess's overrun"
                    if overrun else "Clock expired before a search; no attempted move time")
    return {"game": game_id, "round": round_id, "color": color, **move,
            "overrun_ms": overrun, "evidence": evidence}


def check_game(record, finishes, requested, elapsed, reconstructed_clocks):
    game = chess.pgn.read_game(io.StringIO(record))
    require(game is not None and not game.errors, f"Invalid PGN game: {record[:140]}")
    header = game.headers
    result, white, black = (header[key] for key in ("Result", "White", "Black"))
    tail = RESULT_END.search(record)
    round_id = int(header["Round"])
    require(tail and tail[1] == result and {white, black} == set(ARMS) and 1 <= round_id <= requested // 2
            and header["TimeControl"] == "6+0.06", f"PGN round {round_id}: invalid game headers or result")
    game_id = (round_id - 1) * 2 + (1 if white == "A" else 2)
    require(game_id in finishes, f"Game {game_id}: PGN without fastchess finish")
    finish = finishes[game_id]
    require((finish.white, finish.black, finish.result) == (white, black, result),
            f"Game {game_id}: PGN colors or result disagree with transcript")
    termination = header["Termination"]
    require(termination in ("normal", "time forfeit") and (termination == "time forfeit") == bool(finish.timeout()),
            f"Game {game_id}: unsupported termination or timeout disagreement")

    board = game.board()
    clocks = dict.fromkeys(ARMS, INITIAL_MS)
    moves = []
    late = None
    for node in game.mainline():
        arm = white if board.turn else black
        clock = clocks[arm]
        fields = MOVE_TIME.match(node.comment)
        require(fields and not late, f"Game {game_id}: missing timing or move after flag at ply {len(moves) + 1}")
        move_ms, left_ms = (int(field.replace(".", "")) for field in fields.groups())
        expected = clock - move_ms
        if expected < 0:
            late = ({"arm": arm, "move_number": board.fullmove_number, "move_san": board.san(node.move),
                     "move_uci": node.move.uci(), "elapsed_ms": move_ms, "clock_before_ms": clock})
        else:
            expected += INC_MS
        # Bestmove-only replies keep MoveData.timeleft at its zero default
        # even though fastchess updates the player's actual clock.
        if left_ms == 0 and node.comment.startswith("/0 "):
            reconstructed_clocks[arm] += 1
        else:
            require(left_ms == expected, f"Game {game_id}: clock recurrence disagrees at ply {len(moves) + 1}")
        clocks[arm] = expected
        elapsed[arm].append(move_ms)
        moves.append(node.move.uci())
        board.push(node.move)
    require(len(moves) == int(header["PlyCount"]), f"Game {game_id}: parsed move count differs from PlyCount")
    require(termination == "time forfeit" or not late, f"Game {game_id}: negative clock in a normal finish")
    flag = time_flag(finish, game_id, round_id, clocks, late, board) if finish.timeout() else None
    points = RESULT_POINTS[result]
    return game_id, round_id, ScoredGame(white, header["FEN"], points if white == "A" else 2 - points, tuple(moves)), flag


def wld(games):
    counts = Counter(game.points for game in games)
    return [counts[2], counts[0], counts[1]]


def elo_interval(penta):
    pairs = sum(penta)
    if not pairs:
        return None, None, None
    scores = (0, 0.25, 0.5, 0.75, 1)
    mean = sum(count * score for count, score in zip(penta, scores)) / pairs
    if not 0 < mean < 1:
        return None, None, None

    def logistic_elo(score):
        return -400 * log10(1 / score - 1)

    elo = logistic_elo(mean)
    spread = NORMAL_95 * sqrt(sum(count * (score - mean) ** 2 for count, score in zip(penta, scores))) / pairs
    if pairs < 2 or not 0 < mean - spread <= mean + spread < 1:
        return elo, None, None
    halfwidth = (logistic_elo(mean + spread) - logistic_elo(mean - spread)) / 2
    return elo, [elo - halfwidth, elo + halfwidth], halfwidth


def timing(values):
    total = len(values)
    if not total:
        return {"moves": 0, "sum_ms": 0, "mean_ms": None, "p99_rank": None, "p99_ms": None,
                "max_ms": None, "above_500ms": 0}
    rank = (99 * total + 99) // 100
    move_sum = sum(values)
    return {"moves": total, "sum_ms": move_sum, "mean_ms": move_sum / total, "p99_rank": rank,
            "p99_ms": sorted(values)[rank - 1], "max_ms": max(values),
            "above_500ms": sum(value > 500 for value in values)}


def latest_score(transcript, games, score, penta, elo, width):
    scores = re.findall(r"(?m)^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+), Points: ",
                        transcript)
    pairs = re.findall(r"(?m)^Ptnml\(0-2\): \[(\d+), (\d+), (\d+), (\d+), (\d+)\]", transcript)
    ratings = re.findall(r"(?m)^Elo: (-?\d+(?:\.\d+)?) \+/- (\d+(?:\.\d+)?),", transcript)
    require(scores and list(map(int, scores[-1])) == [games, *score], "Fastchess final W-L-D disagrees with PGN")
    require(pairs and list(map(int, pairs[-1])) == penta, "Fastchess final pentanomial disagrees with PGN")
    if width is not None:
        require(ratings and abs(float(ratings[-1][0]) - elo) <= .0050001
                and abs(float(ratings[-1][1]) - width) <= .0050001,
                "Fastchess final Elo or interval disagrees with PGN")


def analyze(raw, match):
    meta_path = raw / f"{match}.meta"
    if not meta_path.is_file():
        require(not any(raw.glob(f"{match}.*")), f"{match}: raw files without a sidecar")
        return {"status": "not played"}
    meta_bytes = meta_path.read_bytes()
    meta = json.loads(meta_bytes)
    status = meta["status"]
    seed, maximum_games = SCHEDULE[match]
    requested = meta["games_requested"]
    require(meta["match"] == match and status in ("complete", "interrupted") and meta["seed"] == seed
            and meta["timecontrol"] == "6+0.06" and meta["time_margin_ms"] == 0
            and requested == 2 * meta["pairs_requested"] and 0 < requested <= maximum_games
            and (match == "Q2" or requested == maximum_games), f"{match}: invalid match sidecar")
    transcript = file_bytes(raw / f"{match}.out", meta["out_bytes"], meta["out_sha256"]).decode()
    pgn = pgn_bytes(raw, match, meta).decode()
    starts, finishes, native = finish_readback(transcript, requested)
    grouped = defaultdict(list)
    elapsed = {arm: [] for arm in ARMS}
    flags = dict.fromkeys(ARMS, 0)
    reconstructed_clocks = dict.fromkeys(ARMS, 0)
    details, inferred_ids = [], set()
    for chunk in PGN_RECORD.split(pgn):
        if not chunk.strip():
            continue
        game_id, round_id, game, flag = check_game(chunk, finishes, requested, elapsed, reconstructed_clocks)
        require(game_id not in inferred_ids, f"{match}: duplicate game {game_id}")
        inferred_ids.add(game_id)
        grouped[round_id].append(game)
        if flag:
            flags[flag["arm"]] += 1
            details.append(flag)
    require(inferred_ids == finishes.keys(), f"{match}: PGN and transcript game IDs differ")

    pairs, orphan_rounds = [], []
    for round_id, games in sorted(grouped.items()):
        if len(games) == 1:
            orphan_rounds.append(round_id)
            continue
        first, second = games
        require(first.white != second.white and first.fen == second.fen,
                f"{match}: round {round_id} lacks reversed colors or a common opening")
        pairs.append((first, second))
    game_count = len(inferred_ids)
    score = wld(game for games in grouped.values() for game in games)
    paired_score = wld(game for pair in pairs for game in pair)
    penta = [0] * 5
    for first, second in pairs:
        penta[first.points + second.points] += 1
    elo, bounds, width = elo_interval(penta)
    if status == "complete":
        require(meta["fastchess_exit"] == 0 and len(starts) == requested == game_count == 2 * len(pairs),
                f"{match}: complete status without all scheduled games and pairs")
        latest_score(transcript, game_count, score, penta, elo, width)

    transcript_flags = dict.fromkeys(ARMS, 0)
    for finish in finishes.values():
        if timeout := finish.timeout():
            transcript_flags[finish.white if timeout[1] == "White" else finish.black] += 1
    require(flags == transcript_flags, f"{match}: PGN and fastchess individual timeout counts disagree")
    fastchess_flags = native if native is not None else transcript_flags
    unrecorded = {arm: fastchess_flags[arm] - flags[arm] for arm in ARMS}
    require(all(value >= 0 for value in unrecorded.values()) and (status != "complete" or not any(unrecorded.values())),
            f"{match}: native footer and per-game timeout counts disagree")
    move_times = {arm: timing(values) for arm, values in elapsed.items()}
    a_p99, b_p99 = (move_times[arm]["p99_ms"] for arm in ARMS)
    gap = None if a_p99 is None or not b_p99 else abs(a_p99 - b_p99) * 100 / b_p99
    reading = ("NOT OK" if fastchess_flags["A"] else "UNAVAILABLE" if a_p99 is None or b_p99 is None else
               "CLOCK OK" if 10 * abs(a_p99 - b_p99) <= b_p99 else "NOT OK")
    return {
        "status": status, "seed": seed, "games_requested": requested, "games": game_count, "started": len(starts),
        "started_without_recorded_finish": sorted(starts.keys() - inferred_ids), "pairs": len(pairs),
        "orphan_rounds": orphan_rounds, "wld_A": score, "paired_wld_A": paired_score,
        "penta": penta, "elo": elo, "elo95": bounds, "same_moves": sum(a.moves == b.moves for a, b in pairs),
        "timing": move_times, "reconstructed_after_move_clocks": reconstructed_clocks,
        "flags": flags, "fastchess_flags": fastchess_flags,
        "fastchess_flags_source": "native footer" if native is not None else "per-game finish reasons",
        "unrecorded_fastchess_flags": unrecorded, "flag_details": sorted(details, key=lambda row: row["game"]),
        "reading": reading, "p99_gap_pct": gap, "sidecar_sha256": sha256(meta_bytes).hexdigest(),
        "pgn_sha256": meta.get("pgn_sha256"), "out_sha256": meta["out_sha256"],
        "builds": {arm: meta[f"engine_{arm.lower()}"] for arm in ARMS}, "timecontrol": meta["timecontrol"],
        "concurrency": meta["concurrency"], "match_start_utc": meta.get("match_start_utc"),
        "match_end_utc": meta.get("match_end_utc"),
    }


def grade(result, forecast):
    grades = {}
    for key in ("flags_A", "flags_B", "mean_A_ms", "mean_B_ms", "max_A_ms", "max_B_ms", "elo_A"):
        if key.startswith("flags"):
            actual = result["fastchess_flags"][key[-1]]
        elif key == "elo_A":
            actual = result["elo"]
        else:
            statistic, arm, unit = key.split("_")
            actual = result["timing"][arm][f"{statistic}_{unit}"]
        expected = forecast[key]
        row = {"forecast": expected, "observed": actual}
        if isinstance(expected, list):
            low, high = expected
            require(low <= high, f"Prediction: invalid range for {key}")
            row["grade"] = "ungraded" if actual is None else "met" if low <= actual <= high else "missed"
        else:
            row["error_ms"] = None if actual is None else actual - expected
        grades[key] = row
    return grades


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--match", choices=SCHEDULE)
    parser.add_argument("--prediction", type=Path)
    parser.add_argument("--json", type=Path, help="also write the receipt to this path")
    args = parser.parse_args()
    try:
        names = (args.match,) if args.match else SCHEDULE
        matches = {name: analyze(args.raw, name) for name in names}
        if args.prediction:
            forecast = json.loads(args.prediction.read_bytes())
            for name, result in matches.items():
                if name in ("Q1", "Q2") and result["status"] != "not played":
                    result["prediction"] = grade(result, forecast)
        observed = [result["reading"] for name, result in matches.items()
                    if name in ("Q1", "Q2") and (result.get("games") or result.get("fastchess_flags", {}).get("A"))]
        reading = ("NOT OK" if "NOT OK" in observed else "CLOCK OK" if observed and all(x == "CLOCK OK" for x in observed)
                   else "UNAVAILABLE")
        receipt = json.dumps({"matches": matches, "reading": reading}, indent=2, allow_nan=False) + "\n"
        if args.json:
            args.json.write_text(receipt)
        print(receipt, end="")
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
