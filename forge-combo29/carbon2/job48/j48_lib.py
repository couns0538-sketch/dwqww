#!/usr/bin/env python3
"""
Job 48 Shared Harness Library (`j48_lib.py`):
- Uses `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`, `sha256 = 9441524dc1f2e669608f379ab990d80325cc447e4583162b6d51dd194cba45ef`).
- Enforces the strict UCI & runner rules from Jobs 47–48 on EVERY runner:
  1. Keeps every line the engine prints before EVERY `readyok` (recording them in `.meta`)
     and STOPS IMMEDIATELY on `unknown option`, `invalid value`, `illegal`, `invalid FEN`, or `ERROR`
     (catching any misspelt option such as `IdeaB8bb=true` directly on the engine's `unknown option` reply).
  2. Also verifies every sent option name is in the executable's own `uci` -> `uciok` option list.
- Defines `PC20_OPTIONS`, `S14_EXPLICIT_OPTIONS`, and the five leave-one-out bases `L1..L5`.
"""
from __future__ import annotations

import hashlib
import math
import os
import pathlib
import re
import signal
import subprocess
import sys
import time
from typing import Optional, Sequence

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
JOB48 = REPO / "forge-combo29/carbon2/job48"
JOB47 = REPO / "forge-combo29/carbon2/job47"
JOB46 = REPO / "forge-combo29/carbon2/job46"
JOB44 = REPO / "forge-combo29/carbon2/job44"
JOB43 = REPO / "forge-combo29/carbon2/job43"
JOB42 = REPO / "forge-combo29/carbon2/job42"
JOB41 = REPO / "forge-combo29/carbon2/job41"
JOB40 = REPO / "forge-combo29/carbon2/job40"
JOB39 = REPO / "forge-combo29/carbon2/job39"
JOB36 = REPO / "forge-combo29/carbon2/job36"
JOB35 = REPO / "forge-combo29/carbon2/job35"

WORK48 = pathlib.Path("/tmp/carbon2_job48")
WORK44 = pathlib.Path("/tmp/carbon2_job44")
WORK40 = pathlib.Path("/tmp/carbon2_job40")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")

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
    EXP_BUNDLE9_SHA,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    FIVE_S14_OVERRIDES,
    G_EPD_PATH,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    S14_EXPLICIT_OPTIONS,
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
    EXP_PERFT5_NOOPT,
)

EXP_S14_OFF_O_SUM = 9500069

LEAVE_ONE_OUT_SPECS: dict[str, tuple[str, str, str]] = {
    "L1": ("CuckooRep", "false", "CuckooRep false"),
    "L2": ("HistRework", "0", "HistRework 0"),
    "L3": ("TtPruneV2", "false", "TtPruneV2 false"),
    "L4": ("CorrHistV2", "false", "CorrHistV2 false"),
    "L5": ("MateAlphaGuard", "false", "MateAlphaGuard false"),
}


def make_leave_one_out_options(base_key: str) -> list[tuple[str, str]]:
    opt_name, s14_val, _ = LEAVE_ONE_OUT_SPECS[base_key]
    found = False
    out: list[tuple[str, str]] = []
    for k, v in PC20_OPTIONS:
        if k == opt_name:
            out.append((k, s14_val))
            found = True
        else:
            out.append((k, v))
    if not found:
        raise RuntimeError(f"Switch {opt_name!r} not found in PC20_OPTIONS")
    return out


