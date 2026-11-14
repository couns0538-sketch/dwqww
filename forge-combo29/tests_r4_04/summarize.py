#!/usr/bin/env python3
"""Build chunk summaries and REPORT_r4_04.md from match artifacts.

Screening statistics follow fastchess pentanomial Elo (95% z=1.959963984540054).
Option-on is the first engine. This is a screen, not a strength claim.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "tests_r4_04"
REPORT = ROOT / "REPORT_r4_04.md"
BOOK = Path("/tmp/r4_04/UHO_Lichess_4852_v1.epd")
Z95 = 1.959963984540054
ON = "ContHist4PlyRead-on"
OFF = "ContHist4PlyRead-off"

HEADER_RE = re.compile(r'^\[([A-Za-z0-9]+)\s+"(.*)"\]\s*$')
RESULT_BLOCK_RE = re.compile(
    r"Results of ContHist4PlyRead-on vs ContHist4PlyRead-off.*?\n"
    r"Elo: (?P<elo>.*?)\n"
    r"LOS: (?P<los>.*?), DrawRatio: (?P<draw>.*?), PairsRatio: (?P<pairs>.*?)\n"
    r"Games: (?P<games>\d+), Wins: (?P<wins>\d+), Losses: (?P<losses>\d+), "
    r"Draws: (?P<draws>\d+), Points: (?P<points>[\d.]+) \((?P<pct>[\d.]+) %\)\n"
    r"Ptnml\(0-2\): \[(?P<penta>[^\]]+)\]",
    re.S,
)


def elo_from_score(score: float) -> float:
    score = min(max(score, 1e-12), 1.0 - 1e-12)
    return -400.0 * math.log10(1.0 / score - 1.0)


def pentanomial_stats(counts: list[int]) -> dict[str, float]:
    """counts = [LL, LD, DD+WL, WD, WW]. Middle bin shares the 0.5 score."""
    pairs = sum(counts)
    if pairs <= 0:
        return {}
    weights = (0.0, 0.25, 0.5, 0.75, 1.0)
    score = sum(c * w for c, w in zip(counts, weights)) / pairs
    variance = sum(c * (w - score) ** 2 for c, w in zip(counts, weights)) / pairs
    variance_mean = variance / pairs
    se = math.sqrt(variance_mean) if variance_mean > 0 else 0.0
    lo = min(max(score - Z95 * se, 1e-12), 1.0 - 1e-12)
    hi = min(max(score + Z95 * se, 1e-12), 1.0 - 1e-12)
    if variance_mean == 0:
        los = 100.0 if score > 0.5 else (50.0 if score == 0.5 else 0.0)
    else:
        los = (1.0 - math.erf(-(score - 0.5) / math.sqrt(2.0 * variance_mean))) / 2.0 * 100.0
    return {
        "pairs": pairs,
        "games": pairs * 2,
        "score": score,
        "elo": elo_from_score(score),
        "elo_margin": (elo_from_score(hi) - elo_from_score(lo)) / 2.0,
        "elo_lo": elo_from_score(lo),
        "elo_hi": elo_from_score(hi),
        "los": los,
    }


def parse_pgn(path: Path) -> list[dict[str, str]]:
    games: list[dict[str, str]] = []
    current: dict[str, str] = {}
    in_moves = False
    if not path.exists():
        return games
    for line in path.read_text(errors="replace").splitlines():
        match = HEADER_RE.match(line)
        if match and not in_moves:
            current[match.group(1)] = match.group(2)
            continue
        result = current.get("Result", "")
        stripped = line.strip()
        if stripped == "":
            continue
        in_moves = True
        if result in {"1-0", "0-1", "1/2-1/2"} and stripped.endswith(result):
            games.append(current)
            current = {}
            in_moves = False
    return games


def on_point(game: dict[str, str]) -> float | None:
    white = game.get("White", "")
    result = game.get("Result", "")
    if white == ON and result == "1-0":
        return 1.0
    if white == ON and result == "0-1":
        return 0.0
    if white == OFF and result == "0-1":
        return 1.0
    if white == OFF and result == "1-0":
        return 0.0
    if result == "1/2-1/2" and white in {ON, OFF}:
        return 0.5
    return None


def pair_counts(games: list[dict[str, str]]) -> tuple[list[int], dict[str, int], list[str]]:
    by_round: dict[str, list[dict[str, str]]] = {}
    notes: list[str] = []
    wld = {"W": 0, "L": 0, "D": 0, "other": 0}
    for game in games:
        point = on_point(game)
        if point is None:
            wld["other"] += 1
            continue
        if point == 1.0:
            wld["W"] += 1
        elif point == 0.0:
            wld["L"] += 1
        else:
            wld["D"] += 1
        by_round.setdefault(game.get("Round", "?"), []).append(game)
    counts = [0, 0, 0, 0, 0]
    wl = dd = 0
    for round_name, pair in by_round.items():
        if len(pair) != 2:
            notes.append(f"round {round_name} has {len(pair)} scored games")
            continue
        points = [on_point(game) for game in pair]
        if any(point is None for point in points):
            continue
        total = points[0] + points[1]
        index = int(total * 2)
        if index < 0 or index > 4:
            notes.append(f"round {round_name} pair score {total}")
            continue
        counts[index] += 1
        if total == 1.0:
            if points[0] == 0.5 and points[1] == 0.5:
                dd += 1
            else:
                wl += 1
    if sum(counts):
        notes.append(f"middle bin split DD={dd} WL={wl}")
    return counts, wld, notes


def book_lines() -> list[str]:
    if not BOOK.exists():
        return []
    return [line.strip() for line in BOOK.read_text(errors="replace").splitlines() if line.strip()]


def check_openings(games: list[dict[str, str]], start: int, rounds: int, book: list[str]) -> str:
    if not book or not games:
        return "opening check skipped"
    expected = book[start - 1 : start - 1 + rounds]
    seen: dict[str, str] = {}
    for game in games:
        fen = game.get("FEN", "")
        round_name = game.get("Round", "")
        if not fen or not round_name:
            continue
        previous = seen.get(round_name)
        if previous is None:
            seen[round_name] = fen
        elif previous != fen:
            return f"opening mismatch inside round {round_name}"
    mismatches = 0
    checked = 0
    for round_name, fen in seen.items():
        if not round_name.isdigit():
            continue
        index = int(round_name) - 1
        if index < 0 or index >= len(expected):
            mismatches += 1
            continue
        checked += 1
        if fen != expected[index]:
            mismatches += 1
    return f"openings checked {checked} mismatches {mismatches} start {start} rounds {rounds}"


def last_fastchess_block(text: str) -> re.Match[str] | None:
    found = None
    for found in RESULT_BLOCK_RE.finditer(text):
        pass
    return found


def read_kv(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        if " " not in line:
            continue
        key, value = line.split(" ", 1)
        data[key] = value
    return data


def bench_rows(path: Path) -> list[tuple[str, int, int, int]]:
    rows: list[tuple[str, int, int, int]] = []
    if not path.exists():
        return rows
    side = "off"
    for line in path.read_text().splitlines():
        match = re.search(r"nodes (\d+) time (\d+) nps (\d+)", line)
        if not match:
            continue
        nodes, time_ms, nps = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        rows.append((side, nodes, time_ms, nps))
        side = "on" if side == "off" else "off"
    return rows


def mean(values: list[int]) -> float:
    return sum(values) / len(values) if values else 0.0


def write_chunk_summary(chunk_dir: Path, book: list[str]) -> None:
    meta = read_kv(chunk_dir / "meta.txt")
    games = parse_pgn(chunk_dir / "games.pgn")
    counts, wld, notes = pair_counts(games)
    stats = pentanomial_stats(counts)
    start = int(meta.get("start", "1"))
    rounds = int(meta.get("rounds", "500"))
    opening = check_openings(games, start, rounds, book)
    stdout = (chunk_dir / "stdout.txt").read_text(errors="replace") if (chunk_dir / "stdout.txt").exists() else ""
    block = last_fastchess_block(stdout)
    lines = [
        f"chunk {chunk_dir.name}",
        f"meta {meta.get('status', 'unknown')} start={meta.get('start', '?')} rounds={meta.get('rounds', '?')} elapsed_sec={meta.get('elapsed_sec', '?')}",
        f"pgn_games {len(games)} W-L-D {wld['W']}-{wld['L']}-{wld['D']} other {wld['other']}",
        f"pentanomial LL LD DD+WL WD WW {counts}",
        opening,
        *notes,
    ]
    if stats:
        lines.append(
            "independent_pentanomial Elo {elo:.2f} +/- {margin:.2f} (95%) "
            "bounds {lo:.2f} .. {hi:.2f} LOS {los:.2f}% score {score:.4f} pairs {pairs:.0f}".format(
                elo=stats["elo"],
                margin=stats["elo_margin"],
                lo=stats["elo_lo"],
                hi=stats["elo_hi"],
                los=stats["los"],
                score=stats["score"],
                pairs=stats["pairs"],
            )
        )
    if block:
        lines.append("fastchess_tail:")
        lines.append(block.group(0).strip())
    (chunk_dir / "summary.txt").write_text("\n".join(lines) + "\n")


def main() -> None:
    versions = (TEST / "versions.txt").read_text().rstrip() + "\n" if (TEST / "versions.txt").exists() else ""
    pins = (TEST / "pins.txt").read_text().rstrip() + "\n" if (TEST / "pins.txt").exists() else ""
    command = (TEST / "command.txt").read_text().rstrip() + "\n" if (TEST / "command.txt").exists() else ""
    rows = bench_rows(TEST / "bench13_alternating.txt")
    off_nps = [nps for side, _nodes, _time, nps in rows if side == "off"]
    on_nps = [nps for side, _nodes, _time, nps in rows if side == "on"]
    off_nodes = sorted({nodes for side, nodes, _time, _nps in rows if side == "off"})
    on_nodes = sorted({nodes for side, nodes, _time, _nps in rows if side == "on"})
    book = book_lines()
    chunks = sorted(path for path in TEST.glob("chunk*") if path.is_dir())
    for chunk_dir in chunks:
        write_chunk_summary(chunk_dir, book)

    all_games: list[dict[str, str]] = []
    chunk_sections: list[str] = []
    for chunk_dir in chunks:
        games = parse_pgn(chunk_dir / "games.pgn")
        all_games.extend(games)
        summary = (chunk_dir / "summary.txt").read_text().rstrip() if (chunk_dir / "summary.txt").exists() else ""
        sha = ""
        pgn = chunk_dir / "games.pgn"
        if pgn.exists():
            import hashlib

            digest = hashlib.sha256(pgn.read_bytes()).hexdigest()
            sha = f"sha256 {digest} bytes {pgn.stat().st_size}"
        chunk_sections.append(f"### {chunk_dir.name}\n\n{sha}\n\n```\n{summary}\n```\n")

    counts, wld, notes = pair_counts(all_games)
    stats = pentanomial_stats(counts)
    if stats:
        total_line = (
            f"W-L-D (option on first): {wld['W']}-{wld['L']}-{wld['D']}\n\n"
            f"Pentanomial [LL, LD, DD+WL, WD, WW]: {counts[0]}, {counts[1]}, {counts[2]}, {counts[3]}, {counts[4]}\n\n"
            f"Elo 95%: {stats['elo']:.2f} +/- {stats['elo_margin']:.2f} "
            f"({stats['elo_lo']:.2f} to {stats['elo_hi']:.2f})\n\n"
            f"LOS: {stats['los']:.2f}%\n\n"
            f"Pairs: {int(stats['pairs'])}. Games: {int(stats['games'])}. "
            f"Score: {stats['score']:.4f}.\n"
        )
    else:
        total_line = "No completed pairs yet.\n"
    notes_line = "\n".join(f"- {note}" for note in notes) if notes else "- none"

    bench_table = "\n".join(
        f"| {index} | {side} | {nodes} | {time_ms} | {nps} |"
        for index, (side, nodes, time_ms, nps) in enumerate(rows, start=1)
    )
    off_mean = mean(off_nps)
    on_mean = mean(on_nps)

    report = f"""# R4-04 screen: ContHist4PlyRead

