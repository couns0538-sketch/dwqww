#!/usr/bin/env python3
"""Frozen Forge 6.4 TT-tag SPRT, advanced by one natural 100-pair tranche.

Prepare: python3 tools/match/run_hourly_sprt.py --prepare-only
Run/continue: python3 tools/match/run_hourly_sprt.py
Never interrupt a tranche to manufacture a resumable checkpoint. Native fastchess
owns the SPRT decision; this driver independently checks bookkeeping, not Elo.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from pgn_stats import RESULTS, games

RUN = Path("validation/hourly/2026-10-19-initial")
BINS = ("WW", "WD", "WL", "DD", "LD", "LL")
OPTIONS = {"Hash": "64", "Threads": "1", "OwnBook": "false",
           "Ponder": "false", "UseNNUE": "true", "Move Overhead": "10"}
INPUTS = {
    "baseline": (str(RUN / "bin/forge64-baseline-linux"),
                 "aa51d6b62ab8a1ff8f5bfb348d074c981ccf5166eea094bcb9f9259df3ba7aa4"),
    "candidate": (str(RUN / "bin/forge64-tt-tag-linux"),
                  "ac97db014a1b19a37c633d58f6514d0aa0ccc38d8d8fb3bf8ae355144a2e45ad"),
    "runner": (str(RUN / "bin/fastchess-linux"),
               "b0e113170f9feedf6e1ab63c679ddd9fcc47edcc18c133d18881b381c89a3bf5")}
SPRT = {"elo0": 0, "elo1": 5, "alpha": .05, "beta": .05,
        "model": "logistic", "enabled": True}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_new(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(value, out, indent=2, sort_keys=True)
        out.write("\n")


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def prepare(repo, out):
    protocol_path = out / "protocol.json"
    if not protocol_path.exists():
        require(not out.exists() or not any(out.iterdir()),
                "Refusing to prepare over an existing nonempty experiment")
        out.mkdir(parents=True, exist_ok=True)
        for name, (path, sha) in INPUTS.items():
            require(digest(repo / path) == sha, f"Wrong frozen {name} binary")
        source = repo / "tools/openings/forge-10000.epd"
        fens = [" ".join(line.split()[:4]) for line in source.read_text().splitlines()
                if line.strip()]
        require(len(fens) == len(set(fens)) == 10000, "Expected 10,000 unique openings")
        fens.sort(key=lambda fen: hashlib.sha256(f"20261019\n{fen}".encode("ascii")).digest())
        selected = out / "selected.epd"
        with selected.open("x", encoding="ascii") as target:
            target.write("\n".join(fens) + "\n")
        protocol = {
            "schema": 1, "created_utc": utc(), "original_repo": str(repo),
            "original_out": str(out), "baseline_commit":
            "24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b",
            "experiment": "Forge 6.4 independent TT verification bits",
            "inputs": {name: {"relative_path": path, "sha256": sha}
                       for name, (path, sha) in INPUTS.items()},
            "opening_source": {"relative_path": str(source.relative_to(repo)),
                               "sha256": digest(source)},
            "selected_sha256": digest(selected), "selected_count": 10000,
            "opening_order": "SHA256(ASCII(seed + newline + first four FEN fields)); sequential",
            "seed": 20261019, "sprt": SPRT, "tc": "10+0.1",
            "options": OPTIONS, "external_book": None, "external_network": None,
            "nodes": 0, "depth": 0, "adjudication": "disabled",
            "concurrency": 6, "affinity_cpus": list(range(6)), "games_per_pair": 2,
            "max_pairs": 10000, "tranche_pairs": 100,
            "driver_sha256": digest(Path(__file__)),
            "pgn_checker_sha256": digest(Path(__file__).with_name("pgn_stats.py")),
            "resume_policy": "Only verified natural complete prefixes; never resume terminal or interrupted runs",
            "limitations": "Cloud CPU allocation is not dedicated hardware; this opening suite does not establish an absolute Elo rating."
        }
        save_new(protocol_path, protocol)
        (out / "protocol.sha256").write_text(digest(protocol_path) + "\n")
    require(digest(protocol_path) == (out / "protocol.sha256").read_text().strip(),
            "Frozen protocol was modified")
    protocol = json.loads(protocol_path.read_text())
    verify_inputs(repo, out, protocol)
    return protocol


def verify_inputs(repo, out, protocol):
    require(protocol["sprt"] == SPRT and protocol["options"] == OPTIONS,
            "Unexpected frozen protocol")
    require(protocol["inputs"] == {name: {"relative_path": path, "sha256": sha}
                                   for name, (path, sha) in INPUTS.items()},
            "Unexpected frozen binary identity")
    for name, spec in protocol["inputs"].items():
        require(digest(repo / spec["relative_path"]) == spec["sha256"],
                f"Frozen input changed: {name}")
    spec = protocol["opening_source"]
    require(digest(repo / spec["relative_path"]) == spec["sha256"], "Source openings changed")
    require(digest(out / "selected.epd") == protocol["selected_sha256"], "Selected openings changed")
    require(digest(Path(__file__)) == protocol["driver_sha256"], "Driver changed after preparation")
    require(digest(Path(__file__).with_name("pgn_stats.py")) == protocol["pgn_checker_sha256"],
            "PGN checker changed after preparation")


def check_config(cfg, protocol, roots, outs):
    """Check the exact match inputs before allowing a path-only continuation."""
    expected = {"seed": 20261019, "games": 2, "concurrency": 6,
                "report_penta": True, "noswap": False, "reverse": False,
                "variant": 0, "type": 0, "recover": False, "affinity": True}
    for key, value in expected.items():
        require(cfg.get(key) == value, f"Checkpoint setting changed: {key}")
    require(cfg["sprt"] == SPRT, "SPRT settings changed")
    for key in ("resign", "draw", "maxmoves", "tb_adjudication"):
        require(cfg[key]["enabled"] is False, f"Unexpected adjudication: {key}")
    opening = cfg["opening"]
    require({key: opening[key] for key in ("format", "order", "plies", "start")}
            == {"format": 0, "order": 1, "plies": -1, "start": 1}, "Opening policy changed")
    require(opening["file"] in {str(x / "selected.epd") for x in outs}, "Unexpected opening path")
    require(cfg["pgn"]["file"] in {str(x / "games.pgn") for x in outs}, "Unexpected PGN path")
    require(len(cfg["engines"]) == 2, "Unexpected engine count")
    for engine, name, kind in zip(cfg["engines"], ("Candidate", "Baseline"), ("candidate", "baseline")):
        require(engine["name"] == name and engine["args"] == "" and engine["dir"] == ""
                and engine["restart"] is True and engine["variant"] == 0, "Engine identity changed")
        require(engine["cmd"] in {str(root / INPUTS[kind][0]) for root in roots},
                f"Unexpected {name} path")
        require(len(engine["options"]) == len(OPTIONS) and dict(engine["options"]) == OPTIONS,
                f"{name} options changed")
        require(engine["limit"] == {"nodes": 0, "plies": 0, "tc": {
            "increment": 100, "fixed_time": 0, "time": 10000, "moves": 0, "timemargin": 0}},
                f"{name} time or search limits changed")


def verify_outcomes(pgn, cfg, selected, cap, terminal):
    parsed = games(pgn.read_text())
    groups = collections.defaultdict(list)
    positions = selected.read_text().splitlines()
    normalized_ep_rounds = set()
    for tags, moves in parsed:
        require({tags.get("White"), tags.get("Black")} == {"Candidate", "Baseline"},
                "Unexpected PGN players")
        require(tags.get("Termination") == "normal", f"Non-normal game: {tags}")
        rnd = int(tags["Round"])
        require(1 <= rnd <= cap, "Round outside cumulative tranche")
        actual = tags["FEN"].split()[:4]
        expected = positions[rnd - 1].split()
        # The pinned runner removes uncapturable EP targets when writing FENs.
        # Check this allowed serialization normalization, not literal FEN bytes.
        # This is bookkeeping, not a separate chess-legality implementation.
        require(actual[:3] == expected[:3] and
                (actual[3] == expected[3] or actual[3] == "-"),
                f"Opening sequence mismatch in round {rnd}")
        if actual[3] != expected[3]:
            normalized_ep_rounds.add(rnd)
        score = RESULTS[tags["Result"]]
        if tags["Black"] == "Candidate":
            score = 2 - score
        groups[rnd].append((tags, moves, score))
    counts = dict.fromkeys(BINS, 0)
    wdl = [0, 0, 0]  # wins, draws, losses for complete pairs only
    orphans = []
    complete = []
    pair_bin = {(2, 2): "WW", (1, 2): "WD", (0, 2): "WL",
                (1, 1): "DD", (0, 1): "LD", (0, 0): "LL"}
    for rnd, pair in sorted(groups.items()):
        require(len(pair) <= 2, f"Duplicated round {rnd}")
        if len(pair) == 1:
            require(terminal, f"Incomplete natural round {rnd}")
            orphans.append({"round": rnd, "tags": pair[0][0]})
            continue
        a, b = pair
        require(a[0]["White"] == b[0]["Black"] and a[0]["Black"] == b[0]["White"]
                and a[0]["FEN"] == b[0]["FEN"], f"Color/FEN pairing failure {rnd}")
        counts[pair_bin[tuple(sorted((a[2], b[2])))]] += 1
        wdl[2 - a[2]] += 1
        wdl[2 - b[2]] += 1
        complete.append(rnd)
    native = cfg["stats"]
    require(set(native) == {"Candidate vs Baseline"}, "Unexpected native scoreboard")
    native = native["Candidate vs Baseline"]
    require(wdl == [native["wins"], native["draws"], native["losses"]],
            "Native WDL disagrees with complete PGN pairs")
    require(all(native["penta_" + key] == value for key, value in counts.items()),
            "Native six-bin pentanomial disagrees with PGN")
    require(sum(wdl) == 2 * sum(counts.values()), "Native pair totals inconsistent")
    if not terminal:
        require(complete == list(range(1, cap + 1)) and len(parsed) == 2 * cap,
                "Natural checkpoint is not a complete round prefix")
    return {"complete_pairs": len(complete), "all_pgn_games": len(parsed),
            "candidate_wins_draws_losses_complete_pairs": wdl, "penta6": counts,
            "complete_rounds": complete, "orphan_games": orphans,
            "ep_normalized_rounds": sorted(normalized_ep_rounds),
            "terminations": {"normal": len(parsed)}, "elo_claim": None}


def initial_command(repo, out, cap, checkpoint, trace):
    command = [str(repo / INPUTS["runner"][0]), "-config", f"outname={checkpoint}"]
    for name, kind in (("Candidate", "candidate"), ("Baseline", "baseline")):
        command += ["-engine", f"cmd={repo / INPUTS[kind][0]}", f"name={name}"]
    command += ["-each", "proto=uci", "tc=10+0.1", "restart=on"]
    command += [f"option.{name}={value}" for name, value in OPTIONS.items()]
    command += ["-openings", f"file={out / 'selected.epd'}", "format=epd", "order=sequential",
                "-srand", "20261019", "-games", "2", "-rounds", str(cap), "-concurrency", "6",
                "-sprt", "elo0=0", "elo1=5", "alpha=0.05", "beta=0.05", "model=logistic",
                "-report", "penta=true", "-ratinginterval", "2", "-pgnout",
                f"file={out / 'games.pgn'}", "notation=uci", "nodes=true", "nps=true",
                "timeleft=true", "append=false"]
    return command + runtime_options(trace)


def runtime_options(trace):
    # Affinity CPU IDs and strictness are omitted from native JSON serialization.
    return ["-use-affinity", "0,1,2,3,4,5", "-log", f"file={trace}",
            "level=trace", "engine=true", "append=false", "-autosaveinterval", "2", "-strict"]



def native_sprt_status(text):
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    decisions = re.findall(r"SPRT[^\n]*completed - (H[01]) was accepted", text)
    require(len(set(decisions)) <= 1, "Conflicting native SPRT decisions")
    llrs = re.findall(r"LLR:\s*(\S+)", text)
    require(llrs and math.isfinite(float(llrs[-1])), "Missing finite final native LLR output")
    return decisions[-1] if decisions else None, float(llrs[-1])


def run_tranche(repo, out, protocol):
    require(hasattr(os, "sched_getaffinity") and set(range(6)) <= os.sched_getaffinity(0),
            "Frozen cloud affinity CPUs 0..5 are unavailable; do not silently alter resources")
    history = sorted(out.glob("tranche-*-result.json"))
    attempts = sorted(out.glob("tranche-*-command.json"))
    require(len(history) == len(attempts), "Unfinished/interrupted attempt: manual recovery required")
    roots = {repo, Path(protocol["original_repo"])}
    outs = {out, Path(protocol["original_out"])}
    cap = 100
    previous = None
    if history:
        previous = json.loads(history[-1].read_text())
        require(previous["status"] == "natural_complete_inconclusive", "Prior test is terminal or failed")
        cap = previous["cumulative_pair_cap"] + 100
        require(cap <= 10000, "Predeclared 10,000-pair cap reached; no automatic extension")
        roots.add(Path(previous["repo"]))
        outs.add(Path(previous["out"]))
        for filename, sha in previous["outputs"].items():
            require(digest(out / filename) == sha, f"Prior evidence changed: {filename}")
    suffix = f"{cap:05d}"
    prefix = out / f"tranche-{suffix}"
    checkpoint = out / f"checkpoint-{suffix}.json"
    trace = out / f"tranche-{suffix}-engine.log"
    console = out / f"tranche-{suffix}-runner.log"
    require(not any(out.glob(f"*{suffix}*")), "Tranche filenames already exist; refusing overwrite")
    lock = out / "active.lock"
    with lock.open("x") as handle:
        handle.write(f"pid={os.getpid()} utc={utc()}\n")
    result = {"started_utc": utc(), "cumulative_pair_cap": cap,
              "repo": str(repo), "out": str(out), "status": "failed_no_resume",
              "protocol_sha256": digest(out / "protocol.json"), "elo_claim": None}
    try:
        if previous:
            cfg = json.loads((out / previous["checkpoint"]).read_text())
            check_config(cfg, protocol, roots, outs)
            require(cfg["rounds"] == cap - 100, "Prior cumulative round cap changed")
            verify_outcomes(out / "games.pgn", cfg, out / "selected.epd", cap - 100, False)
            # Keep the original checkpoint immutable. Rebase only verified path identities.
            rebased = copy.deepcopy(cfg)
            for engine, kind in zip(rebased["engines"], ("candidate", "baseline")):
                engine["cmd"] = str(repo / INPUTS[kind][0])
            rebased["opening"]["file"] = str(out / "selected.epd")
            rebased["pgn"]["file"] = str(out / "games.pgn")
            rebased["log"]["file"] = str(trace)
            rebased["config_name"] = str(checkpoint)
            resume_input = out / f"resume-input-{suffix}.json"
            save_new(resume_input, rebased)
            command = [str(repo / INPUTS["runner"][0]), "-config", f"file={resume_input}",
                       "stats=true", f"outname={checkpoint}", "-rounds", str(cap)]
            command += runtime_options(trace)
        else:
            require(not (out / "games.pgn").exists(), "Unexpected PGN before initial tranche")
            command = initial_command(repo, out, cap, checkpoint, trace)
        save_new(str(prefix) + "-command.json", {"argv": command, "cwd": str(out),
                 "started_utc": result["started_utc"], "protocol_sha256": result["protocol_sha256"]})
        started = time.monotonic()
        with console.open("x") as log:
            proc = subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT,
                                  env={**os.environ, "NO_COLOR": "1"}, check=False)
        result["exit_code"] = proc.returncode
        result["elapsed_seconds"] = time.monotonic() - started
        require(proc.returncode == 0, f"fastchess exited {proc.returncode}; no automatic resume")
        verify_inputs(repo, out, protocol)
        terminal, final_llr = native_sprt_status(console.read_text())
        result["native_sprt_decision"] = terminal
        result["native_final_llr"] = final_llr
        cfg = json.loads(checkpoint.read_text())
        check_config(cfg, protocol, roots, outs)
        require(cfg["rounds"] == cap, "Unexpected cumulative round cap")
        result["statistics"] = verify_outcomes(out / "games.pgn", cfg, out / "selected.epd", cap, terminal)
        snapshot = out / f"games-through-{suffix}.pgn.gz"
        with (out / "games.pgn").open("rb") as source, snapshot.open("xb") as target:
            with gzip.GzipFile(filename="games.pgn", mode="wb", fileobj=target, mtime=0) as zipped:
                shutil.copyfileobj(source, zipped)
        result["status"] = (f"{terminal}_accepted_terminal" if terminal else
                            "inconclusive_at_total_cap" if cap == 10000 else "natural_complete_inconclusive")
        result["checkpoint"] = checkpoint.name
        result["outputs"] = {path.name: digest(path) for path in
                             (out / "games.pgn", checkpoint, trace, console, snapshot)}
    except BaseException as error:
        result["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        result["finished_utc"] = utc()
        save_new(str(prefix) + "-result.json", result)
        lock.unlink()
        print(json.dumps(result, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, help="Default: initial validation run/matches/tt-tag-sprt")
    parser.add_argument("--prepare-only", action="store_true", help="Freeze/verify protocol without starting games")
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    out = args.out.resolve() if args.out else repo / RUN / "matches/tt-tag-sprt"
    protocol = prepare(repo, out)
    if args.prepare_only:
        print(json.dumps({"status": "prepared_verified", "protocol": str(out / "protocol.json"),
                          "protocol_sha256": digest(out / "protocol.json"), "games_started": 0}, indent=2))
        return 0
    run_tranche(repo, out, protocol)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
