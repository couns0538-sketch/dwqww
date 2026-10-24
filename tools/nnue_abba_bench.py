#!/usr/bin/env python3
"""Preregistered fresh-process bench20 ABBA; internal NPS, descriptive ratios only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time

INPUT = b"setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 20\nquit\n"
FLAGS = "GCC 14.2.0 -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread"
TIMEOUT = 600


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def sequence(blocks):
    if blocks < 4:
        raise ValueError("at least four complete ABBA blocks are required")
    plan = [{"role": role, "pair": None, "block": None} for role in ("OFF", "ON") * 2]
    for block in range(blocks):
        plan.extend({"role": role, "pair": 2*block+pair, "block": block}
                    for role, pair in zip(("OFF", "ON", "ON", "OFF"), (0, 0, 1, 1)))
    return plan


def parse_row(raw):
    lines = [line for line in raw.splitlines() if b"bench depth" in line]
    match = re.fullmatch(rb"info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", lines[0]) if len(lines) == 1 else None
    if not match:
        raise ValueError("expected exactly one complete bench report")
    depth, nodes, milliseconds, nps = map(int, match.groups())
    if depth != 20 or nodes != 11901452 or milliseconds <= 0 or nps != nodes*1000//milliseconds:
        raise ValueError("invalid bench depth, nodes, milliseconds or internal NPS")
    return dict(depth=depth, nodes=nodes, milliseconds=milliseconds, nps=nps)


def source_manifest(root):
    paths = sorted(p for folder in ("src", "include") for p in (root/folder).rglob("*") if p.is_file())
    paths += [root/"CMakeLists.txt"] if (root/"CMakeLists.txt").is_file() else []
    if not paths:
        raise ValueError("source root has no source files: " + str(root))
    files = {str(p.relative_to(root)): sha(p) for p in paths}
    return {"files": files, "sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def pins(binary, source):
    return {"binary_sha256": sha(binary), "source_sha256": source_manifest(source)["sha256"], "runner_sha256": sha(__file__)}


def capture(argv, stdin, folder, timeout):
    (folder/"stdin.bin").write_bytes(stdin)
    record = {"argv": argv, "started_utc": datetime.now(timezone.utc).isoformat(), "actual_exit": None}
    start, process = time.monotonic(), None
    with (folder/"stdout.bin").open("wb") as stdout, (folder/"stderr.bin").open("wb") as stderr:
        try:
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr)
            process.communicate(stdin, timeout=timeout)
            record["status"] = "EXITED"
        except subprocess.TimeoutExpired:
            record["status"] = "TIMEOUT"
            process.kill()
            process.communicate()
        except OSError as error:
            record.update(status="LAUNCH_ERROR", error=repr(error))
        except KeyboardInterrupt:
            record["status"] = "INTERRUPTED"
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                record["actual_exit"] = process.returncode
            record.update(wall_seconds=time.monotonic()-start, closed_utc=datetime.now(timezone.utc).isoformat())
    record.update({name+"_sha256": sha(folder/(name+".bin")) for name in ("stdin", "stdout", "stderr")})
    write(folder/"process.json", record)
    return record


def summarize(rows, blocks):
    if len(rows) != 4 + 4*blocks:
        raise ValueError("incomplete protocol: no ratio summary")
    ratios = []
    for pair in range(2*blocks):
        selected = [row for row in rows if row["pair"] == pair]
        if len(selected) != 2 or {row["role"] for row in selected} != {"OFF", "ON"}:
            raise ValueError("incomplete pair")
        values = {row["role"]: row["nps"] for row in selected}
        ratios.append(values["ON"]/values["OFF"])
    return dict(on_off_pair_ratios=ratios, median_ratio=statistics.median(ratios), min_ratio=min(ratios), max_ratio=max(ratios))


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("baseline", "candidate", "out"):
        parser.add_argument("--"+flag, type=Path, required=True)
    parser.add_argument("--cpu", type=int, default=4)
    parser.add_argument("--blocks", type=int, default=4)
    for flag in ("baseline-source", "candidate-source"):
        parser.add_argument("--"+flag, type=Path, default=Path(__file__).resolve().parents[1])
    for role in ("baseline", "candidate"):
        parser.add_argument("--"+role+"-extra-define", action="append", default=[], choices=("FORGE_NNUE_ALIGN64=0", "FORGE_NNUE_ALIGN64=1"))
    return parser.parse_args(argv)


def preflight(args):
    taskset = shutil.which("taskset")
    if taskset is None or args.cpu not in range(5) or args.cpu not in os.sched_getaffinity(0):
        raise ValueError("taskset and the selected allowed CPU 0..4 are required; no CPU substitution")
    if not args.baseline.is_file() or not args.candidate.is_file():
        raise ValueError("both binaries must be existing files")
    sequence(args.blocks)
    return taskset


def run(args):
    taskset, rows = preflight(args), []
    args.out.mkdir(parents=True, exist_ok=False)
    sources = {"OFF": args.baseline_source.resolve(), "ON": args.candidate_source.resolve()}
    binaries = {"OFF": args.baseline.resolve(), "ON": args.candidate.resolve()}
    profile = {"created_utc": datetime.now(timezone.utc).isoformat(), "purpose": "Intel Xeon Platinum 8573C cloud VM; not physical Ryzen. VM noise remains; median is descriptive, no Elo or automatic gain/acceptance claim.",
               "metric": "engine-reported bench NPS; process wall is diagnostic only", "timeout_seconds": TIMEOUT,
               "cpu": {"selected": args.cpu, "allowed_affinity": sorted(os.sched_getaffinity(0)), "platform": platform.platform(),
                       "model": next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")), "unknown")},
               "declared_build_flags": {role: FLAGS+" -DFORGE_AVX512="+str(int(role == "ON"))+"".join(" -D"+value for value in getattr(args, "baseline_extra_define" if role == "OFF" else "candidate_extra_define")) for role in binaries},
               "build_flags_evidence": "declared from frozen build protocol; not inferred from executable bytes",
               "input_hex": INPUT.hex(), "input_sha256": hashlib.sha256(INPUT).hexdigest(), "effective_bench_options": "bench constructs Searcher(16), default Threads 1; OwnBook is unused by bench",
               "binaries": {role: {"path": str(binary), **pins(binary, sources[role])} for role, binary in binaries.items()},
               "sources": {role: {"path": str(source), **source_manifest(source)} for role, source in sources.items()}, "sequence": sequence(args.blocks)}
    for sample in profile["sequence"]:
        sample["argv"] = [taskset, "-c", str(args.cpu), str(binaries[sample["role"]])]
    (args.out/"stdin.bin").write_bytes(INPUT)
    write(args.out/"profile.json", profile)  # Durable preregistration before the first producer launch.
    try:
        for index, sample in enumerate(profile["sequence"]):
            folder = args.out/f"{index:03d}"
            folder.mkdir()
            role = sample["role"]
            record = {**sample, "before": pins(binaries[role], sources[role])}
            write(folder/"sample.json", record)
            try:
                if record["before"] != {key: profile["binaries"][role][key] for key in record["before"]}:
                    raise ValueError("preregistered binary/source/runner changed before launch")
                record.update(capture(sample["argv"], INPUT, folder, TIMEOUT))
                record["after"] = pins(binaries[role], sources[role])
                if record["after"] != record["before"]:
                    raise ValueError("binary/source/runner changed during sample")
                if record["status"] != "EXITED" or record["actual_exit"] != 0:
                    raise ValueError("producer failed: " + str(record))
                record.update(parse_row((folder/"stdout.bin").read_bytes()))
                rows.append(record)
            finally:
                write(folder/"sample.json", record)
        report = {"status": "COMPLETED", "purpose": profile["purpose"], "metric": profile["metric"], "samples": rows, **summarize(rows, args.blocks)}
    except Exception as error:
        report = {"status": "FAILED", "error": repr(error), "completed_samples": len(rows), "ratios": "withheld because protocol is incomplete; no retry or replacement"}
    report["profile_sha256"] = sha(args.out/"profile.json")
    write(args.out/"summary.json", report)
    return 0 if report["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    sys.exit(run(arguments()))
