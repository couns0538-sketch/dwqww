#!/usr/bin/env python3
"""R3-1 self-play checker: fast self-games between two processes of the same Forge build and options, with a
protocol check after every command. One config per run; run_matrix.py runs the whole set.

usage: opus_selfplay_check.py --name NAME --exe ENGINE [--opt Name=value ...] [--threads N] [--games 500]
           [--parallel 3] [--restart-every 25] [--seed 1] [--out-dir DIR] [--epd tools/openings/forge-10000.epd]
           [--max-plies 200] [--margin-ms 10000] [--git-head SHA] [--preflight-only]
           [--nodes-min 300] [--nodes-max 5000] [--mix nodes=50,clock=15,...] [--exe-arg ARG ...]

Every engine: Hash 16, Threads N, Ponder true (so every bestmove carries a ponder move to check), OwnBook false
(every go searches), then the --opt options in the given order except that NNUEFile is sent last.

Checks (each failure is an error in the game's JSONL record; exit status 1 if any error, 3 if the preflight fails):
- legality: every bestmove is legal in the position of its go, its ponder move legal after it (python-chess);
  every `currmove` and every `pv` move of every info line is legal from the root, in sequence;
- exactly one bestmove per go: after every `position` the harness sends `isready` and waits for `readyok`
  (the engine joins the previous search before it handles `position`, so a second or unsolicited bestmove
  arrives before that readyok); `go infinite` and `go ponder` must not answer before `stop` / `ponderhit`;
  the final quit drains everything left (a bestmove there is an error too);
- no crash: stdout stays open and the process alive; exit status 0 at every quit; nothing on stderr;
- no hang: bestmove within the command's limit + --margin-ms (fixed 30 s + margin for nodes/depth searches,
  measured from stop/ponderhit for those), readyok within 10 s (also during infinite/ponder searches),
  quit within 20 s;
- well-formed output: info lines use known keys with integer values, score cp|mate [lowerbound|upperbound];
  info strings containing error/invalid/illegal/cannot/unknown/fail/exception/assert/abort are errors (the
  transient `ERROR NNUE v2` lines of a half-set request while the options are being sent are logged and must be
  resolved by `isready`); any other unexpected line is an error; a search info line that arrives after its
  bestmove (before the next readyok) is an error (late_search_output, recorded with that search's go command and
  whether its bestmove came from the search thread or the HardDeadline watchdog);
- S08fix profile blocks (Profile=true): schema line + one line per counter right before the search thread's
  bestmove, every block with the same counters in the same order, "pct unknown" only with 0 opportunities;
- options: every configured option is advertised by `uci`; the configuration ends in readyok with the expected
  activation lines (NNUE v2 active, Syzygy tables loaded, LocklessTT active).
Commands vary per move (per-game RNG, seed:game, so game i uses the same opening and plan in every config;
defaults below, --nodes-min/--nodes-max/--mix change them): go nodes 300-5000 (50%), clocked go
wtime/btime/winc/binc from a per-game clock of 0.2-2 s + 0/10/20/30/50 ms (15%), go movetime 5-30 (8%),
go depth 1-6 (8%), go infinite + stop after 5-50 ms (7%), go ponder + ponderhit after 5-50 ms (6%), a ponder
miss (go ponder on another opponent move + stop after 5-50 ms, then a clocked go on the real position, 6%); 30%
of infinite/ponder searches get an `isready` mid-search; 3% of moves send a stray `stop` to the idle engine first.
`ucinewgame` + isready before every game, engines restarted every K games.
A game ends on mate, stalemate, insufficient material, threefold repetition, the 50-move rule, or at --max-plies.
Outputs in --out-dir: <name>.games.jsonl (one record per game + one per worker end), <name>.summary.json,
<name>.preflight.json, <name>.pgn, <name>.events.log, errgames/<name>_g<game>.log (full transcripts of games
with errors).
"""

import argparse
import hashlib
import json
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time
from collections import Counter, deque

import chess
import chess.pgn

IDLE = getattr(subprocess, "IDLE_PRIORITY_CLASS", 0)
T0 = time.perf_counter()

KINDS = (("nodes", 50), ("clock", 15), ("movetime", 8), ("depth", 8), ("infinite", 7), ("ponderhit", 6),
         ("pondermiss", 6))
INT_KEYS = frozenset("depth seldepth time nodes nps hashfull tbhits sbhits multipv currmovenumber cpuload".split())
KNOWN_STRINGS = ("NNUE v2: active", "NNUE v2: loaded", "LocklessTT active", "Syzygy: ", "TtChildPrefetch active",
                 "HardDeadline: no answer within")
BAD_WORDS = ("error", "invalid", "illegal", "cannot", "unknown", "fail", "exception", "assert", "abort")
NNUE_OPTS = ("NNUEKingBuckets", "NNUEOutputBuckets", "NNUEThreats", "NNUEPawnPairs", "PureNnue", "NNUEFile")
ERROR_GROUPS = {
    "crashes": ("crash", "bad_exit_code"),
    "illegal_moves": ("illegal_bestmove", "illegal_ponder", "illegal_pv", "illegal_currmove", "engine_rejected_move"),
    "double_bestmoves": ("extra_bestmove", "bestmove_before_stop"),
    "timeouts": ("timeout_bestmove", "timeout_readyok", "timeout_uciok", "timeout_quit"),
    "malformed_output": ("malformed_info", "malformed_bestmove", "unexpected_line", "error_info_string",
                         "late_search_output", "stderr_output"),
    "config_errors": ("config_error", "option_not_advertised"),
    "harness_errors": ("harness_exception",),
}
UCIOK_S, CONFIG_READY_S, READY_S, QUIT_S, FIXED_S = 30.0, 180.0, 10.0, 20.0, 30.0


def ts(t):
    return round(t - T0, 3)


class Timeout(Exception):
    pass


class EngineDied(Exception):
    pass


class GameError(Exception):
    """A fatal error: the game is aborted and the engine pair restarted (already recorded)."""


