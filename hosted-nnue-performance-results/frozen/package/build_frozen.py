#!/usr/bin/env python3
"""Build and validate frozen inputs; invoked only by the isolated hosted job."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time

READY = "PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH"
FLAGS = "-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto"
SOURCE_PATHS = ["CMakeLists.txt", "include", "src", "tests", "tools", "bench"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def validate_protocol(protocol, environment):
    if protocol["status"] != READY:
        raise ValueError("Protocol remains pending review; no build or timing authorized")
    for label in ("baseline", "candidate"):
        sha = protocol[label + "_sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Unfrozen " + label + " source")
        if environment.get(label.upper() + "_SHA") != sha:
            raise ValueError("Workflow/protocol " + label + " SHA mismatch")
    if protocol["driver_source_sha"] != protocol["candidate_sha"]:
        raise ValueError("Both drivers must come from the same frozen candidate source")
    if protocol["release_flags"] != FLAGS or protocol["compiler"] != "g++-14":
        raise ValueError("Unregistered compiler settings")
    if protocol["attempts"] != 1 or protocol["fault_retries"] != 0:
        raise ValueError("This experiment permits one attempt and no retry")
    if environment.get("GITHUB_RUN_ATTEMPT") != "1":
        raise ValueError("Workflow reruns are excluded")


class Commands:
    def __init__(self, out):
        self.out = out
        self.records = []

    def run(self, name, argv, *, cwd=None, stdin=None, timeout=180):
        stdout = self.out / (name + ".stdout")
        stderr = self.out / (name + ".stderr")
        record = {"name": name, "argv": list(map(str, argv)), "cwd": str(cwd or Path.cwd()),
                  "stdin": stdin, "timeout_seconds": timeout, "started_utc_ns": time.time_ns(),
                  "stdout": stdout.name, "stderr": stderr.name}
        self.records.append(record)
        write_json(self.out / "commands.json", self.records)
        print("+", name, flush=True)
        try:
            with stdout.open("wb") as so, stderr.open("wb") as se:
                result = subprocess.run(list(map(str, argv)), cwd=cwd,
                                        input=None if stdin is None else stdin.encode(),
                                        stdout=so, stderr=se, timeout=timeout, check=False)
            record["returncode"] = result.returncode
            if result.returncode:
                raise RuntimeError(f"{name} failed ({result.returncode}); preserved {stdout} and {stderr}")
        except BaseException as exc:
            record["error"] = str(exc)
            raise
        finally:
            record["finished_utc_ns"] = time.time_ns()
            write_json(self.out / "commands.json", self.records)
        return stdout


def manifest(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*")) if p.is_file()}


def build(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    frozen = out / "frozen"
    frozen.mkdir()
    package = args.package.resolve()
    shutil.copytree(package, frozen / "package", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(args.repo / ".github/workflows/forge-hosted-nnue-performance.yml", frozen / "workflow.yml")
    protocol = json.loads((package / "protocol.json").read_text())
    commands = Commands(out)
    status = {"correctness_passed": False, "timing_started": False}
    try:
        validate_protocol(protocol, os.environ)
        for name, argv in (("compiler-version", ["g++-14", "--version"]),
                           ("cmake-version", ["cmake", "--version"]),
                           ("ctest-version", ["ctest", "--version"]),
                           ("python-version", [sys.executable, "--version"]),
                           ("git-version", ["git", "--version"]),
                           ("host-uname", ["uname", "-a"]), ("host-lscpu", ["lscpu"])):
            path = commands.run(name, argv, timeout=10)
            shutil.copy2(path, frozen / path.name)
        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=False)
        source_roots = {}
        for label in ("baseline", "candidate"):
            sha = protocol[label + "_sha"]
            commands.run(label + "-commit", ["git", "cat-file", "-e", sha + "^{commit}"], cwd=args.repo)
            archive = frozen / ("source-" + label + ".tar")
            commands.run(label + "-archive", ["git", "archive", "--format=tar", "--output=" + str(archive), sha, *SOURCE_PATHS], cwd=args.repo)
            source = work / ("src-" + label)
            source.mkdir()
            with tarfile.open(archive) as tf:
                # The archive is emitted from a verified local immutable Git commit.
                for item in tf.getmembers():
                    target = (source / item.name).resolve()
                    if not target.is_relative_to(source) or item.issym() or item.islnk():
                        raise ValueError("Unexpected path/link in source export")
                tf.extractall(source)
            write_json(frozen / (label + "-source-manifest.json"), {
                "source_commit": sha, "archive_sha256": digest(archive),
                "archive_paths": SOURCE_PATHS, "files_sha256": manifest(source)})
            source_roots[label] = source
        drivers = frozen / "drivers"
        drivers.mkdir()
        for name in ("nnue_update_snapshot.cpp", "nnue_update_benchmark.cpp", "nnue_snapshot.cpp"):
            shutil.copy2(source_roots["candidate"] / "tools" / name, drivers / name)
        for label in ("baseline", "candidate"):
            source = source_roots[label]
            build_dir = work / ("build-" + label)
            artifact = frozen / "artifacts" / label
            artifact.mkdir(parents=True)
            commands.run(label + "-configure", ["cmake", "-S", source, "-B", build_dir,
                "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=g++-14",
                "-DCMAKE_CXX_FLAGS=", "-DCMAKE_CXX_FLAGS_RELEASE=" + FLAGS,
                "-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF", "-DFORGE_NATIVE=OFF",
                "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])
            commands.run(label + "-build", ["cmake", "--build", build_dir, "-j2"])
            for name in ("forge", "libforge_core.a", "compile_commands.json", "CMakeCache.txt"):
                shutil.copy2(build_dir / name, artifact / name)
            compile_commands = json.loads((build_dir / "compile_commands.json").read_text())
            for entry in compile_commands:
                command = entry["command"]
                if any(bad in command for bad in ("-flto", "-ffast-math", "-Ofast", "-march=native")):
                    raise ValueError("Forbidden compile option")
                if any(flag not in command for flag in FLAGS.split()):
                    raise ValueError("Required strict Release compile option missing")
            try:
                commands.run(label + "-ctest", ["ctest", "--test-dir", build_dir, "--output-on-failure"], timeout=150)
            finally:
                test_log = build_dir / "Testing/Temporary/LastTest.log"
                if test_log.exists():
                    shutil.copy2(test_log, out / (label + "-LastTest.log"))
                cost = build_dir / "Testing/Temporary/CTestCostData.txt"
                if cost.exists():
                    shutil.copy2(cost, out / (label + "-CTestCostData.txt"))
            ctest_text = (out / (label + "-ctest.stdout")).read_text()
            if (not re.search(r"100% tests passed, 0 tests failed out of [1-9][0-9]*", ctest_text)
                    or re.search(r"\*\*\*Not Run|\*\*\*Skipped|\*\*\*Disabled", ctest_text)):
                raise ValueError("CTest did not complete a nonempty all-passing suite")
            for name in ("nnue_update_snapshot", "nnue_update_benchmark", "nnue_snapshot"):
                commands.run(label + "-compile-" + name, ["g++-14", "-std=c++20", *FLAGS.split(),
                    "-I", source / "include", drivers / (name + ".cpp"),
                    artifact / "libforge_core.a", "-pthread", "-o", artifact / name])
            sections = commands.run(label + "-core-sections", ["objdump", "-h", artifact / "libforge_core.a"])
            if ".gnu.lto_" in sections.read_text():
                raise ValueError("LTO sections found in actual core")
            disassembly = commands.run(label + "-kernel-disassembly", ["objdump", "-d", "-C", artifact / "nnue_update_benchmark"])
            text = disassembly.read_text()
            calls = [line for line in text.splitlines() if re.search(r"\bcall\b.*forge::nnue::update\(", line)]
            if len(calls) < 2:
                raise ValueError("Expected out-of-line warmup and timed public NNUE update calls")
            (frozen / (label + "-kernel-callsite.txt")).write_text("\n".join(calls) + "\n")
            for name in ("nnue_update_snapshot", "nnue_snapshot"):
                stream = commands.run(label + "-" + name, [artifact / name], timeout=45)
                if stream.stat().st_size == 0:
                    raise ValueError("Empty NNUE snapshot stream")
                shutil.copy2(stream, frozen / (label + "-" + name + ".bin"))
            bench = commands.run(label + "-bench-preflight", [artifact / "forge"], stdin="bench 11\nquit\n", timeout=45)
            nodes = re.findall(r"^info string bench depth 11 nodes ([0-9]+) time [0-9]+ nps [0-9]+\s*$", bench.read_text(), re.MULTILINE)
            if nodes != ["419798"]:
                raise ValueError("Preflight bench must complete exactly once with 419798 nodes")
        for name in ("nnue_update_snapshot", "nnue_snapshot"):
            a = frozen / ("baseline-" + name + ".bin")
            b = frozen / ("candidate-" + name + ".bin")
            commands.run("compare-" + name, ["cmp", "--", a, b])
        shutil.copy2(out / "commands.json", frozen / "build-commands.json")
        write_json(frozen / "correctness.json", {
            "full_ctest_both_passed": True, "both_snapshot_streams_byte_identical": True,
            "bench_nodes_each": 419798, "drivers_from": protocol["driver_source_sha"],
            "compiler": "g++-14", "flags": FLAGS, "build_parallelism": 2,
            "core_lto_sections_absent": True, "public_update_call_sites_verified": True})
        status["correctness_passed"] = True
    except BaseException as exc:
        status["error"] = repr(exc)
        raise
    finally:
        write_json(out / "build-status.json", status)
        write_json(out / "frozen-build-SHA256.json", manifest(frozen))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
