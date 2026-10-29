#!/usr/bin/env python3
"""Bounded native SmpV2 lifecycle regression; reuses the repository UCI driver."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from smp_uci_regression import Run, TIMEOUT  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    run = Run(args.engine, 1)
    e = run.e
    passed: list[str] = []
    error = None
    try:
        e.send("uci")
        uci = e.until(lambda line: line == "uciok", TIMEOUT)
        assert "option name SmpV2 type check default false" in uci, "SmpV2 not advertised OFF by default"
        e.send("setoption name OwnBook value false")
        e.send("setoption name Hash value 16")
        run.sync("initial options")
        for threads in (2, 3):
            e.send(f"setoption name Threads value {threads}")
            e.send("setoption name SmpV2 value true")
            e.send("setoption name SmpBestThread value true")
            e.send("setoption name SmpHelpersPastDepth value true")
            # Presets still own their six original options only. C++ regression additionally
            # verifies SmpV2's stored value survives each preset, including OFF.
            for preset in ("B1", "OFF"):
                e.send(f"setoption name BundlePreset value {preset}")
                run.sync(f"Threads {threads}, preset {preset}")
                run.go("position startpos", "go depth 5 searchmoves e2e4 d2d4")
                move, _ = run.answer("position startpos", "restricted SmpV2")
                assert move in {"e2e4", "d2d4"}, move
            passed.append(f"Threads {threads}: SmpV2 + older SMP switches, presets, restricted root")

            mate = "position fen 7k/8/5KQ1/8/8/8/8/8 w - - 0 1"
            run.go(mate, "go mate 1 searchmoves g6g7")
            lines = e.until(lambda line: line.startswith("bestmove "), TIMEOUT)
            assert lines[-1].split()[1] == "g6g7", lines
            score_lines = [line for line in lines if line.startswith("info depth ") and " pv " in line]
            assert score_lines and "score mate 1" in score_lines[-1], lines
            assert score_lines[-1].split(" pv ", 1)[1].split()[0] == "g6g7", lines
            run.stats["bestmove"] += 1
            run.sync("mate search")
            e.assert_absent(lambda line: line.startswith("bestmove"), 0.05)
            assert not run.legal(run.after(mate, "g6g7")), "expected checkmating fixture"
            passed.append(f"Threads {threads}: mate score and PV remain coherent")

            for value in ("false", "true"):
                run.go("position startpos", "go infinite")
                e.until(lambda line: line.startswith("info depth 2 "), TIMEOUT)
                e.send(f"setoption name SmpV2 value {value}")
                run.answer("position startpos", f"setoption SmpV2 {value} stops and joins search")
                run.go("position startpos", "go depth 4 searchmoves e2e4")
                move, _ = run.answer("position startpos", "search after option toggle")
                assert move == "e2e4", move
            passed.append(f"Threads {threads}: live option toggles stop/join and next search works")

            e.send("position startpos")
            e.send("go depth 4 searchmoves a1a8")
            run.stats["go"] += 1
            lines = e.until(lambda line: line.startswith("bestmove "), TIMEOUT)
            assert lines[-1] == "bestmove 0000", lines
            run.stats["bestmove"] += 1
            assert not any("score mate" in line for line in lines), lines
            run.sync("empty restriction")
            passed.append(f"Threads {threads}: empty searchmoves remains authoritative")
        assert run.stats["go"] == run.stats["bestmove"], run.stats
        assert len([line for line in e.transcript if line.startswith("< bestmove ")]) == run.stats["bestmove"], run.stats
        assert not any("invalid value" in line or "unknown option" in line or "ERROR" in line for line in e.transcript), e.transcript
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            e.close()
        except Exception as exc:
            error = error or f"close: {type(exc).__name__}: {exc}"
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text("\n".join(e.transcript) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS" if error is None else "FAIL", "passed": passed,
                      "stats": run.stats, "error": error, "transcript": str(args.log)}, indent=2))
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
