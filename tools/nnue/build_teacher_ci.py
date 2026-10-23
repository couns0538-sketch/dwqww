#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build immutable Forge data tools and acquire the external SF19 teacher.

Only archived source from the two declared commits is compiled. Output contains
the source archives, matching headers, actual cores/references/adapters, copied
probe/adapter sources, exact commands, stream hashes and artifact identities.
No checkout, worktree, source patch or engine-strength experiment is performed.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
import urllib.request


CURRENT = "1ab50b2dd64d9b2f752f7f1285f6968cad2fd792"
OLD = "5101c2529d386b7c3a04ba9156a69ee34df6bb43"
DRIVER_SHA = "15c32e4095f3804eae82f12f5fa6b0cfe277e826df9f17ca6730aef4c805d065"
PROBE_SHA = "a4d584955d9cdf1185b6bec6efe884d90babf1a7bbcb79de1b0c40f69b647629"
NETWORK_SHA = "41487f328ff51f27417564df45b6f3139d038b7e940dedb121340bd61be9a4d3"
SF_SHA = "0f83d24cc46d2c66c60f16001af5444873bc112b7d028594513426894c12da19"
SF_NETWORK_SHA = "1a298aa575a085434d29027978dc36867fe9c5bcea9376654b7a8eba1e52dfc2"
COMMON = ["-fno-fast-math", "-ffp-contract=off", "-fno-lto"]
CURRENT_ARCH = ["-march=x86-64-v3", "-mtune=znver5"]
ARCHIVE_PATHS = ["CMakeLists.txt", "LICENSE", "src", "include", "tests", "bench"]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size}


def require_hash(path, expected):
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"Frozen artifact SHA256 differs: {path}: {actual} != {expected}")


def header_inventory(root):
    digest = hashlib.sha256()
    files = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            name = path.relative_to(root).as_posix()
            token = sha256(path)
            digest.update(name.encode() + b"\0" + bytes.fromhex(token))
            files.append({"path": name, "sha256": token})
    return {"path": str(Path(root).resolve()), "inventory_sha256": digest.hexdigest(),
            "inventory_rule": "SHA256(sorted relative path + NUL + raw SHA256(file))",
            "files": files, "all_files_from_frozen_git_archive": True}


