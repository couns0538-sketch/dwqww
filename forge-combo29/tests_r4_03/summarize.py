#!/usr/bin/env python3
"""Build the LmrDeeperShallower screening report from local artifacts.

Screening only. Elo here is a sample of this run, not a strength claim.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path("/agent/repos/dwqww")
OUT = ROOT / "forge-combo29" / "tests_r4_03"
REPORT = ROOT / "forge-combo29" / "REPORT_r4_03.md"
ON_NAME = "LmrDeeperShallower"
CI95 = 1.959963984540054


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def load_kv(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in read_text(path).splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def parse_pgn_games(text: str) -> list[dict[str, str]]:
    games: list[dict[str, str]] = []
    chunks = re.split(r'(?=\[Event ")', text)
    for chunk in chunks:
        if not chunk.startswith('[Event "'):
            continue
        headers: dict[str, str] = {}
        body_lines: list[str] = []
        in_body = False
        for line in chunk.splitlines():
            if not in_body and line.startswith("[") and line.endswith("]"):
                match = re.match(r'\[([A-Za-z0-9_]+)\s+"(.*)"\]', line)
                if match:
                    headers[match.group(1)] = match.group(2)
                    continue
            if line.startswith("["):
                continue
            in_body = True
            body_lines.append(line)
        result = headers.get("Result", "")
        if result not in {"1-0", "0-1", "1/2-1/2"}:
            continue
        headers["_moves"] = " ".join(body_lines).strip()
        games.append(headers)
    return games


def game_key(headers: dict[str, str]) -> tuple[str, ...]:
    return (
        headers.get("Round", ""),
        headers.get("White", ""),
        headers.get("Black", ""),
        headers.get("FEN", ""),
        headers.get("Result", ""),
        headers.get("PlyCount", ""),
        headers.get("_moves", "")[:240],
    )


def outcome_for_on(headers: dict[str, str]) -> str | None:
    result = headers.get("Result")
    white = headers.get("White")
    black = headers.get("Black")
    if ON_NAME not in {white, black}:
        return None
    if result == "1/2-1/2":
        return "D"
    white_won = result == "1-0"
    on_is_white = white == ON_NAME
    if white_won == on_is_white:
        return "W"
    return "L"


def pair_key(headers: dict[str, str]) -> tuple[str, str]:
    # Same opening, both colors. Round is per game in fastchess, so group by FEN
    # and fall back to the opening index encoded in the round pair when FEN is absent.
    fen = headers.get("FEN", "")
    if fen:
        return ("fen", fen)
    round_no = headers.get("Round", "")
    try:
        number = int(round_no)
    except ValueError:
        number = 0
    # Games of a pair are consecutive: (1,2), (3,4), ...
    return ("round", str((max(number, 1) + 1) // 2))


def tally(games: list[dict[str, str]]) -> dict[str, int]:
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for game in games:
        key = game_key(game)
        if key in seen:
            continue
        seen.add(key)
        unique.append(game)
    wins = losses = draws = 0
    buckets: dict[tuple[str, str], list[str]] = {}
    for game in unique:
        outcome = outcome_for_on(game)
        if outcome is None:
            continue
        if outcome == "W":
            wins += 1
        elif outcome == "L":
            losses += 1
        else:
            draws += 1
        buckets.setdefault(pair_key(game), []).append(outcome)
    ll = ld = wl = dd = wd = ww = unpaired = 0
    for outcomes in buckets.values():
        if len(outcomes) < 2:
            unpaired += len(outcomes)
            continue
        # A round is two games. Extra duplicates beyond a pair are ignored.
        left, right = outcomes[0], outcomes[1]
        points = (left == "W") + (right == "W")
        draw_count = (left == "D") + (right == "D")
        loss_count = (left == "L") + (right == "L")
        if points == 2:
            ww += 1
        elif points == 1 and draw_count == 1:
            wd += 1
        elif points == 1 and loss_count == 1:
            wl += 1
        elif draw_count == 2:
            dd += 1
        elif loss_count == 1 and draw_count == 1:
            ld += 1
        elif loss_count == 2:
            ll += 1
        else:
            unpaired += 2
    return {
        "games": wins + losses + draws,
        "raw_games": len(games),
        "unique_games": len(unique),
        "W": wins,
        "L": losses,
        "D": draws,
        "LL": ll,
        "LD": ld,
        "WL": wl,
        "DD": dd,
        "WD": wd,
        "WW": ww,
        "unpaired": unpaired,
    }


def score_to_elo(score: float) -> float:
    if score <= 0.0:
        return -math.inf
    if score >= 1.0:
        return math.inf
    return -400.0 * math.log10(1.0 / score - 1.0)


def elo_block(counts: dict[str, int]) -> dict[str, float | int | str]:
    """Match fastchess EloPentanomial (logistic Elo, 95% half-width, LOS, nElo)."""
    ll = counts["LL"]
    ld = counts["LD"]
    wl = counts["WL"]
    dd = counts["DD"]
    wd = counts["WD"]
    ww = counts["WW"]
    pairs = ll + ld + wl + dd + wd + ww
    if pairs == 0:
        return {"pairs": 0, "text": "n/a (no completed pairs)"}
    ww_p = ww / pairs
    wd_p = wd / pairs
    wl_p = wl / pairs
    dd_p = dd / pairs
    ld_p = ld / pairs
    ll_p = ll / pairs
    score = ww_p + 0.75 * wd_p + 0.5 * (wl_p + dd_p) + 0.25 * ld_p
    variance = (
        ww_p * (1.0 - score) ** 2
        + wd_p * (0.75 - score) ** 2
        + (wl_p + dd_p) * (0.5 - score) ** 2
        + ld_p * (0.25 - score) ** 2
        + ll_p * (0.0 - score) ** 2
    )
    elo = score_to_elo(score)
    if variance == 0.0 or pairs == 0:
        error = 0.0
        if score > 0.5:
            los = 100.0
        elif score < 0.5:
            los = 0.0
        else:
            los = 50.0
        nelo = math.inf if score > 0.5 else (-math.inf if score < 0.5 else 0.0)
        nelo_error = math.nan
    else:
        variance_per_pair = variance / pairs
        standard_error = math.sqrt(variance_per_pair)
        upper = score + CI95 * standard_error
        lower = score - CI95 * standard_error
        error = (score_to_elo(upper) - score_to_elo(lower)) / 2.0
        argument = (score - 0.5) / math.sqrt(2.0 * variance_per_pair)
        los = (1.0 - math.erf(-argument)) / 2.0 * 100.0
        def nelo_of(value: float) -> float:
            return (value - 0.5) / math.sqrt(2.0 * variance) * (800.0 / math.log(10.0))

        nelo = nelo_of(score)
        nelo_error = (nelo_of(upper) - nelo_of(lower)) / 2.0
    penta = f"[{ll}, {ld}, {wl + dd}, {wd}, {ww}]"
    return {
        "pairs": pairs,
        "score": score,
        "elo": elo,
        "error": error,
        "los": los,
        "nelo": nelo,
        "nelo_error": nelo_error,
        "penta": penta,
        "text": (
            f"W-L-D {counts['W']}-{counts['L']}-{counts['D']}  "
            f"Elo {elo:.2f} +/- {error:.2f} (95%)  "
            f"LOS {los:.2f} %  "
            f"Ptnml(0-2) {penta}"
        ),
    }


def fmt_num(value: float | int | str) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return f"{value:.2f}"


def parse_bench(log_text: str) -> list[dict[str, str]]:
    runs: list[dict[str, str]] = []
    label = ""
    run_id = ""
    for line in log_text.splitlines():
        match = re.match(r"--- run (\d+) (on|off) ---", line.strip())
        if match:
            run_id, label = match.group(1), match.group(2)
            continue
        if label and "bench depth 13" in line:
            nodes = re.search(r"nodes (\d+)", line)
            time_ms = re.search(r"time (\d+)", line)
            nps = re.search(r"nps (\d+)", line)
            runs.append(
                {
                    "run": run_id,
                    "option": label,
                    "nodes": nodes.group(1) if nodes else "",
                    "time_ms": time_ms.group(1) if time_ms else "",
                    "nps": nps.group(1) if nps else "",
                    "line": line.strip(),
                }
            )
            label = ""
    return runs


def last_fastchess_block(log_text: str) -> str:
    marker = "Results of "
    last = log_text.rfind(marker)
    if last < 0:
        return ""
    snippet = log_text[last:]
    end = snippet.find("Finished match")
    if end == -1:
        # Keep the results paragraph only.
        lines = snippet.splitlines()
        kept: list[str] = []
        for line in lines[:12]:
            kept.append(line)
            if line.startswith("Ptnml"):
                break
        return "\n".join(kept).strip()
    return snippet[:end].strip()


def chunk_starts() -> list[int]:
    starts = [1 + 500 * i for i in range(9)]
    return starts


def collect_chunks() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for start in chunk_starts():
        pgn_path = OUT / f"chunk_{start}.pgn"
        log_path = OUT / f"chunk_{start}.log"
        if not pgn_path.exists() and not log_path.exists():
            continue
        games = parse_pgn_games(read_text(pgn_path))
        counts = tally(games)
        block = elo_block(counts)
        log_text = read_text(log_path)
        interrupted = "Tournament was interrupted" in log_text
        finished = "Finished match" in log_text and not interrupted
        # A resumed log contains an earlier interrupt and a later clean finish.
        # Treat the chunk as finished when the final stanza is a clean finish.
        tail = "\n".join(log_text.splitlines()[-25:])
        if "Finished match" in tail and "Tournament was interrupted" not in tail:
            finished = True
            interrupted = False
        elif "Tournament was interrupted" in tail:
            finished = False
            interrupted = True
        rows.append(
            {
                "start": start,
                "counts": counts,
                "elo": block,
                "fastchess": last_fastchess_block(log_text),
                "finished": finished,
                "interrupted": interrupted,
                "log_bytes": log_path.stat().st_size if log_path.exists() else 0,
                "pgn_bytes": pgn_path.stat().st_size if pgn_path.exists() else 0,
            }
        )
    return rows


def pool(rows: list[dict[str, object]]) -> tuple[dict[str, int], dict[str, float | int | str]]:
    total = {key: 0 for key in ("games", "raw_games", "unique_games", "W", "L", "D", "LL", "LD", "WL", "DD", "WD", "WW", "unpaired")}
    for row in rows:
        counts = row["counts"]
        assert isinstance(counts, dict)
        for key in total:
            total[key] += int(counts[key])
    return total, elo_block(total)


def write_chunk_summary(row: dict[str, object]) -> None:
    start = int(row["start"])
    counts = row["counts"]
    elo = row["elo"]
    assert isinstance(counts, dict)
    assert isinstance(elo, dict)
    path = OUT / f"chunk_{start}_summary.txt"
    lines = [
        f"chunk_start {start}",
        f"openings {start}-{start + 499}",
        f"finished {row['finished']}",
        f"interrupted {row['interrupted']}",
        f"games {counts['games']}",
        f"W {counts['W']}",
        f"L {counts['L']}",
        f"D {counts['D']}",
        f"LL {counts['LL']}",
        f"LD {counts['LD']}",
        f"WL {counts['WL']}",
        f"DD {counts['DD']}",
        f"WD {counts['WD']}",
        f"WW {counts['WW']}",
        f"penta {elo.get('penta', '')}",
        f"elo {fmt_num(elo.get('elo', 'n/a'))}",
        f"elo95 {fmt_num(elo.get('error', 'n/a'))}",
        f"los {fmt_num(elo.get('los', 'n/a'))}",
        f"nelo {fmt_num(elo.get('nelo', 'n/a'))}",
        f"nelo95 {fmt_num(elo.get('nelo_error', 'n/a'))}",
        f"pairs {elo.get('pairs', 0)}",
        f"unpaired_games {counts['unpaired']}",
        "",
        "fastchess_last_block:",
        str(row.get("fastchess") or "(none yet)"),
        "",
    ]
    path.write_text("\n".join(lines))


def build_report() -> str:
    meta = load_kv(OUT / "hashes.txt")
    status = {}
    status_path = OUT / "status.json"
    if status_path.exists():
        status = json.loads(status_path.read_text())
    bench = parse_bench(read_text(OUT / "bench13_alternating.log"))
    rows = collect_chunks()
    for row in rows:
        write_chunk_summary(row)
    total, pooled = pool(rows)
    command = read_text(OUT / "command.txt").strip()
    state = str(status.get("state", "unknown"))
    lines: list[str] = []
    lines.append("# R4-03 screen: LmrDeeperShallower")
    lines.append("")
    lines.append("Screening only. This is not a strength claim.")
    lines.append("")
    lines.append(
        "The owner's earlier stop was +2 ± 13 in 1200 games. "
        "That stop is prior context. This run is a new on-versus-off sample of the existing default-off option and does not by itself establish a strength change."
    )
    lines.append("")
    lines.append(f"State: `{state}`.")
    if status.get("started_utc"):
        lines.append(f"Screen start (UTC): {status['started_utc']}.")
    if status.get("deadline_utc"):
        lines.append(f"Screen deadline (UTC): {status['deadline_utc']} (6 hours from screen start, or 9 chunks, whichever comes first).")
    if status.get("stopped_utc"):
        lines.append(f"Screen stop (UTC): {status['stopped_utc']}.")
    if status.get("note"):
        lines.append(f"Note: {status['note']}")
    lines.append("")
    lines.append("## What was compared")
    lines.append("")
    lines.append("Same binary. Engine 1 is `LmrDeeperShallower` with `option.LmrDeeperShallower=true`. Engine 2 is `default` with `option.LmrDeeperShallower=false`. No engine source was changed. W-L-D is from the option-on engine.")
    lines.append("")
    lines.append("## Build")
    lines.append("")
    lines.append(f"- Source commit: `{meta.get('source_commit', '')}`")
    lines.append(f"- Implementation commit of `LmrDeeperShallower`: `{meta.get('implementation_commit', '')}`")
    lines.append(f"- CPU: {meta.get('cpu', '')}")
    lines.append(f"- AVX-512F present: {meta.get('avx512f', '')}. BMI2 present: {meta.get('bmi2', '')}.")
    lines.append(f"- Effective CPUs (`nproc`): {meta.get('cpus', '')}. Concurrency: {meta.get('concurrency', '')} (effective CPUs minus 1).")
    lines.append("- Owner build (AVX-512F and BMI2 are present), not the portable build.")
    lines.append(f"- Compiler: {meta.get('compiler', '')}")
    lines.append(f"- CMake: `cmake -S forge-combo29 -B /tmp/forge-r4-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++` then `cmake --build /tmp/forge-r4-build -j4`.")
    lines.append(f"- `FORGE_PORTABLE` left OFF. `FORGE_MARCH={meta.get('march', 'x86-64-v4')}`. `FORGE_SPD_SLIDER_PEXT=1`. `FORGE_SPD_NNUE_ZMM=1`.")
    lines.append(f"- Compile flags: `{meta.get('cxx_flags', '')}`")
    lines.append(f"- Binary: `/tmp/forge-r4-build/forge`")
    lines.append(f"- Binary sha256: `{meta.get('binary_sha256', '')}`")
    lines.append(f"- Book: `/tmp/r4tools/UHO_Lichess_4852_v1.epd` ({meta.get('book_lines', '')} lines)")
    lines.append(f"- Book sha256: `{meta.get('book_sha256', '')}`")
    lines.append(f"- Book zip sha256: `{meta.get('book_zip_sha256', '')}` (official-stockfish/books `UHO_Lichess_4852_v1.epd.zip`)")
    lines.append("")
    lines.append("### Pins, option off")
    lines.append("")
    lines.append("These stayed at the required counts with `LmrDeeperShallower` false, including a repeat after turning the option on and then off:")
    lines.append("")
    lines.append("| check | nodes |")
    lines.append("| --- | ---: |")
    lines.append("| bench 11 | 312866 |")
    lines.append("| bench 13 | 862329 |")
    lines.append("| go perft 5 (startpos) | 4865609 |")
    lines.append("")
    lines.append("With the option on, bench 11 was 336538 nodes and bench 13 was 813907 nodes. That difference is the search change under test. The pins above are the option-off counts.")
    lines.append("")
    lines.append("## Bench 13 nps, five alternating runs")
    lines.append("")
    lines.append("Order is off, on, off, on, off. One process, no match running. nps is `nodes * 1000 / time_ms` from the engine line.")
    lines.append("")
    lines.append("| run | option | nodes | time_ms | nps |")
    lines.append("| ---: | --- | ---: | ---: | ---: |")
    for run in bench:
        lines.append(
            f"| {run['run']} | {run['option']} | {run['nodes']} | {run['time_ms']} | {run['nps']} |"
        )
    if not bench:
        lines.append("| | | | | |")
    lines.append("")
    lines.append("Raw lines are in `forge-combo29/tests_r4_03/bench13_alternating.log`.")
    lines.append("")
    lines.append("## Match command")
    lines.append("")
    lines.append(f"- fastchess version: `{meta.get('fastchess_version', '')}`")
    lines.append(f"- fastchess commit: `{meta.get('fastchess_commit', '')}`")
    lines.append(f"- fastchess binary sha256: `{meta.get('fastchess_sha256', '')}`")
    lines.append("- Book order: sequential. Games per opening: 2. Rounds per chunk: 500. Recover: on.")
    lines.append("- Each: `proto=uci nodes=50000 option.Threads=1 option.Hash=16 option.OwnBook=false`.")
    lines.append("- Chunks: `S = 1, 501, 1001, 1501, 2001, 2501, 3001, 3501, 4001` (9), stopped early if the 6 hour deadline is reached.")
    lines.append("")
    lines.append("Full command (`S` is the chunk start):")
    lines.append("")
    lines.append("```")
    lines.append(command or "(command.txt not written yet)")
    lines.append("```")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("W-L-D is option on first. Elo is logistic Elo from the pentanomial model used by this fastchess build (`EloPentanomial`), and the ± value is the 95% half-width. LOS is that model's likelihood of superiority for the option-on side. `Ptnml(0-2)` is `[LL, LD, WL+DD, WD, WW]`.")
    lines.append("")
    if not rows:
        lines.append("No chunk PGN yet.")
    else:
        lines.append("| chunk S | games | W-L-D | Elo 95% | LOS % | Ptnml(0-2) | pairs | state |")
        lines.append("| ---: | ---: | --- | --- | ---: | --- | ---: | --- |")
        for row in rows:
            counts = row["counts"]
            elo = row["elo"]
            assert isinstance(counts, dict)
            assert isinstance(elo, dict)
            state_cell = "finished" if row["finished"] else ("stopped" if row["interrupted"] else "running")
            lines.append(
                "| {start} | {games} | {w}-{l}-{d} | {elo} +/- {err} | {los} | {penta} | {pairs} | {state} |".format(
                    start=row["start"],
                    games=counts["games"],
                    w=counts["W"],
                    l=counts["L"],
                    d=counts["D"],
                    elo=fmt_num(elo.get("elo", "n/a")),
                    err=fmt_num(elo.get("error", "n/a")),
                    los=fmt_num(elo.get("los", "n/a")),
                    penta=elo.get("penta", ""),
                    pairs=elo.get("pairs", 0),
                    state=state_cell,
                )
            )
        lines.append("")
        lines.append(
            "Pooled (all chunks, option on first): "
            f"W-L-D {total['W']}-{total['L']}-{total['D']} over {total['games']} games, "
            f"{pooled.get('pairs', 0)} pairs, "
            f"Elo {fmt_num(pooled.get('elo', 'n/a'))} +/- {fmt_num(pooled.get('error', 'n/a'))} (95%), "
            f"LOS {fmt_num(pooled.get('los', 'n/a'))} %, "
            f"Ptnml(0-2) {pooled.get('penta', '')}."
        )
        lines.append("")
        lines.append(
            f"Split of the pooled middle bin: WL {total['WL']}, DD {total['DD']}. "
            f"Raw pair counts LL {total['LL']}, LD {total['LD']}, WL {total['WL']}, DD {total['DD']}, WD {total['WD']}, WW {total['WW']}. "
            f"Unpaired finished games (excluded from the pentanomial, included in W-L-D): {total['unpaired']}."
        )
        lines.append("")
        lines.append(f"nElo (fastchess pentanomial normalization): {fmt_num(pooled.get('nelo', 'n/a'))} +/- {fmt_num(pooled.get('nelo_error', 'n/a'))}.")
    lines.append("")
    lines.append("### fastchess blocks")
    lines.append("")
    if not rows:
        lines.append("None yet.")
    for row in rows:
        lines.append(f"#### chunk {row['start']}")
        lines.append("")
        block = str(row.get("fastchess") or "").strip()
        if block:
            lines.append("```")
            lines.append(block)
            lines.append("```")
        else:
            lines.append("No fastchess results block in the log yet.")
        lines.append("")
    lines.append("## Reading the sample")
    lines.append("")
    lines.append("A 95% interval that covers zero is a sample consistent with no Elo difference at this time control and book slice. An interval that does not cover zero is still one screen, not a strength claim. The earlier owner stop (+2 ± 13 in 1200 games) remains the prior stop named for this option.")
    lines.append("")
    lines.append("Logs, PGNs, and per-chunk summaries: `forge-combo29/tests_r4_03/`.")
    lines.append("")
    return "\n".join(lines)


def self_test(pgn_path: str) -> int:
    games = parse_pgn_games(Path(pgn_path).read_text(errors="replace"))
    counts = tally(games)
    block = elo_block(counts)
    print(json.dumps({"counts": counts, "elo": {k: fmt_num(v) if isinstance(v, float) else v for k, v in block.items()}}, indent=2))
    return 0


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--self-test":
        return self_test(sys.argv[2])
    OUT.mkdir(parents=True, exist_ok=True)
    report = build_report()
    REPORT.write_text(report)
    summary_path = OUT / "SUMMARY.txt"
    # Short pointer updated with the pooled line for the heartbeat commit.
    rows = collect_chunks()
    total, pooled = pool(rows)
    summary_path.write_text(
        "\n".join(
            [
                "LmrDeeperShallower screen (option on first). Not a strength claim.",
                f"games {total['games']} W {total['W']} L {total['L']} D {total['D']}",
                f"pairs {pooled.get('pairs', 0)}",
                f"elo {fmt_num(pooled.get('elo', 'n/a'))} +/- {fmt_num(pooled.get('error', 'n/a'))}",
                f"los {fmt_num(pooled.get('los', 'n/a'))}",
                f"penta {pooled.get('penta', '')}",
                f"chunks {','.join(str(row['start']) for row in rows)}",
                "",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
