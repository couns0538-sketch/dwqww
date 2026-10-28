"""UCI side of the Forge SPSA tuner (R3-4): read an engine's advertised options and prove it applies the tuned ones.

fastchess only sends `setoption` for options the engine advertises (otherwise it warns, and with -strict it
stops), so every tuned parameter must be an advertised spin option. Forge lists its 20 SPSA constants in every
build (forge/search_tune.hpp AdvertisedParameters) and re-advertises a constant with its current value after a
`setoption`, which gives a cheap proof that a value was applied: uci, setoption ..., uci.
Standard library only, Python 3.10+.
"""
from __future__ import annotations

import re
import subprocess
import threading

_OPTION = re.compile(r"^option name (.+?) type (\S+)(?: default ?(.*?))?(?: min (-?\d+))?(?: max (-?\d+))?(?: var .*)?$")


def parse_options(lines: list[str]) -> dict[str, dict]:
    """{name: {'type', 'default', 'min', 'max'}} from `option` lines (the last line for a name wins)."""
    options: dict[str, dict] = {}
    for raw in lines:
        m = _OPTION.match(raw.strip())
        if not m:
            continue
        name, kind, default, lo, hi = m.groups()
        entry = {"type": kind, "default": default}
        if kind == "spin":
            entry["default"] = int(default) if default not in (None, "") else None
            entry["min"] = int(lo) if lo is not None else None
            entry["max"] = int(hi) if hi is not None else None
        options[name] = entry
    return options


def uci_session(engine: str, commands: list[str], timeout_s: float = 60.0, creationflags: int = 0) -> list[str]:
    """Send `uci` replies' worth of commands and return the engine's output lines. Every `uci` command is answered
    with `uciok` before the next command is sent; ends with `quit`."""
    proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, creationflags=creationflags)
    lines: list[str] = []
    timer = threading.Timer(timeout_s, proc.kill)
    timer.start()
    try:
        assert proc.stdin is not None and proc.stdout is not None
        for command in commands:
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
            if command == "uci":
                for line in proc.stdout:
                    lines.append(line.rstrip("\r\n"))
                    if line.strip() == "uciok":
                        break
                else:
                    raise RuntimeError(f"{engine}: no uciok")
            elif command == "isready":
                for line in proc.stdout:
                    lines.append(line.rstrip("\r\n"))
                    if line.strip() == "readyok":
                        break
                else:
                    raise RuntimeError(f"{engine}: no readyok")
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        rest, _ = proc.communicate(timeout=timeout_s)
        lines += rest.splitlines()
    finally:
        timer.cancel()
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    return lines


def split_replies(lines: list[str]) -> list[list[str]]:
    """The output split after every `uciok`."""
    replies, current = [], []
    for line in lines:
        current.append(line)
        if line.strip() == "uciok":
            replies.append(current)
            current = []
    return replies


def check_params(params, options: dict[str, dict], fresh: bool, allow_start_offset: bool = False) -> list[str]:
    """Problems with tuning `params` (opus_spsa_core.Param) on an engine with these advertised options."""
    problems = []
    for p in params:
        o = options.get(p.name)
        if o is None:
            problems.append(f"{p.name}: not advertised by the engine (fastchess would not send it)")
            continue
        if o["type"] != "spin":
            problems.append(f"{p.name}: advertised as {o['type']}, not spin")
            continue
        if o["min"] is None or o["max"] is None or o["default"] is None:
            problems.append(f"{p.name}: spin option without default/min/max")
            continue
        if p.minimum < o["min"] or p.maximum > o["max"]:
            problems.append(f"{p.name}: tuning bounds [{p.minimum}, {p.maximum}] outside the engine's "
                            f"[{o['min']}, {o['max']}]")
        if fresh and not allow_start_offset and float(p.start) != float(o["default"]):
            problems.append(f"{p.name}: start {p.start} differs from the engine default {o['default']} "
                            f"(set allow_start_offset to tune from another start)")
    return problems


def application_probe(params) -> dict[str, int]:
    """A value per parameter that differs from its start and lies inside its bounds."""
    probe = {}
    for p in params:
        v = int(round(p.start)) + 1
        if v > p.maximum:
            v = int(round(p.start)) - 1
        probe[p.name] = v
    return probe


def prove_application(engine: str, params, creationflags: int = 0) -> tuple[dict[str, dict], list[str]]:
    """uci; setoption name P value v (each tuned P); uci. Returns the first reply's options and the problems: a
    tuned option whose second advertisement does not show the value that was set."""
    probe = application_probe(params)
    commands = ["uci"] + [f"setoption name {n} value {v}" for n, v in probe.items()] + ["uci"]
    lines = uci_session(engine, commands, creationflags=creationflags)
    replies = split_replies(lines)
    if len(replies) < 2:
        return {}, [f"{engine}: expected two uci replies, got {len(replies)}"]
    first, second = parse_options(replies[0]), parse_options(replies[1])
    problems = []
    for name, value in probe.items():
        shown = second.get(name, {}).get("default")
        if shown != value:
            problems.append(f"{name}: set to {value} but the engine then advertises {shown}")
    return first, problems
