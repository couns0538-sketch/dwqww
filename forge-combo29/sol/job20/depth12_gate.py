#!/usr/bin/env python3
"""Replay Job 20's two PCA depth-12 gates and preserve the first difference."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


here = Path(__file__).resolve().parent
for previous in ("job2", "sol-job2"):
    if (here.parent / previous / "run_matrix.py").is_file():
        sys.path.insert(0, str(here.parent / previous))
        break
else:
    raise SystemExit("Job 2 run_matrix.py is missing from the adjacent job2 or sol-job2 directory")

from run_matrix import Engine, PC20, Refused, parse_row, utc_now


FIXTURE_SHA256 = "ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8"
KIMI_REVISION = "5db05e09"
KIMI_ROOT = "forge-combo29/tests_kimi5_job25/rows"
KIMI_SHA256 = {
    "base": "da25830b2b3473ad77e07ed038bee0dd3dcbf4a083b923b4e66a5d8eb164189b",
    "fhb7": "3d926748123bbf88abd4e78883613ef08573edc8efafd9c973d24ff7258bc70d",
}
EXPECTED = {
    "base": (8315168, [21812, 26844, 35173]),
    "fhb7": (7913480, [18623, 19820, 32078]),
}


def load_positions(path):
    raw = path.read_bytes()
    digest = sha256(raw).hexdigest()
    if digest != FIXTURE_SHA256:
        raise ValueError(f"{path}: fixture SHA-256 {digest}, expected {FIXTURE_SHA256}")
    lines = raw.decode("utf-8").splitlines()
    if len(lines) != 200:
        raise ValueError(f"{path}: expected 200 positions, found {len(lines)}")
    positions = []
    for index, line in enumerate(lines, 1):
        fields = line.split()
        if len(fields) < 4:
            raise ValueError(f"{path}:{index}: missing FEN fields")
        positions.append((line, " ".join([*fields[:4], "0", "1"])))
    return positions


def load_expected(path, arm):
    raw = path.read_bytes()
    digest = sha256(raw).hexdigest()
    if digest != KIMI_SHA256[arm]:
        raise ValueError(f"{path}: Kimi5 row SHA-256 {digest}, expected {KIMI_SHA256[arm]}")
    reference = json.loads(raw)
    counts = reference["per_position"]
    moves = reference["bestmove"]
    if (len(counts), len(moves), sum(counts), counts[:3]) != (200, 200, *EXPECTED[arm]):
        raise ValueError(f"{path}: invalid Kimi5 baseline rows")
    return reference


def first_difference(rows, reference):
    for row, nodes, bestmove in zip(rows, reference["per_position"], reference["bestmove"]):
        if (row["nodes"], row["bestmove"]) != (nodes, bestmove):
            return {
                "index": row["index"],
                "pca": row,
                "kimi5": {
                    "fen": row["original_fen"],
                    "nodes": nodes,
                    "bestmove": bestmove,
                    "exe_sha256": reference["exe_sha256"],
                    "id_name": reference["id_name"],
                },
            }
    return None


def run_arm(executable, fixture, output_dir, positions, arm, reference, timeout):
    settings = [
        f"setoption name {name} value {value}"
        for name, value in (
            *PC20, ("Threads", "1"), ("Hash", "16"),
            ("FailHighBlend", "7" if arm == "fhb7" else "0"),
        )
    ]
    search = "go depth 12"
    meta = {
        "command": sys.argv,
        "arm": arm,
        "exe": str(executable),
        "exe_sha256": sha256(executable.read_bytes()).hexdigest(),
        "id_name": None,
        "positions": str(fixture),
        "positions_sha256": FIXTURE_SHA256,
        "positions_requested": len(positions),
        "settings_sent": [],
        "settings_reply": [],
        "external_net_file": None,
        "search": search,
        "setup_per_search": ["ucinewgame", "isready", "position fen <first four fixture fields> 0 1"],
        "reference_revision": KIMI_REVISION,
        "reference_path": f"{KIMI_ROOT}/{arm}_O_d12.json",
        "reference_sha256": KIMI_SHA256[arm],
        "start_utc": utc_now(),
        "status": "incomplete",
    }
    rows = []
    rows_path = output_dir / f"{arm}.jsonl"
    metadata_path = output_dir / f"{arm}.jsonl.meta"
    with rows_path.open("x", encoding="utf-8") as stream, metadata_path.open("x", encoding="utf-8") as metadata:
        try:
            with Engine(executable, timeout) as engine:
                engine.send("uci")
                meta["id_name"] = next(
                    (line for line in engine.until("uciok") if line.startswith("id name ")), None,
                )
                if not meta["id_name"]:
                    raise RuntimeError("missing engine id name")
                for setting in settings:
                    engine.send(setting)
                    meta["settings_sent"].append(setting)
                engine.send("isready")
                meta["settings_reply"] = engine.until("readyok")
                for index, (original_fen, fen) in enumerate(positions, 1):
                    engine.send("ucinewgame")
                    engine.send("isready")
                    engine.until("readyok")
                    engine.send(f"position fen {fen}")
                    engine.send(search)
                    row = parse_row(index, fen, engine.until("bestmove"), require_counter=False)
                    row["original_fen"] = original_fen
                    stream.write(json.dumps(row, separators=(",", ":")) + "\n")
                    stream.flush()
                    rows.append(row)
            meta["status"] = "complete"
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            meta["status"] = "refused" if isinstance(error, Refused) else "incomplete"
            meta["error"] = str(error) or type(error).__name__
        finally:
            counts = [row["nodes"] for row in rows]
            meta["end_utc"] = utc_now()
            meta["positions_completed"] = len(rows)
            meta["nodes_sum"] = sum(counts)
            meta["nodes_first3"] = counts[:3]
            json.dump(meta, metadata, indent=2)
            metadata.write("\n")
    return meta, first_difference(rows, reference)


def run(args):
    executable = args.engine.resolve(strict=True)
    fixture = args.positions.resolve(strict=True)
    positions = load_positions(fixture)
    references = {"base": load_expected(args.expected_base, "base"),
                  "fhb7": load_expected(args.expected_fhb7, "fhb7")}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = args.output_dir / "depth12-summary.txt"
    with summary.open("x", encoding="utf-8") as receipt:
        def log(line):
            print(line)
            print(line, file=receipt, flush=True)

        log(f"Fixture {fixture}, SHA-256 {FIXTURE_SHA256}, {len(positions)} positions.")
        log("PCA used normalized FEN counters 0 1. Kimi5's saved rows used the source lines verbatim.")
        for arm in EXPECTED:
            meta, difference = run_arm(
                executable, fixture, args.output_dir, positions, arm, references[arm], args.timeout,
            )
            want_sum, want_first3 = EXPECTED[arm]
            status = meta["status"]
            log(f"{arm}: {status}, {meta['positions_completed']}/{len(positions)} rows; "
                f"observed sum {meta['nodes_sum']} and first three {meta['nodes_first3']}, "
                f"expected sum {want_sum} and first three {want_first3}.")
            if difference:
                path = args.output_dir / f"{arm}.first-difference.json"
                with path.open("x", encoding="utf-8") as stream:
                    json.dump(difference, stream, indent=2)
                    stream.write("\n")
                log(f"First differing position {difference['index']}; both rows are in {path.name}.")
                log(json.dumps(difference, ensure_ascii=False))
            if status != "complete":
                log(f"STOP: {arm} {status}: {meta.get('error', '')}")
                return 1
            if (meta["nodes_sum"], meta["nodes_first3"]) != (want_sum, want_first3):
                log(f"STOP: {arm} failed the prescribed node counts.")
                return 1
            if difference:
                log(f"STOP: {arm} differs from the saved Kimi5 per-position rows.")
                return 1
            log(f"PASS: {arm} matches the prescribed counts and all {len(positions)} nodes/bestmove rows.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("positions", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--expected-base", type=Path, default=here / "kimi-source/base_O_d12.json")
    parser.add_argument("--expected-fhb7", type=Path, default=here / "kimi-source/fhb7_O_d12.json")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        return run(args)
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
