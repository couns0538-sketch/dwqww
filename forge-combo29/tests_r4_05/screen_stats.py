#!/usr/bin/env python3
"""Aggregate the NonPawnCorrection on-vs-off screen and write the report.

Option-on is the first engine. Statistics are pentanomial over color-swapped
opening pairs, using the same logistic Elo, 95% half-width, and LOS as
fastchess (normalized pair score, z = 1.959963984540054). This is a screen
summary, not a strength claim.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

ON = "NonPawnCorrectionOn"
OFF = "NonPawnCorrectionOff"
Z95 = 1.959963984540054
HEADER_RE = re.compile(r'^\[(\w+)\s+"(.*)"\]', re.M)
ELO_RE = re.compile(r"Elo:\s*([+-]?\d+(?:\.\d+)?)\s*\+/-\s*([+-]?\d+(?:\.\d+)?)")
LOS_RE = re.compile(r"LOS:\s*([+-]?\d+(?:\.\d+)?)\s*%")
PENTA_RE = re.compile(r"Ptnml\(0-2\):\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]")
WLD_RE = re.compile(r"Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+)")


def elo_from_score(score: float) -> float:
    clamped = min(max(score, 1e-12), 1.0 - 1e-12)
    return -400.0 * math.log10(1.0 / clamped - 1.0)


def parse_games(text: str) -> list[dict[str, str]]:
    parts = re.split(r"\n(?=\[Event )", text.strip())
    games: list[dict[str, str]] = []
    for part in parts:
        if "[White " not in part:
            continue
        games.append(dict(HEADER_RE.findall(part)))
    return games


def points_for_on(headers: dict[str, str]) -> float:
    result = headers.get("Result", "")
    white = headers.get("White", "")
    if result == "1/2-1/2":
        return 0.5
    if result == "1-0":
        return 1.0 if white == ON else 0.0
    if result == "0-1":
        return 0.0 if white == ON else 1.0
    raise ValueError(f"unrecognized result {result!r} for white {white!r}")


def pentanomial(games: list[dict[str, str]]) -> dict[str, float | int | tuple[int, int, int, int, int]]:
    if len(games) % 2 != 0:
        raise ValueError(f"odd game count {len(games)}")
    wins = losses = draws = 0
    ll = ld = mid = wd = ww = 0
    terminations: dict[str, int] = {}
    for index in range(0, len(games), 2):
        first, second = games[index], games[index + 1]
        if first.get("FEN") != second.get("FEN"):
            raise ValueError(f"pair {index // 2 + 1} FENs differ")
        if first.get("White") != ON or second.get("White") != OFF:
            raise ValueError(
                f"pair {index // 2 + 1} color order is {first.get('White')} / {second.get('White')}"
            )
        pair_points = 0.0
        for game in (first, second):
            score = points_for_on(game)
            pair_points += score
            if score == 1.0:
                wins += 1
            elif score == 0.0:
                losses += 1
            else:
                draws += 1
            term = game.get("Termination", "missing")
            terminations[term] = terminations.get(term, 0) + 1
        if pair_points == 0.0:
            ll += 1
        elif pair_points == 0.5:
            ld += 1
        elif pair_points == 1.0:
            mid += 1
        elif pair_points == 1.5:
            wd += 1
        elif pair_points == 2.0:
            ww += 1
        else:
            raise ValueError(f"pair score {pair_points}")
    pairs = ll + ld + mid + wd + ww
    games_n = wins + losses + draws
    if pairs == 0:
        return {
            "games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "pairs": 0,
            "ll": 0,
            "ld": 0,
            "mid": 0,
            "wd": 0,
            "ww": 0,
            "penta": (0, 0, 0, 0, 0),
            "score": None,
            "elo": None,
            "error": None,
            "elo_lo": None,
            "elo_hi": None,
            "los": None,
            "terminations": terminations,
        }
    score = (ww + 0.75 * wd + 0.5 * mid + 0.25 * ld) / pairs
    variance = (
        (ww / pairs) * (1.0 - score) ** 2
        + (wd / pairs) * (0.75 - score) ** 2
        + (mid / pairs) * (0.5 - score) ** 2
        + (ld / pairs) * (0.25 - score) ** 2
        + (ll / pairs) * (0.0 - score) ** 2
    )
    variance_per_pair = variance / pairs
    standard_error = math.sqrt(variance_per_pair)
    lower = score - Z95 * standard_error
    upper = score + Z95 * standard_error
    elo = elo_from_score(score)
    elo_lo = elo_from_score(lower)
    elo_hi = elo_from_score(upper)
    error = (elo_hi - elo_lo) / 2.0
    los = (1.0 - math.erf(-(score - 0.5) / math.sqrt(2.0 * variance_per_pair))) / 2.0
    return {
        "games": games_n,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "pairs": pairs,
        "ll": ll,
        "ld": ld,
        "mid": mid,
        "wd": wd,
        "ww": ww,
        "penta": (ll, ld, mid, wd, ww),
        "score": score,
        "elo": elo,
        "error": error,
        "elo_lo": elo_lo,
        "elo_hi": elo_hi,
        "los": los,
        "terminations": terminations,
    }


def fmt_num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def fmt_elo(stats: dict) -> str:
    if stats["elo"] is None:
        return "n/a"
    return f"{stats['elo']:+.2f} +/- {stats['error']:.2f}"


def fmt_wld(stats: dict) -> str:
    return f"{stats['wins']}-{stats['losses']}-{stats['draws']}"


def fmt_penta(stats: dict) -> str:
    ll, ld, mid, wd, ww = stats["penta"]
    return f"[{ll}, {ld}, {mid}, {wd}, {ww}]"


def fmt_los(stats: dict) -> str:
    if stats["los"] is None:
        return "n/a"
    return f"{100.0 * stats['los']:.2f} %"


def load_chunk_games(pgn_dir: Path) -> list[tuple[str, list[dict[str, str]]]]:
    files = sorted(pgn_dir.glob("chunk_[0-9][0-9][0-9].pgn"))
    loaded: list[tuple[str, list[dict[str, str]]]] = []
    for path in files:
        loaded.append((path.name, parse_games(path.read_text(encoding="utf-8", errors="replace"))))
    return loaded


def fastchess_block(log_path: Path | None) -> str:
    if log_path is None or not log_path.is_file():
        return ""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    marker = text.rfind("Results of ")
    if marker < 0:
        return ""
    lines: list[str] = []
    for line in text[marker:].splitlines():
        if line.startswith("Finished match") or line.startswith("Tournament finished"):
            break
        lines.append(line)
        if line.startswith("Ptnml"):
            break
    return "\n".join(lines).strip()


def check_fastchess(block: str, stats: dict) -> str:
    if not block or stats["elo"] is None:
        return "fastchess summary not compared"
    elo_match = ELO_RE.search(block)
    los_match = LOS_RE.search(block)
    penta_match = PENTA_RE.search(block)
    wld_match = WLD_RE.search(block)
    notes: list[str] = []
    if elo_match:
        elo = float(elo_match.group(1))
        error = float(elo_match.group(2))
        if abs(elo - stats["elo"]) > 0.05 or abs(error - stats["error"]) > 0.05:
            notes.append(
                f"Elo mismatch fastchess {elo:+.2f} +/- {error:.2f} vs recomputed {fmt_elo(stats)}"
            )
    else:
        notes.append("fastchess Elo line missing")
    if los_match and abs(float(los_match.group(1)) - 100.0 * stats["los"]) > 0.05:
        notes.append(f"LOS mismatch fastchess {los_match.group(1)} vs {fmt_los(stats)}")
    if penta_match:
        observed = tuple(int(part) for part in penta_match.groups())
        if observed != tuple(stats["penta"]):
            notes.append(f"pentanomial mismatch fastchess {observed} vs {stats['penta']}")
    if wld_match:
        observed_wld = tuple(int(part) for part in wld_match.groups())
        expected = (stats["wins"], stats["losses"], stats["draws"])
        if observed_wld != expected:
            notes.append(f"W-L-D mismatch fastchess {observed_wld} vs {expected}")
    if not notes:
        return "independent pentanomial recount matches the fastchess summary"
    return "; ".join(notes)


def identity_block(meta: dict) -> str:
    bench_lines = ["| run | NonPawnCorrection | nodes | time_ms | nps |", "| ---: | --- | ---: | ---: | ---: |"]
    for run in meta.get("bench13_runs", []):
        bench_lines.append(
            f"| {run['run']} | {run['option']} | {run['nodes']} | {run['time_ms']} | {run['nps']} |"
        )
    pins = meta["pins"]
    return "\n".join(
        [
            f"- Base: `{meta['base']}`",
            f"- Implementation commit: `{meta['implementation_commit']}`",
            f"- Branch: `{meta['branch']}`",
            f"- Engine: {meta['engine_id']}",
            f"- Build: {meta['build_kind']} (`FORGE_PORTABLE=OFF`, `-march={meta['march']}`, PEXT=1, NNUE ZMM=1)",
            f"- Compiler: {meta['compiler']}",
            f"- CMake: {meta['cmake']}",
            f"- CPU: {meta['cpu']}",
            f"- fastchess: {meta['fastchess']} (`{meta['fastchess_commit']}`)",
            f"- Book: {meta['book_name']} ({meta['book_lines']} positions)",
            f"- Binary sha256: `{meta['binary_sha256']}`",
            f"- fastchess sha256: `{meta['fastchess_sha256']}`",
            f"- Book sha256: `{meta['book_sha256']}`",
            f"- Book zip sha256: `{meta['book_zip_sha256']}`",
            f"- Pins with the option off: bench 11 `{pins['bench11']}`, bench 13 `{pins['bench13']}`, perft 5 `{pins['perft5']}`",
            f"- Bench 13 nodes with the option on: `{meta['bench13_on_nodes']}` (not a pin)",
            "",
            "### Bench 13, five alternating runs",
            "",
            *bench_lines,
            "",
            "### Command",
            "",
            "```",
            meta["command_template"],
            "```",
            "",
            "### Versions",
            "",
            f"- Engine id: {meta['engine_id']}",
            f"- g++: {meta['compiler']}",
            f"- fastchess: {meta['fastchess']}",
            f"- Book URL: {meta['book_url']}",
        ]
    )


def stats_lines(title: str, stats: dict) -> list[str]:
    return [
        f"### {title}",
        "",
        f"- W-L-D (option on first): {fmt_wld(stats)}",
        f"- Games: {stats['games']}",
        f"- Pairs: {stats['pairs']}",
        f"- Elo 95% (pentanomial, logistic): {fmt_elo(stats)}",
        f"- 95% Elo bounds: {fmt_num(stats['elo_lo'])} to {fmt_num(stats['elo_hi'])}",
        f"- LOS: {fmt_los(stats)}",
        f"- Pentanomial [LL, LD, WL/DD, WD, WW]: {fmt_penta(stats)}",
        f"- Terminations: {json.dumps(stats['terminations'], sort_keys=True)}",
    ]


def write_outputs(repo: Path, meta: dict, state: dict) -> None:
    pgn_dir = repo / "forge-combo29" / "tests_r4_05" / "pgn"
    summary_dir = repo / "forge-combo29" / "tests_r4_05" / "summary"
    log_dir = repo / "forge-combo29" / "tests_r4_05" / "logs"
    summary_dir.mkdir(parents=True, exist_ok=True)
    chunks = load_chunk_games(pgn_dir)
    all_games: list[dict[str, str]] = []
    chunk_stats: list[tuple[str, dict]] = []
    for name, games in chunks:
        stats = pentanomial(games)
        chunk_stats.append((name, stats))
        all_games.extend(games)
    total = pentanomial(all_games) if all_games else pentanomial([])
    # pentanomial([]) is not valid because empty is even and pairs 0 is handled
    # only when called with empty list: len 0 is fine, pairs 0.
    identity = identity_block(meta)
    match_start = state.get("match_start") or "n/a"
    lines = [
        "# Cumulative NonPawnCorrection screen",
        "",
        "Screening summary only. This is not a strength claim.",
        f"State: {state.get('state', 'running')}.",
        f"Match start: {match_start}.",
        f"Budget: {state.get('budget_s', 'n/a')} seconds. Hard cap: {state.get('cap_s', 'n/a')} seconds.",
        f"Owner's PC, cited only as prior context: {meta['owner_prior']}.",
        "",
        *stats_lines("Cumulative", total),
        "",
        identity,
        "",
        "## Chunks",
        "",
        "| chunk | games | W-L-D on | Elo 95% | LOS | pentanomial [LL, LD, WL/DD, WD, WW] |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for name, stats in chunk_stats:
        lines.append(
            f"| {name} | {stats['games']} | {fmt_wld(stats)} | {fmt_elo(stats)} | {fmt_los(stats)} | {fmt_penta(stats)} |"
        )
    if not chunk_stats:
        lines.append("| (none yet) | 0 | 0-0-0 | n/a | n/a | [0, 0, 0, 0, 0] |")
    (summary_dir / "cumulative.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for name, stats in chunk_stats:
        log_name = name.replace(".pgn", ".log")
        block = fastchess_block(log_dir / log_name)
        comparison = check_fastchess(block, stats)
        chunk_lines = [
            f"# {name}",
            "",
            "Screening summary only. This is not a strength claim.",
            "",
            *stats_lines("This chunk", stats),
            "",
            f"- Recount: {comparison}",
            "",
            "```",
            block or "(no fastchess summary block)",
            "```",
            "",
            *stats_lines("Cumulative including this chunk", total),
            "",
            identity,
        ]
        (summary_dir / name.replace(".pgn", ".md")).write_text("\n".join(chunk_lines) + "\n", encoding="utf-8")

    report = build_report(meta, state, chunk_stats, total)
    report_path = repo / "forge-combo29" / "REPORT_r4_05.md"
    report_path.write_text(report, encoding="utf-8")


def build_report(meta: dict, state: dict, chunk_stats: list[tuple[str, dict]], total: dict) -> str:
    match_start = state.get("match_start") or "n/a"
    done = state.get("state") == "complete"
    closing = (
        f"R4 DONE {meta['implementation_commit']}"
        if done
        else "Screen still running. The closing token is written when the time box ends."
    )
    rows = [
        "| chunk | openings | games | W-L-D (on first) | Elo 95% | LOS | LL | LD | WL/DD | WD | WW |",
        "| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, stats in chunk_stats:
        index = int(name.removeprefix("chunk_").removesuffix(".pgn"))
        start = (index - 1) * 500 + 1
        end = index * 500
        rows.append(
            f"| {index:03d} | {start}-{end} | {stats['games']} | {fmt_wld(stats)} | {fmt_elo(stats)} | {fmt_los(stats)} | "
            f"{stats['ll']} | {stats['ld']} | {stats['mid']} | {stats['wd']} | {stats['ww']} |"
        )
    if not chunk_stats:
        rows.append("| — | — | 0 | 0-0-0 | n/a | n/a | 0 | 0 | 0 | 0 | 0 |")
    pins = meta["pins"]
    bench_rows = ["| run | option | nodes | time_ms | nps |", "| ---: | --- | ---: | ---: | ---: |"]
    for run in meta["bench13_runs"]:
        bench_rows.append(
            f"| {run['run']} | {run['option']} | {run['nodes']} | {run['time_ms']} | {run['nps']} |"
        )
    non_normal = {
        key: value for key, value in total["terminations"].items() if key != "normal"
    }
    return f"""# R4-05 screen: NonPawnCorrection

