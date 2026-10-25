#!/usr/bin/env python3
"""Synthetic software checks only: never invokes GCC, CMake, or a chess engine."""
import ast
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import builtins

ROOT = Path(__file__).resolve().parent
WORKER = ROOT / "forge_sol_pgo_worker_20261025.py"
ast.parse(WORKER.read_text())
spec = importlib.util.spec_from_file_location("pgo_worker", WORKER)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

# Execute the launcher's exact embedded readback against synthetic OS values;
# never change this test process's real affinity, priority or memory limit.
bash = (ROOT / "forge_sol_pgo_build_20261025.sh").read_text()
guard = bash.split("# BEGIN_FORGE_PGO_READBACK_PY\n", 1)[1].split("# END_FORGE_PGO_READBACK_PY", 1)[0]
guard_cap = 3 * 1024 * 1024 * 1024


def guard_fixture(affinity={0, 1, 2, 3}, priority=19, limits=(guard_cap, guard_cap), deadline="2000"):
    fake_os = types.SimpleNamespace(sched_getaffinity=lambda _: affinity, PRIO_PROCESS=0,
                                    getpriority=lambda *_: priority,
                                    environ={"FORGE_PGO_ADMISSION_DEADLINE_UNIX": deadline})
    fake_resource = types.SimpleNamespace(RLIMIT_AS=9, getrlimit=lambda _: limits)
    fake_time = types.SimpleNamespace(time=lambda: 1000.0)
    modules = {"os": fake_os, "resource": fake_resource, "time": fake_time}
    namespace_builtins = vars(builtins).copy()
    original_import = builtins.__import__
    namespace_builtins["__import__"] = lambda name, *a, **kw: modules[name] if name in modules else original_import(name, *a, **kw)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(guard, {"__builtins__": namespace_builtins})
    return output.getvalue()


assert "READBACK_PASS" in guard_fixture()
for bad in ({"affinity": {0, 1}}, {"priority": 18}, {"limits": (guard_cap+1, guard_cap)},
            {"limits": (guard_cap, guard_cap+1)}, {"deadline": "1000"},
            {"deadline": "3581"}, {"deadline": "nan"}, {"deadline": "invalid"}):
    try:
        guard_fixture(**bad)
    except (SystemExit, ValueError):
        pass
    else:
        raise AssertionError("Linux guard accepted invalid synthetic readback: " + str(bad))


def rejected(function):
    try:
        function()
    except RuntimeError:
        return
    raise AssertionError("required failure was accepted")


