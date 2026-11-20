#!/usr/bin/env python3
"""
Job 47 Shared Harness Library (`j47_lib.py`):
- Enforces the strict Job 47 UCI & runner rules on EVERY engine invocation (`bench`, `perft`,
  `O`/`G` depth-12 sweeps, `Set A` / `n[1..60]` `selfgame`, `6b98f217` `S14` sweeps, and `fastchess`):
  1. Parses the executable's own `uci` -> `uciok` option list and verifies EVERY option sent via
     `setoption name <name> value <val>` is present in that `uci` list.
  2. Keeps EVERY line the engine prints before EVERY `readyok` (after `uci`, after `setoption` block,
     after `ucinewgame`, after `position`, and after `bench`/`perft`), recording kept pre-`readyok`
     lines in `.meta`, and STOPS IMMEDIATELY (`RuntimeError`) on `unknown option`, `invalid value`,
     `illegal`, `invalid FEN`, or `ERROR`.
- Builds `bundle10` (`bundle9 + job47/P10_on_bundle9.patch.txt`) and `bundle11` (`bundle10 + job47/P11_K4b.patch.txt`).
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import random
import re
import shutil
import signal
import subprocess
import sys
import time
from typing import Optional, Sequence

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB47 = REPO / "forge-combo29/carbon2/job47"
JOB46 = REPO / "forge-combo29/carbon2/job46"
JOB45 = REPO / "forge-combo29/carbon2/job45"
JOB44 = REPO / "forge-combo29/carbon2/job44"
JOB43 = REPO / "forge-combo29/carbon2/job43"
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB38 = REPO / "forge-combo29/carbon2/job38"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK47 = pathlib.Path("/tmp/carbon2_job47")
WORK45 = pathlib.Path("/tmp/carbon2_job45")
WORK44 = pathlib.Path("/tmp/carbon2_job44")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")
NET768 = "/tmp/carbon2_work/net768.fnn3"

P10_BUNDLE8_PATCH = JOB45 / "P10_B8b_fast.patch.txt"
P10_ON_BUNDLE9_PATCH = JOB47 / "P10_on_bundle9.patch.txt"
P11_K4B_PATCH = JOB47 / "P11_K4b.patch.txt"

EXP_B8_O_SUM = 8262696
EXP_SETA_L_SEARCHES = 26867
EXP_T2_B_RECORDS = 27817
EXP_T2_B_SEARCHES = 27939
EXP_T2_B_NODES = 112503041
EXP_T2_B_SHA = "bd9112cddb7324be81977fee964aee031819a90338a6bc66fdf60c2d7aa85e1d"
EXP_T2_BA_WALL_RATIO = 1.137204
EXP_T2_BA_RPS_RATIO = 0.914732

TEN_BUNDLE10_IDEA_NAMES = [
    "IdeaK4",
    "IdeaS32",
    "IdeaB1",
    "IdeaS13",
    "IdeaS13_Hoist",
    "IdeaS10",
    "IdeaB8",
    "IdeaB8_Fast",
    "IdeaB8b",
    "IdeaB8b_Fast",
]
ALL_TEN_IDEA_FALSE = [(o, "false") for o in TEN_BUNDLE10_IDEA_NAMES]
ALL_ELEVEN_FALSE = ALL_TEN_IDEA_FALSE + [("HindsightDepth", "false")]

ELEVEN_BUNDLE11_IDEA_NAMES = TEN_BUNDLE10_IDEA_NAMES + ["IdeaK4b"]
ALL_ELEVEN_IDEA_FALSE = [(o, "false") for o in ELEVEN_BUNDLE11_IDEA_NAMES]
ALL_TWELVE_FALSE = ALL_ELEVEN_IDEA_FALSE + [("HindsightDepth", "false")]

sys.path.insert(0, str(JOB46))
sys.path.insert(0, str(JOB44))
sys.path.insert(0, str(JOB43))
sys.path.insert(0, str(JOB42))
sys.path.insert(0, str(JOB41))
sys.path.insert(0, str(JOB40))
sys.path.insert(0, str(JOB39))
sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from j46_lib import (  # noqa: E402
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    BUNDLE7_PATCH,
    EXP_B8B_O_SUM,
    EXP_BASE_V3_SHA,
    EXP_BUNDLE7_SHA,
    EXP_BUNDLE9_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_PC_S13_HOIST_G_FIRST5,
    EXP_PC_S13_HOIST_G_SUM,
    EXP_PC_S13_HOIST_O_FIRST5,
    EXP_PC_S13_HOIST_O_SUM,
    EXP_S10_O_SUM,
    EXP_S10_VS_OFF_BM_DIFF,
    EXP_S10_VS_OFF_ND_DIFF,
    EXP_S13_ALONE_O_SUM,
    EXP_S13_VS_OFF_ND_DIFF,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    UHO_BOOK,
    apply_bundle9_to_fresh_v3,
    build_release_v3,
    count_row_diffs,
    fmt_cmp,
    load_fens,
    pgn_to_games_tsv,
    read_j39_rows,
    recount_games_tsv,
    sha256_file,
    utc_now,
)
from j39_lib import (  # noqa: E402
    EXP_BENCH11_NOOPT,
    EXP_BENCH11_PC20,
    EXP_BENCH13_NOOPT,
    EXP_BENCH13_PC20,
    EXP_N60_L_NODES,
    EXP_N60_L_RECORDS,
    EXP_N60_L_SEARCHES,
    EXP_N60_L_SHA,
    EXP_PERFT5_NOOPT,
    LINE_L_CMD,
    generate_diff_u_patch,
    write_v2_v3_rows,
)

_OPT_DECL_RE = re.compile(r"^option name (.+?) type (check|spin|combo|button|string)\b")
_WORD_ERROR_RE = re.compile(r"\berror\b", re.IGNORECASE)


def check_engine_line_strict(line: str, context: str, *, allow_sgerror_prefix: bool = False) -> None:
    """
    Stops immediately on `unknown option`, `invalid value`, `illegal`, `invalid FEN`, or `ERROR`.
    In `selfgame` loops (`allow_sgerror_prefix=True`), valid protocol lines starting with `sgerror `
    are handled by the selfgame parser while any other `error`/`ERROR` token still raises.
    """
    low = line.lower()
    for marker in ("unknown option", "invalid value", "illegal", "invalid fen"):
        if marker in low:
            raise RuntimeError(f"Engine error marker {marker!r} in {context}: {line!r}")
    if allow_sgerror_prefix and line.startswith("sgerror "):
        return
    if "ERROR" in line or _WORD_ERROR_RE.search(line) or (not allow_sgerror_prefix and "error" in low):
        raise RuntimeError(f"Engine ERROR line in {context}: {line!r}")


def parse_uci_declared_options(uci_lines: Sequence[str]) -> set[str]:
    declared: set[str] = set()
    for ln in uci_lines:
        m = _OPT_DECL_RE.match(ln.strip())
        if m:
            declared.add(m.group(1))
    return declared


def assert_options_in_uci_list(
    opt_pairs: Sequence[tuple[str, str]],
    declared_opts: set[str],
    exe_path: str,
) -> None:
    missing = [k for k, _ in opt_pairs if k not in declared_opts]
    if missing:
        raise RuntimeError(
            f"Options sent to {exe_path} are NOT in its uci option list: {missing} "
            f"(declared count={len(declared_opts)})"
        )


class StrictEngineSession:
    """
    Line-buffered UCI engine wrapper that:
    - Reads and keeps all lines up to `uciok`, extracting `id_name` and `declared_options`.
    - Verifies every `setoption` name is in `declared_options`.
    - Keeps every line printed before EVERY `readyok` (stored in `pre_readyok_lines`) and
      calls `check_engine_line_strict` on every stdout and stderr line.
    """

    def __init__(self, exe_path: str, cpu_pin: Optional[int] = None) -> None:
        self.exe_path = str(exe_path)
        self.cpu_pin = cpu_pin
        cmd = [self.exe_path] if cpu_pin is None else ["taskset", "-c", str(cpu_pin), self.exe_path]
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert self.proc.stdin is not None and self.proc.stdout is not None and self.proc.stderr is not None
        self.pre_readyok_lines: list[str] = []
        self.sent_option_lines: list[str] = []
        self.verified_option_count: int = 0

        self.send("uci")
        self.uci_lines = self._read_until_exact("uciok", "uci")
        self.declared_options = parse_uci_declared_options(self.uci_lines)
        self.id_name = ""
        for ln in self.uci_lines:
            if ln.startswith("id name "):
                self.id_name = ln
                break
        if not self.id_name:
            raise RuntimeError(f"Missing 'id name' from {self.exe_path}")

    def send(self, cmd_block: str) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(cmd_block if cmd_block.endswith("\n") else cmd_block + "\n")
        self.proc.stdin.flush()

    def _read_until_exact(self, token: str, ctx: str, *, keep_pre_readyok: bool = False) -> list[str]:
        assert self.proc.stdout is not None and self.proc.stderr is not None
        kept: list[str] = []
        while True:
            ln = self.proc.stdout.readline()
            if ln == "":
                err_txt = self.proc.stderr.read()
                raise RuntimeError(f"Unexpected EOF waiting for {token!r} in {ctx} ({self.exe_path}); stderr={err_txt!r}")
            s = ln.rstrip("\r\n")
            check_engine_line_strict(s, ctx)
            if s == token:
                return kept
            kept.append(s)
            if keep_pre_readyok:
                self.pre_readyok_lines.append(f"[{ctx}] {s}")

    def wait_ready(self, ctx: str) -> list[str]:
        self.send("isready")
        return self._read_until_exact("readyok", ctx, keep_pre_readyok=True)

    def apply_options(self, opt_pairs: Sequence[tuple[str, str]], ctx: str = "setoption") -> list[str]:
        if not opt_pairs:
            return self.wait_ready(ctx)
        assert_options_in_uci_list(opt_pairs, self.declared_options, self.exe_path)
        lines = [f"setoption name {k} value {v}" for k, v in opt_pairs]
        self.sent_option_lines.extend(lines)
        self.verified_option_count += len(opt_pairs)
        self.send("\n".join(lines))
        return self.wait_ready(ctx)

    def close(self) -> None:
        assert self.proc.stdin is not None and self.proc.stderr is not None and self.proc.stdout is not None
        if self.proc.poll() is None:
            try:
                self.send("quit")
            except BrokenPipeError:
                pass
        stderr_txt = self.proc.stderr.read()
        rc = self.proc.wait()
        self.proc.stdin.close()
        self.proc.stdout.close()
        self.proc.stderr.close()
        for sln in stderr_txt.splitlines():
            check_engine_line_strict(sln, "stderr")
        if rc != 0 or stderr_txt:
            raise RuntimeError(f"Engine {self.exe_path} exited rc={rc} stderr={stderr_txt!r}")


def get_id_name_strict(exe_path: str) -> str:
    sess = StrictEngineSession(exe_path)
    name = sess.id_name
    sess.close()
    return name


def verify_uci_option_strict(
    exe_path: str,
    opt_name: str,
    opt_type: str = "check",
    default_val: str = "false",
    test_values: Sequence[str] = ("true", "false"),
) -> tuple[bool, list[str]]:
    sess = StrictEngineSession(exe_path)
    expected_prefix = f"option name {opt_name} type {opt_type} default {default_val}"
    found_decl = any(ln.strip().startswith(expected_prefix) for ln in sess.uci_lines)
    in_set = opt_name in sess.declared_options
    for tv in test_values:
        sess.apply_options([(opt_name, tv)], f"test {opt_name}={tv}")
    pre_cnt = len(sess.pre_readyok_lines)
    sess.close()
    bname = pathlib.Path(exe_path).parent.name
    ok1, s1 = fmt_cmp(f"{bname} uci declares {opt_name} ({opt_type}={default_val})", found_decl and in_set, True)
    ok2, s2 = fmt_cmp(f"{bname} {opt_name} pre-readyok lines", pre_cnt, 0)
    return (ok1 and ok2), [s1, s2]


def run_fresh_bench_strict(exe_path: str, depth: int, opt_pairs: Sequence[tuple[str, str]]) -> int:
    sess = StrictEngineSession(exe_path)
    sess.apply_options(opt_pairs, f"bench {depth} options")
    sess.send(f"bench {depth}")
    assert sess.proc.stdout is not None
    prefix = f"info string bench depth {depth} nodes "
    bench_nodes: Optional[int] = None
    sess.send("isready")
    while True:
        ln = sess.proc.stdout.readline()
        if ln == "":
            raise RuntimeError(f"EOF in bench {depth} from {exe_path}")
        s = ln.rstrip("\r\n")
        check_engine_line_strict(s, f"bench {depth}")
        if s.startswith(prefix):
            bench_nodes = int(s[len(prefix) :].split()[0])
        elif s == "readyok":
            break
    sess.close()
    if bench_nodes is None:
        raise RuntimeError(f"Missing {prefix!r} from {exe_path}")
    return bench_nodes


def run_fresh_perft5_strict(exe_path: str) -> int:
    sess = StrictEngineSession(exe_path)
    sess.wait_ready("perft5 init")
    sess.send("position startpos")
    sess.wait_ready("perft5 position")
    sess.send("go perft 5")
    sess.send("isready")
    assert sess.proc.stdout is not None
    perft_nodes: Optional[int] = None
    while True:
        ln = sess.proc.stdout.readline()
        if ln == "":
            raise RuntimeError(f"EOF in perft 5 from {exe_path}")
        s = ln.rstrip("\r\n")
        check_engine_line_strict(s, "perft 5")
        if s.startswith("nodes "):
            perft_nodes = int(s.split()[1])
        elif s == "readyok":
            break
    sess.close()
    if perft_nodes is None:
        raise RuntimeError(f"Missing 'nodes <N>' in perft 5 from {exe_path}")
    return perft_nodes


def run_epd_depth12_strict(
    exe_path: str,
    set_path: pathlib.Path,
    base_opts: Sequence[tuple[str, str]],
    extra_opts: Optional[Sequence[tuple[str, str]]],
    out_rows: pathlib.Path,
    out_meta: pathlib.Path,
    depth: int = 12,
    cpu_pin: Optional[int] = None,
) -> list[tuple[int, int, str, str]]:
    """
    Strict Job 47 `O`/`G` depth runner:
    - Verifies every option in `base_opts + extra_opts` is in `exe_path`'s `uci` list.
    - Keeps every line printed before EVERY `readyok` (after options, after `ucinewgame`, after `position`).
    - Stops immediately on `unknown option`, `invalid value`, `illegal`, `invalid FEN`, or `ERROR`.
    """
    fens = load_fens(set_path)
    all_opts = list(base_opts) + (list(extra_opts) if extra_opts else [])
    sess = StrictEngineSession(exe_path, cpu_pin=cpu_pin)
    sess.apply_options(all_opts, "initial_options")

    rows: list[tuple[int, int, str, str]] = []
    assert sess.proc.stdout is not None
    for idx, fen in enumerate(fens, start=1):
        sess.send("ucinewgame")
        sess.wait_ready(f"ucinewgame#{idx}")
        sess.send(f"position fen {fen}")
        sess.wait_ready(f"position#{idx}")
        sess.send(f"go depth {depth}")

        d_nodes: Optional[int] = None
        d_score: Optional[str] = None
        bestmove: Optional[str] = None
        while True:
            ln = sess.proc.stdout.readline()
            if ln == "":
                raise RuntimeError(f"EOF at position {idx} from {exe_path}")
            s = ln.rstrip("\r\n")
            check_engine_line_strict(s, f"go_depth_{depth}#{idx}")
            if s.startswith(f"info depth {depth} ") and " nodes " in s and " score " in s:
                toks = s.split()
                ni = toks.index("nodes")
                si = toks.index("score")
                d_nodes = int(toks[ni + 1])
                d_score = f"{toks[si + 1]} {toks[si + 2]}"
            elif s.startswith("bestmove "):
                bestmove = s.split()[1]
                break
        if d_nodes is None or d_score is None or bestmove is None:
            raise RuntimeError(
                f"Missing depth-{depth} info or bestmove at pos {idx}: "
                f"nodes={d_nodes} score={d_score} bestmove={bestmove}"
            )
        rows.append((idx, d_nodes, bestmove, d_score))

    pre_lines = list(sess.pre_readyok_lines)
    sent_lines = list(sess.sent_option_lines)
    verified_cnt = sess.verified_option_count
    id_name = sess.id_name
    sess.close()

    total_nodes = sum(r[1] for r in rows)
    header = [
        f"# set={set_path.name} positions={len(rows)} depth={depth} sum_nodes={total_nodes}",
        "position\tnodes\tbestmove\tscore",
    ]
    body = [f"{pos}\t{nd}\t{bm}\t{sc}" for pos, nd, bm, sc in rows]
    out_rows.write_text("\n".join(header + body) + "\n", encoding="utf-8")

    meta = [
        f"exe_path: {exe_path}",
        f"exe_sha256({exe_path}): {sha256_file(exe_path)}",
        f"id_name: {id_name}",
        f"set_path: {set_path}",
        f"set_sha256({set_path}): {sha256_file(set_path)}",
        f"positions: {len(rows)}",
        f"depth: {depth}",
        f"sum_nodes: {total_nodes}",
        f"options_verified_in_uci_list: {verified_cnt}/{len(all_opts)}",
        f"pre_readyok_lines_count: {len(pre_lines)}",
        "pre_readyok_lines_begin:",
        *[f"  {pln}" for pln in pre_lines],
        "pre_readyok_lines_end",
        "per_search_reset: ucinewgame + isready + position + isready",
        "options_sent_begin:",
        *[f"  {o}" for o in sent_lines],
        "options_sent_end",
        f"utc_completed: {utc_now()}",
    ]
    out_meta.write_text("\n".join(meta) + "\n", encoding="utf-8")
    return rows


def run_selfgame_set_strict(
    exe_path: str,
    seed: str,
    attempts: int,
    net_path: Optional[str],
    extra_opts: Optional[Sequence[tuple[str, str]]] = None,
    cpu_pin: Optional[int] = None,
) -> tuple[object, list[str], int]:
    """
    Strict Job 47 `Set A` / `n[1..60]` `selfgame` runner:
    - Verifies every option sent is in `exe_path`'s `uci` list.
    - Keeps every line printed before EVERY `readyok` (after options and after `ucinewgame`)
      and stops immediately on `unknown option`, `invalid value`, `illegal`, `invalid FEN`, or `ERROR`.
    - Returns `(V3SuiteRun, pre_readyok_lines, verified_option_count)`.
     Note: During timed Part T3 runs, `position startpos moves ...` + `selfgame ...` is sent exactly as
    in `j39_lib.run_selfgame_set_with_options` (after `ucinewgame` + `isready` -> `readyok`), while
    checking every stdout line for `unknown option`, `invalid value`, `illegal`, `invalid FEN`, and `ERROR`.
    """
    import chess
    from loop_driver import parse_sgerror_v2
    from loop_v3_driver import V3AttemptDetail, V3SuiteRun, parse_sgend_v3
    from ref_driver import format_game_records

    all_pre_readyok: list[str] = []
    verified_total = 0

    def start_sess() -> StrictEngineSession:
        nonlocal verified_total
        s = StrictEngineSession(exe_path, cpu_pin=cpu_pin)
        opts = list(PC20_OPTIONS) + (list(extra_opts) if extra_opts else [])
        if net_path is not None:
            opts.append(("NNUEArchFile", net_path))
            opts.append(("NNUEArch", "true"))
        s.apply_options(opts, "selfgame_options")
        verified_total = len(opts)
        return s

    rng = random.Random(seed)
    sess = start_sess()
    full_hasher = hashlib.sha256()
    first10_hasher = hashlib.sha256()
    finished = 0
    thrown_away = 0
    total_records = 0
    total_sg_lines = 0
    moves_finished = 0
    moves_all = 0
    total_searches = 0
    total_nodes = 0
    w_wins = 0
    draws = 0
    b_wins = 0
    details: list[V3AttemptDetail] = []

    try:
        for attempt_idx in range(1, attempts + 1):
            board = chess.Board()
            opening_moves: list[str] = []
            rng.sample(range(0, 8), 8)

            sess.send("ucinewgame")
            sess.wait_ready(f"sg_ucinewgame#{attempt_idx}")

            ended_in_opening = False
            result = 0
            end_reason = ""
            while len(opening_moves) < 8:
                ply = len(opening_moves)
                if not any(board.legal_moves):
                    result = 0 if not board.is_check() else (-1 if board.turn == chess.WHITE else 1)
                    end_reason = "stalemate" if not board.is_check() else "mate"
                    ended_in_opening = True
                    break
                is_rule_draw = (
                    board.is_insufficient_material()
                    or board.halfmove_clock >= 100
                    or board.is_repetition(3)
                )
                if is_rule_draw or ply >= 300:
                    result = 0
                    end_reason = "rule" if is_rule_draw else "plylimit"
                    ended_in_opening = True
                    break
                mv = rng.choice(list(board.legal_moves))
                board.push(mv)
                opening_moves.append(mv.uci())

            if ended_in_opening:
                finished += 1
                moves_finished += len(opening_moves)
                moves_all += len(opening_moves)
                if result == 1:
                    w_wins += 1
                elif result == 0:
                    draws += 1
                else:
                    b_wins += 1
                details.append(
                    V3AttemptDetail(
                        attempt=attempt_idx,
                        finished=True,
                        opening_moves=opening_moves,
                        loop_moves=[],
                        sg_lines=[],
                        sgend_line=None,
                        sgerror_line=None,
                        final_fen=board.fen(),
                        records=0,
                        result=result,
                        plies=len(opening_moves),
                        searches=0,
                        nodes=0,
                        end_reason=end_reason,
                        text_sha256=hashlib.sha256(b"").hexdigest(),
                    )
                )
                continue

            pos_cmd = "position startpos moves " + " ".join(opening_moves) if opening_moves else "position startpos"
            sess.send(f"{pos_cmd}\n{LINE_L_CMD}")

            records: list[tuple[str, str, int, int, bool]] = []
            sg_lines: list[str] = []
            sgend_line: Optional[str] = None
            sgerror_line: Optional[str] = None
            final_fen: Optional[str] = None
            loop_moves: list[str] = []
            thrown = False
            att_plies = len(opening_moves)
            att_searches = 0
            att_nodes = 0

            assert sess.proc.stdout is not None
            while True:
                line = sess.proc.stdout.readline()
                if line == "":
                    rc = sess.proc.wait()
                    raise RuntimeError(f"Unexpected EOF from {exe_path} during selfgame#{attempt_idx} (rc={rc})")
                line = line.rstrip("\r\n")
                check_engine_line_strict(line, f"selfgame#{attempt_idx}", allow_sgerror_prefix=True)
                if line.startswith("sg "):
                    sg_lines.append(line)
                    _, ply_s, x_s, mv_s, fen_s = line.split(" ", 4)
                    was_white = fen_s.split(" ", 2)[1] == "w"
                    records.append((fen_s, mv_s, int(x_s), int(ply_s), was_white))
                elif line.startswith("sgend "):
                    sgend_line = line
                    (
                        result,
                        end_reason,
                        att_plies,
                        _run_val,
                        att_searches,
                        att_nodes,
                        final_fen,
                        loop_moves,
                        _stripped,
                    ) = parse_sgend_v3(line)
                    break
                elif line.startswith("sgerror "):
                    sgerror_line = line
                    kind, thrown_ply, att_searches, att_nodes, _err_fen = parse_sgerror_v2(line)
                    thrown = True
                    att_plies = thrown_ply
                    end_reason = f"thrown@{thrown_ply}" if kind == "noscore" else f"{kind}@{thrown_ply}"
                    all_pre_readyok.extend(sess.pre_readyok_lines)
                    sess.close()
                    sess = start_sess()
                    break
                else:
                    raise RuntimeError(f"Unexpected line during selfgame#{attempt_idx}: {line!r}")

            total_sg_lines += len(sg_lines)
            moves_all += att_plies
            total_searches += att_searches
            total_nodes += att_nodes

            if thrown:
                thrown_away += 1
                details.append(
                    V3AttemptDetail(
                        attempt=attempt_idx,
                        finished=False,
                        opening_moves=opening_moves,
                        loop_moves=[],
                        sg_lines=sg_lines,
                        sgend_line=None,
                        sgerror_line=sgerror_line,
                        final_fen=None,
                        records=0,
                        result=None,
                        plies=att_plies,
                        searches=att_searches,
                        nodes=att_nodes,
                        end_reason=end_reason,
                        text_sha256=hashlib.sha256(b"").hexdigest(),
                    )
                )
            else:
                finished += 1
                moves_finished += att_plies
                total_records += len(records)
                if result == 1:
                    w_wins += 1
                elif result == 0:
                    draws += 1
                else:
                    b_wins += 1
                game_txt = format_game_records(records, result)
                game_bytes = game_txt.encode("ascii")
                full_hasher.update(game_bytes)
                if attempt_idx <= 10:
                    first10_hasher.update(game_bytes)
                details.append(
                    V3AttemptDetail(
                        attempt=attempt_idx,
                        finished=True,
                        opening_moves=opening_moves,
                        loop_moves=loop_moves,
                        sg_lines=sg_lines,
                        sgend_line=sgend_line,
                        sgerror_line=None,
                        final_fen=final_fen,
                        records=len(records),
                        result=result,
                        plies=att_plies,
                        searches=att_searches,
                        nodes=att_nodes,
                        end_reason=end_reason,
                        text_sha256=hashlib.sha256(game_bytes).hexdigest(),
                    )
                )
    finally:
        all_pre_readyok.extend(sess.pre_readyok_lines)
        sess.close()

    run_obj = V3SuiteRun(
        version=3,
        full_sha256=full_hasher.hexdigest(),
        first10_sha256=first10_hasher.hexdigest(),
        attempts=attempts,
        finished=finished,
        thrown_away=thrown_away,
        total_records=total_records,
        total_sg_lines=total_sg_lines,
        moves_finished=moves_finished,
        moves_all=moves_all,
        total_searches=total_searches,
        total_nodes=total_nodes,
        w_wins=w_wins,
        draws=draws,
        b_wins=b_wins,
        details=details,
    )
    return run_obj, all_pre_readyok, verified_total


def verify_all_off_numbers_strict(
    label: str,
    exe_path: str,
    extra_off_opts: Optional[Sequence[tuple[str, str]]] = None,
) -> tuple[bool, list[str]]:
    import concurrent.futures

    pc20_all = list(PC20_OPTIONS) + (list(extra_off_opts) if extra_off_opts else [])
    b11 = run_fresh_bench_strict(exe_path, 11, [])
    b13 = run_fresh_bench_strict(exe_path, 13, [])
    p5 = run_fresh_perft5_strict(exe_path)
    pc_b11 = run_fresh_bench_strict(exe_path, 11, pc20_all)
    pc_b13 = run_fresh_bench_strict(exe_path, 13, pc20_all)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(run_selfgame_set_strict, exe_path, "carbon2-job33-a", 200, None, extra_off_opts, 1)
        fut_n = pool.submit(run_selfgame_set_strict, exe_path, "carbon2-job33-n", 60, NET768, extra_off_opts, 2)
        res_a, pre_a, _ = fut_a.result()
        res_n, pre_n, _ = fut_n.result()

    bad_pre_n = [
        ln for ln in pre_n
        if any(m in ln.lower() for m in ("unknown option", "invalid value", "illegal", "invalid fen", "error"))
    ]
    checks = [
        (f"{label} no-option bench 11", b11, EXP_BENCH11_NOOPT),
        (f"{label} no-option bench 13", b13, EXP_BENCH13_NOOPT),
        (f"{label} no-option perft 5", p5, EXP_PERFT5_NOOPT),
        (f"{label} PC20 bench 11", pc_b11, EXP_BENCH11_PC20),
        (f"{label} PC20 bench 13", pc_b13, EXP_BENCH13_PC20),
        (f"{label} Set A line L records", res_a.total_records, EXP_SETA_L_RECORDS),
        (f"{label} Set A line L searches", res_a.total_searches, EXP_SETA_L_SEARCHES),
        (f"{label} Set A line L nodes", res_a.total_nodes, EXP_SETA_L_NODES),
        (f"{label} Set A line L sha256", res_a.full_sha256, EXP_SETA_L_SHA),
        (f"{label} Set A pre-readyok lines", len(pre_a), 0),
        (f"{label} n[1..60] line L records", res_n.total_records, EXP_N60_L_RECORDS),
        (f"{label} n[1..60] line L searches", res_n.total_searches, EXP_N60_L_SEARCHES),
        (f"{label} n[1..60] line L nodes", res_n.total_nodes, EXP_N60_L_NODES),
        (f"{label} n[1..60] line L sha256", res_n.full_sha256, EXP_N60_L_SHA),
        (f"{label} n[1..60] bad pre-readyok lines (kept={len(pre_n)})", len(bad_pre_n), 0),
    ]
    all_ok = True
    lines = [f"[{label}] exe={exe_path} | sha256={sha256_file(exe_path)} | {get_id_name_strict(exe_path)}"]
    for cname, got, exp in checks:
        ok, s = fmt_cmp(cname, got, exp)
        all_ok = all_ok and ok
        lines.append(s)
    for pn in pre_n:
        lines.append(f"    kept_n60_pre_readyok: {pn}")
    return all_ok, lines


def run_match_strict(
    *,
    tag: str,
    out_dir: pathlib.Path,
    exe_path: pathlib.Path,
    eng1_name: str,
    eng2_name: str,
    e1_switches: Sequence[tuple[str, str]],
    e2_switches: Sequence[tuple[str, str]],
    each_base_opts: Sequence[tuple[str, str]],
    nodes: int,
    start_line: int,
    rounds: int,
    cutoff_epoch: Optional[float] = None,
    concurrency: Optional[int] = None,
) -> dict[str, object]:
    """
    Pre-verifies BOTH sides' complete option blocks against `exe_path`'s own `uci` list and
    `isready -> readyok` replies via `StrictEngineSession`, runs `fastchess`, and scans every
    line of `{tag}_fastchess.txt` for `unknown option`, `invalid value`, `illegal`, `invalid FEN`,
    or `ERROR`.
    """
    WORK47.mkdir(parents=True, exist_ok=True)
    # Pre-verify both sides' full option sets via StrictEngineSession
    s_a = StrictEngineSession(str(exe_path))
    s_a.apply_options(list(each_base_opts) + list(e1_switches), f"{tag}_SideA_preflight")
    pre_a = list(s_a.pre_readyok_lines)
    ver_a = s_a.verified_option_count
    id_name = s_a.id_name
    s_a.close()

    s_b = StrictEngineSession(str(exe_path))
    s_b.apply_options(list(each_base_opts) + list(e2_switches), f"{tag}_SideB_preflight")
    pre_b = list(s_b.pre_readyok_lines)
    ver_b = s_b.verified_option_count
    s_b.close()

    cores = os.cpu_count() or 4
    conc = concurrency if concurrency is not None else cores

    pgn_tmp = WORK47 / f"tmp_{tag}.pgn"
    if pgn_tmp.exists():
        pgn_tmp.unlink()

    fc_out_path = out_dir / f"{tag}_fastchess.txt"
    meta_out_path = out_dir / f"{tag}_fastchess.txt.meta"
    tsv_out_path = out_dir / f"{tag}_games.tsv"
    rec_out_path = out_dir / f"{tag}_recount.txt"

    each_cli = [f"option.{k}={v}" for k, v in each_base_opts]
    e1_cli = [f"option.{k}={v}" for k, v in e1_switches]
    e2_cli = [f"option.{k}={v}" for k, v in e2_switches]

    cmd = [
        str(FASTCHESS_BIN),
        "-engine",
        f"cmd={exe_path}",
        f"name={eng1_name}",
        f"nodes={nodes}",
        *e1_cli,
        "-engine",
        f"cmd={exe_path}",
        f"name={eng2_name}",
        f"nodes={nodes}",
        *e2_cli,
        "-each",
        "proto=uci",
        *each_cli,
        "-openings",
        f"file={UHO_BOOK}",
        "format=epd",
        "order=sequential",
        f"start={start_line}",
        "-rounds",
        str(rounds),
        "-games",
        "2",
        "-repeat",
        "-concurrency",
        str(conc),
        "-pgnout",
        f"file={pgn_tmp}",
        "notation=uci",
        "-ratinginterval",
        "50",
    ]

    print(
        f"[{utc_now()}] Starting {tag}: {rounds * 2} games at nodes={nodes} "
        f"(book lines {start_line}..{start_line + rounds - 1}, concurrency={conc})",
        flush=True,
    )
    t0 = time.time()
    start_u = utc_now()
    was_cut = False
    with open(fc_out_path, "wb") as out_f:
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK47))
        while True:
            rc = proc.poll()
            if rc is not None:
                break
            if cutoff_epoch is not None and time.time() >= cutoff_epoch:
                was_cut = True
                proc.send_signal(signal.SIGINT)
                try:
                    rc = proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    rc = proc.wait()
                break
            time.sleep(1.0)
    wall_s = time.time() - t0
    end_u = utc_now()

    fc_text = fc_out_path.read_text(encoding="utf-8", errors="replace")
    bad_fc_lines: list[str] = []
    for ln in fc_text.splitlines():
        low = ln.lower()
        if (
            "unknown option" in low
            or "invalid value" in low
            or "illegal" in low
            or "invalid fen" in low
            or "ERROR" in ln
            or _WORD_ERROR_RE.search(ln)
        ):
            bad_fc_lines.append(ln)

    n_games = pgn_to_games_tsv(pgn_tmp, tsv_out_path, eng1_name, eng2_name) if pgn_tmp.exists() else 0
    if pgn_tmp.exists():
        pgn_tmp.unlink()
    if n_games < rounds * 2:
        was_cut = True

    meta_lines = [
        f"match_tag: {tag}",
        f"exe_path: {exe_path}",
        f"exe_sha256({exe_path}): {sha256_file(exe_path)}",
        f"id_name: {id_name}",
        f"sideA_options_verified_in_uci_list: {ver_a}",
        f"sideB_options_verified_in_uci_list: {ver_b}",
        f"sideA_preflight_pre_readyok_lines: {len(pre_a)}",
        f"sideB_preflight_pre_readyok_lines: {len(pre_b)}",
        f"fastchess_path: {FASTCHESS_BIN}",
        f"fastchess_sha256({FASTCHESS_BIN}): {sha256_file(FASTCHESS_BIN)}",
        f"book_path: {UHO_BOOK}",
        f"book_sha256({UHO_BOOK}): {sha256_file(UHO_BOOK)}",
        f"start_line: {start_line}",
        f"end_line_target: {start_line + rounds - 1}",
        f"rounds: {rounds}",
        f"target_games: {rounds * 2}",
        f"finished_games: {n_games}",
        f"nodes_per_move: {nodes}",
        f"concurrency: {conc}",
        f"bad_error_lines_in_fastchess_output: {len(bad_fc_lines)}",
        f"command: {' '.join(cmd)}",
        f"start_utc: {start_u}",
        f"end_utc: {end_u}",
        f"wall_s: {wall_s:.3f}",
        f"exit_code: {rc}",
        f"was_cut: {was_cut}",
    ]
    meta_out_path.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

    rec = recount_games_tsv(
        tag=tag,
        tsv_path=tsv_out_path,
        fc_txt_path=fc_out_path,
        out_recount_path=rec_out_path,
        engine1=eng1_name,
        engine2=eng2_name,
        book_path=UHO_BOOK,
        start_line=start_line,
        target_rounds=rounds,
        was_cut=was_cut,
    )
    ok_bad, s_bad = fmt_cmp(f"{tag} fastchess error/unknown/invalid/illegal lines", len(bad_fc_lines), 0)
    with open(rec_out_path, "a", encoding="utf-8") as rf:
        rf.write(s_bad + "\n")
        rf.write(f"tsv_sha256({tsv_out_path}): {sha256_file(tsv_out_path)}\n")
        rf.write(f"fastchess_txt_sha256({fc_out_path}): {sha256_file(fc_out_path)}\n")
    if not ok_bad:
        raise RuntimeError(f"{tag} fastchess output had error lines: {bad_fc_lines[:5]}")
    rec["wall_s"] = wall_s
    return rec
