#!/usr/bin/env python3
"""Long mixed workload for the forge engine under a sanitizer build.

Design decisions that exist because of traps this audit already paid for:

* One engine PROCESS PER PHASE, and every process is drained to EOF before its
  verdict is recorded. A sanitizer that reports at exit (LeakSanitizer, a
  static destructor, an atexit handler) prints after `bestmove` and after
  `quit`; a harness that stops reading at `bestmove` or that kills the child
  records a clean zero for it. Draining is the only way to see those.
* Evidence is checkpointed after every phase, so a long run that is cut short
  still yields attributable rows instead of nothing.
* Every probe is bounded. A watchdog sends `stop` (never `quit`) and the phase
  process is killed if it still will not answer. Nothing is piped into a live
  search.

Usage: workload.py <exe> <outdir> [--quick] [--phases a,b,c] [--time-cap SECONDS]
"""
import json
import os
import re
import signal
import sys
import time

sys.path.insert(0, "/tmp/forge")
from driver import Engine  # noqa: E402

SAN_PAT = re.compile(
    r"(runtime error:|AddressSanitizer|UndefinedBehaviorSanitizer|SUMMARY: |"
    r"ERROR: LeakSanitizer|LeakSanitizer|SEGV|stack-overflow|DEADLYSIGNAL)")
INFO_NODES = re.compile(r"^info depth (\d+).*?nodes (\d+)")
EXIT_MARKERS = ("runtime error:", "AddressSanitizer", "LeakSanitizer", "SUMMARY:")


def esc(s):
    return s.encode("unicode_escape").decode("ascii")


