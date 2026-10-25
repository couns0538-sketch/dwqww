#!/usr/bin/env python3
"""Pure-PGO build worker; run only inside the reviewed external resource envelope.

Phases are explicit so the PC runner can gate every new engine with bench11.
Build/training orchestration never kills a process. Linux internal QA runs
unchanged tests that may kill an owned engine on timeout; PC rejects that phase.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time

RECIPE_SHA256 = "a5c88c838ff91b778501d913de38dc1286e1958268b78810b0483cea5306bd23"
NET_SHA256 = "74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b"
FLAGS = ["-std=c++20", "-O3", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256",
         "-ffp-contract=off", "-fno-fast-math", "-march=znver5", "-static", "-pthread"]
SOURCES = ["src/" + name + ".cpp" for name in
           ("bitboard", "board", "book", "eval", "eval_params", "nnue", "search", "uci")]
NODES = {11: 308972, 13: 745494, 16: 2460422, 20: 11901452, 22: 31111774}
BINARIES = {"baseline": "forge_sol_pgo_baseline_20261025.exe",
            "instrumented": "forge_sol_pgo_instrumented_20261025.exe",
            "pgo": "forge_sol_pgo_final_20261025.exe"}
FENS = [
    # Start, tactical/castling, developed middlegame, pawn/rook endgame,
    # quiet development, king/rook endgame. All literal inputs, no data files.
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
]


def admit():
    deadline = os.environ.get("FORGE_PGO_ADMISSION_DEADLINE_UNIX")
    if deadline is None or time.time() >= float(deadline):
        raise RuntimeError("shared 43-minute admission deadline reached or missing; no new work")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def source_hashes(source):
    files = [source / "CMakeLists.txt"]
    files += sorted(p for d in ("include", "src", "bench", "tests", "tools")
                    for p in (source / d).rglob("*") if p.is_file())
    return {p.relative_to(source).as_posix(): sha(p) for p in files}


def command(argv, cwd, stem, env, allowed_codes=(0,)):
    admit()
    write_json(str(stem) + ".command.json", {"argv": list(map(str, argv)), "cwd": str(cwd)})
    with open(str(stem) + ".stdout", "wb") as out, open(str(stem) + ".stderr", "wb") as err:
        code = subprocess.call(list(map(str, argv)), cwd=cwd, env=env, stdout=out, stderr=err)
    errors = Path(str(stem) + ".stderr").read_text(encoding="utf-8", errors="replace")
    write_json(str(stem) + ".exit.json", {"returncode": code})
    if code not in allowed_codes or re.search(r"(?im)\bwarning\s*:", errors):
        raise RuntimeError(f"command failed or emitted a warning; see {stem}.stderr")
    return Path(str(stem) + ".stdout").read_text(encoding="utf-8", errors="replace")


def validate_test_core(source, out, compiler, cmake, env):
    """Run original tests against imported final PGO core objects.

    Tests' own translation units have no profile; they compile with common flags.
    No core is rebuilt under a different object path, and no test is changed.
    """
    root = out / "validation-project"
    root.mkdir()
    def quoted(value):
        return '"' + str(value).replace("\\", "/").replace('"', '\\"') + '"'
    original = (source / "CMakeLists.txt").read_text(encoding="utf-8")
    tail = original[original.index("add_executable(forge_tests "):]
    tail = re.sub(r"\$\{CMAKE_CURRENT_SOURCE_DIR\}([^\s)]*)",
                  lambda m: quoted(source.as_posix() + m[1]), tail)
    tail = re.sub(r"(?<![\w/])((?:tests|bench|tools)/[A-Za-z0-9_./-]+\.cpp)",
                  lambda m: '"' + (source / m[1]).as_posix() + '"', tail)
    objects = [out / "work/obj" / (Path(name).stem + ".o") for name in SOURCES[:-1]]
    text = "cmake_minimum_required(VERSION 3.16)\nproject(ForgePgoValidation LANGUAGES CXX)\n"
    text += "find_package(Threads REQUIRED)\nadd_library(forge_core OBJECT IMPORTED GLOBAL)\n"
    text += "set_property(TARGET forge_core PROPERTY IMPORTED_OBJECTS " + " ".join(map(quoted, objects)) + ")\n"
    text += "target_include_directories(forge_core INTERFACE " + quoted(source / "include") + ")\n"
    text += "target_compile_features(forge_core INTERFACE cxx_std_20)\n"
    text += "target_compile_options(forge_core INTERFACE " + " ".join(map(quoted, FLAGS)) + ")\n"
    text += "target_link_options(forge_core INTERFACE " + " ".join(map(quoted, FLAGS)) + ")\n"
    text += "add_executable(forge IMPORTED GLOBAL)\nset_property(TARGET forge PROPERTY IMPORTED_LOCATION "
    text += quoted(out / "bin" / BINARIES["pgo"]) + ")\n" + tail
    (root / "CMakeLists.txt").write_text(text, encoding="utf-8")
    build = out / "validation-build"
    generator = "Ninja" if os.name == "nt" else "Unix Makefiles"
    command([cmake, "-S", str(root), "-B", str(build), "-G", generator, "-DCMAKE_BUILD_TYPE=Release",
             "-DCMAKE_CXX_COMPILER=" + compiler, "-DPython3_EXECUTABLE=" + sys.executable],
            out, out / "raw/validation-configure", env)
    command([cmake, "--build", str(build), "--parallel", "1"],
            out, out / "raw/validation-build", env)
    # Let CTest return its normal failure code for the exact known-lock failure.
    ctest = str(Path(cmake).with_name("ctest.exe" if os.name == "nt" else "ctest"))
    text = command([ctest, "--test-dir", str(build), "--output-on-failure"],
                   out, out / "raw/validation-ctest", env, allowed_codes=(0, 8))
    failures = re.findall(r"(?m)^FAIL: (.*)$", text)
    expected = ["WAC 001 expected g3g6 got f6h5", "WAC 001 score 661 below 31997",
                "unrestricted search chooses the winning rook underpromotion over stalemating queen promotion",
                "unrestricted search chooses the winning rook underpromotion over stalemating queen promotion"]
    if sorted(failures) != sorted(expected) or not re.search(r"1 tests failed out of 14", text):
        raise RuntimeError("CTest differs from the exact 13/14 known-four-lines lock policy")
    # Require that the sole failed test is forge_tests, not another failing suite.
    section = text.split("The following tests FAILED:")
    if len(section) != 2 or re.findall(r"(?m)^\s*\d+ - ([\w_]+) \(Failed\)", section[1]) != ["forge_tests"]:
        raise RuntimeError("CTest sole expected failing test was not forge_tests")
    return {"ctest": "13/14; exact four known FAIL lines", "failures": failures,
            "core": "final use-stage imported objects; test-main TUs compiled without PGO",
            "scope": "Linux internal QA; unchanged uci_regression.py may process.kill() on timeout; no global no-kill guarantee",
            "generated_cmake_sha256": sha(root / "CMakeLists.txt")}


def training(binary, out, env, depths=(11, 16), fens=FENS, tag="training"):
    """Synchronous bench gate, bench16, then wait for each actual bestmove."""
    raw = out / "raw" / tag
    commands = []
    process = None
    reader = None
    with raw.with_suffix(".stdout").open("w", encoding="utf-8", newline="\n") as stdout, \
         raw.with_suffix(".stderr").open("wb") as stderr:
        try:
            admit()
            process = subprocess.Popen([str(binary)], cwd=out / "work", env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=stderr, text=True, bufsize=1)
            lines = queue.Queue()

            def pump():
                try:
                    for line in process.stdout:
                        stdout.write(line)
                        stdout.flush()
                        lines.put(line)
                finally:
                    lines.put(None)

            reader = threading.Thread(target=pump, daemon=True)
            reader.start()

            def send(line):
                admit()
                commands.append(line)
                process.stdin.write(line + "\n")
                process.stdin.flush()

            def until(predicate):
                while True:
                    admit()
                    try:
                        line = lines.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    if line is None:
                        raise RuntimeError("training engine exited before its required response")
                    if "invalid FEN" in line or "illegal move" in line:
                        raise RuntimeError("training engine rejected an input")
                    if predicate(line.rstrip("\r\n")):
                        return line.rstrip("\r\n")

            send("uci")
            until(lambda line: line == "uciok")
            for line in ("setoption name Threads value 1", "setoption name Hash value 16",
                         "setoption name OwnBook value false", "setoption name UseNNUE value true",
                         "setoption name NnueInt16 value false", "setoption name SingTtPv value false",
                         "setoption name RefutLmr value false", "isready"):
                send(line)
            until(lambda line: line == "readyok")
            # First engine work is always lock bench11, before any training FEN.
            for depth in depths:
                send(f"bench {depth}")
                line = until(lambda line: line.startswith("info string bench depth "))
                m = re.fullmatch(r"info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", line)
                if not m or int(m[1]) != depth or int(m[2]) != NODES[depth] or int(m[4]) <= 0:
                    raise RuntimeError(f"training lock bench{depth} mismatch: {line}")
            for fen in fens:
                send("ucinewgame")
                send("position fen " + fen)
                send("go depth 8")
                until(lambda line: bool(re.fullmatch(r"bestmove [a-h][1-8][a-h][1-8][qrbn]?(?: ponder [a-h][1-8][a-h][1-8][qrbn]?)?", line)))
            send("quit")
            process.stdin.close()
            code = process.wait()
            reader.join()
            if code != 0:
                raise RuntimeError(f"training exit {code}")
        finally:
            # No kill, timeout, process-name cleanup or cross-job signaling.
            # On failure request a normal shutdown of this owned child only.
            if process is not None and process.poll() is None:
                try:
                    commands.extend(("stop", "quit"))
                    raw.with_suffix(".stdin").write_text("\n".join(commands) + "\n", encoding="utf-8")
                    process.stdin.write("stop\nquit\n")
                    process.stdin.flush()
                    process.stdin.close()
                except (BrokenPipeError, ValueError, OSError):
                    pass
                process.wait()
            if reader is not None:
                reader.join()
            raw.with_suffix(".stdin").write_text("\n".join(commands) + "\n", encoding="utf-8")
    if raw.with_suffix(".stderr").stat().st_size:
        raise RuntimeError("training stderr was nonempty; inspect raw/training.stderr")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("all", "baseline", "check-baseline", "generate", "train", "check-instrumented", "use", "check-use", "validate"))
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument("--cxx", required=True)
    parser.add_argument("--platform", required=True, choices=("linux", "pc-msys2"))
    parser.add_argument("--cmake", default="cmake")
    args = parser.parse_args(argv)
    if os.environ.get("FORGE_PGO_REVIEWED_ENVELOPE") != "ACTIVE":
        parser.error("launch through the reviewed Job 1 resource supervisor; worker enforces no resource limits itself")
    admit()
    if args.platform == "pc-msys2" and args.phase == "validate":
        parser.error("NATIVE_CTEST_UNVERIFIED_NOT_RUN_KILL_NOTHING_CONTRACT: original UCI regression may process.kill() on timeout")
    if args.phase == "all":
        common = ["--source", str(args.source), "--out", str(args.out), "--recipe", str(args.recipe),
                  "--cxx", args.cxx, "--platform", args.platform, "--cmake", args.cmake]
        phases = ("baseline", "check-baseline", "generate", "train", "check-instrumented", "use", "check-use")
        if args.platform == "linux":
            phases += ("validate",)
        for phase in phases:
            main(["--phase", phase] + common)
        if args.platform == "linux":
            print("PGO BUILD + LOCK_BENCH + LINUX_QA_CTEST PASS; original tests may kill owned engines on timeout; no global no-kill guarantee")
        else:
            print("PGO BUILD + LOCK_BENCH PASS; NATIVE_CTEST_UNVERIFIED_NOT_RUN_KILL_NOTHING_CONTRACT")
        print("perft/FMA/timings/Elo NOT_MEASURED by this phase pipeline; inspect platform/compiler identity")
        return
    source, out, recipe = args.source.resolve(), args.out.resolve(), args.recipe.resolve()
    if source == out or source in out.parents or out in source.parents:
        parser.error("source and output must be disjoint; source is read-only")
    if sha(recipe) != RECIPE_SHA256:
        parser.error("authoritative recovered PC recipe SHA256 mismatch")
    if sha(source / "src/nnue_weights.inc") != NET_SHA256:
        parser.error("lock network SHA256 mismatch")
    compiler = shutil.which(args.cxx)
    if compiler is None:
        parser.error("compiler not found")
    compiler = str(Path(compiler).resolve())
    # Version commands are short read-only preflight; no compilation is attempted.
    admit()
    version = subprocess.check_output([compiler, "-dumpfullversion", "-dumpversion"], text=True).strip()
    banner = subprocess.check_output([compiler, "--version"], text=True)
    target = subprocess.check_output([compiler, "-dumpmachine"], text=True).strip()
    if args.platform == "pc-msys2":
        if os.name != "nt" or version != "15.2.0" or "MSYS2" not in banner or "Rev14" not in banner or target != "x86_64-w64-mingw32":
            parser.error("exact native Windows MSYS2 Rev14 GCC15.2.0 toolchain required")
    elif os.name == "nt":
        parser.error("Linux worker cannot label a Windows run Linux")
    elif int(version.split(".")[0]) < 13:
        parser.error("Linux script requires GNU g++ >=13 per the handoff")
    identity = {"source": str(source), "source_sha256": source_hashes(source),
                "compiler": compiler, "compiler_sha256": sha(compiler), "version": version,
                "banner": banner, "target": target, "platform": args.platform,
                "recipe_sha256": sha(recipe), "base_flags": FLAGS, "sources": SOURCES}
    if args.phase == "baseline":
        if out.exists() and any(out.iterdir()):
            parser.error("baseline output must be new or empty; refusing evidence overwrite")
        for directory in ("work/obj", "work/link", "work/profile", "tmp", "raw", "bin", "receipts"):
            (out / directory).mkdir(parents=True, exist_ok=True)
        write_json(out / "receipts/identity.json", identity)
        shutil.copy2(recipe, out / "receipts/recovered_build_h256_e12.ps1")
    else:
        if json.loads((out / "receipts/identity.json").read_text()) != identity:
            parser.error("source/compiler/flags identity changed since baseline")
        predecessors = {"check-baseline": "baseline", "generate": "baseline", "train": "generate",
                        "check-instrumented": "train", "use": "train", "check-use": "use", "validate": "use"}
        previous = out / "receipts" / (predecessors[args.phase] + ".PASS.json")
        if not previous.is_file():
            parser.error("required predecessor PASS receipt missing")
    receipt = out / "receipts" / (args.phase + ".PASS.json")
    if receipt.exists() or (out / "raw" / (args.phase + ".STARTED.json")).exists():
        parser.error("phase already attempted; preserve it and use a fresh output for retries")
    write_json(out / "raw" / (args.phase + ".STARTED.json"), identity)
    env = os.environ.copy()
    for name in ("TMP", "TEMP", "TMPDIR"):
        env[name] = str(out / "tmp")
    env["LC_ALL"] = "C"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Prevent inherited gcov redirection from moving or mixing profile files.
    for name in ("GCOV_PREFIX", "GCOV_PREFIX_STRIP", "GCOV_EXIT_AT_ERROR", "GCOV_ERROR_FILE"):
        env.pop(name, None)
    env["GCOV_EXIT_AT_ERROR"] = "1"
    profile = out / "work/profile"
    frozen_profile = out / "work/profile-frozen"
    if args.phase.startswith("check-"):
        phase = args.phase.removeprefix("check-")
        label = {"baseline": "baseline", "instrumented": "instrumented", "use": "pgo"}[phase]
        predecessor = {"baseline": "baseline", "instrumented": "generate", "use": "use"}[phase]
        built = json.loads((out / "receipts" / (predecessor + ".PASS.json")).read_text())
        binary = out / "bin" / BINARIES[label]
        if sha(binary) != built["binary_sha256"]:
            raise RuntimeError("lock-check executable identity changed")
        training(binary, out, env, depths=tuple(NODES), fens=(), tag=args.phase)
        write_json(receipt, {"binary_sha256": sha(binary), "bench_nodes": NODES,
                            "scope": "lock depth/node correctness; no speed conclusion"})
        return
    if args.phase == "validate":
        cmake = shutil.which(args.cmake)
        if cmake is None:
            raise RuntimeError("CMake/Make/CTest toolchain required for Linux internal QA CTest gate")
        used = json.loads((out / "receipts/use.PASS.json").read_text())
        if sha(out / "bin" / BINARIES["pgo"]) != used["binary_sha256"] or any(
                sha(out / "work/obj" / name) != value for name, value in used["objects_sha256"].items()):
            raise RuntimeError("final PGO executable/core object identity changed")
        result = validate_test_core(source, out, compiler, cmake, env)
        if source_hashes(source) != identity["source_sha256"]:
            raise RuntimeError("source changed during CTest validation")
        write_json(receipt, result)
        return
    if args.phase == "train":
        instrumented = out / "bin" / BINARIES["instrumented"]
        generated = json.loads((out / "receipts/generate.PASS.json").read_text())
        if sha(instrumented) != generated["binary_sha256"] or list(profile.rglob("*.gcda")):
            raise RuntimeError("instrumented binary changed or profile directory is not fresh")
        training(instrumented, out, env)
        gcda = sorted(profile.rglob("*.gcda"))
        if len(gcda) != len(SOURCES) or any(p.stat().st_size == 0 for p in gcda):
            raise RuntimeError("expected eight nonempty per-TU profile files")
        by_tu = {}
        for name in SOURCES:
            stem = Path(name).stem
            matches = [p for p in gcda if p.name == stem + ".gcda" or p.name.endswith("#" + stem + ".gcda")]
            if len(matches) != 1:
                raise RuntimeError("profile identity missing/ambiguous for " + name)
            by_tu[name] = matches[0].relative_to(profile).as_posix()
        # Freeze immediately after the declared workload. Subsequent
        # instrumented validation writes only to the original runtime directory.
        shutil.copytree(profile, frozen_profile)
        frozen_hashes = {p.relative_to(frozen_profile).as_posix(): sha(p) for p in frozen_profile.rglob("*.gcda")}
        if frozen_hashes != {p.relative_to(profile).as_posix(): sha(p) for p in gcda}:
            raise RuntimeError("profile freeze copy differs from declared training dataset")
        write_json(receipt, {"instrumented_sha256": sha(instrumented), "bench_nodes": {11: NODES[11], 16: NODES[16]},
                            "profile_by_translation_unit": by_tu, "fen_depth": 8, "fens": FENS,
                            "profile_sha256": frozen_hashes, "frozen_profile": str(frozen_profile),
                            "stdin_sha256": sha(out / "raw/training.stdin"),
                            "stdout_sha256": sha(out / "raw/training.stdout")})
        return
    extra = []
    if args.phase == "generate":
        if list(profile.iterdir()):
            raise RuntimeError("generation profile directory must be empty")
        extra = ["-fprofile-generate=" + str(profile)]
    if args.phase == "use":
        trained = json.loads((out / "receipts/train.PASS.json").read_text())
        actual = {p.relative_to(frozen_profile).as_posix(): sha(p) for p in frozen_profile.rglob("*.gcda")}
        if actual != trained["profile_sha256"]:
            raise RuntimeError("frozen training profile identity changed")
        extra = ["-fprofile-use=" + str(frozen_profile), "-Werror=missing-profile", "-Werror=coverage-mismatch"]
    objects = [out / "work/obj" / (Path(name).stem + ".o") for name in SOURCES]
    for index, (name, obj) in enumerate(zip(SOURCES, objects)):
        if obj.exists():
            obj.unlink()
        argv = [compiler] + FLAGS + ["-Werror"] + extra + ["-Iinclude", "-c", name, "-o", str(obj)]
        command(argv, source, out / "raw" / (args.phase + f"-compile-{index:02d}"), env)
        if not obj.is_file():
            raise RuntimeError("successful compiler did not produce its object")
    intermediate = out / "work/link/forge.exe"
    if intermediate.exists():
        intermediate.unlink()
    command([compiler] + FLAGS + ["-Werror"] + extra + list(map(str, objects)) + ["-o", str(intermediate)],
            source, out / "raw" / (args.phase + "-link"), env)
    if source_hashes(source) != identity["source_sha256"]:
        raise RuntimeError("source changed while building")
    if not intermediate.is_file() or intermediate.stat().st_size == 0:
        raise RuntimeError("successful linker did not produce a new nonempty executable")
    if args.phase == "use":
        if {p.relative_to(frozen_profile).as_posix(): sha(p) for p in frozen_profile.rglob("*.gcda")} != trained["profile_sha256"]:
            raise RuntimeError("profile changed during use build")
    label = {"baseline": "baseline", "generate": "instrumented", "use": "pgo"}[args.phase]
    binary = out / "bin" / BINARIES[label]
    shutil.copy2(intermediate, binary)
    write_json(receipt, {"binary": str(binary), "binary_sha256": sha(binary),
                        "objects_sha256": {p.name: sha(p) for p in objects},
                        "phase": args.phase, "extra_flags": extra,
                        "qualification": "NOT_RUN; newly built engine requires bench11 first"})


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PGO STOP: " + str(exc), file=sys.stderr)
        sys.exit(1)