class Engine:
    """One engine process: reader threads timestamp every stdout/stderr line; every line sent or received goes to
    the transcript."""

    def __init__(self, cmd, tag, cwd):
        self.tag = tag
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     creationflags=IDLE, cwd=cwd)
        self.q = queue.Queue()
        self.transcript = deque(maxlen=40000)
        self.stderr = []
        self.closed = False
        threading.Thread(target=self._read_out, daemon=True).start()
        threading.Thread(target=self._read_err, daemon=True).start()

    def _read_out(self):
        for raw in iter(self.proc.stdout.readline, b""):
            t = time.perf_counter()
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            self.transcript.append((t, "<", line))
            self.q.put((t, line))
        t = time.perf_counter()
        self.transcript.append((t, "<", "<EOF>"))
        self.q.put((t, None))

    def _read_err(self):
        for raw in iter(self.proc.stderr.readline, b""):
            t = time.perf_counter()
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            self.transcript.append((t, "!", line))
            self.stderr.append((t, line))

    def send(self, cmd):
        t = time.perf_counter()
        self.transcript.append((t, ">", cmd))
        try:
            self.proc.stdin.write((cmd + "\n").encode())
            self.proc.stdin.flush()
        except OSError as exc:
            raise EngineDied(f"write of {cmd[:40]!r} failed ({exc}); exit status {self.proc.poll()}")
        return t

    def get(self, deadline):
        while True:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                raise Timeout()
            try:
                t, line = self.q.get(timeout=min(remaining, 0.5))
            except queue.Empty:
                continue
            if line is None:
                self.closed = True
                self.q.put((t, None))   # keep the EOF marker for later readers
                try:
                    code = self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    code = "still running"
                raise EngineDied(f"stdout closed, exit status {code}")
            return t, line

    def pending(self):
        out = []
        while True:
            try:
                item = self.q.get_nowait()
            except queue.Empty:
                return out
            if item[1] is None:
                self.q.put(item)
                return out
            out.append(item)

    def context(self, n=40):
        return [[ts(t), d, s] for t, d, s in list(self.transcript)[-n:]]

    def dump(self):
        return "\n".join(f"{ts(t):12.3f} {self.tag} {d} {s}" for t, d, s in list(self.transcript))

    def kill(self):
        try:
            if self.proc.poll() is None:
                self.proc.kill()
                self.proc.wait(timeout=10)
        except Exception:
            pass


def opt_order(opts):
    """Options as sent: NNUE ones after the others, NNUEFile last (a half-set v2 request prints a transient ERROR)."""
    first = [(n, v) for n, v in opts if n not in NNUE_OPTS]
    nnue = sorted([(n, v) for n, v in opts if n in NNUE_OPTS], key=lambda nv: NNUE_OPTS.index(nv[0]))
    return first + nnue


def is_int(text):
    return text.lstrip("-").isdigit() and text.count("-") <= 1


def new_stats():
    return dict(kinds=Counter(), lat={}, info_lines=0, pv_moves=0, currmoves=0, empty_pv=0, ponder_checked=0,
                barriers=0, mid_isready=0, stray_stops=0, overruns=0, overrun_max_ms=0.0, clock_resets=0,
                hd_fired=0, tbhits_max=0, max_depth=0, strings=Counter(), prof_blocks=0, prof_lines=0,
                prof_overflow=0, bestmoves=0, bestmoves_without_prof=0, watchdog_answers=0,
                late_after_watchdog=0, late_after_search=0)


class Shared:
    def __init__(self, args, openings):
        self.args = args
        self.openings = openings
        self.lock = threading.Lock()
        self.next = 0
        self.records = []
        self.abort = False
        self.prof_names = None   # counter names of the first complete profile block (S08fix Profile=true)
        self.started = time.perf_counter()
        os.makedirs(args.out_dir, exist_ok=True)
        os.makedirs(os.path.join(args.out_dir, "errgames"), exist_ok=True)
        base = os.path.join(args.out_dir, args.name)
        self.jsonl = open(base + ".games.jsonl", "w", newline="\n", encoding="utf-8")
        self.pgn = open(base + ".pgn", "w", newline="\n", encoding="utf-8")
        self.events = open(base + ".events.log", "w", newline="\n", encoding="utf-8")

    def next_game(self):
        with self.lock:
            if self.abort or self.next >= self.args.games:
                return None
            if self.args.max_minutes and time.perf_counter() - self.started > 60 * self.args.max_minutes:
                return None
            gi = self.next
            self.next += 1
            return gi

    def event(self, text):
        with self.lock:
            self.events.write(f"{time.strftime('%H:%M:%S')} {ts(time.perf_counter()):10.3f} {text}\n")
            self.events.flush()

    def write(self, rec, pgn_text=None, dumps=None):
        with self.lock:
            self.records.append(rec)
            self.jsonl.write(json.dumps(rec, separators=(",", ":")) + "\n")
            self.jsonl.flush()
            if pgn_text:
                self.pgn.write(pgn_text + "\n\n")
                self.pgn.flush()
            if dumps:
                path = os.path.join(self.args.out_dir, "errgames", f"{self.args.name}_g{rec.get('game', 'w')}"
                                    f"{'' if rec.get('record') == 'game' else '_w' + str(rec.get('worker'))}.log")
                with open(path, "w", newline="\n", encoding="utf-8") as f:
                    f.write(dumps)


