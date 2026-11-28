"""The replaceable engine: how to start it with a given net, and a small UCI client.

Two ways to bind a net to an engine (config key engine.mode):
  net_option     one exe; the net file is loaded through a UCI option (Stockfish: EvalFile)
  build_per_net  the net is compiled into the exe; engine.build_cmd makes an exe for each net
"""
from __future__ import annotations

import hashlib
import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .common import log, run_logged, child_env


@dataclass
class EngineSpec:
    exe: str
    options: dict = field(default_factory=dict)
    cwd: str | None = None


def file_sha12(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:12]


def engine_for_net(cfg: dict, net_path: str | None) -> EngineSpec:
    e = cfg["engine"]
    opts = dict(e.get("uci_options", {}))
    # [engine] tuned_only_for_tuned_net = true gives the tuned search values (forge_tuned_options.json) only to the
    # net they were found with (tuned_with_net_sha12) and the default settings to every other net. OFF by default
    # since 2026-11-15 03:20: it was on for two hours on the belief that the values were worth nothing to another
    # net. Measured since (Opus, 2,000 games each with b_full at 50,000 nodes): the "shape" half of the values gives
    # another net +11.0 +/- 9.7, the "margin" half +1.4 +/- 9.3. So they help another net too, only less than their
    # own (+47), and a candidate at default settings would be playing its weaker setting.
    tuned_net, tuned_names = e.get("tuned_for_net_sha12"), e.get("tuned_option_names")
    if (e.get("tuned_only_for_tuned_net") and tuned_net and tuned_names and net_path
            and file_sha12(net_path) != tuned_net):
        opts = {k: v for k, v in opts.items() if k not in set(tuned_names)}
    mode = e.get("mode", "net_option")
    if mode == "net_option":
        if net_path:
            opts[e["net_option"]] = str(net_path)
        return EngineSpec(e["cmd"], opts, e.get("cwd") or None)
    if mode == "build_per_net":
        if not net_path:
            return EngineSpec(e["cmd"], opts, e.get("cwd") or None)
        if str(net_path).lower().endswith(".fnn3"):
            # A FORGENN3 net (king-bucketed, forge/r7, 2026-11-15) is not compiled in: ONE exe serves all of them
            # and the net is given by two options. The exe is built on first use by engine.v3_build_cmd, its
            # profile step run with the net that asked first; engine.v3_build_tag names the build.
            if not e.get("v3_build_cmd"):
                raise RuntimeError("a .fnn3 net needs engine.v3_build_cmd in the config")
            cache = Path(cfg["paths"]["runs"]) / "engines" / ("v3-" + str(e.get("v3_build_tag", "r7clang") or "r7clang"))
            exe = cache / e.get("built_exe_name", "engine.exe")
            if not exe.exists():
                cache.mkdir(parents=True, exist_ok=True)
                cmd = e["v3_build_cmd"].format(net=str(net_path), out_exe=str(exe), out_dir=str(cache))
                log(f"building the v3 engine (profile net {net_path}) -> {exe}")
                rc = run_logged(cmd, cache / "build.log", env=child_env(cfg))
                if rc != 0 or not exe.exists():
                    raise RuntimeError(f"v3 engine build failed (exit {rc}); see {cache / 'build.log'}")
            # [engine] v3_uci_options (2026-11-15, a table like uci_options; not set = nothing added): search settings
            # that every king-bucket net gets, in the loop and in every tool that asks here. The place for tuned
            # values of this kind of net once they have passed their matches (the file forge_tuned_options.json
            # belongs to the round 2 net).
            opts = {**opts, **dict(e.get("v3_uci_options") or {}),
                    "NNUEArchFile": str(net_path).replace("\\", "/"), "NNUEArch": True}
            return EngineSpec(str(exe), opts, e.get("cwd") or None)
        # engine.build_tag names the build variant (for example "pgo"). It is part of the cache folder,
        # so changing build_cmd together with build_tag rebuilds every net the same way and two nets
        # never meet in a match with different build types.
        tag = str(e.get("build_tag", "") or "")
        cache = Path(cfg["paths"]["runs"]) / "engines" / (file_sha12(net_path) + (f"-{tag}" if tag else ""))
        exe = cache / e.get("built_exe_name", "engine.exe")
        if not exe.exists():
            cache.mkdir(parents=True, exist_ok=True)
            cmd = e["build_cmd"].format(net=str(net_path), out_exe=str(exe), out_dir=str(cache))
            log(f"building engine for net {net_path} -> {exe}")
            rc = run_logged(cmd, cache / "build.log", env=child_env(cfg))
            if rc != 0 or not exe.exists():
                raise RuntimeError(f"engine build failed (exit {rc}); see {cache / 'build.log'}")
        return EngineSpec(str(exe), opts, e.get("cwd") or None)
    raise ValueError(f"unknown engine.mode {mode!r}")


