"""Generic self-play data generator: any UCI engine, fixed nodes per move, .plain output.

Each worker process owns one engine. Games start from the standard position (or a random book
line), a few random moves diversify the openings, then the engine plays both sides. Every searched
position is written as: fen / best move / score (side to move) / ply / game result (side to move).
Files are written per worker as *.plain.part and renamed to *_nCOUNT.plain when closed, so a crash
loses at most the games in progress. Leftover .part files are salvaged on the next start.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import random
import re
import time
from pathlib import Path

from .common import cpu_speed_pct, read_hwinfo, log, stop_requested
from .engine import EngineError, EngineSpec, UciEngine, engine_for_net, make_score_converter

_COUNT_RE = re.compile(r"_n(\d+)\.plain$")


def _book_lines(path: str) -> list[str] | None:
    if not path:
        return None
    lines = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                lines.append(" ".join(parts[:4]) + " 0 1")
    return lines or None


def play_game(eng: UciEngine, rng: random.Random, g: dict, convert, book):
    """Play one self-play game. Returns (plain_text, n_records, result_white, plies)."""
    import chess

    if book:
        start_fen = rng.choice(book)
        board = chess.Board(start_fen)
        pos_prefix = f"position fen {start_fen}"
    else:
        board = chess.Board()
        pos_prefix = "position startpos"
    moves: list[str] = []
    lo, hi = int(g["random_move_min_ply"]), int(g["random_move_max_ply"])
    k = min(int(g["random_move_count"]), max(0, hi - lo + 1))
    random_plies = set(rng.sample(range(lo, hi + 1), k)) if k > 0 else set()
    nodes = int(g["nodes"])
    # [datagen] soft_nodes (2026-11-14): with N > 0 the labelled searches use `go softnodes N`: the engine stops
    # after the first FINISHED iteration with at least N nodes (hard cap 4 N) instead of being cut off in the
    # middle of an iteration at `nodes`. With `go nodes 5000` the last finished iteration ended at 3,433 nodes on
    # average and the rest (31 %) was thrown away: the move and the score both come from that iteration.
    soft = int(g.get("soft_nodes", 0) or 0)
    go_cmd = f"go softnodes {soft}" if soft > 0 else f"go nodes {nodes}"
    eval_limit = int(g["eval_limit"])
    write_min_ply = int(g["write_min_ply"])
    max_ply = int(g["max_ply"])
    dr_ply, dr_score, dr_count = int(g["draw_adj_ply"]), int(g["draw_adj_score"]), int(g["draw_adj_count"])
    move_timeout = float(g.get("move_timeout_s", 60))
    rmpv = int(g.get("random_multi_pv", 0))
    rmpv_diff = int(g.get("random_multi_pv_diff", 100))
    recs = []
    result = None  # +1 white wins, 0 draw, -1 black wins
    draw_run = 0
    eng.new_game()
    while True:
        ply = len(moves)
        # one legal-move generation decides both mate and stalemate
        if not any(board.generate_legal_moves()):
            result = (-1 if board.turn == chess.WHITE else 1) if board.is_check() else 0
            break
        # a third occurrence needs at least 8 reversible plies, so the repetition scan is skipped before that
        if (board.is_insufficient_material() or board.halfmove_clock >= 100
                or (board.halfmove_clock >= 8 and board.is_repetition(3)) or ply >= max_ply):
            result = 0
            break
        pos_cmd = pos_prefix + (" moves " + " ".join(moves) if moves else "")
        if ply in random_plies:
            mv = None
            if rmpv > 1:
                # random choice among the engine's best few moves that are close to the best one
                lines = eng.search_multipv(pos_cmd, f"go nodes {nodes * rmpv}", rmpv, timeout=move_timeout)
                cps = [(m, convert(v, board)) for m, (kind, v) in lines if kind == "cp"]
                if cps:
                    top = max(s for _m, s in cps)
                    pick = rng.choice([m for m, s in cps if s >= top - rmpv_diff])
                    try:
                        cand = chess.Move.from_uci(pick)
                        if board.is_legal(cand):
                            mv = cand
                    except ValueError:
                        pass
                elif lines:
                    try:
                        cand = chess.Move.from_uci(lines[0][0])
                        if board.is_legal(cand):
                            mv = cand
                    except ValueError:
                        pass
            if mv is None:
                mv = rng.choice(list(board.legal_moves))
            board.push(mv)
            moves.append(mv.uci())
            continue
        bm, sc = eng.search(pos_cmd, go_cmd, timeout=move_timeout)
        if sc is None or not bm or bm in ("(none)", "0000"):
            # the position is named so that the case can be repeated by hand (seen twice in 45 million
            # `go softnodes` searches on 2026-11-15: a move without any score line)
            raise EngineError(f"no move/score at ply {ply}: bestmove={bm} score={sc}; fen {board.fen()}; "
                              f"command {go_cmd}")
        kind, val = sc
        white_to_move = board.turn == chess.WHITE
        if kind == "mate":
            result = (1 if white_to_move else -1) * (1 if val > 0 else -1)
            break
        score = convert(val, board)
        if abs(score) >= eval_limit:
            result = (1 if white_to_move else -1) * (1 if score > 0 else -1)
            break
        try:
            mv = chess.Move.from_uci(bm)
        except ValueError:
            raise EngineError(f"unparsable bestmove {bm!r}")
        if not board.is_legal(mv):
            raise EngineError(f"illegal bestmove {bm} in {board.fen()}")
        if ply >= write_min_ply:
            recs.append((board.fen(), bm, score, ply, white_to_move))
        if ply >= dr_ply and abs(score) <= dr_score:
            draw_run += 1
            if draw_run >= dr_count:
                result = 0
                break
        else:
            draw_run = 0
        board.push(mv)
        moves.append(bm)
    out = []
    for fen, bm, score, ply, wtm in recs:
        res = result if wtm else -result
        out.append(f"fen {fen}\nmove {bm}\nscore {score}\nply {ply}\nresult {res}\ne\n")
    return "".join(out), len(recs), result, len(moves)


def _worker(wid: int, spec_d: dict, cfg: dict, out_dir: str, rotate: int, seed: str,
            n_pos, n_games, n_plies, n_restarts, stop_ev, pause_ev=None, active=None) -> None:
    g = cfg["datagen"]
    rng = random.Random(seed)
    convert = make_score_converter(cfg)
    book = _book_lines(g.get("book", ""))
    spec = EngineSpec(**spec_d)
    stamp = f"{int(time.time())}_{os.getpid()}"
    out = Path(out_dir)
    idx = 0
    fh = None
    part = None
    in_file = 0
    eng = None
    fails = 0

    def close_file():
        nonlocal fh, part, in_file, idx
        if fh is None:
            return
        fh.close()
        if in_file > 0:
            os.replace(part, part.with_name(part.name[: -len(".plain.part")] + f"_n{in_file}.plain"))
        else:
            part.unlink(missing_ok=True)
        fh, part, in_file = None, None, 0
        idx += 1

    try:
        while not stop_ev.is_set():
            if pause_ev is not None and pause_ev.is_set():
                time.sleep(1.0)       # cooling pause asked for by the heat guard: idle between games
                continue
            if active is not None and wid >= active.value:
                time.sleep(1.0)       # the heat guard lets fewer workers play for now: this one idles between games
                continue
            try:
                if eng is None:
                    eng = UciEngine(spec)
                text, n, _result, plies = play_game(eng, rng, g, convert, book)
                fails = 0
            except EngineError as e:
                fails += 1
                with n_restarts.get_lock():
                    n_restarts.value += 1
                # Why the engine was restarted (2026-11-15: the first restart in about 100 million positions came
                # without a trace). One line per event in <round>/data/engine_restarts.log; the game is thrown away.
                try:
                    code = None if eng is None else eng.p.poll()
                    with open(out.parent / "engine_restarts.log", "a", encoding="utf-8") as lf:
                        lf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} worker {wid}: {e}; engine exit code {code}\n")
                except OSError:
                    pass
                if eng is not None:
                    eng.quit()
                    eng = None
                if fails >= 5:
                    raise RuntimeError(f"worker {wid}: engine failed 5 times in a row: {e}")
                time.sleep(1.0)
                continue
            if n:
                if fh is None:
                    part = out / f"sp_w{wid:02d}_{stamp}_{idx:03d}.plain.part"
                    fh = open(part, "w", encoding="ascii", newline="\n")
                fh.write(text)
                fh.flush()
                in_file += n
            with n_pos.get_lock():
                n_pos.value += n
            with n_games.get_lock():
                n_games.value += 1
            with n_plies.get_lock():
                n_plies.value += plies
            if in_file >= rotate:
                close_file()
    finally:
        close_file()
        if eng is not None:
            eng.quit()


def salvage_parts(out_dir: Path) -> int:
    """Turn leftover *.plain.part files (from a crash) into finished files, keeping whole records."""
    saved = 0
    for part in sorted(out_dir.glob("*.plain.part")):
        data = part.read_bytes()
        cut = data.rfind(b"\ne\n")
        data = data[: cut + 3] if cut >= 0 else b""
        n = data.count(b"\ne\n")
        if n > 0:
            final = part.with_name(part.name[: -len(".plain.part")] + f"_n{n}.plain")
            tmp = part.with_name(part.name + ".salv")
            tmp.write_bytes(data)
            os.replace(tmp, final)
            saved += n
        part.unlink(missing_ok=True)
    return saved


def count_done(out_dir: Path) -> int:
    total = 0
    for p in out_dir.glob("*.plain"):
        m = _COUNT_RE.search(p.name)
        if m:
            total += int(m.group(1))
    return total


class StopRequested(RuntimeError):
    pass


class HeatGuard:
    """Pauses self-play when the CPU is too hot, and resumes it when it has cooled.

    Source 1: the CPU temperature in HWiNFO's log file (if the owner has that logging on).
    Source 2, when there is no fresh log: the CPU's speed. A CPU that overheats lowers its frequency,
    so a lasting drop below `speed_drop` of the speed seen at the start of this run counts as "hot".
    Config, block [limits]: cpu_temp_pause_c (default 92), cpu_temp_resume_c (default 80),
    heat_checks (default 6 checks 20 s apart must agree), cool_seconds (default 180, the shortest pause),
    heat_guard (default true).

    Since 2026-11-14 22:45 it first lets FEWER WORKERS play before it pauses all of them (heat_throttle,
    default true; only with a real temperature reading). Why: with the graphics card training in the same case
    the CPU reached 94 C with 16 workers, and the guard then cycled 2 minutes of play and 3 minutes of pause,
    so self-play ran 40 % of the time and the CPU went up and down by 8 C every five minutes. Now: at the pause
    temperature or above on 2 checks in a row, 2 workers fewer play (never fewer than heat_min_workers, default
    4); at heat_add_worker_c (default: 2 C under the pause temperature) or below on 2 checks in a row, 1 more
    plays. The CPU then stays just under the limit and self-play goes on. Only when the smallest number of
    workers is still too hot for heat_checks checks does the full pause come, as before.
    """

    def __init__(self, cfg: dict, pause_ev, active=None, n_workers: int = 0):
        lim = cfg.get("limits") or {}
        self.cfg = cfg
        self.pause_ev = pause_ev
        self.active = active            # shared number: workers 0 .. active-1 play, the others idle
        self.n_workers = int(n_workers)
        self.min_workers = max(1, min(int(lim.get("heat_min_workers", 4)), self.n_workers or 1))
        self.throttle = bool(lim.get("heat_throttle", True)) and active is not None and self.n_workers > 0
        self.t_add = float(lim.get("heat_add_worker_c", float(lim.get("cpu_temp_pause_c", 92)) - 2.0))
        self.up = 0
        self.down = 0
        self.min_active = self.n_workers
        self.changes = 0
        self.temp_c = None
        self.on = bool(lim.get("heat_guard", True))
        self.t_pause = float(lim.get("cpu_temp_pause_c", 92))
        self.t_resume = float(lim.get("cpu_temp_resume_c", 80))
        self.need = int(lim.get("heat_checks", 6))
        self.cool_s = float(lim.get("cool_seconds", 180))
        self.speed_drop = float(lim.get("cpu_speed_drop", 0.85))
        self.every = float(lim.get("heat_check_seconds", 20))
        self.last = 0.0
        self.hot = 0
        self.pauses = 0
        self.cpu_max = None
        self.paused_at = None
        self.speeds: list[float] = []
        self.base_speed = None
        self.text = "heat guard starting"

    def _read(self):
        """(is_hot, can_resume, text)"""
        h = read_hwinfo(self.cfg)
        fake = os.environ.get("NNLOOP_FAKE_CPU_FILE")    # test hook: a file holding a pretended temperature
        if fake:
            try:
                with open(fake, encoding="ascii") as fh:
                    h = {"cpu_c": float(fh.read().strip()), "throttle": False}
            except (OSError, ValueError):
                pass
        if h and h.get("cpu_c") is not None:
            t = h["cpu_c"]
            self.temp_c = t
            self.cpu_max = t if self.cpu_max is None else max(self.cpu_max, t)
            return (t >= self.t_pause or bool(h.get("throttle"))), t <= self.t_resume, f"CPU {t:.0f} C"
        self.temp_c = None
        sp = cpu_speed_pct(0.5)
        if sp is None:
            return False, True, "no temperature or speed reading"
        if self.paused_at is None:
            if len(self.speeds) < 9:
                self.speeds.append(sp)
                self.base_speed = sorted(self.speeds)[len(self.speeds) // 2]
        base = self.base_speed or sp
        return sp < self.speed_drop * base, True, f"no temperature log, CPU speed {sp:.0f}% (start {base:.0f}%)"

    def tick(self) -> None:
        if not self.on or time.time() - self.last < self.every:
            return
        self.last = time.time()
        try:
            hot, cool, text = self._read()
        except Exception as e:  # noqa: BLE001
            self.text = f"heat guard error {type(e).__name__}"
            return
        self.text = text
        if self.paused_at is None:
            if self.throttle and self.temp_c is not None:
                now = self.active.value
                if hot:
                    self.down, self.up = self.down + 1, 0
                    if now > self.min_workers:
                        self.hot = 0          # no full pause while fewer workers can still be tried
                        if self.down >= 2:
                            new = max(self.min_workers, now - 2)
                            self.active.value = new
                            self.down = 0
                            self.changes += 1
                            self.min_active = min(self.min_active, new)
                            log(f"HEAT GUARD: {text}. {new} of {self.n_workers} self-play workers play now (was {now}).")
                        return
                elif self.temp_c <= self.t_add:
                    self.up, self.down = self.up + 1, 0
                    if self.up >= 2 and now < self.n_workers:
                        self.active.value = now + 1
                        self.up = 0
                        self.changes += 1
                        log(f"HEAT GUARD: {text}. {now + 1} of {self.n_workers} self-play workers play now (was {now}).")
                else:
                    self.up = self.down = 0
            self.hot = self.hot + 1 if hot else 0
            if self.hot >= self.need:
                self.pause_ev.set()
                self.paused_at = time.time()
                self.pauses += 1
                self.hot = 0
                log(f"HEAT GUARD: {text} for {self.need} checks in a row. Self-play pauses to cool down "
                    f"(pause number {self.pauses} of this stage).")
        else:
            waited = time.time() - self.paused_at
            if waited >= self.cool_s and cool and not hot:
                self.pause_ev.clear()
                log(f"HEAT GUARD: {text} after {waited:.0f} s of pause. Self-play goes on.")
                self.paused_at = None
            elif waited >= 20 * 60:
                self.pause_ev.clear()
                log(f"HEAT GUARD: still {text} after 20 minutes of pause. Self-play goes on anyway; "
                    f"please check the cooler, the fans and the room temperature.")
                self.paused_at = None

    def status(self) -> str:
        part = ""
        if self.throttle and self.active.value < self.n_workers:
            part = f", {self.active.value} of {self.n_workers} workers playing (heat)"
        return self.text + part + (" (PAUSED to cool)" if self.paused_at is not None else "")


def generate(cfg: dict, round_no: int, net_path: str | None, out_dir: Path, target: int) -> dict:
    g = cfg["datagen"]
    out_dir.mkdir(parents=True, exist_ok=True)
    salvaged = salvage_parts(out_dir)
    have = count_done(out_dir)
    if salvaged:
        log(f"selfplay: salvaged {salvaged} positions from interrupted files")
    if have >= target:
        log(f"selfplay: already have {have} >= {target} positions")
        return {"positions": have, "backend": "uci_selfplay", "resumed_with": have}
    spec = engine_for_net(cfg, net_path)
    spec_d = {"exe": spec.exe, "options": spec.options, "cwd": spec.cwd}
    workers = int(g["workers"])
    rotate = max(2000, int(g.get("chunk_positions", 250000)) // workers)
    ctx = mp.get_context("spawn")
    n_pos, n_games, n_plies, n_restarts = (ctx.Value("q", 0) for _ in range(4))
    stop_ev = ctx.Event()
    pause_ev = ctx.Event()
    active = ctx.Value("i", workers)
    guard = HeatGuard(cfg, pause_ev, active, workers)
    need = target - have
    log(f"selfplay: round {round_no}, need {need} more positions (have {have}), {workers} workers, "
        f"{('softnodes ' + str(g['soft_nodes'])) if int(g.get('soft_nodes', 0) or 0) > 0 else str(g['nodes']) + ' nodes'}/move, engine {spec.exe}, options {spec.options}")
    procs = []
    for w in range(workers):
        seed = f"{g.get('seed', 1)}-{round_no}-{w}-{time.time_ns()}"
        p = ctx.Process(target=_worker, args=(w, spec_d, cfg, str(out_dir), rotate, seed,
                                              n_pos, n_games, n_plies, n_restarts, stop_ev, pause_ev, active),
                        daemon=True)
        p.start()
        procs.append(p)
    t0 = time.time()
    last_log = t0
    stopped_by_user = False
    try:
        while True:
            time.sleep(2.0)
            done = n_pos.value
            if done >= need:
                break
            if stop_requested(cfg):
                stopped_by_user = True
                break
            guard.tick()
            alive = sum(p.is_alive() for p in procs)
            if alive == 0:
                raise RuntimeError("selfplay: all workers died; see errors above")
            if time.time() - last_log >= 60:
                el = time.time() - t0
                rate = done / el if el > 0 else 0
                eta = (need - done) / rate / 60 if rate > 0 else float("inf")
                log(f"selfplay: {have + done}/{target} positions, {n_games.value} games, {rate:.0f} pos/s, "
                    f"{alive}/{workers} workers alive, {n_restarts.value} engine restarts, ETA {eta:.1f} min; "
                    f"{guard.status()}")
                last_log = time.time()
    finally:
        stop_ev.set()
        deadline = time.time() + 180
        for p in procs:
            p.join(timeout=max(1, deadline - time.time()))
        for p in procs:
            if p.is_alive():
                p.terminate()
    salvage_parts(out_dir)
    el = time.time() - t0
    total = count_done(out_dir)
    stats = {"positions": total, "new_positions": n_pos.value, "games": n_games.value,
             "plies": n_plies.value, "seconds": round(el, 1),
             "pos_per_s": round(n_pos.value / el, 1) if el > 0 else 0,
             "engine_restarts": n_restarts.value, "backend": "uci_selfplay", "workers": workers,
             "nodes": int(g["nodes"]), "soft_nodes": int(g.get("soft_nodes", 0) or 0), "net": str(net_path),
             "cooling_pauses": guard.pauses, "cpu_c_max": guard.cpu_max,
             "heat_worker_changes": guard.changes, "heat_fewest_workers": guard.min_active,
             "workers_playing_at_end": active.value}
    log(f"selfplay: finished with {total} positions in {el:.0f} s ({stats['pos_per_s']} pos/s, "
        f"{n_games.value} games, {n_restarts.value} engine restarts)")
    if stopped_by_user:
        raise StopRequested("STOP file found during self-play")
    return stats