class Worker:
    def __init__(self, wid, shared, cfg_opts):
        self.wid = wid
        self.sh = shared
        self.a = shared.args
        self.opts = cfg_opts
        self.engines = None
        self.gen = 0
        self.errors = []
        self.st = new_stats()
        self.ply = None
        self.kind = None
        self.prof_block = None
        self.prof_overflow = False

    # ---------------- error recording ----------------
    def err(self, etype, eng, detail, lines=(), fatal=False):
        rec = dict(type=etype, engine=eng.tag if eng else None, ply=self.ply, kind=self.kind, detail=detail,
                   lines=[[ts(t), s] for t, s in lines],
                   context=eng.context() if eng else [])
        self.errors.append(rec)
        self.sh.event(f"ERROR w{self.wid} {etype} {eng.tag if eng else '-'} ply {self.ply} {self.kind}: {detail} "
                      f"| {' || '.join(s for _, s in lines)[:300]}")
        if fatal:
            raise GameError(etype)

    def get(self, e, deadline, etype, what):
        try:
            return e.get(deadline)
        except Timeout:
            self.err(etype, e, f"no answer to {what}", fatal=True)
        except EngineDied as exc:
            self.err("crash", e, f"{exc} (while waiting for the answer to {what})", fatal=True)

    def send(self, e, cmd):
        try:
            return e.send(cmd)
        except EngineDied as exc:
            self.err("crash", e, str(exc), fatal=True)

    # ---------------- output checks ----------------
    def check_prof(self, e, t, line, text):
        """S08fix profile block (Profile=true): 'prof schema 1 scope search_only setup_excluded 1 overflow 0|1', then
        one 'prof <name> count <n> denominator <name> opportunities <n> pct <x>|unknown' line per counter; the block
        comes right before the search thread's bestmove and has the same counters, in the same order, every time."""
        st, toks = self.st, text.split()
        st["prof_lines"] += 1
        if len(toks) >= 2 and toks[1] == "schema":
            if len(toks) != 9 or toks[2:8] != ["1", "scope", "search_only", "setup_excluded", "1", "overflow"] or \
                    toks[8] not in ("0", "1"):
                self.err("malformed_info", e, "bad profile schema line", [(t, line)])
            if self.prof_block is not None:
                self.err("malformed_info", e, f"profile block cut short after {len(self.prof_block)} counters",
                         [(t, line)])
            self.prof_block = []
            self.prof_overflow = toks[-1] == "1"
            st["prof_blocks"] += 1
            st["prof_overflow"] += self.prof_overflow
            return
        ok = (len(toks) == 10 and toks[2] == "count" and toks[3].isdigit() and toks[4] == "denominator" and
              toks[6] == "opportunities" and toks[7].isdigit() and toks[8] == "pct")
        if ok:
            if toks[9] == "unknown":
                ok = toks[7] == "0" or self.prof_overflow
            else:
                try:
                    ok = float(toks[9]) >= 0 and toks[7] != "0"
                except ValueError:
                    ok = False
        if not ok or self.prof_block is None:
            self.err("malformed_info", e, "bad profile counter line" if not ok else "profile counter outside a block",
                     [(t, line)])
            return
        self.prof_block.append(toks[1])

    def close_prof_block(self, e, t, line):
        """At a bestmove: the profile block before it (if any) must be complete and identical in layout."""
        block, self.prof_block = self.prof_block, None
        self.st["bestmoves"] += 1
        e.last_answer = "watchdog" if getattr(e, "watchdog_pending", False) else "search thread"
        e.watchdog_pending = False
        self.st["watchdog_answers"] += e.last_answer == "watchdog"
        if block is None:
            self.st["bestmoves_without_prof"] += 1
            return
        with self.sh.lock:
            if self.sh.prof_names is None:
                self.sh.prof_names = list(block)
            ref = self.sh.prof_names
        if block != ref:
            first = next((i for i, (x, y) in enumerate(zip(block, ref)) if x != y), min(len(block), len(ref)))
            self.err("malformed_info", e, f"profile block has {len(block)} counters, the first block had {len(ref)} "
                     f"(first difference at counter {first})", [(t, line)])

    def check_string(self, e, t, line, text, config=False):
        if text.startswith("prof "):
            self.check_prof(e, t, line, text)
            self.st["strings"]["prof schema (profile block)" if text.startswith("prof schema") else
                               "prof <counter lines>"] += 1
            return "ok"
        low = text.lower()
        if any(w in low for w in BAD_WORDS):
            if config and text.startswith("ERROR NNUE v2:"):
                return "transient"
            if "illegal move" in low:
                self.err("engine_rejected_move", e, "the engine rejected a move the harness sent", [(t, line)],
                         fatal=True)
            self.err("error_info_string", e, "error text in an info string", [(t, line)], fatal=not config)
            return "error"
        if text.startswith("HardDeadline:"):
            e.watchdog_pending = True
            self.st["hd_fired"] += 1
            key = "HardDeadline: no answer within ... (watchdog bestmove)"
        else:
            # known activation lines verbatim; others (e.g. NnueLazyAcc per-search stats) with numbers as #
            key = text if text.startswith(KNOWN_STRINGS[:5]) else re.sub(r"[0-9]+(\.[0-9]+)?", "#", text)[:80]
        self.st["strings"][key] += 1
        return "ok"

    def check_info(self, e, t, line, root):
        """Well-formed info line; currmove / pv moves legal from `root` (None outside a search)."""
        st = self.st
        toks = line.split()
        if toks[0] != "info" or len(toks) < 2:
            self.err("malformed_info", e, "empty info line", [(t, line)])
            return
        if toks[1] == "string":
            self.check_string(e, t, line, line.split(" ", 2)[2] if len(toks) > 2 else "")
            return
        st["info_lines"] += 1
        if root is None:
            answer = getattr(e, "last_answer", None)
            self.st["late_after_watchdog" if answer == "watchdog" else "late_after_search"] += 1
            self.err("late_search_output", e, f"search info line after the bestmove of '{getattr(e, 'last_go', None)}' "
                     f"(that bestmove was sent by the {answer})", [(t, line)])
            return
        i = 1
        while i < len(toks):
            key = toks[i]
            i += 1
            if key in INT_KEYS:
                if i >= len(toks) or not is_int(toks[i]) or int(toks[i]) < 0 or \
                        (key == "hashfull" and int(toks[i]) > 1000):
                    self.err("malformed_info", e, f"bad value for {key}", [(t, line)])
                    return
                value = int(toks[i])
                i += 1
                if key == "tbhits":
                    st["tbhits_max"] = max(st["tbhits_max"], value)
                elif key == "depth":
                    st["max_depth"] = max(st["max_depth"], value)
            elif key == "score":
                if i + 1 >= len(toks) or toks[i] not in ("cp", "mate") or not is_int(toks[i + 1]):
                    self.err("malformed_info", e, "bad score", [(t, line)])
                    return
                i += 2
                if i < len(toks) and toks[i] in ("lowerbound", "upperbound"):
                    i += 1
            elif key == "wdl":
                if i + 3 > len(toks) or not all(is_int(x) for x in toks[i:i + 3]):
                    self.err("malformed_info", e, "bad wdl", [(t, line)])
                    return
                i += 3
            elif key == "currmove":
                if i >= len(toks):
                    self.err("malformed_info", e, "currmove without a move", [(t, line)])
                    return
                st["currmoves"] += 1
                if not self.legal(root, toks[i]):
                    self.err("illegal_currmove", e, f"currmove {toks[i]} is not legal at the root", [(t, line)])
                i += 1
            elif key == "pv":
                moves = toks[i:]
                i = len(toks)
                if not moves:
                    st["empty_pv"] += 1
                b = root.copy(stack=False)
                for k, m in enumerate(moves):
                    try:
                        mv = chess.Move.from_uci(m)
                    except ValueError:
                        mv = None
                    if mv is None or not b.is_legal(mv):
                        self.err("illegal_pv", e, f"pv move {k + 1} ({m}) is not legal", [(t, line)])
                        break
                    b.push(mv)
                    st["pv_moves"] += 1
            else:
                self.err("malformed_info", e, f"unknown info key {key!r}", [(t, line)])
                return

    @staticmethod
    def legal(board, uci):
        try:
            mv = chess.Move.from_uci(uci)
        except ValueError:
            return False
        return board.is_legal(mv)

    def check_bestmove(self, e, t, line, board):
        toks = line.split()
        if len(toks) not in (2, 4) or (len(toks) == 4 and toks[2] != "ponder"):
            self.err("malformed_bestmove", e, "bestmove line not 'bestmove <m> [ponder <m>]'", [(t, line)], fatal=True)
        try:
            mv = chess.Move.from_uci(toks[1])
        except ValueError:
            mv = None
        if mv is None or not board.is_legal(mv):
            self.err("illegal_bestmove", e, f"bestmove {toks[1]} is not legal in {board.fen()}", [(t, line)],
                     fatal=True)
        if len(toks) == 4:
            after = board.copy(stack=False)
            after.push(mv)
            self.st["ponder_checked"] += 1
            if not self.legal(after, toks[3]):
                self.err("illegal_ponder", e, f"ponder move {toks[3]} is not legal after {toks[1]} in {board.fen()}",
                         [(t, line)])
        return mv

    def handle_idle_line(self, e, t, line, what):
        """A line while no search is expected to answer (barriers, configuration)."""
        if line.startswith("bestmove"):
            self.err("extra_bestmove", e, f"bestmove with no search running ({what})", [(t, line)], fatal=True)
        elif line.startswith("info"):
            self.check_info(e, t, line, None)
        else:
            self.err("unexpected_line", e, f"unexpected output ({what})", [(t, line)], fatal=True)

    def barrier(self, e, what):
        """isready -> readyok; nothing but info strings may come before it."""
        self.st["barriers"] += 1
        t0 = self.send(e, "isready")
        while True:
            t, line = self.get(e, t0 + READY_S, "timeout_readyok", f"isready after {what}")
            if line == "readyok":
                return
            self.handle_idle_line(e, t, line, f"before readyok after {what}")

    # ---------------- engine lifecycle ----------------
    def configure(self, e, log=None):
        """uci, advertised options, setoption, isready; raises GameError on any configuration problem."""
        t0 = self.send(e, "uci")
        advertised, lines = set(), []
        while True:
            t, line = self.get(e, t0 + UCIOK_S, "timeout_uciok", "uci")
            lines.append((t, line))
            if line == "uciok":
                break
            if line.startswith("option name "):
                advertised.add(line[len("option name "):].split(" type ")[0])
            elif not (line.startswith("id ") or line.startswith("info string")):
                self.err("unexpected_line", e, "unexpected output during uci", [(t, line)], fatal=True)
        missing = [n for n, _ in self.opts if n not in advertised]
        if missing:
            self.err("option_not_advertised", e, f"options not advertised by uci: {missing}", fatal=True)
        for name, value in self.opts:
            self.send(e, f"setoption name {name} value {value}")
        t_ready = self.send(e, "isready")
        n_uci = len(lines)
        try:
            while True:
                t, line = e.get(t_ready + CONFIG_READY_S)
                lines.append((t, line))
                if line == "readyok":
                    break
        except Timeout:
            self.err("timeout_readyok", e, "no readyok after the options", lines[n_uci:], fatal=True)
        except EngineDied as exc:
            self.err("config_error", e, f"engine exited during configuration: {exc}", lines[n_uci:], fatal=True)
        cfg_lines = lines[n_uci:]
        transient, v2_active, syzygy, lockless = [], False, None, False
        for t, line in cfg_lines:
            if line == "readyok":
                continue
            if not line.startswith("info string "):
                self.err("config_error", e, "unexpected line during configuration", [(t, line)], fatal=True)
            text = line[len("info string "):]
            if self.check_string(e, t, line, text, config=True) == "transient":
                transient.append((t, line))
            if text.startswith("NNUE v2: active"):
                v2_active = True
            if text.startswith("Syzygy: "):
                syzygy = text
            if text.startswith("LocklessTT active"):
                lockless = True
        names = {n: v for n, v in self.opts}
        wants_v2 = any(n in names and names[n] not in ("0", "false", "<empty>", "") for n in NNUE_OPTS)
        if transient and not (wants_v2 and v2_active):
            self.err("config_error", e, "NNUE v2 ERROR lines not resolved by an active net", transient, fatal=True)
        if wants_v2 and not v2_active:
            self.err("config_error", e, "NNUE v2 options set but no 'NNUE v2: active' line", cfg_lines, fatal=True)
        if names.get("SyzygyPath", "<empty>") not in ("<empty>", "") and \
                (syzygy is None or syzygy.startswith("Syzygy: 0 WDL") or "skipped" in syzygy):
            self.err("config_error", e, f"Syzygy tables not loaded cleanly: {syzygy}", cfg_lines, fatal=True)
        if names.get("LocklessTT") == "true" and not lockless:
            self.err("config_error", e, "LocklessTT set but no 'LocklessTT active' line", cfg_lines, fatal=True)
        if log is not None:
            log.update(advertised=sorted(advertised), config_lines=[[ts(t), s] for t, s in cfg_lines],
                       transient_errors=[s for _, s in transient], id=[s for _, s in lines if s.startswith("id ")])

    def start_pair(self):
        self.gen += 1
        self.engines = {}
        for tag in ("A", "B"):
            e = Engine(self.a.cmd, f"w{self.wid}{tag}{self.gen}", self.a.tmp_dir)
            self.engines[tag] = e
            self.configure(e)

    def quit_engine(self, e):
        """quit; the process must exit with status 0 within QUIT_S; leftover output must not contain a bestmove."""
        try:
            t0 = e.send("quit")
        except EngineDied as exc:
            self.err("crash", e, str(exc))
            e.kill()
            return
        try:
            code = e.proc.wait(timeout=QUIT_S)
        except subprocess.TimeoutExpired:
            self.err("timeout_quit", e, f"no exit within {QUIT_S} s after quit")
            e.kill()
            return
        rest = []   # everything up to EOF (the reader thread may still hold the last lines)
        try:
            while True:
                rest.append(e.get(time.perf_counter() + 5.0))
        except (EngineDied, Timeout):
            pass
        for t, line in rest:
            if line.startswith("bestmove"):
                self.err("extra_bestmove", e, "bestmove after the last search answered (at quit)", [(t, line)])
            elif line.startswith("info"):
                self.check_info(e, t, line, None)
            else:
                self.err("unexpected_line", e, "unexpected output at quit", [(t, line)])
        if e.stderr:
            self.err("stderr_output", e, "the engine wrote to stderr", e.stderr[:20])
        if code != 0:
            self.err("bad_exit_code", e, f"exit status {code} after quit (sent at {ts(t0)})")

    def stop_pair(self, clean=True):
        if not self.engines:
            return
        for e in self.engines.values():
            if clean:
                try:
                    self.quit_engine(e)
                except GameError:
                    pass
            else:
                try:
                    e.send("quit")
                    e.proc.wait(timeout=5)
                except Exception:
                    pass
                e.kill()
        self.engines = None

    # ---------------- one search ----------------
    def search(self, e, board, kind, rng, clock, inc):
        """One go on `board` (the engine already has the position); returns the bestmove (validated)."""
        st, a = self.st, self.a
        side = board.turn
        finish, limit = None, None
        clocked = f"wtime {clock[chess.WHITE]} btime {clock[chess.BLACK]} winc {inc} binc {inc}"
        if kind == "nodes":
            cmd = f"go nodes {rng.randint(a.nodes_min, a.nodes_max)}"
        elif kind == "depth":
            cmd = f"go depth {rng.randint(1, 6)}"
        elif kind == "movetime":
            limit = rng.randint(5, 30)
            cmd = f"go movetime {limit}"
        elif kind == "clock":
            limit = clock[side]
            cmd = f"go {clocked}"
        elif kind == "infinite":
            cmd, finish, limit = "go infinite", "stop", 0
        elif kind == "ponderhit":
            cmd, finish, limit = f"go ponder {clocked}", "ponderhit", clock[side]
        elif kind == "ponder_stop":
            cmd, finish, limit = f"go ponder {clocked}", "stop", 0
        else:
            raise ValueError(kind)
        t_go = self.send(e, cmd)
        e.last_go = cmd
        t_ref = t_go
        if finish:
            time.sleep(rng.randint(5, 50) / 1000)
            for t, line in e.pending():
                self.search_line(e, t, line, board, f"{cmd} before {finish}", early=True)
            if rng.random() < 0.3:
                st["mid_isready"] += 1
                t_r = self.send(e, "isready")
                while True:
                    t, line = self.get(e, t_r + READY_S, "timeout_readyok", f"isready during {cmd}")
                    if line == "readyok":
                        break
                    self.search_line(e, t, line, board, f"{cmd} before {finish} (isready)", early=True)
            t_ref = self.send(e, finish)
        timeout_ms = (FIXED_S * 1000 if limit is None else limit) + a.margin_ms
        while True:
            t, line = self.get(e, t_ref + timeout_ms / 1000, "timeout_bestmove",
                               f"{cmd}{' + ' + finish if finish else ''} (limit {limit} ms + {a.margin_ms} ms)")
            mv = self.search_line(e, t, line, board, cmd)
            if mv is not None:
                break
        elapsed = (t - t_ref) * 1000
        lat = st["lat"].setdefault(kind, dict(n=0, sum_ms=0.0, max_ms=0.0, max_over_ms=None, slow=0))
        lat["n"] += 1
        lat["sum_ms"] += elapsed
        lat["max_ms"] = max(lat["max_ms"], elapsed)
        if limit is not None:
            over = elapsed - limit
            lat["max_over_ms"] = over if lat["max_over_ms"] is None else max(lat["max_over_ms"], over)
            if over > 1000:
                lat["slow"] += 1
        if kind in ("clock", "ponderhit"):
            left = clock[side] - elapsed
            if left < 0:
                st["overruns"] += 1
                st["overrun_max_ms"] = max(st["overrun_max_ms"], -left)
                clock[side] = self.clock_base
                st["clock_resets"] += 1
            else:
                clock[side] = int(left) + inc
        return mv

    def search_line(self, e, t, line, board, what, early=False):
        if line.startswith("info"):
            self.check_info(e, t, line, board)
            return None
        if line.startswith("bestmove"):
            if early:
                self.err("bestmove_before_stop", e, f"bestmove during {what}", [(t, line)], fatal=True)
            self.close_prof_block(e, t, line)
            return self.check_bestmove(e, t, line, board)
        self.err("unexpected_line", e, f"unexpected output during {what}", [(t, line)], fatal=True)
        return None

    # ---------------- one game ----------------
    @staticmethod
    def position_cmd(start_fen, moves):
        return f"position fen {start_fen}" + (" moves " + " ".join(m.uci() for m in moves) if moves else "")

    @staticmethod
    def game_end(board):
        if not any(board.generate_legal_moves()):
            return "checkmate" if board.is_check() else "stalemate"
        if board.is_insufficient_material():
            return "insufficient_material"
        if board.halfmove_clock >= 100:
            return "fifty_moves"
        if board.is_repetition(3):
            return "threefold"
        return None

    def one_move(self, e, board, start_fen, kind, rng, clock, inc):
        st = self.st
        st["kinds"][kind] += 1
        if rng.random() < 0.03:
            st["stray_stops"] += 1
            self.send(e, "stop")
        if kind == "pondermiss":
            prev = board.copy()
            last = prev.pop() if prev.move_stack else None
            alts = [m for m in prev.legal_moves if m != last] if last is not None else []
            rng.shuffle(alts)
            alt_board = None
            for m in alts:
                b = prev.copy()
                b.push(m)
                if any(b.generate_legal_moves()):
                    alt_board = b
                    break
            if alt_board is None:
                kind = "ponderhit"
                st["kinds"]["pondermiss_fallback_hit"] += 1
            else:
                self.send(e, self.position_cmd(start_fen, alt_board.move_stack))
                self.barrier(e, "position (ponder guess)")
                self.search(e, alt_board, "ponder_stop", rng, clock, inc)
                kind = "clock"
        self.send(e, self.position_cmd(start_fen, board.move_stack))
        self.barrier(e, "position")
        return self.search(e, board, kind, rng, clock, inc)

    def play_game(self, gi):
        a = self.a
        rng = random.Random(f"{a.seed}:{gi}")
        oi = rng.randrange(len(self.sh.openings))
        fen, oid = self.sh.openings[oi]
        board = chess.Board(fen)
        a_white = gi % 2 == 0
        self.errors, self.st = [], new_stats()
        self.prof_block, self.prof_overflow = None, False
        self.ply, self.kind = None, "start"
        self.clock_base = rng.randint(200, 2000)
        inc = rng.choice((0, 10, 20, 30, 50))
        clock = {chess.WHITE: self.clock_base, chess.BLACK: self.clock_base}
        t_start = time.perf_counter()
        termination, result, restart = None, "*", False
        gen_at_start = self.gen
        try:
            if self.engines is None:
                self.start_pair()
                gen_at_start = self.gen
            for e in self.engines.values():
                self.send(e, "ucinewgame")
                self.barrier(e, "ucinewgame")
            while True:
                self.ply, self.kind = len(board.move_stack), None
                termination = self.game_end(board)
                if termination:
                    if termination == "checkmate":
                        result = "0-1" if board.turn == chess.WHITE else "1-0"
                    else:
                        result = "1/2-1/2"
                    break
                if len(board.move_stack) >= a.max_plies:
                    termination = "ply_cap"
                    break
                tag = "A" if (board.turn == chess.WHITE) == a_white else "B"
                total = sum(w for _, w in a.kinds)
                r = rng.randrange(total)
                for kind, w in a.kinds:
                    if r < w:
                        break
                    r -= w
                self.kind = kind
                board.push(self.one_move(self.engines[tag], board, fen, kind, rng, clock, inc))
        except GameError:
            termination, result, restart = "error", "*", True
        except Exception as exc:   # harness bug: record it as an error too
            self.err("harness_exception", None, f"{type(exc).__name__}: {exc}")
            termination, result, restart = "error", "*", True
        dumps = None
        if self.errors and self.engines:
            dumps = "\n".join(e.dump() for e in self.engines.values())
        if restart:
            self.stop_pair(clean=False)
        st = self.st
        rec = dict(record="game", config=a.name, game=gi, worker=self.wid, engine_gen=gen_at_start, opening=oi + 1,
                   opening_id=oid, start_fen=fen, white="A" if a_white else "B", result=result,
                   termination=termination, plies=len(board.move_stack), clock_base_ms=self.clock_base,
                   clock_inc_ms=inc, duration_s=round(time.perf_counter() - t_start, 3),
                   kinds=dict(st["kinds"]), barriers=st["barriers"], mid_isready=st["mid_isready"],
                   stray_stops=st["stray_stops"], info_lines=st["info_lines"], pv_moves=st["pv_moves"],
                   currmoves=st["currmoves"], empty_pv=st["empty_pv"], ponder_checked=st["ponder_checked"],
                   overruns=st["overruns"], overrun_max_ms=round(st["overrun_max_ms"], 1),
                   hard_deadline_fired=st["hd_fired"], tbhits_max=st["tbhits_max"], max_depth=st["max_depth"],
                   bestmoves=st["bestmoves"], prof_blocks=st["prof_blocks"], prof_lines=st["prof_lines"],
                   prof_overflow=st["prof_overflow"], bestmoves_without_prof=st["bestmoves_without_prof"],
                   watchdog_answers=st["watchdog_answers"], late_after_watchdog=st["late_after_watchdog"],
                   late_after_search=st["late_after_search"],
                   lat={k: dict(v, sum_ms=round(v["sum_ms"], 1), max_ms=round(v["max_ms"], 1),
                                max_over_ms=None if v["max_over_ms"] is None else round(v["max_over_ms"], 1))
                        for k, v in st["lat"].items()},
                   strings=dict(st["strings"]), moves=" ".join(m.uci() for m in board.move_stack),
                   errors=self.errors)
        game = chess.pgn.Game.from_board(board)
        game.headers.update({"Event": f"R3-1 selfplay {a.name}", "Site": "opus_selfplay_check.py",
                             "Round": str(gi), "White": f"{os.path.basename(a.exe)} {'A' if a_white else 'B'}",
                             "Black": f"{os.path.basename(a.exe)} {'B' if a_white else 'A'}", "Result": result,
                             "Termination": termination or "", "Opening": f"{oid} (#{oi + 1})"})
        self.sh.write(rec, str(game), dumps)
        if self.errors:
            self.sh.event(f"game {gi} w{self.wid}: {len(self.errors)} error(s), termination {termination}")

    def run(self):
        played_since_start = 0
        try:
            while True:
                gi = self.sh.next_game()
                if gi is None:
                    break
                if self.engines is not None and played_since_start >= self.a.restart_every:
                    self.errors, self.st = [], new_stats()
                    self.ply, self.kind = None, "restart"
                    self.stop_pair(clean=True)
                    if self.errors:   # quit problems: own record, counted in the summary
                        self.sh.write(dict(record="restart", config=self.a.name, worker=self.wid, before_game=gi,
                                           errors=self.errors))
                    self.sh.event(f"w{self.wid}: restarted the engine pair before game {gi}")
                if self.engines is None:
                    played_since_start = 0
                self.play_game(gi)
                played_since_start += 1
                if self.engines is None and self.errors and \
                        any(x["type"] in ("config_error", "option_not_advertised") for x in self.errors):
                    self.sh.abort = True   # every game would fail the same way
        finally:
            self.errors, self.st = [], new_stats()
            self.ply, self.kind = None, "final quit"
            self.stop_pair(clean=True)
            self.sh.write(dict(record="worker_end", config=self.a.name, worker=self.wid, engine_generations=self.gen,
                               errors=self.errors), None,
                          None)