class Phase:
    """One engine process, one phase of the workload, drained to EOF."""

    def __init__(self, exe, outdir, env, name):
        self.name = name
        self.exe = exe
        self.outdir = outdir
        self.probes = []
        self.san = []
        self.stream = []
        self.restarts = 0
        self.e = Engine(exe, env_extra=env, cwd=outdir)
        ls, tok = self.e.cmd("uci", ("uciok",), 180)
        self.record(ls)
        if tok != "uciok":
            raise RuntimeError(f"{name}: uci handshake failed ({tok})")
        self.record(self.e.cmd("isready", ("readyok",), 180)[0])

    def record(self, lines):
        for ln in lines:
            self.stream.append(ln)
            if SAN_PAT.search(ln):
                self.san.append(esc(ln))

    def alive(self):
        return self.e.p.poll() is None

    def restart(self, reason):
        if self.alive():
            try:
                self.e.p.kill()
            except Exception:
                pass
        self.restarts += 1
        self.e = Engine(self.exe, env_extra=self.e.env if hasattr(self.e, "env") else None,
                        cwd=self.outdir)
        self.e.cmd("uci", ("uciok",), 180)
        self.e.cmd("isready", ("readyok",), 180)

    def probe(self, label, cmd, timeout_s, tokens=("bestmove",)):
        if not self.alive():
            self.restart("dead before probe")
        t0 = time.monotonic()
        out, tok = self.e.cmd(cmd, tokens, timeout_s)
        if tok is not None and tok != "EOF":
            # The terminating line often arrives together with more output, and
            # the remainder may still be in flight. Drain briefly so the
            # evidence holds the terminating line itself (`nodes N`, the bench
            # signature, `info string eval`) and not just what preceded it.
            out += self.e.read_until(("\x00never\x00",), 0.25)[0]
        self.record(out)
        wd = False
        if tok is None:
            wd = True
            o2, tok = self.e.cmd("stop", tokens, 25.0)
            self.record(o2)
            out += o2
        dt = time.monotonic() - t0
        rc = self.e.p.poll()
        depth = nodes = None
        for l in out:
            m = INFO_NODES.match(l)
            if m:
                depth, nodes = int(m.group(1)), int(m.group(2))
        res = {
            "phase": self.name, "probe": label, "cmd": cmd,
            "answered": tok is not None and tok != "EOF", "token": tok,
            "watchdog_stop_sent": wd, "seconds": round(dt, 2),
            "exit_code_after": rc, "process_dead": rc is not None,
            "san_lines": [esc(l) for l in out if SAN_PAT.search(l)],
            "bestmove": next((l for l in out if l.startswith("bestmove")), None),
            "info_count": sum(1 for l in out if l.startswith("info ")),
            "last_depth": depth, "last_nodes": nodes,
            "node_line": next((l for l in out if l.startswith("nodes ")), None),
            # bench prints `info string bench depth D nodes N ...`, which is not
            # an `info depth D ... nodes N` search line; capture it separately so
            # a bench probe can be checked for a node count at all.
            "bench_line": next((l for l in out if l.startswith("info string bench depth")), None),
            "eval_line": next((l for l in out if l.startswith("info string eval")), None),
            "book_line": next((l for l in out if "book move" in l), None),
            "refused": [esc(l) for l in out if "invalid FEN" in l or "illegal move" in l],
        }
        rec = res
        if rc is not None:
            rec["tail"] = [esc(l) for l in self.e.log[-10:]]
            self.restart("died during probe")
            rec["restarted"] = True
        self.probes.append(rec)
        return rec

    def position(self, label, fen):
        """Set the position and wait for an isready ack.

        `position` emits no reply, so the only deterministic barrier is
        `isready`/`readyok`; sleeping for a fixed interval is both slower and
        weaker (it can still race a slow parse, and it wastes the interval on a
        fast one).
        """
        if not self.alive():
            self.restart("dead before position")
        self.e.send(f"position fen {fen}")
        self.e.send("isready")
        out, tok = self.e.read_until(("readyok",), 30.0)
        self.record(out)
        self.probes.append({"phase": self.name, "probe": label, "cmd": "position+isready",
                            "lines": len(out), "acked": tok == "readyok",
                            "san_lines": [esc(l) for l in out if SAN_PAT.search(l)]})
        return out

    def position_moves(self, label, moves):
        if not self.alive():
            self.restart("dead before position")
        cmd = "position startpos" if not moves else f"position startpos moves {moves}"
        self.e.send(cmd)
        self.e.send("isready")
        out, tok = self.e.read_until(("readyok",), 30.0)
        self.record(out)
        self.probes.append({"phase": self.name, "probe": label, "cmd": "position moves+isready",
                            "lines": len(out), "acked": tok == "readyok",
                            "san_lines": [esc(l) for l in out if SAN_PAT.search(l)]})
        return out

    def raw(self, label, cmd, wait_s, tokens=("\x00never\x00",)):
        if not self.alive():
            self.restart("dead before raw")
        self.e.send(cmd)
        out, tok = self.e.read_until(tokens, wait_s)
        self.record(out)
        self.probes.append({"phase": self.name, "probe": label, "cmd": cmd,
                            "lines": len(out),
                            "eval_line": next((l for l in out if l.startswith("info string eval")), None),
                            "bench_line": next((l for l in out if l.startswith("info string bench depth")), None),
                            "san_lines": [esc(l) for l in out if SAN_PAT.search(l)]})
        return out

    def setopt(self, name, value):
        self.raw(f"opt {name}={value}", f"setoption name {name} value {value}", 1.5)
        self.raw(f"isready {name}", "isready", 5.0, ("readyok",))

    def drain_and_close(self, grace=25.0):
        """Send quit, then read to EOF. This is where exit-time reports appear."""
        exit_report = []
        rc = None
        if self.alive():
            try:
                self.e.send("quit")
            except Exception:
                pass
            # read everything that comes after quit, including at-exit reports
            out, tok = self.e.read_until(("\x00never\x00",), grace)
            self.record(out)
            exit_report = [esc(l) for l in out if SAN_PAT.search(l)]
            try:
                rc = self.e.p.wait(timeout=grace)
            except Exception:
                self.e.p.kill()
                rc = self.e.p.poll()
                exit_report.append("KILLED_AFTER_QUIT")
            tail, _ = self.e.read_until(("\x00never\x00",), 2.0)
            self.record(tail)
            exit_report += [esc(l) for l in tail if SAN_PAT.search(l)]
        else:
            rc = self.e.p.poll()
            tail, _ = self.e.read_until(("\x00never\x00",), 2.0)
            self.record(tail)
            exit_report = [esc(l) for l in tail if SAN_PAT.search(l)]
        return {"exit_code": rc, "at_exit_san_lines": exit_report,
                "drained_to_eof": True, "sanitizer_lines_total": len(self.san),
                "restarts": self.restarts, "probe_count": len(self.probes)}

    def summary(self):
        return {
            "phase": self.name, "probes": self.probes,
            "sanitizer_lines": [esc(l) for l in self.san],
            "stream_lines": len(self.stream),
        }


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    quick = "--quick" in sys.argv
    only = None
    cap = None
    for i, a in enumerate(sys.argv):
        if a == "--phases":
            only = set(sys.argv[i + 1].split(","))
        if a == "--time-cap":
            cap = float(sys.argv[i + 1])
    os.makedirs(outdir, exist_ok=True)
    positions = json.load(open("/tmp/forge/positions.json"))
    stress = json.load(open("/tmp/forge/stress_positions.json"))
    mates = json.load(open("/tmp/forge/mate_positions.json"))
    if quick:
        positions, stress, mates = positions[:10], stress[:3], mates[:2]
    d_lo = 6 if quick else 12

    env = dict(os.environ)
    env.update({
        "UBSAN_OPTIONS": "print_stacktrace=1:halt_on_error=0:report_error_type=1",
        "ASAN_OPTIONS": "detect_leaks=1:abort_on_error=1:detect_stack_use_after_return=1",
    })

    t_start = time.monotonic()
    results = {"exe": exe, "quick": quick, "env": {k: env[k] for k in ("UBSAN_OPTIONS", "ASAN_OPTIONS")},
               "phases": {}, "order": []}

    def save():
        with open(os.path.join(outdir, "workload.json"), "w") as fh:
            json.dump(results, fh, indent=1)

    def run_phase(name, body):
        if only and name not in only:
            return
        if cap and time.monotonic() - t_start > cap:
            print(f"SKIP {name} (time cap)")
            return
        print(f"=== phase {name}", flush=True)
        p = Phase(exe, outdir, env, name)
        try:
            body(p)
        except Exception as exc:  # noqa: BLE001
            results.setdefault("phase_errors", {})[name] = repr(exc)
        close = p.drain_and_close()
        rec = p.summary()
        rec["close"] = close
        results["phases"][name] = rec
        results["order"].append(name)
        save()
        with open(os.path.join(outdir, f"stream-{name}.log"), "w") as fh:
            for ln in p.stream:
                fh.write(esc(ln) + "\n")
        print(json.dumps({"phase": name, "probes": len(p.probes),
                          "san": len(p.san), "exit": close["exit_code"],
                          "at_exit_san": len(close["at_exit_san_lines"])}), flush=True)

    def ph_pins(p):
        for d in (11, 13, 16):
            p.probe(f"bench {d} neton", f"bench {d}", 3600, ("info string bench depth",))
        p.setopt("UseNNUE", "false")
        for d in (11, 13, 16):
            p.probe(f"bench {d} netoff", f"bench {d}", 3600, ("info string bench depth",))

    def ph_perft(p):
        p.position_moves("startpos", "")
        p.probe("perft 5 startpos", "go perft 5", 1800, ("nodes ",))
        for i, q in enumerate(positions[:24]):
            p.position(f"pos{i}", q["fen"])
            p.probe(f"perft4 pos{i}", "go perft 4", 600, ("nodes ",))

    def ph_depth(p):
        for mpv in (1, 2, 4):
            p.setopt("MultiPV", str(mpv))
            for i, q in enumerate(positions):
                p.position(f"pos{i}", q["fen"])
                p.probe(f"depth{d_lo} mpv{mpv} pos{i}", f"go depth {d_lo}", 300)

    def ph_deep(p):
        p.setopt("MultiPV", "1")
        d = 10 if quick else 16
        for i, q in enumerate(positions[: (4 if quick else 20)]):
            p.position(f"pos{i}", q["fen"])
            p.probe(f"depth{d} pos{i}", f"go depth {d}", 900)

    def ph_netoff(p):
        p.setopt("UseNNUE", "false")
        for i, q in enumerate(positions[: (4 if quick else 60)]):
            p.position(f"pos{i}", q["fen"])
            p.probe(f"depth{d_lo} netoff pos{i}", f"go depth {d_lo}", 300)
            p.raw(f"eval pos{i}", "eval", 5.0, ("info string eval",))

    def ph_eval(p):
        for i, q in enumerate(positions):
            p.position(f"pos{i}", q["fen"])
            p.raw(f"eval pos{i}", "eval", 5.0, ("info string eval",))

    def ph_mate(p):
        for i, q in enumerate(mates):
            p.position(f"matepos{i}", q["fen"])
            for n in (1, 2, 3, 5):
                p.probe(f"go mate {n} matepos{i}", f"go mate {n}", 120)

    def ph_book(p):
        p.position_moves("startpos", "")
        for own in ("true", "false"):
            p.setopt("OwnBook", own)
            for variety in (0, 30, 100):
                p.setopt("Book Variety", str(variety))
                for k in range(2):
                    p.position_moves("startpos", "")
                    p.probe(f"book own{own} var{variety} k{k}", "go movetime 250", 60)
        p.setopt("OwnBook", "true")
        p.setopt("Book Variety", "30")
        p.position_moves("startpos", "")
        p.probe("clocks wtime/btime/winc", "go wtime 60000 btime 60000 winc 1000 binc 1000", 60)
        p.probe("clocks movestogo", "go wtime 60000 btime 60000 movestogo 20", 60)
        for seq in ("e2e4", "e2e4 e7e5", "d2d4 d7d5 c2c4"):
            p.position_moves(f"seq {seq}", seq)
            p.probe(f"book seq {seq}", "go movetime 250", 60)

    def ph_stress(p):
        for i, q in enumerate(stress):
            p.position(f"stress{i}", q["fen"])
            p.raw(f"eval stress{i}", "eval", 5.0, ("info string eval",))
            p.probe(f"depth13 stress{i}", "go depth 13", 400)
            p.probe(f"perft3 stress{i}", "go perft 3", 600, ("nodes ",))

    def ph_stress_netoff(p):
        p.setopt("UseNNUE", "false")
        for i, q in enumerate(stress):
            p.position(f"stress{i}", q["fen"])
            p.raw(f"eval stress{i}", "eval", 5.0, ("info string eval",))
            p.probe(f"depth12 stress{i} netoff", "go depth 12", 400)

    def ph_malformed(p):
        p.position_moves("startpos", "")
        forms = ["go nodes abc", "go mate abc", "go depth abc", "go movetime abc",
                 "go wtime abc btime def", "go searchmoves a1a2", "go perft 99",
                 "go depth 999999", "go nodes 100000000000000000000",
                 "go movetime -5", "go movestogo 0", "go mate 99", "go winc x",
                 "go depth", "go nodes", "go mate", "go movetime"]
        for form in forms:
            p.probe(f"malformed: {form}", form, 10.0)
        p.probe("go infinite", "go infinite", 6.0)
        p.probe("go ponder", "go ponder", 6.0)

    def ph_protocol(p):
        for form in ("position fen 8/8/8/8/8/8/8/8 w - - 0 1", "position fen bogus",
                     "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 extra",
                     "position fen 4k3/8/8/8/8/8/8/4K3 x - - 0 1",
                     "position startpos moves e2e4 e7e5 g1f3 b8c6",
                     "position startpos moves e2e4 a1a8",
                     "position startpos moves",
                     "ucinewgame"):
            p.raw(f"proto {form}", form, 2.0)
            p.probe(f"after {form}", "go depth 8", 120)
        p.probe("no position then go depth 12", "go depth 12", 180)

    phases = [
        ("pins", ph_pins), ("perft", ph_perft), ("depth", ph_depth),
        ("deep", ph_deep), ("netoff", ph_netoff), ("eval", ph_eval),
        ("mate", ph_mate), ("book", ph_book), ("stress", ph_stress),
        ("stress_netoff", ph_stress_netoff), ("malformed", ph_malformed),
        ("protocol", ph_protocol),
    ]
    for name, body in phases:
        run_phase(name, body)

    results["elapsed_s"] = round(time.monotonic() - t_start, 1)
    results["totals"] = {
        "probes": sum(len(v["probes"]) for v in results["phases"].values()),
        "sanitizer_lines": sum(len(v["sanitizer_lines"]) for v in results["phases"].values()),
        "at_exit_sanitizer_lines": sum(len(v["close"]["at_exit_san_lines"])
                                       for v in results["phases"].values()),
        "dead_probes": sum(1 for v in results["phases"].values()
                           for pr in v["probes"] if pr.get("process_dead")),
        "unanswered": sum(1 for v in results["phases"].values()
                          for pr in v["probes"] if pr.get("answered") is False),
        "watchdog_stops": sum(1 for v in results["phases"].values()
                              for pr in v["probes"] if pr.get("watchdog_stop_sent")),
        "phases": len(results["phases"]),
    }
    save()
    print(json.dumps(results["totals"], indent=1))


if __name__ == "__main__":
    main()
