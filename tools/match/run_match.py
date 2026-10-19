#!/usr/bin/env python3
"""Reproducible external Fastchess match runner (MIT; Python standard library only).
Run in an otherwise idle environment. Use --mode smoke for infrastructure tests,
not Elo evidence. A SPRT reaches a decision only at an actual likelihood boundary.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

from pgn_stats import summarize


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sprt_decision(console: str, pairs: int, cap: int) -> str:
    """Trust native boundary completion, never a rounded LLR or positive Elo."""
    if not re.search(r"LLR: [+-]?[0-9]+(?:\.[0-9]+)?", console):
        raise RuntimeError("missing or non-finite native SPRT likelihood")
    accepted = re.findall(r"SPRT[^\n]*completed - (H[01]) was accepted", console)
    if accepted:
        return "H1_accepted" if accepted[-1] == "H1" else "H0_accepted"
    if pairs != cap:
        raise RuntimeError("match stopped before cap without a native SPRT decision")
    return "inconclusive_at_pair_cap"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fastchess", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--openings", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--mode", choices=("smoke", "sprt"), default="smoke")
    p.add_argument("--pairs", type=int, default=8)
    p.add_argument("--seed", type=int, default=20261003)
    p.add_argument("--nodes", type=int, default=0)
    p.add_argument("--tc", default="10+0.1")
    p.add_argument("--cpu", type=int, default=None)
    p.add_argument("--hash-mb", type=int, default=32)
    p.add_argument("--overhead-ms", type=int, default=10)
    p.add_argument("--aa", action="store_true")
    a = p.parse_args()
    for field in ("fastchess", "baseline", "candidate", "openings"):
        path = getattr(a, field).resolve(strict=True)
        setattr(a, field, path)
        if not path.is_file():
            p.error(f"{field} must name a regular file")
    if a.pairs < 1 or a.seed < 1 or a.nodes < 0 or a.hash_mb < 1 or a.overhead_ms < 0:
        p.error("invalid numerical settings")
    if a.aa and (digest(a.baseline) != digest(a.candidate) or a.nodes == 0):
        p.error("A/A determinism requires identical binaries and a positive node budget")
    if a.mode == "sprt" and (a.nodes or a.aa):
        p.error("strength SPRT uses equal time, not nodes/A-A")
    lines = a.openings.read_text().splitlines()
    positions = [" ".join(line.split()[:4]) for line in lines if line.strip()]
    if len(positions) != len(set(positions)) or a.pairs > len(positions):
        p.error("openings must be unique and at least as numerous as requested pairs")
    # Freeze a platform-independent permutation instead of depending on std::shuffle.
    ordered = sorted(positions, key=lambda fen: hashlib.sha256(
        f"{a.seed}\n{fen}".encode("ascii")).digest())[:a.pairs]
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=False)  # Never overwrite an earlier experiment.
    selected = a.out / "selected.epd"
    selected.write_text("\n".join(ordered) + "\n", encoding="ascii")
    # No -config discard=true after the engine arguments: that resets parsed CLI state.
    # A fresh directory ensures no existing config can be auto-loaded.
    command = [str(a.fastchess), "-config", "outname=state.json",
               "-engine", f"cmd={a.candidate}", "name=Candidate",
               "-engine", f"cmd={a.baseline}", "name=Baseline",
               "-each", "proto=uci", f"tc={a.tc}", f"option.Hash={a.hash_mb}",
               f"option.Move Overhead={a.overhead_ms}", "restart=on",
               "-openings", f"file={selected}", "format=epd", "order=sequential",
               "-srand", str(a.seed), "-rounds", str(a.pairs), "-games", "2",
               "-concurrency", "1", "-report", "penta=true", "-ratinginterval", "2",
               "-pgnout", "file=games.pgn", "append=false", "notation=uci", "nodes=true",
               "timeleft=true", "-log", "file=fastchess.log", "level=warn", "append=false",
               "-autosaveinterval", "2", "-strict"]
    if a.nodes:
        command += ["-each", f"nodes={a.nodes}"]
    if a.mode == "sprt":
        command += ["-sprt", "elo0=0", "elo1=5", "alpha=0.05", "beta=0.05", "model=logistic"]
    else:
        command += ["-maxmoves", "200"]  # Smoke-only runtime bound, not a strength test.
    if a.cpu is not None:
        if not hasattr(os, "sched_setaffinity") or a.cpu not in os.sched_getaffinity(0):
            p.error("requested CPU affinity unavailable")
        os.sched_setaffinity(0, {a.cpu})  # Child and UCI engine processes inherit it.
    version = subprocess.check_output([str(a.fastchess), "-version"], text=True).strip()
    manifest = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "running", "mode": a.mode, "command": command,
        "fastchess_version": version, "platform": platform.platform(),
        "python": platform.python_version(), "cpu": platform.processor(),
        "cpuinfo": Path("/proc/cpuinfo").read_text() if Path("/proc/cpuinfo").exists() else None,
        "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        "inputs": {field: {"path": str(getattr(a, field)), "sha256": digest(getattr(a, field))}
                   for field in ("fastchess", "baseline", "candidate", "openings")},
        "selected_sha256": digest(selected), "seed": a.seed, "max_pairs": a.pairs,
        "harness_sha256": {name: digest(Path(__file__).with_name(name))
                           for name in ("run_match.py", "pgn_stats.py")},
        "same_engine_threads": 1, "concurrency": 1,
        "sprt": {"elo0": 0, "elo1": 5, "alpha": .05, "beta": .05,
                 "model": "logistic", "bounds": [-2.94443897916644, 2.94443897916644]}
                if a.mode == "sprt" else None,
        "limitations": "Pinned execution is not dedicated hardware. Smoke results are not Elo evidence."
    }
    manifest_path = a.out / "manifest.json"
    def save() -> None:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    save()
    started = time.monotonic()
    try:
        with (a.out / "console.txt").open("w") as log:
            result = subprocess.run(command, cwd=a.out, stdout=log, stderr=subprocess.STDOUT,
                                    env={**os.environ, "NO_COLOR": "1"}, check=False)
        manifest["exit_code"] = result.returncode
        if result.returncode:
            raise RuntimeError(f"Fastchess exited {result.returncode}; inspect console.txt")
        stats = summarize((a.out / "games.pgn").read_text(), require_identical_pairs=a.aa)
        console = re.sub(r'\x1b\[[0-9;]*m', '', (a.out / "console.txt").read_text())
        penta = re.findall(r'Ptnml\(0-2\):\s*\[([^\]]+)\]', console)
        if not penta or [int(n.strip()) for n in penta[-1].split(',')] != stats["pentanomial_0_half_1_1half_2"]:
            raise RuntimeError("independent pentanomial counts disagree with Fastchess")
        if stats["pairs"] != a.pairs and a.mode != "sprt":
            raise RuntimeError("incomplete smoke match")
        for field, recorded in manifest["inputs"].items():
            if digest(getattr(a, field)) != recorded["sha256"]:
                raise RuntimeError(f"input changed during match: {field}")
        # Do not infer PASS from WDL, a nonzero Elo estimate, or merely finishing.
        manifest["status"] = "completed"
        manifest["statistics"] = stats
        manifest["sprt_decision"] = sprt_decision(console, stats["pairs"], a.pairs) if a.mode == "sprt" else "not applicable"
        manifest["outputs"] = {name: digest(a.out / name) for name in
                               ("games.pgn", "console.txt", "selected.epd")}
        (a.out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    except (Exception, KeyboardInterrupt) as error:
        manifest["status"] = "failed_or_interrupted"
        manifest["error"] = str(error)
        raise
    finally:
        manifest["elapsed_seconds"] = time.monotonic() - started
        save()
    print(json.dumps(manifest["statistics"], indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