class EngineError(RuntimeError):
    pass


# 2026-11-16 (Opus; Fable's job of 04:38, "did any match of ours send an option its exe did not have?"): an engine
# answers an option it does not take with ONE line and plays on (Forge: "info string unknown option X" / "info string
# invalid value for option X", the value then unchanged; Stockfish: "No such option: X"), and fastchess does not show
# that line. The audit of all 286 recorded engine starts found none (tmp/opus_scratch/option_audit/), and it found
# that the ten oldest Forge builds say NOTHING to an unknown name. So: the self-play client refuses on such a reply,
# and every fastchess command built by nnloop.match._engine_args is checked once before it is used (check_options).
class OptionRefused(EngineError):
    pass


_REFUSAL_MARKS = ("info string unknown option", "info string invalid value", "No such option",
                  "info string ERROR")
_PLANTED_NAME = "ForgePreflightNoSuchOption"    # an option no engine has: does this exe report an unknown name?
_options_checked: set = set()


def refusal_lines(lines) -> list[str]:
    return [ln for ln in lines if any(m in ln for m in _REFUSAL_MARKS)]


def uci_value(v) -> str:
    return ("true" if v else "false") if isinstance(v, bool) else str(v)


def check_options(spec: "EngineSpec", timeout: float = 120.0) -> None:
    """Start spec.exe once and send its options exactly as fastchess will (in order, bools as true / false), each
    followed by isready. Raise OptionRefused when the engine answers one of them with a refusal line, or, for an exe
    that does not report an unknown option at all (shown by a planted name first), when a name is not in its uci list.
    Nothing is checked for a spec without options (the loop's tests use a made-up exe with none). Once per (exe,
    options) per process. FORGE_OPTION_CHECK=0 switches it off."""
    import os
    if not spec.options or os.environ.get("FORGE_OPTION_CHECK", "1") == "0":
        return
    key = (str(spec.exe), tuple((str(k), uci_value(v)) for k, v in spec.options.items()))
    if key in _options_checked:
        return
    if not Path(spec.exe).exists():
        raise OptionRefused(f"option check: {spec.exe} does not exist")
    eng = UciEngine(EngineSpec(spec.exe, {}, spec.cwd), startup_timeout=timeout)
    try:
        eng.send(f"setoption name {_PLANTED_NAME} value 1")
        silent = not refusal_lines(eng.ready(timeout))
        bad = []
        for k, v in spec.options.items():
            eng.send(f"setoption name {k} value {uci_value(v)}")
            bad += [f"{k}={uci_value(v)}: {ln}" for ln in refusal_lines(eng.ready(timeout))]
            if silent and k not in eng.listed:
                bad.append(f"{k}={uci_value(v)}: not in the uci list of this exe, which does not report unknown options")
    finally:
        eng.quit()
    if bad:
        raise OptionRefused(f"option check of {spec.exe}: " + "; ".join(bad))
    _options_checked.add(key)


