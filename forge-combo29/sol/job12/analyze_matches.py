#!/usr/bin/env python3
"""Check the paired Forge PGNs and grade the fastchess match forecasts."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from math import log10, sqrt
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
NUMBER = r"[+-]?\d+(?:\.\d+)?"
MATCHUP = re.compile(r"^Results of ([AB]) vs ([AB])\s*\(")
ELO = re.compile(rf"^Elo:\s*({NUMBER})\s*\+/-\s*({NUMBER})(?:\s|,|$)")
GAME_COUNTS = re.compile(r"^Games:\s*(\d+),\s*Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+)")
PENTA = re.compile(r"^Ptnml\(0-2\):\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]")
REFUSAL = re.compile(r"unknown option|invalid value|\bERROR\b", re.IGNORECASE)
MATCHES = {
    "K": (200, 7101, 20000, None),
    "C": (400, 7102, 10000, None),
    "E": (2000, 7103, 20000, {"name": "EvalSwingMult", "value": "3"}),
    "I": (2000, 7104, 20000, {"name": "IirDepth", "value": "1"}),
}
CATEGORIES = ("R", "S", "neither")
CI95 = 1.959963984540054


@dataclass
class Game:
    round: int
    white: str
    black: str
    result: str
    start: str
    points_a: int
    moves: tuple
    termination: str


@dataclass
class Match:
    name: str
    status: str
    raw_games: int = 0
    games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    penta: tuple = ()
    elo: Fraction | None = None
    width: Fraction | None = None
    abnormal: int = 0
    note: str = ""
    match_start: str | None = None
    match_end: str | None = None
    provenance: tuple = ()

    @property
    def interval(self):
        if self.elo is None:
            return None
        return self.elo - self.width, self.elo + self.width


def pgn_module(directory):
    if directory is not None:
        sys.path.insert(0, str(directory))
    try:
        import chess.pgn as pgn
    except ImportError:
        fallback = HERE.parent / "sol-job3" / "deps"
        if not fallback.is_dir():
            raise ValueError("python-chess required. Provide --python-chess-dir or install chess for this interpreter.")
        sys.path.insert(0, str(fallback))
        import chess.pgn as pgn
    return pgn


def digest(path):
    result = sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(data)
    return result.hexdigest()


def read_meta(directory, name):
    path = directory / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        return None, "unfinished: metadata missing or unfinished"
    data = json.loads(path.read_text(encoding="utf-8"))
    games, seed, nodes_a, variant = MATCHES[name]
    actual = (data["match"], data["games_requested"], data["seed"], data["nodes_a"],
              data["nodes_b"], data["engine_a"], data["engine_b"], data["variant"], data["maxmoves"])
    if actual != (name, games, seed, nodes_a, 20000, "A", "B", variant, 300):
        raise ValueError(f"{path}: wrong match identity or controls")
    workers = data["nproc"] // 2 if name in ("E", "I") else data["nproc"]
    if data["concurrency"] != workers or workers < 1:
        raise ValueError(f"{path}: wrong worker count")
    if not {"setoption name Threads value 1", "setoption name Hash value 16",
            "setoption name OwnBook value false"} <= set(data["settings_b"]):
        raise ValueError(f"{path}: baseline settings differ in threads, hash or book")
    if data["status"] == "refused":
        return None, f"refused: {data.get('error', '')}"
    if not data.get("pgn_sha256") or not data.get("out_sha256"):
        return None, f"{data['status']}: {data.get('error', 'PGN or fastchess output missing')}"
    if data["status"] == "complete" and data.get("fastchess_exit") != 0:
        raise ValueError(f"{path}: complete match has a nonzero fastchess exit")
    for key, suffix in (("pgn_sha256", "pgn"), ("out_sha256", "out")):
        input_path = directory / f"{name}.{suffix}"
        if digest(input_path) != data[key]:
            raise ValueError(f"{input_path}: SHA-256 differs from sidecar")
    expected_options = list(data["settings_b"])
    if variant:
        expected_options.append(f"setoption name {variant['name']} value {variant['value']}")
    if data["preflight_settings_sent"] != data["settings_a"] or data["settings_a"] != expected_options:
        raise ValueError(f"{path}: preflight or candidate options differ from the specified single change")
    if (data["preflight_reply"][-1:] != ["readyok"]
            or any(REFUSAL.search(line) for line in data["preflight_reply"])):
        raise ValueError(f"{path}: missing clean full-settings acknowledgment")
    return data, ""


def parse_games(path, pgn, exact_moves):
    groups = defaultdict(list)
    with path.open(encoding="utf-8") as contents:
        while True:
            parsed = pgn.read_game(contents) if exact_moves else pgn.read_game(contents, Visitor=pgn.HeadersBuilder)
            if parsed is None:
                break
            if exact_moves:
                if parsed.errors:
                    raise ValueError(f"{path}: PGN move parse errors: {parsed.errors}")
                header = parsed.headers
                moves = tuple(move.uci() for move in parsed.mainline_moves())
            else:
                header, moves = parsed, ()
            if (header["White"], header["Black"]) not in (("A", "B"), ("B", "A")):
                raise ValueError(f"{path}: expected opposite A/B engine names")
            outcome = header["Result"]
            white_points = {"1-0": 2, "0-1": 0, "1/2-1/2": 1}
            if outcome not in white_points:
                raise ValueError(f"{path}: incomplete result in PGN round {header['Round']}")
            first = white_points[outcome]
            points_a = first if header["White"] == "A" else 2 - first
            round_ = int(header["Round"])
            if round_ < 1:
                raise ValueError(f"{path}: invalid PGN round {round_}")
            groups[round_].append(Game(round_, header["White"], header["Black"], outcome,
                                      header.get("FEN", "startpos"), points_a, moves, header.get("Termination", "")))
    return groups


def move_discrepancy(round_, first, second, reason):
    print(f"First differing K pair, PGN round {round_}: {reason}.")
    for game in (first, second):
        print(f"White {game.white}, Black {game.black}, result {game.result}, FEN {game.start}")
        print(" ".join(game.moves) or "(no moves)")


def tally_pairs(groups, exact_moves):
    counts = [0, 0, 0]
    penta = [0, 0, 0, 0, 0]
    abnormal = 0
    for round_, games in sorted(groups.items()):
        if len(games) == 1:
            continue
        if len(games) != 2:
            raise ValueError(f"PGN round {round_}: expected exactly two games, got {len(games)}")
        first, second = games
        if (first.white, first.black, first.start) != (second.black, second.white, second.start):
            if exact_moves:
                move_discrepancy(round_, first, second, "colors or opening differ")
            raise ValueError(f"PGN round {round_}: colors or opening differ")
        pair_points = first.points_a + second.points_a
        if exact_moves and (first.moves != second.moves or pair_points != 2):
            differing = next((index for index, (x, y) in enumerate(zip(first.moves, second.moves), 1) if x != y), None)
            reason = f"first different ply {differing}" if differing is not None else (
                f"move lengths {len(first.moves)} and {len(second.moves)}" if first.moves != second.moves
                else f"pair scored {pair_points / 2:.1f} for A")
            move_discrepancy(round_, first, second, reason)
            raise ValueError("K identical-game gate failed")
        for game in games:
            counts[game.points_a] += 1
            abnormal += bool(game.termination and game.termination.lower() not in ("normal", "adjudication"))
        penta[pair_points] += 1
    return (counts[2], counts[0], counts[1]), tuple(penta), abnormal


def summarized_output(path):
    last = None
    summaries = []
    with path.open(encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            line = raw.strip()
            if match := MATCHUP.match(line):
                last = {"reverse": match[1] == "B"}
            if last is None:
                continue
            if match := ELO.match(line):
                last["elo"], last["margin"] = (Fraction(value) for value in match.groups())
            if match := GAME_COUNTS.match(line):
                last["games"], last["wins"], last["losses"], last["draws"] = map(int, match.groups())
            if match := PENTA.match(line):
                last["penta"] = tuple(map(int, match.groups()))
                if {"elo", "margin", "games", "wins", "losses", "draws"} <= last.keys():
                    if last["reverse"]:
                        last["wins"], last["losses"] = last["losses"], last["wins"]
                        last["elo"] = -last["elo"]
                        last["penta"] = last["penta"][::-1]
                    summaries.append(last)
                last = None
    return summaries


def penta_elo(penta):
    pairs = sum(penta)
    points = tuple(index / 4 for index in range(5))
    mean = sum(score * count for score, count in zip(points, penta)) / pairs
    spread = CI95 * sqrt(sum(count * (score - mean) ** 2 for score, count in zip(points, penta)) / pairs ** 2)
    if not 0 < mean - spread <= mean + spread < 1:
        return None
    def elo(score):
        return -400 * log10(1 / score - 1)
    return elo(mean), (elo(mean + spread) - elo(mean - spread)) / 2


def read_match(directory, name, pgn):
    meta, reason = read_meta(directory, name)
    if meta is None:
        return Match(name, "unavailable", note=reason)
    source = directory / f"{name}.pgn"
    groups = parse_games(source, pgn, exact_moves=name == "K")
    game_count = sum(map(len, groups.values()))
    expected = MATCHES[name][0]
    if game_count > expected or max(groups, default=0) > expected // 2:
        raise ValueError(f"{source}: unexpected games or pairing ID")
    (wins, losses, draws), penta, abnormal = tally_pairs(groups, exact_moves=name == "K")
    matched_games = 2 * sum(penta)
    if meta["status"] == "complete" and (game_count != expected or matched_games != expected):
        raise ValueError(f"{source}: complete match did not contain {expected} games in color-reversed pairs")
    print(f"{name}: {game_count} PGN games, {matched_games} in complete pairs, "
          f"{game_count - matched_games} unpaired, A W-L-D {wins}-{losses}-{draws}, "
          f"penta {penta}, abnormal terminations {abnormal}.")
    scores = [
        entry for entry in summarized_output(directory / f"{name}.out")
        if (entry["games"], entry["wins"], entry["losses"], entry["draws"], entry["penta"])
        == (matched_games, wins, losses, draws, penta)
    ]
    result = Match(
        name, meta["status"], game_count, matched_games, wins, losses, draws, penta, abnormal=abnormal,
        match_start=meta.get("match_start_utc"), match_end=meta.get("match_end_utc"),
        provenance=(meta["exe_sha256"], meta["fastchess_sha256"], meta["book_sha256"], tuple(meta["settings_b"])),
    )
    if not scores:
        if meta["status"] == "complete":
            raise ValueError(f"{name}: no printed pentanomial interval matching the complete PGN pairs")
        result.note = "no printed interval matches all complete pairs"
        return result
    result.elo, result.width = scores[-1]["elo"], scores[-1]["margin"]
    recomputed = penta_elo(penta)
    if recomputed is None or any(
        abs(float(printed) - correct) > 0.0050001
        for printed, correct in zip((result.elo, result.width), recomputed, strict=True)
    ):
        raise ValueError(f"{name}: printed Elo or 95% halfwidth disagrees with its pentanomial counts")
    print(f"{name}: printed Elo {number(result.elo)} ± {number(result.width, sign=False)} "
          f"matches the paired reconstruction, 95% {interval(result.interval)}.")
    return result


def number(value, sign=True, digits=2):
    if value is None:
        return "n/a"
    return f"{float(value):{('+' if sign else '')}.{digits}f}"


def interval(bounds, digits=2):
    if bounds is None:
        return "n/a"
    return "[" + ", ".join(number(value, digits=digits) for value in bounds) + "]"


def run_gates(directory, pgn, only_k):
    k = read_match(directory, "K", pgn)
    if k.status != "complete" or k.penta != (0, 0, 100, 0, 0):
        raise ValueError(f"K failed: {k.note or k.status}; expected 100 identical equal-point pairs")
    print("K PASS: 100 pairs with equal ordered moves and 1–1 A/B points.")
    if only_k:
        return
    c = read_match(directory, "C", pgn)
    assert_control(c)
    print(f"C PASS: Elo {number(c.elo)} and upper 95% bound {number(c.interval[1])}.")


def assert_control(c):
    if c.status != "complete" or c.elo is None or c.elo > -30 or c.interval[1] >= 0:
        raise ValueError(f"C failed: {c.note or c.status}; expected Elo at most −30 and upper 95% bound below zero")


def markdown_row(path, heading, first_column):
    section = False
    first = cells = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            if section:
                break
            section = line.lstrip("#").strip().startswith(heading)
        if not section or not line.startswith("|"):
            continue
        columns = [item.strip() for item in line.strip("|").split("|")]
        if first is None:
            first = columns
        if columns[0] == first_column:
            if cells is not None:
                raise ValueError(f"{path}: duplicate {first_column} in {heading}")
            cells = columns
    if not first or not cells or len(first) != len(cells):
        raise ValueError(f"{path}: could not find {first_column} in {heading}")
    return dict(zip(first, cells, strict=True))


def prior_table(directory, filename, job):
    scratch = directory / filename
    return scratch if scratch.is_file() else directory.resolve().parent.parent / f"REPORT_sol_job{job}.md"


def judge_effects(job10, job11):
    units = {}
    for judge, directory in (("R", job10), ("S", job11)):
        unit = json.loads((directory / "ruler-units.json").read_text(encoding="utf-8"))["U_hard"]
        if type(unit) is not int or not unit:
            raise ValueError(f"{directory}: invalid hard ruler unit")
        units[judge] = unit
    reference = {
        "R": markdown_row(prior_table(job10, "table-R.txt", 10), "Table R", "nodes 10000"),
        "S": markdown_row(prior_table(job11, "table-R-prime.txt", 11), "Table R", "nodes 10000"),
    }
    effects = {
        "C": {judge: Fraction(int(row["b"]) - int(row["a"]), units[judge]) for judge, row in reference.items()},
    }
    for name, setting, direction in (("E", "EvalSwingMult", "plus"), ("I", "IirDepth", "minus")):
        old = markdown_row(prior_table(job10, "table-AB.txt", 10), "Table B.", setting)
        new = markdown_row(prior_table(job11, "table-AB-prime.txt", 11), "Table B'.", setting)
        delta = {
            "R": int(old[f"Hard {direction}"].split(",")[0]),
            "S": int(new[f"Hard {direction} S"].split(",")[0]),
        }
        if delta["R"] != int(new[f"Hard {direction} R"].split(",")[0]):
            raise ValueError(f"{setting}: Job 10 and Job 11 Forge deltas disagree")
        effects[name] = {judge: Fraction(value, units[judge]) for judge, value in delta.items()}
    return effects


def classification(bounds, effects):
    inside = [judge for judge in ("R", "S") if bounds[0] <= effects[judge] <= bounds[1]]
    return "both" if len(inside) == 2 else inside[0] if inside else "neither"


def read_prediction(path):
    results = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts or parts[0] not in ("E", "I"):
            continue
        if len(parts) != 3 or parts[2] not in CATEGORIES or parts[0] in results:
            raise ValueError(f"{path}: expected {parts[0]} SIGNED_ELO R|S|neither")
        value = Fraction(0) if parts[1] == "zero" else Fraction(parts[1])
        results[parts[0]] = (value, parts[2])
    if set(results) != {"E", "I"}:
        raise ValueError(f"{path}: missing E or I prediction")
    return results


def grade_elo(guess, observed):
    if observed is None:
        return "ungraded"
    if guess == 0 or observed == 0:
        return "survives" if guess == observed else "KILLED (zero)"
    if guess * observed < 0:
        return "KILLED (sign)"
    return "survives" if 2 * abs(guess) / 3 <= abs(observed) <= 3 * abs(guess) / 2 else "KILLED"


def print_table(directory, pgn, forecasts, job10, job11):
    c = read_match(directory, "C", pgn)
    assert_control(c)
    candidates = {name: read_match(directory, name, pgn) for name in ("E", "I")}
    if any(result.provenance and result.provenance != c.provenance for result in candidates.values()):
        raise ValueError("E and I must use C's engine, fastchess executable, book and baseline settings")
    e, i = (candidates[name] for name in ("E", "I"))
    if e.match_start and e.match_end and i.match_start and i.match_end:
        if max(e.match_start, i.match_start) >= min(e.match_end, i.match_end):
            raise ValueError("E and I did not play concurrently")
        print(f"Recorded E interval {e.match_start}–{e.match_end}; I interval {i.match_start}–{i.match_end}.")
    refs = judge_effects(job10, job11)
    unit = abs(c.elo)
    verdicts = {}
    print("\n## Prediction grades\n")
    print("A nonzero Elo forecast requires the observed sign and a magnitude within a factor of 1.5. "
          "Zero requires zero. Judge forecasts are exact categories.\n")
    print("| Match | Forecast Elo | Measured Elo | Elo grade | Forecast judge | Measured judge | Judge grade |")
    print("|---|---:|---:|---|---|---|---|")
    for name, result in candidates.items():
        guess, judge = forecasts[name]
        bounds = tuple(value / unit for value in result.interval) if result.interval else None
        observed = classification(bounds, refs[name]) if bounds else None
        verdicts[name] = observed
        judge_grade = "ungraded" if observed is None else "survives" if judge == observed else "KILLED"
        print(f"| {name} | {number(guess)} | {number(result.elo)} | {grade_elo(guess, result.elo)} | "
              f"{judge} | {observed or 'n/a'} | {judge_grade} |")
    print("\n## Table G. Paired game outcomes and agreement judges\n")
    print(f"All results are from engine A's perspective. One C-normalized unit is "
          f"{number(unit, sign=False)} Elo. Judge coverage uses the inclusive 95% interval in those units.\n")
    print("| Match | Status | Paired games | W-L-D | Pentanomial | Elo [95% interval] | "
          "C-normalized Elo [95% interval] | R agreement doublings | S agreement doublings |")
    print("|---|---|---:|---|---|---|---|---:|---:|")
    for name, result in {"C": c, **candidates}.items():
        if result.note:
            status = f"{result.status}: {result.note}"
        else:
            status = result.status
        unpaired = result.raw_games - result.games
        if unpaired:
            status += f" ({unpaired} unpaired PGN {'game' if unpaired == 1 else 'games'} excluded)"
        status = status.replace("|", "&#124;").replace("\n", " ")
        normalized = tuple(value / unit for value in result.interval) if result.interval else None
        paired = result.games if result.penta else "n/a"
        wld = f"{result.wins}-{result.losses}-{result.draws}" if result.penta else "n/a"
        print(f"| {name} | {status} | {paired} | "
              f"{wld} | {', '.join(map(str, result.penta)) or 'n/a'} | "
              f"{number(result.elo)} {interval(result.interval)} | "
              f"{number(result.elo / unit if result.elo is not None else None, digits=4)} {interval(normalized, digits=4)} | "
              f"{number(refs[name]['R'], digits=4)} | {number(refs[name]['S'], digits=4)} |")
    print()
    for name, winner in verdicts.items():
        print(f"{name}: Games side with {winner}." if winner else f"{name}: Judge comparison unavailable.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for name in ("gates", "table"):
        sub = modes.add_parser(name)
        sub.add_argument("match_dir", type=Path)
        sub.add_argument("--python-chess-dir", type=Path)
        if name == "gates":
            sub.add_argument("--only-k", action="store_true")
        else:
            for path in ("job10-dir", "job11-dir", "prediction"):
                sub.add_argument("--" + path, type=Path, required=True)
    args = parser.parse_args()
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        run_gates(args.match_dir, pgn, args.only_k)
    else:
        forecasts = read_prediction(args.prediction)
        print_table(args.match_dir, pgn, forecasts, args.job10_dir, args.job11_dir)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
