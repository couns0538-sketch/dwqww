#!/usr/bin/env python3
"""B2: real UCI clock/ponder lifecycle with TmSoftHardClamp, not a timing benchmark."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from smp_uci_regression import Run, TIMEOUT  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("engine", type=Path)
    p.add_argument("--log", required=True, type=Path)
    args = p.parse_args()
    run = Run(args.engine, 1)
    e = run.e
    passed = []
    error = None
    try:
        e.send("uci")
        advertised = e.until(lambda line: line == "uciok", TIMEOUT)
        assert "option name TmSoftHardClamp type check default false" in advertised
        e.send("setoption name TmSoftHardClamp value invalid")
        assert "info string invalid value for option TmSoftHardClamp" in e.until(lambda line: "invalid value" in line)
        e.send("setoption name Hash value 16")
        e.send("setoption name OwnBook value false")
        e.send("setoption name Ponder value true")
        e.send("setoption name TmSoftHardClamp value true")
        run.sync("initial settings")
        for threads in (1, 2):
            e.send(f"setoption name Threads value {threads}")
            e.send("setoption name BundlePreset value B1")
            e.send("setoption name BundlePreset value OFF")
            run.sync("preset and threads")
            for clock in ("wtime 100 btime 100 winc 10000 binc 10000",
                          "wtime 1 btime 1 winc 10000 binc 10000",
                          "wtime 100 btime 100 winc 10000 binc 10000 movestogo 1"):
                run.go("position startpos", "go " + clock)
                run.answer("position startpos", f"Threads {threads} clock {clock}")
            passed.append(f"Threads {threads}: large increment, tiny time, movestogo 1 return one legal move")
            # Before ponderhit the 100 ms clock must not expire. The 150 ms
            # absence window tests that lifecycle rule, not scheduler precision.
            run.go("position startpos", "go ponder wtime 100 btime 100 winc 10000 binc 10000")
            e.until(lambda line: line.startswith("info depth "), TIMEOUT)
            run.wait_without_bestmove(0.15, "clock cannot expire before ponderhit")
            run.sync("ponder isready")
            since = time.monotonic()
            e.send("ponderhit")
            run.answer("position startpos", "ponderhit with large increment", since,
                       "max_ponderhit_latency_s")
            passed.append(f"Threads {threads}: clock starts on ponderhit, no premature or duplicate answer")
            run.go("position startpos", "go ponder wtime 1 btime 1 winc 10000 binc 10000")
            e.send("ponderhit")
            run.answer("position startpos", "immediate ponderhit tiny clock")
            passed.append(f"Threads {threads}: immediate ponderhit tiny clock")
            # setoption must quiesce workers before writing requested options.
            for value in ("false", "true"):
                run.go("position startpos", "go infinite")
                e.until(lambda line: line.startswith("info depth 2 "), TIMEOUT)
                e.send(f"setoption name TmSoftHardClamp value {value}")
                run.answer("position startpos", "option change stops and joins")
                run.go("position startpos", "go depth 4 searchmoves e2e4")
                move, _ = run.answer("position startpos", "search after option change")
                assert move == "e2e4"
            passed.append(f"Threads {threads}: option OFF/ON transitions stop and join cleanly")
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
                      "stats": run.stats, "error": error}, indent=2))
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
