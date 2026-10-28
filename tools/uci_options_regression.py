#!/usr/bin/env python3
"""R3-5: UCI option parsing regression (src/uci.cpp, `uci` and `setoption`).

usage: uci_options_regression.py <engine> [--syzygy DIR] [--log FILE]
       (--syzygy defaults to the FORGE_SYZYGY_PATH environment variable; without tables those checks are skipped)

Checks, generic over whatever `uci` advertises (so options added later are covered by type):
  - `uci` lists every option exactly once, well formed (spin: min <= default <= max; check: true/false), twice
    the same; the options of the default build are all there (UseNNUE and NetScale together or not at all);
  - spin: min, max and default are accepted silently; below min / above max are clamped silently (Hash and
    Threads are not set to their maximum: 2 GB of table / 256 search threads); "abc", "1.5", "7x" and a missing
    value are rejected with `info string invalid value for option <name>`; NNUEThreats, NNUEPawnPairs and
    PureNnue (spin 0-1, documented to accept true/false too) reject out-of-range values instead of clamping;
  - check: true / false accepted, anything else (maybe, TRUE, 1, missing) rejected by name;
  - clamps that are observable are verified: bench node counts for CorrHistPlus, HistRework, CorrMargins, CorrExt
    and NetScale (value beyond the bound == the bound), the NNUE v2 error text for NNUEKingBuckets /
    NNUEOutputBuckets (the clamped count is named);
  - strings with spaces: Book File, NNUEFile and SyzygyPath take the rest of the line (the engine echoes the
    full path or reads a file in a folder whose name has spaces); `<empty>` resets each;
  - the NNUE v2 options follow the fail-loud rule: a nonzero request without a net prints `info string ERROR
    NNUE v2: ...` at once and is withdrawn again before the next isready;
  - unknown names, an empty name and a bare `setoption` are ignored silently; an unadvertised tunable name is
    still parsed (invalid value reported by name);
  - after the whole sweep (every option back at its default) bench gives the node count of the start and a
    search still returns a legal move; with --syzygy the real tables load and a tablebase win is reported.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uci_regression import Engine  # noqa: E402

TIMEOUT = 120.0  # seconds per response; generous for sanitizer builds
OPTION = re.compile(r"^option name (?P<name>.+?) type (?P<type>spin|check|string|button|combo)"
                    r"(?: default (?P<default>.*?))?(?: min (?P<min>-?\d+) max (?P<max>-?\d+))?$")
# The options of the default build (CMake defaults, NNUE compiled in), src/uci.cpp.
CORE = {"Hash", "Threads", "Move Overhead", "Ponder", "OwnBook", "Book File", "Book Depth", "Book Variety",
        "SmpExactNodes", "SmpBestThread", "LocklessTT", "SyzygyPath", "SyzygyProbeDepth", "Syzygy50MoveRule",
        "CorrHistPlus", "HardDeadline", "NNUEFile", "NNUEKingBuckets", "NNUEOutputBuckets", "NNUEThreats",
        "NNUEPawnPairs", "PureNnue", "CorrMargins", "CorrExt", "CuckooRep", "MaterialKeyTable", "HistRework",
        "IntendedThreefold", "Clear Hash"}
NO_MAX = {"Hash": "2048 MB table", "Threads": "256 search threads"}
ZERO_ONE = {"NNUEThreats", "NNUEPawnPairs", "PureNnue"}       # 0 / 1 / true / false only
V2_REQUEST = {"NNUEKingBuckets", "NNUEOutputBuckets"} | ZERO_ONE  # nonzero = a v2 net request (fail-loud)
STRINGS_WITH_PATHS = {"Book File", "SyzygyPath", "NNUEFile"}
INVALID_SPIN = ["abc", "1.5", "7x", None]
INVALID_CHECK = ["maybe", "TRUE", "1", None]
BENCH_DEPTH = 5


class Session:
    def __init__(self, engine: Path):
        self.e = Engine(engine)
        self.passed: list[str] = []

    def ok(self, label: str):
        self.passed.append(label)

    def sync(self) -> list[str]:
        """isready; returns the lines printed before readyok."""
        self.e.send("isready")
        return self.e.until(lambda line: line == "readyok", TIMEOUT)[:-1]

    def setoption(self, name: str, value: str | None) -> list[str]:
        self.e.send(f"setoption name {name}" + ("" if value is None else f" value {value}"))
        return self.sync()

    def set_quiet(self, name: str, value: str | None):
        out = self.setoption(name, value)
        assert not any("invalid value" in line or "ERROR" in line for line in out), (name, value, out)
        return out

    def rejected(self, name: str, value: str | None):
        out = self.setoption(name, value)
        assert f"info string invalid value for option {name}" in out, (name, value, out)

    def v2_request(self, name: str, value: str, expect: str | None = None):
        """A nonzero NNUE v2 request without a net: the error at once, then withdrawn before isready."""
        self.e.send(f"setoption name {name} value {value}")
        lines = self.e.until(lambda line: line.startswith("info string ERROR NNUE v2:") or "invalid value" in line,
                             TIMEOUT)
        assert lines[-1].startswith("info string ERROR NNUE v2:"), (name, value, lines)
        if expect is not None:
            assert expect in lines[-1], (name, value, expect, lines[-1])
        self.e.send(f"setoption name {name} value 0")
        self.e.until(lambda line: line.startswith("info string NNUE v2:"), TIMEOUT)
        assert not any("ERROR" in line for line in self.sync()), name

    def bench(self) -> int:
        self.e.send(f"bench {BENCH_DEPTH}")
        line = self.e.until(lambda row: row.startswith("info string bench depth"), TIMEOUT)[-1]
        return int(re.search(r" nodes (\d+)", line).group(1))

    def legal_moves(self, position: str) -> set[str]:
        self.e.send(position)
        self.e.send("go perft 1")
        lines = self.e.until(lambda line: line.startswith("nodes "), TIMEOUT)
        return {line.split(":")[0] for line in lines if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?: \d+", line)}

    def search(self, position: str, go: str) -> tuple[str, list[str]]:
        self.e.send(position)
        self.e.send(go)
        lines = self.e.until(lambda line: line.startswith("bestmove "), TIMEOUT)
        return lines[-1].split()[1], lines


def path_strings(s: Session, folder: Path):
    """Book File, NNUEFile and SyzygyPath take the rest of the line. The files stay in `folder` (never deleted)."""
    e = s.e
    folder.mkdir(parents=True, exist_ok=True)
    book = folder / "no such  book file.bin"
    out = s.setoption("Book File", str(book))
    assert f"info string cannot load book {book}" in out, out
    assert s.setoption("Book File", "<empty>") == []
    assert s.setoption("Book File", None) == []
    s.ok("Book File: the whole rest of the line is the path (spaces kept), <empty> and no value reset")

    net = folder / "no such net v2.fnn2"
    e.send(f"setoption name NNUEFile value {net}")
    line = e.until(lambda row: row.startswith("info string ERROR NNUE v2:"), TIMEOUT)[-1]
    assert f"NNUEFile {net}" in line, line
    e.send("setoption name NNUEFile value <empty>")
    e.until(lambda row: row.startswith("info string NNUE v2:"), TIMEOUT)
    assert s.sync() == []
    s.ok("NNUEFile: a path with spaces is used whole (named in the fail-loud error), <empty> withdraws it")

    tb_dir = folder / "tb dir with spaces"
    tb_dir.mkdir(exist_ok=True)
    (tb_dir / "KQvK.rtbw").write_bytes(b"\x00" * 64)  # a table name with invalid contents
    out = s.setoption("SyzygyPath", str(tb_dir))
    assert "info string Syzygy: 0 WDL and 0 DTZ tables, up to 0 pieces, 1 invalid files skipped" in out, out
    assert s.setoption("SyzygyPath", "<empty>") == ["info string Syzygy tablebases off"]
    assert s.setoption("SyzygyPath", None) == ["info string Syzygy tablebases off"]
    s.ok("SyzygyPath: a folder whose name has spaces is read (its invalid table is rejected), <empty> and no "
         "value switch the tables off")


def parse_options(lines: list[str]) -> dict:
    options = {}
    for line in lines:
        if not line.startswith("option "):
            continue
        match = OPTION.match(line)
        assert match, f"malformed option line: {line!r}"
        name = match["name"]
        assert name not in options, f"option listed twice: {name}"
        options[name] = match.groupdict()
    return options


def run(s: Session, syzygy: str, workdir: Path) -> dict:
    e = s.e
    values = {}
    try:
        # --- uci: every option exactly once, well formed, stable ---------------------------------------------------
        e.send("uci")
        first = e.until(lambda line: line == "uciok", TIMEOUT)
        options = parse_options(first)
        e.send("uci")
        assert parse_options(e.until(lambda line: line == "uciok", TIMEOUT)) == options, "second uci differs"
        missing = CORE - options.keys()
        assert not missing, f"options missing from uci: {sorted(missing)}"
        assert ("UseNNUE" in options) == ("NetScale" in options), "UseNNUE and NetScale are advertised together"
        for name, o in options.items():
            if o["type"] == "spin":
                assert o["min"] is not None and o["default"] is not None, name
                assert int(o["min"]) <= int(o["default"]) <= int(o["max"]), (name, o)
            elif o["type"] == "check":
                assert o["default"] in ("true", "false"), (name, o)
            elif o["type"] == "string":
                assert o["default"] is not None, (name, o)
        values["options"] = sorted(options)
        s.ok(f"uci lists {len(options)} options exactly once, well formed, identical on a second uci")
        assert s.sync() == []
        start_bench = s.bench()
        values["bench_start"] = start_bench

        # --- spin options -----------------------------------------------------------------------------------------
        for name, o in options.items():
            if o["type"] != "spin":
                continue
            low, high, default = int(o["min"]), int(o["max"]), o["default"]
            if name in V2_REQUEST:
                assert low == 0 and default == "0", (name, o)
                s.set_quiet(name, "0")
                if name in ZERO_ONE:
                    s.v2_request(name, "1", f"{name} is 1 but no v2 net is loaded")
                    s.v2_request(name, "true", f"{name} is 1 but no v2 net is loaded")
                    s.set_quiet(name, "false")
                    for bad in ["2", "-1", "yes", None]:
                        s.rejected(name, bad)
                else:
                    s.v2_request(name, str(high), f"{name} {high} is set")
                    s.v2_request(name, str(high + 7), f"{name} {high} is set")  # clamped: the error names the max
                    s.set_quiet(name, str(low - 3))                            # clamped to 0: nothing requested
                    for bad in INVALID_SPIN:
                        s.rejected(name, bad)
                s.set_quiet(name, default)
                continue
            for value in [str(low), default] + ([] if name in NO_MAX else [str(high)]):
                s.set_quiet(name, value)
            s.set_quiet(name, str(low - 1))
            if name not in NO_MAX:
                s.set_quiet(name, str(high + 1))
            for bad in INVALID_SPIN:
                s.rejected(name, bad)
            s.set_quiet(name, default)
        s.ok("spin options: min/max/default accepted, out-of-range clamped silently, non-integers and a missing "
             "value rejected by name (" + ", ".join(sorted(n for n, o in options.items() if o["type"] == "spin")) + ")")
        s.ok("NNUE v2 spins: nonzero requests fail loud at once and are withdrawn; 0/1 spins reject out-of-range")

        # Observable clamps: a value beyond the bound searches exactly like the bound.
        clamp_cases = [("CorrHistPlus", "99", "7"), ("CorrHistPlus", "-5", "0"), ("HistRework", "99", "3"),
                       ("CorrMargins", "5", "1"), ("CorrExt", "5", "1"), ("NetScale", "999", "150"),
                       ("NetScale", "1", "50")]
        observed = {}
        for name, beyond, bound in clamp_cases:
            if name not in options:
                continue
            s.set_quiet(name, bound)
            at_bound = s.bench()
            s.set_quiet(name, beyond)
            clamped = s.bench()
            s.set_quiet(name, options[name]["default"])
            assert clamped == at_bound, (name, beyond, bound, clamped, at_bound)
            observed[f"{name} {beyond}->{bound}"] = clamped
        assert s.bench() == start_bench, "defaults restored after the clamp checks"
        values["bench_clamps"] = observed
        s.ok("observable clamps: bench nodes with the out-of-range value equal those at the bound (" +
             ", ".join(observed) + ")")

        # --- check options ----------------------------------------------------------------------------------------
        for name, o in options.items():
            if o["type"] != "check":
                continue
            for value in ("true", "false"):
                s.set_quiet(name, value)
            for bad in INVALID_CHECK:
                s.rejected(name, bad)
            s.set_quiet(name, o["default"])
        s.ok("check options: true/false accepted, maybe/TRUE/1/missing rejected by name (" +
             ", ".join(sorted(n for n, o in options.items() if o["type"] == "check")) + ")")

        # --- strings with spaces ------------------------------------------------------------------------------------
        path_strings(s, workdir / "forge r3 options")

        # --- buttons, unknown names, malformed commands, unadvertised tunables ----------------------------------------
        assert s.setoption("Clear Hash", None) == []
        for command in ("setoption name NoSuchOption value 5", "setoption name Hash2 value 64",
                        "setoption name Threads Count value 2", "setoption name", "setoption",
                        "setoption value 5", "setoption foo bar"):
            e.send(command)
            assert s.sync() == [], command
        s.ok("Clear Hash accepted without a value; unknown names, an empty name and a bare setoption are ignored silently")
        if "RazorDepth" not in options:
            s.rejected("RazorDepth", "abc")
            s.ok("an unadvertised tunable name is still parsed (invalid value reported by name)")

        # --- the engine is unchanged after the sweep ------------------------------------------------------------------
        assert s.bench() == start_bench, "bench after the sweep equals bench at the start"
        legal = s.legal_moves("position startpos")
        move, _ = s.search("position startpos", "go depth 3")
        assert move in legal, move
        s.ok(f"after the sweep: bench {start_bench} unchanged, go depth 3 plays the legal {move}")

        # --- real tables (optional) -----------------------------------------------------------------------------------
        if syzygy:
            out = s.setoption("SyzygyPath", syzygy)
            summary = [row for row in out if row.startswith("info string Syzygy:")]
            assert summary and re.search(r"up to [345] pieces", summary[0]), out
            fen = "8/8/8/K7/7Q/3k4/8/8 w - - 0 1"  # KQvK, win (tests/syzygy_fixtures.tsv)
            winning = {"h4f4", "a5b4", "h4e1", "h4a4", "h4b4", "h4g4", "h4e7", "a5a4", "a5b5", "a5b6", "h4g3", "h4g5",
                       "h4h5", "h4f6", "h4h6", "h4h7", "h4d8", "a5a6", "h4h1", "h4f2", "h4h2", "h4h3", "h4h8"}
            move, lines = s.search(f"position fen {fen}", "go depth 8")
            scores = [re.search(r" score (cp -?\d+|mate -?\d+)", row) for row in lines if row.startswith("info depth 8 ")]
            assert move in winning and scores and (scores[-1][1] == "cp 31870" or scores[-1][1].startswith("mate ")), lines
            assert s.setoption("SyzygyPath", "<empty>") == ["info string Syzygy tablebases off"]
            values["syzygy"] = {"summary": summary[0], "KQvK": [move, scores[-1][1]]}
            s.ok(f"SyzygyPath {syzygy}: tables load, KQvK reports a tablebase win ({scores[-1][1]}) with a winning move")
        else:
            print("SKIP: real tablebase check (no --syzygy and no FORGE_SYZYGY_PATH)")
    finally:
        s.e.close()
    return {"passed": s.passed, "values": values}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--syzygy", default=os.environ.get("FORGE_SYZYGY_PATH", ""))
    parser.add_argument("--workdir", type=Path, help="folder for the test files (default: a new temporary folder)")
    parser.add_argument("--log", type=Path, help="UCI transcript")
    args = parser.parse_args()
    workdir = args.workdir if args.workdir else Path(tempfile.mkdtemp(prefix="forge-r3-options-"))
    s = Session(args.engine)
    try:
        result = run(s, args.syzygy, workdir)
    finally:
        if args.log:
            args.log.parent.mkdir(parents=True, exist_ok=True)
            args.log.write_text("\n".join(s.e.transcript) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("PASS uci_options_regression")


if __name__ == "__main__":
    main()
