"""Fixed-work instrumentation experiment; no timing comparison or cache."""
import hashlib
import json
from pathlib import Path
import queue
import re
import subprocess
import threading

OUT = Path(__file__).resolve().parent
BASE = Path("/workspace/.cloud-setup/nnue-output-reuse-instrumented")
BASELINE = Path("/workspace/.cloud-setup/forge-nnue-capture-release/forge")
INSTRUMENTED = BASE / "build/forge"
CASES = [
    ("start", "startpos", 7),
    ("kiwipete", "fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 6),
    ("middlegame", "fen r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10", 6),
    ("endgame", "fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 7),
    ("promotion_white", "fen 8/k1P5/2K5/8/8/8/8/8 w - - 0 1", 1),
    ("promotion_black", "fen 8/8/8/8/8/2k5/K1p5/8 b - - 0 1", 1),
]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")
def normalized(lines):
    return [re.sub(r"\b(?:time|nps|hashfull) \d+", lambda m: m.group().split()[0] + " <normalized>", x)
            for x in lines]

class Engine:
    def __init__(self, binary, directory):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=False)
        self.commands = []
        self.rows = []
        self.lines = queue.Queue()
        self.stderr = (directory / "stderr.jsonl").open("wb")
        self.process = subprocess.Popen([str(binary)], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.stderr,
                                        text=True, bufsize=1)
        def read():
            for row in self.process.stdout:
                row = row.rstrip("\r\n")
                self.rows.append(row)
                self.lines.put(row)
            self.lines.put(None)
        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()
    def send(self, command):
        self.commands.append(command)
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
    def until(self, predicate):
        result = []
        while True:
            row = self.lines.get(timeout=60)
            if row is None:
                raise RuntimeError("Engine exited before expected UCI response")
            result.append(row)
            if predicate(row):
                return result
    def ready(self):
        self.send("isready")
        self.until(lambda row: row == "readyok")
    def close(self):
        if self.process.poll() is None:
            self.send("quit")
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
            raise
        finally:
            self.reader.join(timeout=2)
            self.stderr.close()
            (self.directory / "stdout.txt").write_text("\n".join(self.rows) + "\n")
            (self.directory / "stdin.txt").write_text("\n".join(self.commands) + "\n")
            save(self.directory / "process.json", {"returncode": self.process.returncode})
        assert self.process.returncode == 0

def case(binary, label, item):
    name, position, depth = item
    engine = Engine(binary, OUT / "raw" / label / name)
    searches = []
    try:
        engine.send("uci")
        engine.until(lambda row: row == "uciok")
        for command in ("setoption name Threads value 1", "setoption name Hash value 32",
                        "setoption name OwnBook value false", "setoption name Ponder value false"):
            engine.send(command)
        engine.ready()
        for state in ("cold", "warm"):
            if state == "cold":
                engine.send("ucinewgame")
            engine.send("position " + position)
            engine.ready()
            engine.send("go depth " + str(depth))
            rows = engine.until(lambda row: row.startswith("bestmove "))
            searches.append({"state": state, "normalized": normalized(rows), "raw": rows})
    finally:
        engine.close()
    stderr = (engine.directory / "stderr.jsonl").read_text()
    events = [json.loads(row) for row in stderr.splitlines()]
    summary = [row for row in events if row["event"] == "nnue_reuse_summary"]
    if label == "baseline":
        assert not stderr
    else:
        assert len(summary) == 2
    save(engine.directory / "result.json", {"searches": searches, "summaries": summary})
    return {"searches": searches, "summaries": summary}

def bench(binary, label):
    directory = OUT / "raw" / label / "bench11"
    directory.mkdir(parents=True, exist_ok=False)
    command = [str(binary)]
    (directory / "stdin.txt").write_text("bench 11\nquit\n")
    with (directory / "stdout.txt").open("wb") as stdout, (directory / "stderr.jsonl").open("wb") as stderr:
        result = subprocess.run(command, input=b"bench 11\nquit\n", stdout=stdout, stderr=stderr, timeout=120)
    save(directory / "process.json", {"command": command, "returncode": result.returncode})
    assert result.returncode == 0
    stdout = (directory / "stdout.txt").read_text()
    match = re.findall(r"^info string bench depth 11 nodes (\d+) time \d+ nps \d+$", stdout, re.M)
    assert match == ["419798"]
    events = [json.loads(row) for row in (directory / "stderr.jsonl").read_text().splitlines()]
    summary = [row for row in events if row["event"] == "nnue_reuse_summary"]
    assert len(summary) == (0 if label == "baseline" else 8)
    if summary:
        assert sum(row["nodes"] for row in summary) == 419798
    return {"nodes": 419798, "summaries": summary}

def totals(rows):
    keys = ["network_calls", "actual_public_evaluate_calls", "duplicate_identity",
            "duplicate_exact_input", "changed_input_same_identity", "output_mismatch",
            "key_fen_mismatch", "unmarked_position_change", "real_invalidations",
            "null_invalidations", "tt_raw_eval_hits", "nodes"]
    result = {key: sum(row[key] for row in rows) for key in keys}
    result["duplicate_fraction_of_network_calls"] = (
        result["duplicate_exact_input"] / result["network_calls"] if result["network_calls"] else 0)
    return result

def main():
    source_record = json.loads((OUT / "instrumented-source.json").read_text())
    source_hashes = {str(BASE / "source" / path): digest
                     for path, digest in source_record["source_files_sha256"].items()}
    frozen = {str(p): sha(p) for p in [BASELINE, INSTRUMENTED, Path(__file__), OUT / "instrumentation.patch"]}
    frozen.update(source_hashes)
    result = {"base_source": "c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e",
              "status": "running", "binary_hashes": {str(p): sha(p) for p in [BASELINE, INSTRUMENTED]},
              "timing_comparison": False, "cache_implemented": False}
    save(OUT / "initial-inputs.json", frozen)
    data = {}
    try:
        for label, binary in [("baseline", BASELINE), ("instrumented-1", INSTRUMENTED),
                              ("instrumented-2", INSTRUMENTED)]:
            data[label] = {item[0]: case(binary, label, item) for item in CASES}
            data[label]["bench11"] = bench(binary, label)
        for name, _, _ in CASES:
            reference = [row["normalized"] for row in data["baseline"][name]["searches"]]
            for label in ("instrumented-1", "instrumented-2"):
                assert [row["normalized"] for row in data[label][name]["searches"]] == reference, (label, name)
            assert data["instrumented-1"][name]["summaries"] == data["instrumented-2"][name]["summaries"], name
        assert data["instrumented-1"]["bench11"] == data["instrumented-2"]["bench11"]
        summaries = [row for item in data["instrumented-1"].values() for row in item["summaries"]]
        assert all(row["network_calls"] == row["actual_public_evaluate_calls"] for row in summaries)
        assert all(row["worker"] == 0 for row in summaries)
        result.update(status="passed_fixed_work_counter_and_parity",
                      search_parity=True, deterministic_counter_summaries=True,
                      case_totals={name: totals(item["summaries"]) for name, item in data["instrumented-1"].items()},
                      totals=totals(summaries), rows=summaries, raw_search_sets=data)
    except BaseException as error:
        result.update(status="failed_preserved", error=repr(error), partial_data=data)
        raise
    finally:
        changed = [path for path, digest in frozen.items() if sha(Path(path)) != digest]
        result["final_inputs_unchanged"] = not changed
        result["changed_inputs"] = changed
        if changed:
            result["status"] = "failed_changed_inputs"
        save(OUT / "results.json", result)
    print(json.dumps({key: result[key] for key in ["status", "totals", "case_totals"]}))

if __name__ == "__main__":
    main()