Screening only. This is one fixed-node match of the existing UCI check `ContHist4PlyRead` (default false) on one binary, option on versus option off. It is not a strength claim, not an SPRT, and not a replication of another machine.

The owner's PC screen was +3.1 +/- 6.9 over 4000 games. That number is context for this screen. It is not a result from this run.

## Setup

Same binary both sides. Engine source was not modified. Tested tree `e04556ddc3a430b2e751159b0d46111ef56c8b89`. The option was introduced in `b68d49fedcc8e705484d06fb02cf0a417734839f` and is present, default off, in the tested tree.

Owner build: the host has AVX-512F and BMI2, so this is the non-portable lock (`FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`, `-march=x86-64-v4`), not the portable build.

Conditions: `go nodes 50000`, Threads 1, Hash 16, OwnBook false, `ContHist4PlyRead` true versus false. Book `UHO_Lichess_4852_v1.epd` (2632036 lines, sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`), order sequential, chunks of 500 openings, both colors (`-repeat`, 1000 games per full chunk). No resign adjudication and no score draw adjudication. Engines restart each game. Concurrency 2. fastchess alpha 1.8.3.

Match budget: sequential chunks until 6 hours from the first chunk, and not past 9 hours. Chunks already started are allowed to finish inside that outer limit.

## Command

```
{command.rstrip()}
```

`START` is 1, 501, 1001, ... and `CHUNK` is the chunk directory. The command is also in `tests_r4_04/command.txt`.

## Versions and hashes

```
{versions.rstrip()}
```

## Pins

Default option state (ContHist4PlyRead false). `scripts/check_pins.sh` on this binary:

```
{pins.rstrip()}
```

The three named pins are unchanged: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. With the option on, bench 13 nodes move to 989877. That is the same on-value already recorded for this candidate. The screen uses one binary; the option is the only difference.

## bench 13 nps, five alternating runs

Order is off, on, off, on, off, on, off, on, off, on. Nodes stay on the pin when the option is off.

| run | option | nodes | time_ms | nps |
| ---: | --- | ---: | ---: | ---: |
{bench_table}

Off mean nps {off_mean:.0f} over {len(off_nps)} runs, nodes {off_nodes}. On mean nps {on_mean:.0f} over {len(on_nps)} runs, nodes {on_nodes}. These nps figures are from this container. They are not a speed claim.

## Pooled screen

Scores are from the option-on side. W-L-D is wins, losses, draws for option on. Pentanomial bins are pair results over the two colors of one opening: LL, LD (or DL), DD+WL, WD (or DW), WW. Elo and LOS use the fastchess pentanomial model: pair score in game-point units, variance of that score, 95% interval z=1.959963984540054, Elo = -400 log10(1/p - 1), and the printed margin is half the distance between the Elo values of the two score bounds. LOS is the normal probability that the true score is above 0.5.

{total_line}
Pair notes:

{notes_line}

## Chunks

{''.join(chunk_sections) if chunk_sections else "No chunk has been written yet.\n"}
"""
    REPORT.write_text(report)


if __name__ == "__main__":
    main()
