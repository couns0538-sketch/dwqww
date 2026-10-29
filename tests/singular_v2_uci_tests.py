#!/usr/bin/env python3
"""Native SingularV2 advertisement, exclusivity and N1 equivalence regression."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from uci_regression import Engine


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    engine = Engine(args.engine)
    checks: list[str] = []
    benches: list[dict] = []
    error = None
    def check(ok: bool, name: str) -> None:
        if not ok:
            raise AssertionError(name)
        checks.append(name)
    def option(name: str, value: str) -> list[str]:
        engine.send(f"setoption name {name} value {value}")
        engine.send("isready")
        return engine.until(lambda line: line == "readyok", 120)
    def bench(label: str) -> int:
        engine.send("bench 11")
        lines = engine.until(lambda line: line.startswith("info string bench depth "), 120)
        matches = [re.fullmatch(r"info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", line) for line in lines]
        records = [match for match in matches if match is not None]
        check(len(records) == 1 and int(records[0][1]) == 11, label + ": complete bench record")
        record = records[0]
        benches.append({"label": label, "depth": 11, "nodes": int(record[2]), "time_ms": int(record[3]), "nps": int(record[4])})
        return int(record[2])
    try:
        engine.send("uci")
        lines = engine.until(lambda line: line == "uciok", 120)
        check("option name SingularV2 type spin default 0 min 0 max 1" in lines, "SingularV2 is advertised default 0")
        preset = [line for line in lines if line.startswith("option name BundlePreset ")]
        check(len(preset) == 1 and " var N1" in preset[0], "BundlePreset advertises N1")
        option("Threads", "1"); option("Hash", "16"); option("OwnBook", "false")
        option("BundlePreset", "OFF"); option("CorrExt", "0")
        off = bench("OFF")
        check(off == 312866, "OFF d11 matches pinned baseline")
        option("CorrHistPlus", "4"); option("SingularV2", "1")
        manual = bench("manual_N1")
        option("BundlePreset", "OFF")
        check(bench("OFF_after_manual") == off, "OFF resets SingularV2 and all preset-owned options")
        reply = option("BundlePreset", "N1")
        check(any("BundlePreset N1:" in line and "CorrHistPlus=4" in line and "SingularV2=1" in line for line in reply), "N1 acknowledgement identifies both options")
        check(bench("preset_N1") == manual, "N1 equals explicit CorrHistPlus4 + SingularV2")
        check(manual != off, "N1 changes the search tree (not a strength claim)")
        reply = option("CorrExt", "1")
        check(any("CorrExt refused" in line for line in reply), "CorrExt refused while SingularV2 active")
        check(bench("N1_after_refused_CorrExt") == manual, "refused CorrExt leaves N1 intact")
        for value in ("2", "-1", "true", "1x"):
            reply = option("SingularV2", value)
            check(any("invalid value for option SingularV2" in line for line in reply), "invalid SingularV2 value rejected: " + value)
        check(bench("N1_after_invalid_values") == manual, "invalid values leave SingularV2 intact")
        option("BundlePreset", "B1"); option("CorrExt", "1")
        before = bench("B1_CorrExt")
        reply = option("SingularV2", "1")
        check(any("SingularV2 refused" in line for line in reply), "SingularV2 refused while CorrExt active")
        reply = option("BundlePreset", "N1")
        check(any("BundlePreset N1 refused" in line for line in reply), "N1 refuses incompatible CorrExt before mutation")
        check(bench("B1_CorrExt_after_refusals") == before, "refused N1 leaves every preset-owned option intact")
        option("CorrExt", "0"); option("BundlePreset", "OFF")
        check(bench("final_OFF") == off, "final OFF restores pinned search")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            engine.close()
        except Exception as exc:
            error = error or f"close: {type(exc).__name__}: {exc}"
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text("\n".join(engine.transcript) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS" if error is None else "FAIL", "checks": checks, "benches": benches, "error": error}, indent=2))
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