saved_deadline = os.environ.get("FORGE_PGO_ADMISSION_DEADLINE_UNIX")
saved_marker = os.environ.get("FORGE_PGO_REVIEWED_ENVELOPE")
try:
    os.environ.pop("FORGE_PGO_ADMISSION_DEADLINE_UNIX", None)
    rejected(worker.admit)
    os.environ["FORGE_PGO_ADMISSION_DEADLINE_UNIX"] = str(time.time() - 1)
    rejected(worker.admit)
    os.environ["FORGE_PGO_ADMISSION_DEADLINE_UNIX"] = str(time.time() + 60)
    worker.admit()
    os.environ["FORGE_PGO_REVIEWED_ENVELOPE"] = "ACTIVE"
    rejected_stderr = io.StringIO()
    with contextlib.redirect_stderr(rejected_stderr):
        try:
            worker.main(["--phase", "validate", "--platform", "pc-msys2", "--source", "not-read",
                         "--out", "not-written", "--recipe", "not-read", "--cxx", "not-invoked"])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("PC CTest path was not blocked")
    assert "KILL_NOTHING_CONTRACT" in rejected_stderr.getvalue()
    assert worker.BINARIES == {"baseline": "forge_sol_pgo_baseline_20261025.exe",
                               "instrumented": "forge_sol_pgo_instrumented_20261025.exe",
                               "pgo": "forge_sol_pgo_final_20261025.exe"}
    assert worker.FLAGS == ["-std=c++20", "-O3", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256",
                            "-ffp-contract=off", "-fno-fast-math", "-march=znver5", "-static", "-pthread"]
    with tempfile.TemporaryDirectory(prefix="forge_sol_pgo_fixtures_", dir=ROOT) as temp:
        root = Path(temp)
        (root / "raw").mkdir()
        (root / "work").mkdir()
        # A synthetic text protocol fixture, not an engine. It deliberately
        # fails bench11; later training work must never be sent.
        fixture = root / "protocol_fixture"
        fixture.write_text("#!" + sys.executable + "\n" + '''import sys
for line in sys.stdin:
    line=line.strip()
    if line=='uci': print('uciok',flush=True)
    elif line=='isready': print('readyok',flush=True)
    elif line.startswith('bench '):
        print('info string bench depth 11 nodes 1 time 1 nps 1',flush=True)
    elif line=='quit': break
''')
        fixture.chmod(0o755)
        rejected(lambda: worker.training(fixture, root, os.environ.copy()))
        sent = (root / "raw/training.stdin").read_text().splitlines()
        assert sent[-2:] == ["stop", "quit"]
        assert sent.count("bench 11") == 1
        assert "bench 16" not in sent and not any(s.startswith("position fen ") for s in sent)
        # Warning-with-exit0 is a failure, retaining its actual output.
        rejected(lambda: worker.command([sys.executable, "-c", "import sys; print('warning: fixture',file=sys.stderr)"],
                                         root, root / "raw/warning", os.environ.copy()))
        assert "warning: fixture" in (root / "raw/warning.stderr").read_text()
        # Generate the CMake projection under a source path containing spaces,
        # with every external command replaced by a data-only stub.
        source = root / "source with spaces"
        source.mkdir()
        (source / "CMakeLists.txt").write_text('''add_executable(forge_tests tests/tests.cpp)
target_link_libraries(forge_tests PRIVATE forge_core Threads::Threads)
enable_testing()
add_test(NAME forge_tests COMMAND forge_tests)
add_test(NAME fixture COMMAND fixture ${CMAKE_CURRENT_SOURCE_DIR}/tests/a.tsv)
''')
        calls = []
        expected = ["WAC 001 expected g3g6 got f6h5", "WAC 001 score 661 below 31997"] + [
            "unrestricted search chooses the winning rook underpromotion over stalemating queen promotion"] * 2
        ctest_text = "\n".join("FAIL: " + line for line in expected)
        ctest_text += "\n93% tests passed, 1 tests failed out of 14\nThe following tests FAILED:\n 1 - forge_tests (Failed)\n"
        original_command = worker.command

        def fake_command(argv, cwd, stem, env, allowed_codes=(0,)):
            calls.append(argv)
            return ctest_text if "ctest" in str(argv[0]) else ""

        worker.command = fake_command
        try:
            result = worker.validate_test_core(source, root, "/not-run/g++", "/not-run/cmake", {})
        finally:
            worker.command = original_command
        generated = (root / "validation-project/CMakeLists.txt").read_text()
        assert '"' + source.as_posix() + '/tests/a.tsv"' in generated
        assert '"' + source.as_posix() + '/tests/tests.cpp"' in generated
        assert "OBJECT IMPORTED GLOBAL" in generated and len(calls) == 3
        assert calls[0][calls[0].index("-G")+1] == "Unix Makefiles"
        assert len(result["failures"]) == 4
    print("PASS: Linux guard synthetic readback (1 accept/8 reject), AST, deadline gates, PC CTest rejection, dated binary names, exact flags, first-bench failure stop, recovery transcript, warning rejection, Make/CMake path quoting/test-core projection")
    print("SYNTHETIC_ONLY: no GCC, CMake, chess engine, profile generation, Windows runtime or timing executed")
finally:
    if saved_deadline is None:
        os.environ.pop("FORGE_PGO_ADMISSION_DEADLINE_UNIX", None)
    else:
        os.environ["FORGE_PGO_ADMISSION_DEADLINE_UNIX"] = saved_deadline
    if saved_marker is None:
        os.environ.pop("FORGE_PGO_REVIEWED_ENVELOPE", None)
    else:
        os.environ["FORGE_PGO_REVIEWED_ENVELOPE"] = saved_marker