class UciEngine:
    """Minimal UCI client with timeouts (a hung engine raises instead of blocking forever)."""

    def __init__(self, spec: EngineSpec, startup_timeout: float = 120.0):
        self.spec = spec
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.p = subprocess.Popen([spec.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, cwd=spec.cwd, text=True, bufsize=1,
                                  creationflags=flags)
        self.q: queue.Queue = queue.Queue()
        self._pending: list[str] = []      # lines of the batch being handed out, last line first
        threading.Thread(target=self._reader, daemon=True).start()
        self.send("uci")
        lines = self.wait_for("uciok", startup_timeout)
        self.listed = {ln.split("option name ", 1)[1].split(" type ", 1)[0]
                       for ln in lines if ln.startswith("option name ") and " type " in ln}
        for k, v in spec.options.items():
            if isinstance(v, bool):
                v = "true" if v else "false"
            self.send(f"setoption name {k} value {v}")
        bad = refusal_lines(self.ready(startup_timeout))
        if bad:
            # 2026-11-16: an option the engine did not take is no longer played on (see OptionRefused).
            self.quit()
            raise OptionRefused(f"{spec.exe} refused an option: {'; '.join(bad)}")

    def _reader(self) -> None:
        # "info" lines are held back and handed over together with the line that ends them (bestmove, readyok,
        # uciok, ...): one hand-over between the two threads per search instead of one per line (2026-11-14:
        # with about nine lines per search the hand-overs were most of a self-play worker's own CPU time).
        # Every command this client waits on ends with a line that does not start with "info".
        batch: list[str] = []
        try:
            for line in self.p.stdout:
                line = line.rstrip("\r\n")
                batch.append(line)
                if not line.startswith("info"):
                    self.q.put(batch)
                    batch = []
        except Exception:
            pass
        if batch:
            self.q.put(batch)
        self.q.put(None)

    def send(self, line: str) -> None:
        try:
            self.p.stdin.write(line + "\n")
            self.p.stdin.flush()
        except (OSError, ValueError) as e:
            raise EngineError(f"engine pipe closed: {e}")

    def _get(self, deadline: float) -> str:
        if self._pending:
            return self._pending.pop()
        try:
            batch = self.q.get(timeout=max(0.01, deadline - time.time()))
        except queue.Empty:
            raise EngineError("engine timeout")
        if batch is None:
            self.q.put(None)               # stay "exited" for every later call
            raise EngineError(f"engine exited (code {self.p.poll()})")
        batch.reverse()
        self._pending = batch
        return self._pending.pop()

    def wait_for(self, token: str, timeout: float) -> list[str]:
        deadline = time.time() + timeout
        lines = []
        while True:
            line = self._get(deadline)
            lines.append(line)
            if line.startswith(token):
                return lines

    def ready(self, timeout: float = 60.0) -> list[str]:
        self.send("isready")
        return self.wait_for("readyok", timeout)

    def new_game(self) -> None:
        self.send("ucinewgame")
        self.ready()

    def search(self, position_cmd: str, go_cmd: str, timeout: float = 60.0):
        """Returns (bestmove, score) where score is ('cp'|'mate', int) from the side to move, or None."""
        self.send(position_cmd)
        self.send(go_cmd)
        deadline = time.time() + timeout
        exact = None
        bound = None
        while True:
            line = self._get(deadline)
            if line.startswith("info") and " score " in line:
                t = line.split()
                try:
                    i = t.index("score")
                    sc = (t[i + 1], int(t[i + 2]))
                    if len(t) > i + 3 and t[i + 3] in ("lowerbound", "upperbound"):
                        bound = sc
                    else:
                        exact = sc
                except (ValueError, IndexError):
                    pass
            elif line.startswith("bestmove"):
                parts = line.split()
                bm = parts[1] if len(parts) > 1 else None
                return bm, (exact or bound)

    def search_multipv(self, position_cmd: str, go_cmd: str, k: int, timeout: float = 60.0):
        """Search with MultiPV=k. Returns [(move, ('cp'|'mate', int)), ...] best line first."""
        self.send(f"setoption name MultiPV value {k}")
        self.send(position_cmd)
        self.send(go_cmd)
        deadline = time.time() + timeout
        found: dict[int, tuple] = {}
        while True:
            line = self._get(deadline)
            if line.startswith("info") and " multipv " in line and " score " in line and " pv " in line:
                t = line.split()
                try:
                    idx = int(t[t.index("multipv") + 1])
                    i = t.index("score")
                    found[idx] = (t[t.index("pv") + 1], (t[i + 1], int(t[i + 2])))
                except (ValueError, IndexError):
                    pass
            elif line.startswith("bestmove"):
                break
        self.send("setoption name MultiPV value 1")
        return [found[i] for i in sorted(found)]

    def quit(self) -> None:
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            pass
        if self.p.poll() is None:
            self.p.kill()


def make_score_converter(cfg: dict):
    """Turn the engine's UCI 'score cp' into the unit the trainer expects.

    sf_normalized_cp: Stockfish prints cp = 100 * internal / a(material). The data must hold the
    internal value, so this inverts it with the same polynomial (uci.cpp, win_rate_params).
    raw: keep the number as printed.
    """
    sc = cfg["engine"].get("score", {})
    unit = sc.get("unit", "raw")
    if unit == "raw":
        mul = float(sc.get("multiplier", 1.0))
        return lambda cp, board: int(round(cp * mul))
    if unit == "sf_normalized_cp":
        import chess

        a0, a1, a2, a3 = sc["wdl_as"]

        def conv(cp: int, board) -> int:
            material = (chess.popcount(board.pawns) + 3 * chess.popcount(board.knights)
                        + 3 * chess.popcount(board.bishops) + 5 * chess.popcount(board.rooks)
                        + 9 * chess.popcount(board.queens))
            m = min(78, max(17, material)) / 58.0
            a = ((a0 * m + a1) * m + a2) * m + a3
            return int(round(cp * a / 100.0))

        return conv
    raise ValueError(f"unknown engine.score.unit {unit!r}")


def check_engine_loads_net(cfg: dict, net_path: str | None, nodes: int = 20000) -> dict:
    """Start the engine with the net and run one short search. Raises if anything is off."""
    spec = engine_for_net(cfg, net_path)
    eng = UciEngine(spec)
    try:
        t0 = time.time()
        bm, sc = eng.search("position startpos", f"go nodes {nodes}", timeout=120)
        dt_ = time.time() - t0
    finally:
        eng.quit()
    if not bm or bm in ("(none)", "0000") or sc is None:
        raise EngineError(f"engine gave no usable move with net {net_path}: bestmove={bm} score={sc}")
    return {"bestmove": bm, "score": list(sc), "seconds": round(dt_, 2)}
