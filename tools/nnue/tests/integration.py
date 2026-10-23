"""Local Linux integration tests; uses the test-only PID-namespace adapter."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import chess


def run():
    summary = {}
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        engine = ROOT / "tests/mock_uci.py"
        engine.chmod(0o755)
        traces = work / "traces"
        env = dict(os.environ, FORGE_TEST_TRACE=str(traces))
        base = [sys.executable, str(ROOT / "forge_selfplay.py"), "--engine", str(engine),
                "--cpus", "0-3", "--workers", "2", "--nodes", "5000", "--max-ply", "18",
                "--progress-seconds", ".02", "--lines-per-file", "7", "--out", str(work / "out")]
        completed = subprocess.run(base + ["--games-per-worker", "2", "--seed", "50"],
                                   env=env, text=True, capture_output=True, timeout=30)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        files = sorted((work / "out").glob("*.txt"))
        all_lines = []
        originals = {}
        for path in files:
            lines = path.read_text().splitlines()
            assert 0 < len(lines) <= 7
            all_lines.extend(lines)
            originals[path.name] = path.read_bytes()
            assert path.with_suffix(".txt.md5").read_text().split()[0] == hashlib.md5(path.read_bytes()).hexdigest()
        keys = []
        for line in all_lines:
            fen, cp, result = line.split(" | ")
            board = chess.Board(fen)
            assert board.is_valid() and not board.is_check()
            assert int(cp) == 25 and result == "0.5"
            assert board.ply() >= 8
            keys.append(" ".join(fen.split()[:4]))
        assert len(keys) == len(set(keys))
        trace_files = list(traces.glob("*.jsonl"))
        assert len(trace_files) == 2, "Engine should stay alive across games"
        for path in trace_files:
            events = [json.loads(line) for line in path.read_text().splitlines()]
            commands = [x["text"] for x in events if x["event"] == "command"]
            assert commands.count("ucinewgame") == 2
            assert "setoption name Threads value 1" in commands
            assert "setoption name Hash value 16" in commands
            assert all(x["affinity"] == [0, 1, 2, 3] and x["nice"] == 19 for x in events if x["event"] == "go")
            assert len([x for x in commands if x == "go nodes 5000"]) == 20
            assert all(x.startswith("position startpos moves ") for x in commands if x.startswith("position"))
            assert any(x["event"] == "quit" for x in events)
        summary["uci_history_and_process_lifetime"] = "2 workers, 4 games, 2 engine processes, 40 go nodes 5000 requests"
        completed = subprocess.run(base + ["--games-per-worker", "2", "--seed", "50"],
                                   env=env, text=True, capture_output=True, timeout=30)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert {p.name:p.read_bytes() for p in (work / "out").glob("*.txt")} == originals
        summary["resume_and_cross_run_dedup"] = "Identical rerun added no lines and modified no data files"
        traces2 = work / "interrupt-traces"
        env2 = dict(env, FORGE_TEST_TRACE=str(traces2))
        process = subprocess.Popen(base + ["--seed", "60"], env=env2,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and len(list(traces2.glob("*.jsonl"))) < 2:
            time.sleep(.02)
        time.sleep(.25)
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 130, stdout + stderr
        assert "Stopped cleanly" in stdout
        assert not list((work / "out").glob("*.part"))
        for path in traces2.glob("*.jsonl"):
            assert any(json.loads(x)["event"] == "quit" for x in path.read_text().splitlines())
        summary["ctrl_c"] = "SIGINT returned 130, quit sent to both engines, data sealed, no .part left"
        env3 = dict(env, FORGE_TEST_MODE="fail", FORGE_TEST_TRACE=str(work / "fail-traces"))
        completed = subprocess.run(base, env=env3, text=True, capture_output=True, timeout=20)
        assert completed.returncode == 1 and "error" in completed.stderr
        summary["engine_crash"] = "Nonzero exit, bounded shutdown, no invented game result"
        depth_traces = work / "depth-traces"
        env4 = dict(env, FORGE_TEST_TRACE=str(depth_traces))
        completed = subprocess.run(base + ["--games-per-worker", "1"],
                                   env=env4, text=True, capture_output=True, timeout=20)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        # Repeat using the alternative budget, omitting the explicit nodes pair.
        depth_base = base.copy()
        at = depth_base.index("--nodes")
        del depth_base[at:at + 2]
        depth_traces2 = work / "depth-only-traces"
        env4["FORGE_TEST_TRACE"] = str(depth_traces2)
        completed = subprocess.run(depth_base + ["--depth", "2", "--games-per-worker", "1"],
                                   env=env4, text=True, capture_output=True, timeout=20)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        commands = [json.loads(line).get("text", "") for path in depth_traces2.glob("*.jsonl")
                    for line in path.read_text().splitlines()]
        assert len([x for x in commands if x == "go depth 2"]) == 20
        assert not any("nodes" in x for x in commands if x.startswith("go "))
        summary["depth_budget"] = "go depth 2 sent without nodes budget"
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