def write_probe_source_receipt(path, *, probe, probe_cpp, current_source, core,
                               support_revision, compile_command, build_receipt=None):
    """Write the JSON contract consumed by prepare_teacher_data --probe-source.

    All seven actual source files and the actual linked static core are bound.
    This may also describe an already-built probe without changing its original
    build receipt or rebuilding any executable.
    """
    current_source, path = Path(current_source), Path(path)
    source_paths = [Path(probe_cpp), *[current_source / relative for relative in (
        "src/nnue.cpp", "include/forge/nnue.hpp", "src/eval.cpp", "src/eval_params.cpp",
        "src/search.cpp", "src/nnue_weights.inc")], Path(core)]
    require_hash(probe_cpp, PROBE_SHA)
    require_hash(current_source / "src/nnue_weights.inc", NETWORK_SHA)
    record = {"status": "FROZEN_ACTUAL_SHIPPED_CORE_PROBE_IDENTITY",
              "source_commit": support_revision, "core_source_commit": CURRENT,
              "probe": identity(probe), "probe_sha256": sha256(probe), "core": identity(core),
              "sources": [identity(source) for source in source_paths],
              "compile_argv": [str(value) for value in compile_command],
              "usage": "--hce-only; no network forward on held-out audit before candidate freeze"}
    if build_receipt:
        record["original_build_receipt"] = identity(build_receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return identity(path)


def extract_source(archive, destination):
    destination = Path(destination)
    destination.mkdir()
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        for member in members:
            if (Path(member.name).is_absolute() or ".." in Path(member.name).parts
                    or not (member.isfile() or member.isdir())):
                raise ValueError("Unexpected archived source path: " + member.name)
        stream.extractall(destination, members=members, filter="data")
    if not (destination / "bench/benchmark.cpp").is_file():
        raise ValueError("Frozen source archive lacks the CMake-required bench directory")


def download(url, target):
    request = urllib.request.Request(url, headers={"User-Agent": "Forge-independent-teacher-build/1"})
    with urllib.request.urlopen(request, timeout=120) as source, Path(target).open("xb") as output:
        shutil.copyfileobj(source, output, length=1024 * 1024)


def stockfish_asset():
    url = "https://api.github.com/repos/official-stockfish/Stockfish/releases/tags/sf_19"
    request = urllib.request.Request(url, headers={"User-Agent": "Forge-independent-teacher-build/1"})
    with urllib.request.urlopen(request, timeout=60) as stream:
        release = json.load(stream)
    candidates = [asset for asset in release["assets"] if
                  "linux-x86-64-universal" in asset["name"] and
                  (asset["name"].endswith(".tar.gz") or asset["name"].endswith(".tar"))]
    if len(candidates) != 1:
        raise ValueError("Expected exactly one official SF19 Linux x86-64 universal archive")
    return candidates[0]["browser_download_url"], {"release_api": url, "asset": candidates[0]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("/workspace/dwqww"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--shard", type=int, choices=range(4), required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--cxx", default="g++-14")
    parser.add_argument("--cmake", default="cmake")
    parser.add_argument("--stockfish-url")
    parser.add_argument("--stockfish-archive", type=Path, help="Use an existing official archive; binary SHA is still mandatory")
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 8:
        parser.error("jobs must be 1..8")
    repo, out = args.repo.resolve(), args.out.resolve()
    cxx, cmake = shutil.which(args.cxx), shutil.which(args.cmake)
    if not cxx or not cmake:
        parser.error("Install the declared C++ compiler and CMake before invoking this helper")
    if out.exists() and any(out.iterdir()):
        parser.error("Build output must be fresh; immutable build receipts are never overwritten")
    out.mkdir(parents=True, exist_ok=True)
    for directory in ("bin", "sources", "support", "external"):
        (out / directory).mkdir()
    driver, probe = repo / "tools/nnue/native_game_driver.cpp", repo / "tools/nnue/engine_probe.cpp"
    require_hash(driver, DRIVER_SHA)
    require_hash(probe, PROBE_SHA)
    frozen_support = {str(driver): DRIVER_SHA, str(probe): PROBE_SHA}
    shutil.copyfile(driver, out / "support/native_game_driver.cpp")
    shutil.copyfile(probe, out / "support/engine_probe.cpp")
    paths, builds, records = {}, [], []
    started = time.monotonic()
    log = gzip.open(out / "build-log.jsonl.gz", "wt", compresslevel=1)
    receipt = {"schema": "forge-independent-teacher-ci-build-v1", "shard": args.shard,
               "status": "building", "helper": identity(Path(__file__)),
               "source_support_pins": frozen_support, "paths": paths,
               "builds": builds, "commands": records}
    def run(stage, command, input_text=None):
        command = [str(value) for value in command]
        before = time.monotonic()
        result = subprocess.run(command, cwd=repo, input=input_text, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        fact = {"stage": stage, "argv": command, "cwd": str(repo), "exit": result.returncode,
                "seconds": time.monotonic() - before,
                "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()}
        records.append(fact)
        log.write(json.dumps({**fact, "stdin": input_text, "stdout": result.stdout, "stderr": result.stderr}) + "\n")
        log.flush()
        print(json.dumps({"stage": stage, "exit": result.returncode, "seconds": fact["seconds"]}), flush=True)
        if result.returncode:
            raise RuntimeError("Build command failed: " + stage)
        return result.stdout
    try:
        receipt["support_repository_head"] = run("support-revision", ["git", "-C", repo, "rev-parse", "HEAD"]).strip()
        receipt["compiler_version"] = run("compiler-version", [cxx, "--version"])
        receipt["cmake_version"] = run("cmake-version", [cmake, "--version"])
        for name, revision in (("current", CURRENT), ("5101", OLD)):
            archive, source = out / f"sources/{name}.tar", out / f"sources/{name}"
            run("archive-" + name, ["git", "-C", repo, "archive", "--format=tar", "--output", archive,
                                    revision, *ARCHIVE_PATHS])
            extract_source(archive, source)
            require_hash(source / "src/nnue_weights.inc", NETWORK_SHA)
            architecture = CURRENT_ARCH if name == "current" else []
            core_dir = out / ("core-" + name)
            run("configure-" + name, [cmake, "-S", source, "-B", core_dir,
                "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=" + cxx,
                "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF",
                "-DCMAKE_CXX_FLAGS=" + " ".join([*architecture, *COMMON])])
            run("core-" + name, [cmake, "--build", core_dir, "--target", "forge", "--parallel", args.jobs])
            core, reference = core_dir / "libforge_core.a", out / ("bin/forge-" + name)
            shutil.copy2(core_dir / "forge", reference)
            adapter = out / ("bin/native-" + name)
            command = [cxx, "-std=c++20", "-O3", "-DNDEBUG", *COMMON, *architecture,
                *(["-DFORGE_DRIVER_EXCLUSIVE_TT"] if name == "current" else []),
                '-DFORGE_DRIVER_SOURCE_ID="' + revision + '"', "-I" + str(source / "include"),
                out / "support/native_game_driver.cpp", core, "-pthread", "-o", adapter]
            run("adapter-" + name, command)
            build = {"source_commit": revision, "source_archive": identity(archive),
                     "source_directory": str(source), "headers": header_inventory(source / "include"),
                     "network": identity(source / "src/nnue_weights.inc"), "core": identity(core),
                     "original_uci_reference": identity(reference), "adapter": identity(adapter),
                     "source": identity(out / "support/native_game_driver.cpp"),
                     "command": [str(value) for value in command], "compile_exit_code": 0}
            builds.append(build)
            prefix = "current" if name == "current" else "old"
            paths.update({"native_" + name: str(adapter), prefix + "_core": str(core),
                          prefix + "_reference": str(reference), prefix + "_network": str(source / "src/nnue_weights.inc")})
            for label, binary in (("reference", reference), ("adapter", adapter)):
                answer = run("uci-" + name + "-" + label, [binary], "uci\nquit\n")
                if "uciok" not in answer:
                    raise ValueError("Built executable did not complete UCI identification")
        native_provenance = out / "native-build.json"
        native_provenance.write_text(json.dumps({"builds": builds,
            "purpose": "Original adapters over unchanged revision-specific Forge cores"}, indent=2) + "\n")
        paths["build_provenance"] = str(native_provenance)
        current = builds[0]
        compiled_probe = out / "bin/probe"
        probe_command = [cxx, "-std=c++20", "-O3", "-DNDEBUG", *COMMON, *CURRENT_ARCH,
            "-I" + current["headers"]["path"], out / "support/engine_probe.cpp",
            current["core"]["path"], "-pthread", "-o", compiled_probe]
        run("probe-build", probe_command)
        probe_answer = run("probe-hce-smoke", [compiled_probe, "--hce-only"],
                           "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\n")
        fact = json.loads(probe_answer)
        if not (fact["hce_only"] and fact["nnue_available"] and fact["residual_mode"] and fact["hidden_size"] == 128):
            raise ValueError("Native probe does not satisfy the shipped H128 residual contract")
        probe_receipt = out / "probe-source.json"
        write_probe_source_receipt(probe_receipt, probe=compiled_probe,
            probe_cpp=out / "support/engine_probe.cpp", current_source=current["source_directory"],
            core=current["core"]["path"], support_revision=receipt["support_repository_head"],
            compile_command=probe_command)
        paths.update(probe=str(compiled_probe), probe_source=str(probe_receipt),
                     probe_cpp=str(out / "support/engine_probe.cpp"))
        sf_archive = out / "external/stockfish-19.archive"
        if args.stockfish_archive:
            shutil.copyfile(args.stockfish_archive.resolve(), sf_archive)
            sf_origin = {"local_archive": str(args.stockfish_archive.resolve())}
        else:
            sf_url, sf_origin = (args.stockfish_url, {}) if args.stockfish_url else stockfish_asset()
            sf_origin["url"] = sf_url
            download(sf_url, sf_archive)
        sf_binary = out / "bin/stockfish"
        with tarfile.open(sf_archive) as archive:
            candidates = [member for member in archive.getmembers() if member.isfile()
                          and Path(member.name).name == "stockfish-linux-x86-64-universal"]
            if len(candidates) != 1:
                raise ValueError("Official archive lacks exactly one expected SF19 universal binary")
            with archive.extractfile(candidates[0]) as incoming, sf_binary.open("xb") as destination:
                shutil.copyfileobj(incoming, destination, length=1024 * 1024)
        sf_binary.chmod(0o755)
        require_hash(sf_binary, SF_SHA)
        answer = run("stockfish-uci-smoke", [sf_binary], "uci\nquit\n")
        if "id name Stockfish 19" not in answer or "uciok" not in answer:
            raise ValueError("External teacher does not identify itself as Stockfish 19")
        receipt["teacher"] = {**identity(sf_binary), "archive": identity(sf_archive), "origin": sf_origin,
                              "embedded_network_sha256": SF_NETWORK_SHA}
        paths["stockfish"] = str(sf_binary)
        for path, expected in frozen_support.items():
            require_hash(path, expected)
        receipt["artifacts"] = {name: identity(path) for name, path in paths.items()}
        receipt["status"] = "PASS_IMMUTABLE_BUILDS_EXTERNAL_TEACHER_AND_NATIVE_PROBE"
    except BaseException as error:
        receipt.update(status="FAILED", error=repr(error))
        raise
    finally:
        log.close()
        receipt["elapsed_seconds"] = time.monotonic() - started
        receipt["build_log"] = identity(out / "build-log.jsonl.gz")
        (out / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt": identity(out / "build-receipt.json"), "paths": paths}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