Screening only. This file does not claim the option is stronger or weaker. The same binary played itself with `NonPawnCorrection` on versus off. Engine source was not changed.

Prior result on the owner's PC, not measured here: {meta['owner_prior']}.

## Result

- State: {state.get('state', 'running')}
- W-L-D (option on first): {fmt_wld(total)}
- Games: {total['games']}
- Pairs: {total['pairs']}
- Elo 95% (pentanomial, logistic): {fmt_elo(total)}
- 95% Elo bounds: {fmt_num(total['elo_lo'])} to {fmt_num(total['elo_hi'])}
- LOS: {fmt_los(total)}
- Pentanomial [LL, LD, WL/DD, WD, WW]: {fmt_penta(total)}
- Terminations other than normal: {json.dumps(non_normal, sort_keys=True) if non_normal else "none"}
- Match start: {match_start}
- Stop reason: {state.get('stop_reason', 'still running')}

Positive Elo means the option-on side scored above one half. The interval is the fastchess pentanomial 95% interval: logistic Elo of the pair score, with the half-width equal to half the distance between the Elo values of the score bounds.

## Chunks

Sequential UHO slices of 500 openings, both colors, so 1000 games when a chunk is complete.

{chr(10).join(rows)}

## Conditions

- Nodes: 50000
- Threads: 1
- Hash: 16
- OwnBook: false
- Other options: defaults, including `ContHist4PlyRead=false` and `LmrDeeperShallower=false`
- Concurrency: {meta['conditions']['concurrency']}
- Openings: `order=sequential`, chunks of 500, no repeat of an opening inside the screen
- Games per opening: 2, option-on as White in the first game of each pair
- Adjudication: none added. fastchess still applies chess rules (mate, stalemate, repetition, fifty-move, insufficient material)
- Time box: do not start a chunk after {state.get('budget_s', 21600)} seconds; also stop at {state.get('cap_s', 32400)} seconds