def preflight(args, opts, openings_dir):
    """One engine: the options are advertised and accepted (readyok, no ERROR), activation lines logged,
    go depth 5 from the start position and bench 11 (node signature)."""
    sh = argparse.Namespace(event=lambda text: None, lock=threading.Lock(), prof_names=None)
    w = Worker.__new__(Worker)
    w.wid, w.sh, w.a, w.opts, w.errors, w.st, w.ply, w.kind = "P", sh, args, opts, [], new_stats(), None, "preflight"
    w.prof_block, w.prof_overflow = None, False
    e = Engine(args.cmd, "P", args.tmp_dir)
    log = dict(config=args.name, exe=args.exe, exe_sha256=sha256(args.exe), git_head=args.git_head,
               setoption=[f"{n}={v}" for n, v in opts])
    ok = True
    try:
        w.configure(e, log)
        board = chess.Board()
        w.send(e, "position startpos")
        w.barrier(e, "position")
        t0 = w.send(e, "go depth 5")
        go_lines = []
        while True:
            t, line = w.get(e, t0 + FIXED_S + args.margin_ms / 1000, "timeout_bestmove", "go depth 5")
            go_lines.append([ts(t), line])
            if w.search_line(e, t, line, board, "go depth 5") is not None:
                break
        log["go_depth5"] = go_lines
        t0 = w.send(e, "bench 11")
        while True:
            t, line = w.get(e, t0 + 600, "timeout_bestmove", "bench 11")
            if line.startswith("info string bench depth 11 nodes "):
                log["bench11_nodes"] = int(line.split()[6])
                log["bench11_line"] = line
                break
            if line.startswith("bestmove") or not line.startswith("info"):
                w.err("unexpected_line", e, "unexpected output during bench", [(t, line)], fatal=True)
        w.quit_engine(e)
    except GameError:
        ok = False
        e.kill()
    log["info_strings"] = [s for t, d, s in e.transcript if d == "<" and s.startswith("info string")
                           and not s.startswith("info string bench")]
    log["errors"] = w.errors
    log["ok"] = ok and not w.errors
    with open(os.path.join(args.out_dir, f"{args.name}.preflight.json"), "w", newline="\n", encoding="utf-8") as f:
        json.dump(log, f, indent=1)
    with open(os.path.join(args.out_dir, f"{args.name}.preflight.log"), "w", newline="\n", encoding="utf-8") as f:
        f.write(e.dump() + "\n")
    return log


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_openings(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            b = chess.Board()
            ops = b.set_epd(line.strip())
            b.halfmove_clock, b.fullmove_number = 0, 7   # 12 plies into the game (manifest.json)
            out.append((b.fen(), ops.get("id", "")))
    return out


def summarize(args, records, preflight_log, wall_s):
    games = [r for r in records if r.get("record") == "game"]
    errors = [x for r in records for x in r.get("errors", [])]
    by_type = Counter(x["type"] for x in errors)
    lat = {}
    for g in games:
        for k, v in g["lat"].items():
            s = lat.setdefault(k, dict(n=0, sum_ms=0.0, max_ms=0.0, max_over_ms=None, slow=0))
            s["n"] += v["n"]
            s["sum_ms"] += v["sum_ms"]
            s["max_ms"] = max(s["max_ms"], v["max_ms"])
            s["slow"] += v["slow"]
            if v["max_over_ms"] is not None:
                s["max_over_ms"] = v["max_over_ms"] if s["max_over_ms"] is None else max(s["max_over_ms"],
                                                                                        v["max_over_ms"])
    for s in lat.values():
        s["mean_ms"] = round(s["sum_ms"] / s["n"], 2) if s["n"] else None
        s["sum_ms"] = round(s["sum_ms"], 1)
    kinds = Counter()
    strings = Counter()
    for g in games:
        kinds.update(g["kinds"])
        strings.update(g["strings"])
    tot = lambda key: sum(g[key] for g in games)
    summary = dict(
        config=args.name, exe=args.exe, exe_sha256=preflight_log.get("exe_sha256"), git_head=args.git_head,
        threads=args.threads, options=[f"{n}={v}" for n, v in args.sent_opts], games_requested=args.games,
        games=len(games), plies=tot("plies"), plies_mean=round(tot("plies") / len(games), 1) if games else None,
        errors=len(errors), errors_by_type=dict(by_type),
        **{group: sum(by_type[t] for t in types) for group, types in ERROR_GROUPS.items()},
        preflight_ok=preflight_log.get("ok"), bench11_nodes=preflight_log.get("bench11_nodes"),
        activation_lines=preflight_log.get("info_strings"),
        results=dict(Counter(g["result"] for g in games)), terminations=dict(Counter(g["termination"] for g in games)),
        commands=dict(kinds), barriers=tot("barriers"), mid_isready=tot("mid_isready"), stray_stops=tot("stray_stops"),
        info_lines=tot("info_lines"), pv_moves_checked=tot("pv_moves"), currmoves_checked=tot("currmoves"),
        empty_pv_lines=tot("empty_pv"), ponder_moves_checked=tot("ponder_checked"),
        clock_overruns=tot("overruns"), clock_overrun_max_ms=max([g["overrun_max_ms"] for g in games] or [0]),
        hard_deadline_fired=tot("hard_deadline_fired"), tbhits_max=max([g["tbhits_max"] for g in games] or [0]),
        bestmoves=tot("bestmoves"), prof_blocks=tot("prof_blocks"), prof_lines=tot("prof_lines"),
        prof_overflow=tot("prof_overflow"), bestmoves_without_prof=tot("bestmoves_without_prof"),
        watchdog_answers=tot("watchdog_answers"), late_after_watchdog=tot("late_after_watchdog"),
        late_after_search=tot("late_after_search"),
        games_with_tbhits=sum(1 for g in games if g["tbhits_max"] > 0),
        max_depth=max([g["max_depth"] for g in games] or [0]),
        engine_generations=sum(r.get("engine_generations", 0) for r in records if r.get("record") == "worker_end"),
        latency=lat, info_strings=dict(strings.most_common(20)), wall_s=round(wall_s, 1),
        parallel=args.parallel, restart_every=args.restart_every, seed=args.seed, max_plies=args.max_plies,
        margin_ms=args.margin_ms, nodes_range=[args.nodes_min, args.nodes_max],
        mix={k: w for k, w in args.kinds})
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--exe", required=True, help="engine exe, or a .py UCI wrapper (run with this python -I -B)")
    ap.add_argument("--exe-arg", action="append", default=[], help="argument for the engine command (repeatable)")
    ap.add_argument("--opt", action="append", default=[], help="Name=value (repeatable, order kept)")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--games", type=int, default=500)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--restart-every", type=int, default=25)
    ap.add_argument("--seed", default="1")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--tmp-dir", default=None)
    ap.add_argument("--epd", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools",
                                                  "openings", "forge-10000.epd"))
    ap.add_argument("--max-plies", type=int, default=200)
    ap.add_argument("--nodes-min", type=int, default=300, help="go nodes N: N from this ...")
    ap.add_argument("--nodes-max", type=int, default=5000, help="... to this")
    ap.add_argument("--mix", default=",".join(f"{k}={w}" for k, w in KINDS),
                    help="command weights per move, e.g. nodes=50,clock=15,movetime=8,depth=8,infinite=7,"
                         "ponderhit=6,pondermiss=6 (the default)")
    ap.add_argument("--margin-ms", type=int, default=10000)
    ap.add_argument("--max-minutes", type=float, default=0)
    ap.add_argument("--git-head", default="")
    ap.add_argument("--preflight-only", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    args.tmp_dir = args.tmp_dir or args.out_dir
    args.cmd = ([sys.executable, "-I", "-B", args.exe] if args.exe.endswith(".py") else [args.exe]) + args.exe_arg
    user = []
    try:
        args.kinds = tuple((k, int(w)) for k, w in (item.split("=") for item in args.mix.split(",")))
    except ValueError:
        ap.error(f"--mix {args.mix!r}: expected kind=weight,...")
    unknown = [k for k, _ in args.kinds if k not in dict(KINDS)]
    if unknown or sum(w for _, w in args.kinds) <= 0 or not 1 <= args.nodes_min <= args.nodes_max:
        ap.error(f"bad --mix / --nodes-min / --nodes-max (unknown kinds {unknown})")
    for o in args.opt:
        name, sep, value = o.partition("=")
        if not sep:
            ap.error(f"--opt {o!r}: expected Name=value")
        user.append((name, value))
    args.sent_opts = [("Hash", str(args.hash)), ("Threads", str(args.threads)), ("Ponder", "true"),
                      ("OwnBook", "false")] + opt_order(user)

    pf = preflight(args, args.sent_opts, args.out_dir)
    print(f"[{args.name}] preflight {'OK' if pf['ok'] else 'FAILED'}: bench11 {pf.get('bench11_nodes')}; "
          f"activation: {pf.get('info_strings')}", flush=True)
    if not pf["ok"]:
        for x in pf["errors"]:
            print(f"  {x['type']}: {x['detail']} {x['lines']}", flush=True)
        with open(os.path.join(args.out_dir, f"{args.name}.summary.json"), "w", newline="\n") as f:
            json.dump(dict(config=args.name, preflight_ok=False, errors=len(pf["errors"]),
                           preflight_errors=pf["errors"]), f, indent=1)
        return 3
    if args.preflight_only:
        return 0
    openings = load_openings(args.epd)
    sh = Shared(args, openings)
    sh.event(f"start {args.name}: exe {args.exe} sha256 {pf['exe_sha256']} options {args.sent_opts} "
             f"games {args.games} parallel {args.parallel}")
    t0 = time.perf_counter()
    workers = [Worker(i, sh, args.sent_opts) for i in range(args.parallel)]
    threads = [threading.Thread(target=w.run, name=f"worker{w.wid}") for w in workers]
    for t in threads:
        t.start()
    last = 0
    while any(t.is_alive() for t in threads):
        time.sleep(1.0)
        with sh.lock:
            n = len([r for r in sh.records if r.get("record") == "game"])
        if n // 50 > last // 50:
            print(f"[{args.name}] {n} games, {time.perf_counter() - t0:.0f} s", flush=True)
        last = n
    for t in threads:
        t.join()
    summary = summarize(args, sh.records, pf, time.perf_counter() - t0)
    with open(os.path.join(args.out_dir, f"{args.name}.summary.json"), "w", newline="\n", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    sh.event(f"end: {summary['games']} games {summary['plies']} plies {summary['errors']} errors")
    for fh in (sh.jsonl, sh.pgn, sh.events):
        fh.close()
    print(f"[{args.name}] games {summary['games']}/{args.games} plies {summary['plies']} errors {summary['errors']} "
          f"crashes {summary['crashes']} illegal {summary['illegal_moves']} double_bestmove "
          f"{summary['double_bestmoves']} timeouts {summary['timeouts']} malformed {summary['malformed_output']} "
          f"wall {summary['wall_s']} s", flush=True)
    if summary["errors"]:
        print(f"[{args.name}] errors by type: {summary['errors_by_type']}", flush=True)
        return 1
    return 0 if summary["games"] == args.games else 4


if __name__ == "__main__":
    sys.exit(main())
