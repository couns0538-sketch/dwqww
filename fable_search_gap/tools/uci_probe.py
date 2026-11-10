"""Small UCI driver for short, pinned probes of an unmodified Forge exe (standard library only).

Sub-commands
  pins   Check an exe against the combo29 lock pins: bench d11/13/16/20/22 with the net on and
         off, perft 5 on the start position and on kiwipete. Exit 0 only if every number matches.
  go     One search on one position (depth or node limit); records every info line and the bestmove.
  batch  The same search on every line of a FEN/EPD file; writes one JSON object per line.

Every run is on CPU 3-6 at Idle (tools/pinguard.py); start it through tools/pin.ps1.
The engine is never given a clock, a book or more than one thread, so results are deterministic.
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PINS_NET_ON = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
PINS_NET_OFF = {11: 375354, 13: 907205, 16: 2448617, 20: 13573040, 22: 24506465}
PERFT5 = {"startpos": 4865609, "kiwipete": 193690690}


class Engine:
    def __init__(self, exe: str, workdir: str, log_path: str | None = None):
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=workdir, text=True, bufsize=1, encoding="utf-8", errors="replace")
        self.q: queue.Queue = queue.Queue()
        self.log = open(log_path, "a", encoding="utf-8", newline="\n") if log_path else None
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.proc.stdout:
            self.q.put(line.rstrip("\r\n"))
        self.q.put(None)

    def send(self, line: str):
        if self.log:
            self.log.write(f"> {line}\n")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, prefix: str, timeout_s: float) -> list[str]:
        lines = []
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"no line starting with {prefix!r} within {timeout_s}s")
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError(f"no line starting with {prefix!r} within {timeout_s}s")
            if line is None:
                raise RuntimeError("engine closed its output")
            if self.log:
                self.log.write(f"< {line}\n")
            lines.append(line)
            if line.startswith(prefix):
                return lines

    def handshake(self, options: dict[str, str]):
        self.send("uci")
        self.read_until("uciok", 30)
        for name, value in options.items():
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
        self.read_until("readyok", 60)

    def close(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=20)
        except Exception:
            self.proc.kill()  # only ever our own child
        if self.log:
            self.log.close()


def base_options(extra: list[str] | None) -> dict[str, str]:
    opts = {"Threads": "1", "Hash": "16", "OwnBook": "false"}
    for item in extra or []:
        name, _, value = item.partition("=")
        opts[name.strip()] = value.strip()
    return opts


def parse_info(line: str) -> dict:
    tok = line.split()
    out: dict = {}
    i = 1
    while i < len(tok):
        t = tok[i]
        if t in ("depth", "seldepth", "nodes", "nps", "time", "hashfull", "multipv") and i + 1 < len(tok):
            try:
                out[t] = int(tok[i + 1])
            except ValueError:
                out[t] = tok[i + 1]
            i += 2
        elif t == "score" and i + 2 < len(tok):
            out["score_kind"] = tok[i + 1]
            out["score"] = int(tok[i + 2])
            i += 3
            if i < len(tok) and tok[i] in ("lowerbound", "upperbound"):
                out["bound"] = tok[i]
                i += 1
        elif t == "pv":
            out["pv"] = tok[i + 1:]
            break
        else:
            i += 1
    return out


def run_go(eng: Engine, fen: str, moves: str, limit: str, timeout_s: float) -> dict:
    eng.send("ucinewgame")
    pos = "position startpos" if fen == "startpos" else f"position fen {fen}"
    if moves:
        pos += f" moves {moves}"
    eng.send(pos)
    eng.send("isready")
    eng.read_until("readyok", 60)
    t0 = time.monotonic()
    eng.send(f"go {limit}")
    lines = eng.read_until("bestmove", timeout_s)
    wall = time.monotonic() - t0
    infos = [parse_info(x) for x in lines if x.startswith("info ") and " pv " in x + " "]
    infos = [x for x in infos if "depth" in x]
    strings = [x for x in lines if x.startswith("info string")]
    best = lines[-1].split()
    return {"fen": fen, "moves": moves, "limit": limit, "bestmove": best[1] if len(best) > 1 else None,
            "final": infos[-1] if infos else None, "iterations": infos, "info_strings": strings,
            "wall_s": round(wall, 3)}


def cmd_pins(a) -> int:
    depths = [int(x) for x in a.depths.split(",")]
    result = {"exe": a.exe, "pin": pinguard.ensure(), "bench": {}, "perft5": {}, "ok": True}
    for label, use_net, pins in (("net_on", "true", PINS_NET_ON), ("net_off", "false", PINS_NET_OFF)):
        eng = Engine(a.exe, a.workdir, a.log)
        opts = base_options(None)
        opts["UseNNUE"] = use_net
        eng.handshake(opts)
        for d in depths:
            eng.send(f"bench {d}")
            line = eng.read_until("info string bench depth", 1800)[-1].split()
            nodes = int(line[line.index("nodes") + 1])
            nps = int(line[line.index("nps") + 1])
            good = nodes == pins[d]
            result["bench"][f"{label}_d{d}"] = {"nodes": nodes, "want": pins[d], "match": good, "nps": nps}
            result["ok"] &= good
            print(f"bench {label} d{d}: {nodes} want {pins[d]} {'OK' if good else 'MISMATCH'} ({nps} nps)", flush=True)
        eng.close()
    eng = Engine(a.exe, a.workdir, a.log)
    eng.handshake(base_options(None))
    for name, fen in (("startpos", "startpos"), ("kiwipete", KIWIPETE)):
        eng.send("position startpos" if fen == "startpos" else f"position fen {fen}")
        eng.send("go perft 5")
        nodes = int(eng.read_until("nodes ", 1800)[-1].split()[1])
        good = nodes == PERFT5[name]
        result["perft5"][name] = {"nodes": nodes, "want": PERFT5[name], "match": good}
        result["ok"] &= good
        print(f"perft5 {name}: {nodes} want {PERFT5[name]} {'OK' if good else 'MISMATCH'}", flush=True)
    eng.close()
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=1)
    print("PINS " + ("MATCH" if result["ok"] else "MISMATCH"), flush=True)
    return 0 if result["ok"] else 1


def cmd_go(a) -> int:
    print(pinguard.ensure(), flush=True)
    eng = Engine(a.exe, a.workdir, a.log)
    eng.handshake(base_options(a.setoption))
    res = run_go(eng, a.fen, a.moves, a.limit, a.timeout)
    eng.close()
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    fin = res["final"] or {}
    print(f"bestmove {res['bestmove']} depth {fin.get('depth')} score {fin.get('score_kind')} {fin.get('score')} "
          f"nodes {fin.get('nodes')} pv {' '.join((fin.get('pv') or [])[:8])}", flush=True)
    return 0


def cmd_batch(a) -> int:
    print(pinguard.ensure(), flush=True)
    eng = Engine(a.exe, a.workdir, a.log)
    eng.handshake(base_options(a.setoption))
    n = 0
    with open(a.epd, encoding="utf-8") as src, open(a.out, "w", encoding="utf-8", newline="\n") as dst:
        for raw in src:
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            head, _, tag = raw.partition(";")
            fields = head.split()
            fen = " ".join(fields[:6]) if len(fields) >= 6 else " ".join(fields[:4]) + " 0 1"
            res = run_go(eng, fen, "", a.limit, a.timeout)
            res["tag"] = tag.strip()
            if not a.keep_iterations:
                res.pop("iterations", None)
            dst.write(json.dumps(res) + "\n")
            dst.flush()
            n += 1
            fin = res["final"] or {}
            print(f"{n}: {res['bestmove']} d{fin.get('depth')} {fin.get('score_kind')} {fin.get('score')} "
                  f"n{fin.get('nodes')} | {res['tag'][:60]}", flush=True)
    eng.close()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("pins", "go", "batch"):
        s = sub.add_parser(name)
        s.add_argument("--exe", required=True)
        s.add_argument("--workdir", required=True, help="engine working directory (on D:)")
        s.add_argument("--out", required=True)
        s.add_argument("--log", default=None, help="append the raw UCI dialogue here")
        if name == "pins":
            s.add_argument("--depths", default="11,13,16,20,22")
        else:
            s.add_argument("--limit", required=True, help="text after 'go', e.g. 'depth 20' or 'nodes 2000000'")
            s.add_argument("--timeout", type=float, default=900)
            s.add_argument("--setoption", action="append", help="Name=Value, repeatable")
        if name == "go":
            s.add_argument("--fen", required=True, help="FEN or 'startpos'")
            s.add_argument("--moves", default="")
        if name == "batch":
            s.add_argument("--epd", required=True)
            s.add_argument("--keep-iterations", action="store_true")
    a = p.parse_args()
    return {"pins": cmd_pins, "go": cmd_go, "batch": cmd_batch}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