BUNDLE9_SIDE_A_SWITCHES: list[tuple[str, str]] = [
    (o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES
] + [("HindsightDepth", "true")]
BUNDLE9_SIDE_B_SWITCHES: list[tuple[str, str]] = list(ALL_TEN_FALSE)

_OPT_DECL_RE = re.compile(r"^option name (.+?) type (check|spin|combo|button|string)\b")
_WORD_ERROR_RE = re.compile(r"\berror\b", re.IGNORECASE)


class EngineReplyStopError(RuntimeError):
    def __init__(self, message: str, *, engine_line: str, marker: str, context: str) -> None:
        super().__init__(message)
        self.engine_line = engine_line
        self.marker = marker
        self.context = context


def check_engine_line_strict(line: str, context: str) -> None:
    low = line.lower()
    for marker in ("unknown option", "invalid value", "illegal", "invalid fen"):
        if marker in low:
            raise EngineReplyStopError(
                f"STOP on engine '{marker}' line in {context}: {line}",
                engine_line=line,
                marker=marker,
                context=context,
            )
    if "ERROR" in line or _WORD_ERROR_RE.search(line):
        raise EngineReplyStopError(
            f"STOP on engine 'ERROR' line in {context}: {line}",
            engine_line=line,
            marker="ERROR",
            context=context,
        )


def parse_uci_declared_options(uci_lines: Sequence[str]) -> set[str]:
    declared: set[str] = set()
    for ln in uci_lines:
        m = _OPT_DECL_RE.match(ln.strip())
        if m:
            declared.add(m.group(1))
    return declared


class StrictEngineSession:
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

        try:
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
        except Exception:
            self.abort_close()
            raise

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
            if keep_pre_readyok and s != token:
                self.pre_readyok_lines.append(f"[{ctx}] {s}")
            check_engine_line_strict(s, ctx)
            if s == token:
                return kept
            kept.append(s)

    def wait_ready(self, ctx: str) -> list[str]:
        self.send("isready")
        return self._read_until_exact("readyok", ctx, keep_pre_readyok=True)

    def apply_options(self, opt_pairs: Sequence[tuple[str, str]], ctx: str = "setoption") -> list[str]:
        if not opt_pairs:
            return self.wait_ready(ctx)
        lines = [f"setoption name {k} value {v}" for k, v in opt_pairs]
        self.sent_option_lines.extend(lines)
        self.send("\n".join(lines))
        # Read every engine line before readyok FIRST so engine 'unknown option' / 'invalid value' replies stop here
        kept = self.wait_ready(ctx)
        # Also verify every sent option name is in the executable's own uci list
        missing = [k for k, _ in opt_pairs if k not in self.declared_options]
        if missing:
            raise RuntimeError(f"Option(s) {missing} not in uci option list of {self.exe_path}")
        self.verified_option_count += len(opt_pairs)
        return kept

    def abort_close(self) -> None:
        try:
            if self.proc.poll() is None:
                try:
                    self.send("quit")
                except Exception:
                    self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
            self.proc.wait()
        finally:
            for st in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
                if st is not None:
                    try:
                        st.close()
                    except Exception:
                        pass

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


def ensure_bundle9_exe() -> tuple[str, str, str]:
    b9_p = WORK44 / "bld_bundle9/forge"
    if b9_p.exists() and sha256_file(b9_p) == EXP_BUNDLE9_SHA:
        return str(b9_p), EXP_BUNDLE9_SHA, "reused /tmp/carbon2_job44/bld_bundle9/forge with matching sha256"
    src_b9 = WORK48 / "src_bundle9"
    apply_bundle9_to_fresh_v3(src_b9)
    exe_s, sha_s, _, _ = build_release_v3(src_b9, WORK48 / "bld_bundle9")
    return exe_s, sha_s, f"rebuilt {exe_s} (sha256={sha_s})"


def get_id_name_strict(exe_path: str) -> str:
    sess = StrictEngineSession(exe_path)
    name = sess.id_name
    sess.close()
    return name


def run_fresh_bench_strict(exe_path: str, depth: int, opt_pairs: Sequence[tuple[str, str]]) -> int:
    sess = StrictEngineSession(exe_path)
    try:
        sess.apply_options(opt_pairs, f"bench {depth} options")
        sess.send(f"bench {depth}")
        sess.send("isready")
        assert sess.proc.stdout is not None
        prefix = f"info string bench depth {depth} nodes "
        bench_nodes: Optional[int] = None
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
    except Exception:
        sess.abort_close()
        raise
    sess.close()
    if bench_nodes is None:
        raise RuntimeError(f"Missing {prefix!r} from {exe_path}")
    return bench_nodes


def run_fresh_perft5_strict(exe_path: str) -> int:
    sess = StrictEngineSession(exe_path)
    try:
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
    except Exception:
        sess.abort_close()
        raise
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
    fens = load_fens(set_path)
    all_opts = list(base_opts) + (list(extra_opts) if extra_opts else [])
    sess = StrictEngineSession(exe_path, cpu_pin=cpu_pin)
    rows: list[tuple[int, int, str, str]] = []
    try:
        sess.apply_options(all_opts, "initial_options")
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
    except Exception:
        sess.abort_close()
        raise

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


def diff_elo_interval(elo_k: float, hw95_k: float, elo_0: float, hw95_0: float) -> tuple[float, float, float, float]:
    """
    File 48 formula:
      diff = elo_k - elo_0
      se_k = hw95_k / 1.96, se_0 = hw95_0 / 1.96
      se = sqrt(se_k^2 + se_0^2), hw95_diff = 1.96 * se = sqrt(hw95_k^2 + hw95_0^2)
    """
    diff = elo_k - elo_0
    se_k = hw95_k / 1.96
    se_0 = hw95_0 / 1.96
    se_diff = math.sqrt(se_k * se_k + se_0 * se_0)
    hw95_diff = 1.96 * se_diff
    return diff, hw95_diff, diff - hw95_diff, diff + hw95_diff


def run_match_strict_j48(
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
    WORK48.mkdir(parents=True, exist_ok=True)
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

    pgn_tmp = WORK48 / f"tmp_{tag}.pgn"
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
        "100",
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
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT, cwd=str(WORK48))
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
    rec["was_cut"] = was_cut
    return rec
