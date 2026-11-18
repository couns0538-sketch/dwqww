#!/usr/bin/env python3
"""Read Job 18 UCI transcripts and derive the mate census independently."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ORDER = "ABDCEGF"
ENGINE_SHA = "40ace81ab55777c1e46787b079c35d02279b7eab59dcf70068a33a167894f910"
FIXTURE_SHA = "b2131c5af5307ac14174fe30d66780d8007dab68c7fbc6a8b9126f52637389ab"
CENSUS_DEPTH = 16
PIECE_BINS = ((12, 15, "12–15"), (16, 19, "16–19"), (20, 32, "20+"))

COMMON_OPTIONS = [
    ("Threads", 1), ("Hash", 16),
]
SEARCH_OPTIONS = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
    ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
    ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
    ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
    ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
S14 = COMMON_OPTIONS + SEARCH_OPTIONS
PC20 = (
    COMMON_OPTIONS
    + [("MultiPV", 1), ("UseNNUE", "true"), ("OwnBook", "false")]
    + SEARCH_OPTIONS
    + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
)
QUIET_ONLY = [("HistReworkQuiet", 2), ("HistReworkCorrection", 0)]
SETTINGS = {
    "A": S14,
    "B": S14 + QUIET_ONLY,
    "D": S14 + QUIET_ONLY + [("QuietReadPlainR3", 1)],
    "C": S14 + QUIET_ONLY + [("QuietReadPlainR1", 1)],
    "E": PC20,
    "G": PC20 + [("HistReworkQuiet", 0)],
    "F": PC20 + [("QuietReadPlainR3", 1)],
}
CAPTURE_FIELDS = (
    "index fen game plies_before_end pieces first_mate_depth first_mate_nodes "
    "info_depth score_type score nodes bestmove nc0 nc1 nc2 nc3 nc4"
).split()
REFUSAL = re.compile(r"\b(?:unknown option|invalid value|ERROR)\b", re.IGNORECASE)
BESTMOVE = re.compile(r"bestmove ((?:[a-h][1-8]){2}[qrbn]?|0000|\(none\))(?: ponder \S+)?")
COUNTERS = re.compile(r"NC0 (\d+) (\d+) (\d+) (\d+) (\d+)")
EXIT = re.compile(r"^(?:exit(?:_code)?|driver_exit)(?:=|\s+)(-?\d+)$", re.MULTILINE)


@dataclass(frozen=True)
class Position:
    fen: str
    game: int
    plies: int
    pieces: int


ROW24 = Position("8/8/kp3QK1/p2R4/2p5/3n4/PP6/8 w - - 6 49", 8, 7, 10)


@dataclass(frozen=True)
class Info:
    depth: int
    kind: str
    score: int
    nodes: int
    bound: str | None
    line: str

    def positive_mate(self):
        return self.kind == "mate" and self.score > 0


@dataclass(frozen=True)
class Result:
    first: Info | None
    last: Info
    move: str
    nc: tuple[int, ...]
    bestmove_line: str


def positions_from_file(path):
    fixtures = path.read_bytes()
    if b"\r" in fixtures or not fixtures.endswith(b"\n"):
        raise ValueError(f"{path}: fixture requires LF line endings and a final LF")
    positions = []
    for index, line in enumerate(fixtures.decode("ascii").splitlines(), 1):
        fen, raw_game, raw_plies, raw_pieces = line.split("\t")
        game, plies, pieces = int(raw_game), int(raw_plies), int(raw_pieces)
        fields = fen.split()
        if len(fields) != 6 or game < 1 or plies not in (3, 5, 7) or not 2 <= pieces <= 32:
            raise ValueError(f"{path}:{index}: invalid position entry")
        on_board = sum(piece in "prnbqkPRNBQK" for piece in fields[0])
        if pieces != on_board:
            raise ValueError(f"{path}:{index}: labels {pieces} pieces, FEN carries {on_board}")
        positions.append(Position(fen, game, plies, pieces))
    if len(positions) != 120:
        raise ValueError(f"{path}: expected 120 positions, got {len(positions)}")
    previous_game = 0
    for start in range(0, len(positions), 3):
        trio = positions[start:start + 3]
        game = trio[0].game
        if (game <= previous_game or any(position.game != game for position in trio)
                or [position.plies for position in trio] != [3, 5, 7] or trio[-1].pieces < 14):
            raise ValueError(f"{path}:{start + 1}: invalid group for fixture game {game}")
        previous_game = game
    return positions, hashlib.sha256(fixtures).hexdigest()


def check_commands(path, setting, positions, depth):
    commands = path.read_text().splitlines()
    expected = ["uci"] + [
        f"setoption name {name} value {value}" for name, value in SETTINGS[setting]
    ]
    setup_ready = commands[len(expected):len(expected) + 1] == ["isready"]
    if setup_ready:
        expected.append("isready")
    for position in positions:
        expected.extend(["ucinewgame", "isready", f"position fen {position.fen}", f"go depth {depth}"])
    expected.append("quit")
    for index, (wanted, actual) in enumerate(zip(expected, commands), 1):
        if wanted != actual:
            raise ValueError(f"{path}:{index}: expected {wanted!r}, got {actual!r}")
    if len(commands) != len(expected):
        raise ValueError(f"{path}: expected {len(expected)} commands, got {len(commands)}")
    return setup_ready


def parse_info(line, depth_limit):
    parts = line.split()
    try:
        depth = int(parts[1 + parts.index("depth")])
        nodes = int(parts[1 + parts.index("nodes")])
        score_index = parts.index("score")
        kind, raw_score = parts[score_index + 1:score_index + 3]
        value = int(raw_score)
    except (ValueError, IndexError) as error:
        raise ValueError(f"malformed depth info: {line}") from error
    bounds = [word for word in ("lowerbound", "upperbound") if word in parts]
    if not 0 <= depth <= depth_limit or nodes < 0 or kind not in ("cp", "mate") or len(bounds) > 1:
        raise ValueError(f"invalid depth info: {line}")
    return Info(depth, kind, value, nodes, bounds[0] if bounds else None, line)


def classify_line(line):
    if line in ("uciok", "readyok"):
        return line
    for prefix, label in (("info depth ", "info"), ("bestmove ", "bestmove"), ("NC0 ", "NC0")):
        if line.startswith(prefix):
            return label
    return "other"


def read_stdout(path, setup_ready, positions, depth):
    lines = path.read_text().splitlines()
    refused = next((line for line in lines if REFUSAL.search(line)), None)
    if refused is not None:
        raise ValueError(f"{path}: engine refusal: {refused}")
    events = iter((kind, line) for line in lines if (kind := classify_line(line)) != "other")

    def require(kind, context):
        event = next(events, None)
        if event is None:
            raise ValueError(f"{path}: EOF while waiting for {kind} ({context})")
        if event[0] != kind:
            raise ValueError(f"{path}: expected {kind} ({context}), got {event[1]!r}")
        return event[1]

    require("uciok", "UCI startup")
    if setup_ready:
        require("readyok", "configured engine")
    results = []
    for index, _ in enumerate(positions, 1):
        context = f"position {index}"
        require("readyok", context)
        last = None
        first = None
        for kind, line in events:
            if kind == "info":
                last = parse_info(line, depth)
                if first is None and last.positive_mate() and last.bound is None:
                    first = last
            elif kind == "bestmove":
                bestmove = BESTMOVE.fullmatch(line)
                if bestmove is None or last is None:
                    raise ValueError(f"{path}: invalid bestmove or missing depth info ({context}): {line}")
                break
            else:
                raise ValueError(f"{path}: unexpected UCI event before bestmove ({context}): {line}")
        else:
            raise ValueError(f"{path}: EOF before bestmove ({context})")
        counter_line = require("NC0", context)
        counts = COUNTERS.fullmatch(counter_line)
        if counts is None:
            raise ValueError(f"{path}: invalid NC0 line ({context}): {counter_line}")
        results.append(Result(first, last, bestmove[1], tuple(map(int, counts.groups())), bestmove[0]))
    extra = next(events, None)
    if extra is not None:
        raise ValueError(f"{path}: extra UCI event after the last search: {extra[1]}")
    return results


def check_rows(path, positions, results):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != CAPTURE_FIELDS:
            raise ValueError(f"{path}: unexpected TSV columns: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != len(positions):
        raise ValueError(f"{path}: expected {len(positions)} rows, got {len(rows)}")
    for index, (position, search, row) in enumerate(zip(positions, results, rows), 1):
        first_depth = "" if search.first is None else str(search.first.depth)
        first_nodes = "" if search.first is None else str(search.first.nodes)
        values = (
            index, position.fen, position.game, position.plies, position.pieces, first_depth, first_nodes,
            search.last.depth, search.last.kind, search.last.score, search.last.nodes, search.move, *search.nc,
        )
        for field, value in zip(CAPTURE_FIELDS, values):
            if row.get(field) != str(value):
                raise ValueError(f"{path}: row {index}, {field}: raw {value!r}, TSV {row.get(field)!r}")
        if None in row:
            raise ValueError(f"{path}: row {index} has surplus columns")


def checked_run(root, setting, positions, depth=CENSUS_DEPTH):
    directory = root / setting
    commands = directory / "engine.commands.txt"
    stdout = directory / "engine.stdout.txt"
    stderr = directory / "engine.stderr.txt"
    rows = directory / "rows.tsv"
    metadata = directory / "run.meta"
    meta = metadata.read_text()
    if ENGINE_SHA not in meta:
        raise ValueError(f"{metadata}: missing expected Forge binary SHA-256")
    exits = EXIT.findall(meta)
    if exits != ["0"]:
        raise ValueError(f"{metadata}: expected one successful exit, got {exits}")
    if REFUSAL.search(stderr.read_text()):
        raise ValueError(f"{stderr}: contains an engine refusal")
    setup_ready = check_commands(commands, setting, positions, depth)
    results = read_stdout(stdout, setup_ready, positions, depth)
    check_rows(rows, positions, results)
    receipt = {
        "searches": len(results),
        "setup_isready": setup_ready,
        "meta_exit_codes": [int(code) for code in exits],
        "sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in (commands, stdout, stderr, rows, metadata)},
    }
    return results, receipt


def row_position(index, positions):
    position = positions[index]
    return {"index": index + 1, "fen": position.fen, "game": position.game,
            "plies_before_end": position.plies, "pieces": position.pieces}


def search_details(search):
    return {
        "first_mate_depth": None if search.first is None else search.first.depth,
        "first_mate_nodes": None if search.first is None else search.first.nodes,
        "first_mate_info": None if search.first is None else search.first.line,
        "last_depth": search.last.depth, "last_score_type": search.last.kind,
        "last_score": search.last.score, "last_bound": search.last.bound,
        "last_nodes": search.last.nodes, "bestmove": search.move,
        "last_info": search.last.line, "bestmove_line": search.bestmove_line,
    }


def analyze(positions, runs, indexes):
    base = runs["A"]
    mate_cohort = {index for index in indexes if base[index].last.positive_mate()}
    result = {"position_count": len(indexes), "M_size": len(mate_cohort),
              "M_indexes": sorted(i + 1 for i in mate_cohort), "settings": {}}
    missed = {}
    delayed = {}
    for setting, searches in runs.items():
        events = {index: searches[index] for index in indexes}
        found = {index for index, search in events.items() if search.first is not None}
        missing = sorted(mate_cohort - found)
        missed[setting] = set(missing)
        counts = dict.fromkeys(("earlier", "same", "later", "none", "unclassified"), 0)
        counts["none"] = len(missing)
        delayed[setting] = set()
        for index in sorted(mate_cohort & found):
            first_a = base[index].first
            this = searches[index].first
            if first_a is None:
                counts["unclassified"] += 1
            elif this.depth < first_a.depth:
                counts["earlier"] += 1
            elif this.depth > first_a.depth:
                counts["later"] += 1
                delayed[setting].add(index)
            else:
                counts["same"] += 1
        outside_m = sorted(found - mate_cohort)
        result["settings"][setting] = {
            "positions_with_first_exact_mate": len(found),
            "positions_with_last_positive_mate": sum(search.last.positive_mate() for search in events.values()),
            "on_M": counts,
            "mates_outside_M": [
                row_position(index, positions) | {
                    "A_had_first_exact_mate": base[index].first is not None,
                    "A": search_details(base[index]), "setting": search_details(searches[index]),
                } for index in outside_m
            ],
            "outside_M_where_A_never_found_exact_mate": [
                index + 1 for index in outside_m if base[index].first is None
            ],
            "misses_on_M": [
                row_position(index, positions) | {
                    "A": search_details(base[index]), "setting": search_details(searches[index]),
                } for index in missing
            ],
            "delays_on_M": [
                row_position(index, positions) | {
                    "A": search_details(base[index]), "setting": search_details(searches[index]),
                } for index in sorted(delayed[setting])
            ],
            "first_vs_last_mate_presence_disagreements": [
                row_position(index, positions) | search_details(search)
                for index, search in events.items()
                if (search.first is not None) != search.last.positive_mate()
            ],
            "last_positive_mates_with_bound": [
                row_position(index, positions) | search_details(search)
                for index, search in events.items()
                if search.last.positive_mate() and search.last.bound is not None
            ],
        }

    def recovery(control, treatment):
        recovered = sorted(missed[control] - missed[treatment])
        new_misses = sorted(missed[treatment] - missed[control])
        comparable = sorted(mate_cohort - missed[control] - missed[treatment])
        depth_changes = {index: runs[treatment][index].first.depth - runs[control][index].first.depth
                         for index in comparable}
        deltas = Counter(depth_changes.values())

        def paired_row(index):
            return row_position(index, positions) | {
                "A": search_details(base[index]),
                "control": search_details(runs[control][index]),
                "treatment": search_details(runs[treatment][index]),
            }

        return {
            "count": len(recovered),
            "of_control_misses": len(missed[control]),
            "positions": [row_position(index, positions) for index in recovered],
            "recovered_details": [paired_row(index) for index in recovered],
            "paired_on_M": {
                "earlier": sum(count for delta, count in deltas.items() if delta < 0),
                "same": deltas[0],
                "later": sum(count for delta, count in deltas.items() if delta > 0),
                "new_miss": len(new_misses),
                "recovered": len(recovered),
                "both_miss": len(missed[control] & missed[treatment]),
                "first_depth_delta_histogram": dict(sorted(deltas.items())),
            },
            "new_miss_indexes": [index + 1 for index in new_misses],
            "new_miss_details": [paired_row(index) for index in new_misses],
            "changed_first_depth_details": [
                paired_row(index) | {"depth_delta": delta}
                for index, delta in depth_changes.items() if delta != 0
            ],
            "delayed_in_control_removed_or_earlier_than_A": [
                paired_row(index) for index in sorted(delayed[control] - delayed[treatment] - missed[treatment])
            ],
        }

    result["recoveries_on_M"] = {
        f"{control}_to_{treatment}": recovery(control, treatment)
        for control, treatment in (("B", "C"), ("B", "D"), ("E", "G"), ("E", "F"))
        if control in missed and treatment in missed
    }
    return result


def audit_row24(root):
    fixture = root / "row24.txt"
    expected = f"{ROW24.fen}\t{ROW24.game}\t{ROW24.plies}\t{ROW24.pieces}\n".encode("ascii")
    if fixture.read_bytes() != expected:
        raise ValueError(f"{fixture}: differs from the stipulated Job 17 row 24")
    output = {"job17_index": 24, "requested_depth": 22, "position": row_position(0, [ROW24]), "settings": {}}
    for setting in "DA":
        raw, receipt = checked_run(root, setting, [ROW24], depth=22)
        search = raw[0]
        output["settings"][setting] = {"result": search_details(search), "nc": search.nc, "receipt": receipt}
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_dir", type=Path, nargs="?", help="directory with positions.txt and census/")
    parser.add_argument("--settings", choices=tuple(ORDER[:n] for n in range(1, len(ORDER) + 1)),
                        default=ORDER, help="completed settings in prescribed order")
    row24 = parser.add_mutually_exclusive_group()
    row24.add_argument("--row24-dir", type=Path, help="also check the two completed depth-22 searches here")
    row24.add_argument("--row24-only", type=Path, help="check only the two depth-22 searches here")
    args = parser.parse_args()
    if args.job_dir is None and args.row24_only is None:
        parser.error("job_dir is required unless --row24-only is given")
    try:
        if args.row24_only is not None:
            print(json.dumps(audit_row24(args.row24_only), indent=2, ensure_ascii=False))
            return
        positions, digest = positions_from_file(args.job_dir / "positions.txt")
        runs, receipts = {}, {}
        for setting in args.settings:
            runs[setting], receipts[setting] = checked_run(args.job_dir / "census", setting, positions)
        report = analyze(positions, runs, range(len(positions)))
        groups = {label: [i for i, position in enumerate(positions) if lower <= position.pieces <= upper]
                  for lower, upper, label in PIECE_BINS}
        residual = [i for i, position in enumerate(positions) if position.pieces < 12]
        if residual:
            groups["below 12"] = residual
        report["piece_bins"] = {label: analyze(positions, runs, indexes) for label, indexes in groups.items()}
        if args.row24_dir is not None:
            report["row24_depth22"] = audit_row24(args.row24_dir)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    report.update({
        "positions": len(positions), "positions_sha256": digest,
        "matches_expected_position_fixture": digest == FIXTURE_SHA,
        "expected_forge_sha256": ENGINE_SHA, "audited_setting_order": args.settings,
        "raw_receipts": receipts,
    })
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
