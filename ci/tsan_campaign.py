"""ThreadSanitizer campaign: the command thread against the search threads (Opus session, 2026-11-15; from Fable's
job text HELPER_JOB2_deepseek.txt). Runs with an engine built with -fsanitize=thread.

Scenarios, in order of importance, each in its own engine process(es) with its own stderr file:
 S1  stop in mid-search: 300 x (position, go infinite, wait 5..200 ms, stop, bestmove)
 S2  changes between searches: 60 rounds of go depth 7, then in turn Threads 1/2/8/3/4, Hash 1/64/16,
     NNUEArch false, NNUEArch true, NNUEArchFile set again, ucinewgame; then isready
 S3  quit in mid-search: 40 fresh processes (go infinite, wait 20..300 ms, quit); a process still there after 10 s
     is a finding
 S4  ponder: Ponder true; 100 x (go ponder, wait 20..200 ms, ponderhit, 50 ms, stop) and 100 x (go ponder, wait, stop)
 S5  clock and limits: 200 x go movetime 40, 200 x go nodes 20000, 200 x go wtime 1500 btime 1500 winc 15 binc 15
 S6  MultiPV 4, go depth 8, 100 positions
 S7  Threads 8, go depth 10, 150 positions
Unless a scenario says otherwise: Threads 4, Hash 16, OwnBook false. Every scenario runs twice: all with the file net
(NNUEArchFile + NNUEArch true) first, then all with the built-in net (NNUEArch false). Waits come from
random.Random(20261118). Positions: the 500 of seed 20261115 (positions.py). Every bestmove is checked for
legality with python-chess. For S1 and S3 the evidence that the command met a running search is that the search was
"go infinite" (it cannot end by itself) and that its info lines had arrived before the command (counted).

    python tsan_campaign.py <tsan engine exe> <file net .fnn3> <results dir> [minutes, default 140]
Exit code: 0 = no finding; 1 = findings; 2 = the check itself failed.
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import positions as pos  # noqa: E402
from uci import Engine  # noqa: E402

BASE = {"OwnBook": "false", "Threads": "4", "Hash": "16"}
# FORGE_CI_SCALE (default 1) shrinks every repetition count, for a quick trial of the scripts themselves.
SCALE = float(os.environ.get("FORGE_CI_SCALE", "1"))


def n(x: int) -> int:
    return max(1, round(x * SCALE))


def is_legal(fen: str, bm: str | None) -> bool:
    b = chess.Board(fen)
    if bm in (None, "", "0000", "(none)"):
        return not any(True for _ in b.legal_moves)
    try:
        return chess.Move.from_uci(bm) in b.legal_moves
    except ValueError:
        return False


def tsan_count(path: str) -> int:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().count("WARNING: ThreadSanitizer:")
    except OSError:
        return 0


class Scenario:
    def __init__(self, res: str, name: str, net: str, exe: str, netfile: str):
        self.res, self.name, self.net, self.exe, self.netfile = res, name, net, exe, netfile
        self.stderr = os.path.join(res, f"stderr_{name}_{net}.txt")
        self.reps = self.no_bestmove = self.illegal = 0
        self.notes: list[str] = []
        self.exit_codes: list = []
        self.transcript: list[str] = []
        self.t0 = time.time()

    def options(self, extra: dict | None = None) -> dict:
        o = dict(BASE)
        o["NNUEArchFile"] = self.netfile
        o["NNUEArch"] = "true" if self.net == "file" else "false"
        o.update(extra or {})
        return o

    def start(self, extra: dict | None = None) -> Engine | None:
        e = Engine(self.exe, self.stderr)
        if not e.start_uci(self.options(extra), timeout=60):
            self.notes.append("engine did not answer uci/isready")
            self.finish(e)
            return None
        return e

    def finish(self, e: Engine, timeout: float = 30.0) -> None:
        if e.alive():
            rc, secs = e.quit(timeout)
            if rc is None:
                self.notes.append(f"the engine did not end within {timeout} s after quit")
        else:
            rc = e.p.returncode
            self.notes.append(f"the engine had ended by itself, exit code {rc}")
        self.exit_codes.append(rc)
        try:
            e.err.close()
        except OSError:
            pass
        self.transcript += e.transcript

    def bestmove(self, e: Engine, fen: str, timeout: float) -> str | None:
        ok, lines = e.wait_for("bestmove", timeout)
        if not ok:
            self.no_bestmove += 1
            self.notes.append(f"no bestmove within {timeout} s ({fen})")
            return None
        parts = lines[-1].split()
        bm = parts[1] if len(parts) > 1 else None
        if not is_legal(fen, bm):
            self.illegal += 1
            self.notes.append(f"illegal or missing move '{bm}' in {fen}")
        return bm

    def row(self) -> dict:
        return {"scenario": self.name, "net": self.net, "repetitions": self.reps, "exit_codes": self.exit_codes,
                "seconds": round(time.time() - self.t0, 1), "tsan_reports": tsan_count(self.stderr),
                "no_bestmove": self.no_bestmove, "illegal": self.illegal, "notes": self.notes[:50]}


def s1(sc: Scenario, fens, rng) -> None:
    e = sc.start()
    if not e:
        return
    met = 0
    for i in range(n(300)):
        fen = fens[i % len(fens)]
        e.send(f"position fen {fen}")
        e.send("go infinite")
        time.sleep(rng.uniform(0.005, 0.2))
        before = e.pending()
        if any(x.startswith("info") for x in before):
            met += 1
        e.send("stop")
        sc.bestmove(e, fen, 30.0)
        sc.reps += 1
        if not e.alive():
            break
    sc.notes.append(f"evidence: info lines had arrived before the stop in {met} of {sc.reps} searches (go infinite)")
    sc.finish(e)


def s2(sc: Scenario, fens, rng) -> None:
    e = sc.start()
    if not e:
        return
    changes = [("Threads", "1"), ("Threads", "2"), ("Threads", "8"), ("Threads", "3"), ("Threads", "4"),
               ("Hash", "1"), ("Hash", "64"), ("Hash", "16"), ("NNUEArch", "false"), ("NNUEArch", "true"),
               ("NNUEArchFile", sc.netfile), ("ucinewgame", None)]
    for r in range(n(60)):
        fen = fens[(r * 7) % len(fens)]
        e.send(f"position fen {fen}")
        e.send("go depth 7")
        sc.bestmove(e, fen, 180.0)
        name, value = changes[r % len(changes)]
        e.send("ucinewgame" if value is None else f"setoption name {name} value {value}")
        ok, secs = e.ready(60.0)
        if not ok:
            sc.notes.append(f"round {r + 1}: no readyok within 60 s after {name} {value or ''}")
        sc.reps += 1
        if not e.alive():
            break
    sc.finish(e)


def s3(sc: Scenario, fens, rng) -> None:
    slow, met = 0, 0
    for i in range(n(40)):
        e = sc.start()
        if not e:
            continue
        fen = fens[(i * 11) % len(fens)]
        e.send(f"position fen {fen}")
        e.send("go infinite")
        time.sleep(rng.uniform(0.02, 0.3))
        if any(x.startswith("info") for x in e.pending()):
            met += 1
        t = time.time()
        rc, secs = e.quit(10.0)
        if rc is None:
            slow += 1
            sc.notes.append(f"process {i + 1}: still there 10 s after quit; killed")
        sc.exit_codes.append(rc)
        try:
            e.err.close()
        except OSError:
            pass
        sc.transcript += e.transcript
        sc.reps += 1
    sc.notes.append(f"evidence: info lines had arrived before the quit in {met} of {sc.reps} processes (go infinite)")


def s4(sc: Scenario, fens, rng) -> None:
    e = sc.start({"Ponder": "true"})
    if not e:
        return
    half = n(100)
    for i in range(2 * half):
        fen = fens[(i * 3) % len(fens)]
        e.send(f"position fen {fen}")
        e.send("go ponder wtime 60000 btime 60000")
        time.sleep(rng.uniform(0.02, 0.2))
        if i < half:
            e.send("ponderhit")
            time.sleep(0.05)
        e.send("stop")
        sc.bestmove(e, fen, 30.0)
        sc.reps += 1
        if not e.alive():
            break
    sc.finish(e)


def s5(sc: Scenario, fens, rng) -> None:
    e = sc.start()
    if not e:
        return
    for i, go in enumerate(["go movetime 40"] * n(200) + ["go nodes 20000"] * n(200)
                           + ["go wtime 1500 btime 1500 winc 15 binc 15"] * n(200)):
        fen = fens[(i * 5) % len(fens)]
        e.send(f"position fen {fen}")
        e.send(go)
        sc.bestmove(e, fen, 60.0)
        sc.reps += 1
        if not e.alive():
            break
    sc.finish(e)


def s6(sc: Scenario, fens, rng) -> None:
    e = sc.start({"MultiPV": "4"})
    if not e:
        return
    for i in range(n(100)):
        fen = fens[(i * 13) % len(fens)]
        e.send(f"position fen {fen}")
        e.send("go depth 8")
        sc.bestmove(e, fen, 180.0)
        sc.reps += 1
        if not e.alive():
            break
    sc.finish(e)


def s7(sc: Scenario, fens, rng) -> None:
    e = sc.start({"Threads": "8"})
    if not e:
        return
    for i in range(n(150)):
        fen = fens[(i * 17) % len(fens)]
        e.send(f"position fen {fen}")
        e.send("go depth 10")
        sc.bestmove(e, fen, 300.0)
        sc.reps += 1
        if not e.alive():
            break
    sc.finish(e)


SCENARIOS = [("S1", s1), ("S2", s2), ("S3", s3), ("S4", s4), ("S5", s5), ("S6", s6), ("S7", s7)]


def main() -> int:
    exe, netfile, res = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]
    minutes = float(sys.argv[4]) if len(sys.argv) > 4 else 140.0
    os.makedirs(res, exist_ok=True)
    fens, _ = pos.generate(20261115, 8, 60, 500)
    rng = random.Random(20261118)
    t_all = time.time()
    rows, not_done = [], []
    for net in ("file", "builtin"):
        for name, fn in SCENARIOS:
            if time.time() - t_all > minutes * 60:
                not_done.append(f"{name} {net}")
                continue
            sc = Scenario(res, name, net, exe, netfile)
            try:
                fn(sc, fens, rng)
            except Exception as ex:  # noqa: BLE001 - a broken scenario is reported, the others still run
                sc.notes.append(f"the scenario script failed: {type(ex).__name__}: {ex}")
            rows.append(sc.row())
            with open(os.path.join(res, f"transcript_{name}_{net}.txt"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(sc.transcript) + "\n")
            print(f"{name} {net}: {rows[-1]['repetitions']} repetitions, {rows[-1]['tsan_reports']} TSan reports, "
                  f"{rows[-1]['seconds']} s", flush=True)
    stderr_files = [os.path.join(res, f) for f in sorted(os.listdir(res)) if f.startswith("stderr_")]
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tsan_group.py"),
                    os.path.join(res, "tsan_groups.txt"), *stderr_files], check=False)
    findings = []
    for r in rows:
        if r["tsan_reports"]:
            findings.append(f"{r['scenario']} {r['net']}: {r['tsan_reports']} ThreadSanitizer reports")
        if r["no_bestmove"] or r["illegal"]:
            findings.append(f"{r['scenario']} {r['net']}: {r['no_bestmove']} searches without bestmove, "
                            f"{r['illegal']} illegal moves")
        bad_exit = [c for c in r["exit_codes"] if c not in (0,)]
        if bad_exit:
            findings.append(f"{r['scenario']} {r['net']}: exit codes {bad_exit}")
        findings += [f"{r['scenario']} {r['net']}: {n}" for n in r["notes"] if "still there" in n or "failed" in n]
    lines = [f"ThreadSanitizer campaign: {len(rows)} scenario runs in {(time.time() - t_all) / 60:.1f} minutes "
             f"(limit {minutes:.0f}); not done: {', '.join(not_done) if not_done else 'none'}", ""]
    lines.append("scenario | net | repetitions | exit codes | seconds | TSan reports | no bestmove | illegal")
    for r in rows:
        codes = sorted(set(map(str, r["exit_codes"])))
        lines.append(f"{r['scenario']} | {r['net']} | {r['repetitions']} | {','.join(codes)} | {r['seconds']} | "
                     f"{r['tsan_reports']} | {r['no_bestmove']} | {r['illegal']}")
        lines += [f"     note: {n}" for n in r["notes"][:8]]
    lines += ["", "FINDINGS: " + ("none" if not findings and not not_done else str(len(findings)))]
    lines += ["  " + f for f in findings]
    lines += ["", "Groups of ThreadSanitizer reports: tsan_groups.txt"]
    with open(os.path.join(res, "summary.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(res, "results.json"), "w", encoding="utf-8") as fh:
        json.dump({"rows": rows, "not_done": not_done}, fh, indent=1)
    print("\n".join(lines))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