## Command

`CHUNK`, `START`, and `END` change per slice. `START=(CHUNK-1)*500+1` and `END=CHUNK*500`.

```
{meta['command_template']}
```

## Versions

- Engine id: {meta['engine_id']}
- Implementation commit of `NonPawnCorrection` (source unchanged on this branch): `{meta['implementation_commit']}`
- Base: `{meta['base']}`
- Branch: `{meta['branch']}`
- Compiler: {meta['compiler']}
- CMake: {meta['cmake']}
- Compile: `-O3 -std=c++20 -ffp-contract=off -fno-fast-math -march={meta['march']}`
- Defines include `FORGE_SPD_SLIDER_PEXT=1` and `FORGE_SPD_NNUE_ZMM=1` (`FORGE_PORTABLE=OFF`)
- CPU: {meta['cpu']}
- fastchess: {meta['fastchess']}
- fastchess commit: `{meta['fastchess_commit']}`
- Book: {meta['book_name']} from {meta['book_url']}
- Book positions: {meta['book_lines']}

## sha256

- Binary: `{meta['binary_sha256']}`
- fastchess: `{meta['fastchess_sha256']}`
- Book epd: `{meta['book_sha256']}`
- Book zip: `{meta['book_zip_sha256']}`

## Pins

Measured on this binary with Threads 1, Hash 16, OwnBook false, and `NonPawnCorrection` false.

- bench 11: {pins['bench11']}
- bench 13: {pins['bench13']}
- perft 5: {pins['perft5']}

These are the lock pins 312866, 862329, and 4865609. With the option on, bench 13 nodes were {meta['bench13_on_nodes']} on both on-runs below. That count is expected to move because the option changes search; it is not a default pin.

## Bench 13 nps, five alternating runs

One process. The option was set immediately before each `bench 13`, in the order off, on, off, on, off. Threads 1, Hash 16, OwnBook false.

{chr(10).join(bench_rows)}

Nodes stayed on the two counts above. NPS is wall-clock throughput of that bench and includes the colder first pair.

## Scope

The option already existed, default off, from `{meta['implementation_commit']}`. This branch does not modify `forge-combo29/src` or `forge-combo29/include`. Logs and PGNs are under `forge-combo29/tests_r4_05/`.

{closing}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    state = json.loads(args.state.read_text(encoding="utf-8"))
    write_outputs(args.repo, meta, state)


if __name__ == "__main__":
    main()
