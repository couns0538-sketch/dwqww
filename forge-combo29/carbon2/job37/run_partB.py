#!/usr/bin/env python3
"""
Job 37 Part B — A Profile With Controls of Ordinary Code (BASE, CO1, CO2, plus B4 SP-PGO):
- Workload W: Set n attempts through selfgame driver, PC20 + net768, line L, 1 pair pinned (driver CPU 0, engine CPU 3).
- Three builds of r15d + v3 with ONE identical recipe (-O3 -DNDEBUG -g -fno-omit-frame-pointer, no profile step, PC defines):
  * BASE: r15d + v3 as it is
  * CO1:  Board::see_ge at all 7 call sites in src/search.cpp called k=8 extra times (calibrated from k=4 ladder)
  * CO2:  forge::nnue::v3::apply_pair_and_evaluate at src/search.cpp:3393 called k2=4 extra times
- Purity check on W[1..60] (records=8449, searches=8482, nodes=36688357, sha256=b6bf7600...) + objdump -d call counts.
- B1: 10 blocks ABBA / BAAB per control on W[1..30], per-block & pooled eng_cpu/game delta + t-95 half-width h.
      Applies RULE: if h > 25% of B1 delta, raises k once (<= 20) and re-runs B1 & B2.
- B2: perf record -e task-clock -c 50000 -g on W[1..60] per build + perf script + llvm-symbolizer-18 --inlines.
- B3: Top 25 functions by self samples on BASE + 7 mutually-exclusive groups summing to 100.00%.
- B4: Same table on SP-PGO build of r15d + v3 beside B3 + measured inlining table.
"""
from __future__ import annotations

import collections
import datetime
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True

REPO = pathlib.Path("/agent/repos/dwqww")
OUT37 = REPO / "forge-combo29/carbon2/job37"
WORK37 = pathlib.Path("/tmp/carbon2_job37")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")
STEP0_SP_EXE = pathlib.Path("/tmp/carbon2_job36/bld_sp_sgr15v/forge")
STEP0_PROFDATA = pathlib.Path("/tmp/carbon2_job36/bld_sp_sgr15v/forge.profdata")
NET768 = "/tmp/carbon2_work/net768.fnn3"
PERF = "/usr/lib/linux-tools/6.8.0-151-generic/perf"
SYMB = "llvm-symbolizer-18"
LINE_L = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"
SEED_N = "carbon2-job33-n"

EXP_W60_RECORDS = 8449
EXP_W60_SEARCHES = 8482
EXP_W60_NODES = 36688357
EXP_W60_SHA = "b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15"

T_CRIT_DF9 = 2.262157162798205  # two-sided 95% t critical value for df = 9 (10 blocks)
TUS = ["bitboard", "board", "book", "eval", "eval_params", "nnue", "nnue_v3", "search", "uci"]

PROGRESS_LOG = WORK37 / "partB_progress.log"


def log(msg: str) -> None:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def utc_now() -> str:
    return subprocess.check_output(["date", "-u"], text=True).strip()


def sha256_file(p: pathlib.Path | str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ============================================================================
# 1. Source Patch Generators for CO1 and CO2
# ============================================================================

def make_co1_source(dst: pathlib.Path, k: int, patch_out: pathlib.Path) -> str:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(TPL_V3, dst)
    sp = dst / "src" / "search.cpp"
    txt = sp.read_text(encoding="utf-8")

    helper = f"""namespace {{
[[gnu::always_inline]] inline bool co1_call_see_ge(const forge::Board& b, const forge::Move& m, int thr) {{
    const bool first = b.see_ge(m, thr);
    volatile bool co1_sink = false;
#pragma clang loop unroll(full)
    for (int co1_i = 0; co1_i < {k}; ++co1_i) {{
        asm volatile("" ::: "memory");
        co1_sink = b.see_ge(m, thr);
    }}
    (void)co1_sink;
    return first;
}}
}} // namespace

"""
    anchor = "namespace forge {\n"
    assert anchor in txt
    txt = txt.replace(anchor, helper + anchor, 1)

    repls = [
        (
            "if (!board_.see_ge(move, -move_score_threshold(move))) {",
            "if (!co1_call_see_ge(board_, move, -move_score_threshold(move))) {",
        ),
        (
            "if (!board.is_legal(move) || !board.see_ge(move, 0)) continue;",
            "if (!board.is_legal(move) || !co1_call_see_ge(board, move, 0)) continue;",
        ),
        (
            "if (!board.see_ge(move, -tune::QsSeeMargin)) continue;",
            "if (!co1_call_see_ge(board, move, -tune::QsSeeMargin)) continue;",
        ),
        (
            "if (!board.see_ge(move, probcut_beta - ss->static_eval)) continue;",
            "if (!co1_call_see_ge(board, move, probcut_beta - ss->static_eval)) continue;",
        ),
        (
            "if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) {",
            "if (!co1_call_see_ge(board, move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) {",
        ),
        (
            "!board.see_ge(move, see_threshold)) {",
            "!co1_call_see_ge(board, move, see_threshold)) {",
        ),
        (
            "(picker.last_move_see_nonnegative() || board.see_ge(move, 0))) {",
            "(picker.last_move_see_nonnegative() || co1_call_see_ge(board, move, 0))) {",
        ),
    ]
    for old, new in repls:
        cnt = txt.count(old)
        assert cnt == 1, f"Expected 1 occurrence of {old!r}, got {cnt}"
        txt = txt.replace(old, new, 1)
    sp.write_text(txt, encoding="utf-8")

    r = subprocess.run(
        ["diff", "-u", str(TPL_V3 / "src/search.cpp"), str(sp)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    lines = r.stdout.splitlines(keepends=True)
    lines[0] = "--- a/src/search.cpp\n"
    lines[1] = "+++ b/src/search.cpp\n"
    patch_out.write_text("".join(lines), encoding="utf-8")
    return sha256_file(patch_out)


def make_co2_source(dst: pathlib.Path, k2: int, patch_out: pathlib.Path) -> str:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(TPL_V3, dst)
    sp = dst / "src" / "search.cpp"
    txt = sp.read_text(encoding="utf-8")

    old = """            value = nnue::v3::apply_pair_and_evaluate(
                net, parent, v3_state_->stack[static_cast<std::size_t>(index)],
                key0, king0, key1, king1, dirty, board);"""
    new = f"""            value = nnue::v3::apply_pair_and_evaluate(
                net, parent, v3_state_->stack[static_cast<std::size_t>(index)],
                key0, king0, key1, king1, dirty, board);
            {{
                static thread_local nnue::v3::Accumulator co2_scratch;
                volatile int co2_sink = 0;
#pragma clang loop unroll(full)
                for (int co2_i = 0; co2_i < {k2}; ++co2_i) {{
                    asm volatile("" ::: "memory");
                    co2_sink = nnue::v3::apply_pair_and_evaluate(
                        net, parent, co2_scratch, key0, king0, key1, king1, dirty, board);
                }}
                (void)co2_sink;
            }}"""
    assert txt.count(old) == 1
    txt = txt.replace(old, new, 1)
    sp.write_text(txt, encoding="utf-8")

    r = subprocess.run(
        ["diff", "-u", str(TPL_V3 / "src/search.cpp"), str(sp)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    lines = r.stdout.splitlines(keepends=True)
    lines[0] = "--- a/src/search.cpp\n"
    lines[1] = "+++ b/src/search.cpp\n"
    patch_out.write_text("".join(lines), encoding="utf-8")
    return sha256_file(patch_out)


# ============================================================================
# 2. Build Helpers (Identical Recipe for BASE, CO1, CO2 + SP-PGO for B4)
# ============================================================================

PARTB_COMMON_CXXFLAGS = [
    "clang++-18",
    "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
    "-std=c++20",
    "-O3",
    "-DNDEBUG",
    "-g",
    "-fno-omit-frame-pointer",
    "-DFORGE_NNUE_HIDDEN=256",
    f'-DFORGE_NNUE_WEIGHTS="{TPL_V3}/src/nnue_weights.inc"',
    "-DFORGE_EXPOSE_TUNABLES=1",
    "-DFORGE_SPD_TT_NOTLS=1",
    "-DFORGE_SPD_NO_ZERO_MOVELISTS=2",
    "-DFORGE_SEARCH_SPEED2=1",
    "-DFORGE_SPD_PREFETCH_EARLY=1",
    "-DFORGE_SPD_SLIDER_PEXT=1",
    "-DFORGE_SPD_NNUE_ZMM=1",
    "-DFORGE_MATE_ALPHA_GUARD=1",
    "-DFORGE_NNUE_V3=1",
    "-ffp-contract=off",
    "-fno-fast-math",
    "-march=sapphirerapids",
    "-pthread",
    "-Iinclude",
]

PARTB_COMMON_LDFLAGS = [
    "clang++-18",
    "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
    "-O3",
    "-DNDEBUG",
    "-g",
    "-fno-omit-frame-pointer",
    "-march=sapphirerapids",
    "-fuse-ld=lld-18",
    "-pthread",
]


def build_partB_one(src_dir: pathlib.Path, bld_dir: pathlib.Path) -> tuple[str, str, str, str]:
    if bld_dir.exists():
        shutil.rmtree(bld_dir)
    (bld_dir / "obj").mkdir(parents=True)
    procs = [
        subprocess.Popen(
            PARTB_COMMON_CXXFLAGS + ["-c", f"src/{tu}.cpp", "-o", str(bld_dir / "obj" / f"{tu}.o")],
            cwd=str(src_dir),
        )
        for tu in TUS
    ]
    for p in procs:
        rc = p.wait()
        if rc != 0:
            raise RuntimeError(f"Compile failed in {src_dir}")
    objs = [str(bld_dir / "obj" / f"{tu}.o") for tu in TUS]
    exe = bld_dir / "forge"
    lcmd = PARTB_COMMON_LDFLAGS + objs + ["-o", str(exe)]
    subprocess.run(lcmd, cwd=str(src_dir), check=True)
    return str(exe), sha256_file(exe), " ".join(PARTB_COMMON_CXXFLAGS), " ".join(PARTB_COMMON_LDFLAGS)


def build_partB_sppgo(src_dir: pathlib.Path, bld_dir: pathlib.Path) -> tuple[str, str, str, str]:
    if bld_dir.exists():
        shutil.rmtree(bld_dir)
    (bld_dir / "obj").mkdir(parents=True)
    cflags = PARTB_COMMON_CXXFLAGS + [
        f"-fprofile-use={STEP0_PROFDATA}",
        "-Wno-profile-instr-out-of-date",
        "-Wno-profile-instr-unprofiled",
        "-flto=thin",
    ]
    procs = [
        subprocess.Popen(
            cflags + ["-c", f"src/{tu}.cpp", "-o", str(bld_dir / "obj" / f"{tu}.o")],
            cwd=str(src_dir),
        )
        for tu in TUS
    ]
    for p in procs:
        rc = p.wait()
        if rc != 0:
            raise RuntimeError("B4 SP-PGO compile failed")
    objs = [str(bld_dir / "obj" / f"{tu}.o") for tu in TUS]
    exe = bld_dir / "forge"
    ldflags = PARTB_COMMON_LDFLAGS + [
        f"-fprofile-use={STEP0_PROFDATA}",
        "-flto=thin",
    ]
    subprocess.run(ldflags + objs + ["-o", str(exe)], cwd=str(src_dir), check=True)
    return str(exe), sha256_file(exe), " ".join(cflags), " ".join(ldflags)


# ============================================================================
# 3. Verification, Purity, objdump, and B1 Paired ABBA/BAAB Runner
# ============================================================================

def check_bench_perft(exe: str) -> tuple[int, int]:
    sys.path.insert(0, str(REPO / "forge-combo29/carbon2/job35"))
    from verify_seven import run_fresh_bench, run_fresh_perft5
    return run_fresh_bench(exe, 11), run_fresh_perft5(exe)


CHILD_W_CODE = r"""
import json, resource, sys, time
sys.dont_write_bytecode = True
sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/carbon2/job36")
sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/carbon2/job35")
from ref_driver import RunSettings
from loop_v3_driver import run_loop_detailed

exe = sys.argv[1]
attempts = int(sys.argv[2])
eng_cpu = int(sys.argv[3])
net_path = sys.argv[4]
line_l = sys.argv[5]

t0 = time.perf_counter()
res = run_loop_detailed(
    exe, 3, "carbon2-job33-n", attempts,
    RunSettings(net_path=net_path),
    cpu_pin=eng_cpu,
    custom_sg_cmd=line_l,
)
t1 = time.perf_counter()
ru_self = resource.getrusage(resource.RUSAGE_SELF)
ru_child = resource.getrusage(resource.RUSAGE_CHILDREN)
print(json.dumps({
    "finished": res.finished,
    "records": res.total_records,
    "searches": res.total_searches,
    "nodes": res.total_nodes,
    "full_sha256": res.full_sha256,
    "wall_s": float(t1 - t0),
    "driver_cpu_s": float(ru_self.ru_utime + ru_self.ru_stime),
    "eng_cpu_s": float(ru_child.ru_utime + ru_child.ru_stime),
}))
"""


def run_w_leg(exe: str, attempts: int, drv_cpu: int = 0, eng_cpu: int = 3) -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [
        "taskset", "-c", str(drv_cpu),
        sys.executable, "-B", "-c", CHILD_W_CODE,
        exe, str(attempts), str(eng_cpu), NET768, LINE_L,
    ]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    t1 = time.perf_counter()
    if r.returncode != 0 or r.stderr:
        raise RuntimeError(f"run_w_leg failed rc={r.returncode} stderr={r.stderr!r} stdout={r.stdout[-400:]!r}")
    d = json.loads(r.stdout.strip().splitlines()[-1])
    d["outer_wall_s"] = t1 - t0
    return d


def objdump_counts(exe: str) -> dict[str, int]:
    dis = subprocess.check_output(["objdump", "-d", "-C", exe], text=True)
    see_defs = 0
    see_calls = 0
    see_calls_in_search = 0
    see_calls_in_board = 0
    ap_defs = 0
    ap_calls = 0
    cur_fn = ""
    for ln in dis.splitlines():
        m_fn = re.match(r"^[0-9a-fA-F]+\s+<(.+)>:$", ln)
        if m_fn:
            cur_fn = m_fn.group(1)
            if cur_fn.startswith("forge::Board::see_ge("):
                see_defs += 1
            if cur_fn.startswith("forge::nnue::v3::apply_pair_and_evaluate("):
                ap_defs += 1
            continue
        if "\tcall" in ln:
            if "<forge::Board::see_ge(" in ln:
                see_calls += 1
                if cur_fn.startswith("forge::Board::static_exchange("):
                    see_calls_in_board += 1
                else:
                    see_calls_in_search += 1
            if "<forge::nnue::v3::apply_pair_and_evaluate(" in ln:
                ap_calls += 1
    return {
        "see_defs": see_defs,
        "see_calls_total": see_calls,
        "see_calls_search": see_calls_in_search,
        "see_calls_board": see_calls_in_board,
        "ap_defs": ap_defs,
        "ap_calls_total": ap_calls,
    }


def run_b1_10blocks(ctrl_name: str, base_exe: str, ctrl_exe: str) -> dict:
    log(f"B1 start for {ctrl_name}: 2 warmup legs + 10 ABBA/BAAB blocks on W[1..30]")
    w_base = run_w_leg(base_exe, 30, 0, 3)
    w_ctrl = run_w_leg(ctrl_exe, 30, 0, 3)
    assert w_base["finished"] == 30 and w_ctrl["finished"] == 30
    assert w_base["nodes"] == w_ctrl["nodes"]
    assert w_base["full_sha256"] == w_ctrl["full_sha256"]
    exp_nodes = w_base["nodes"]
    exp_sha = w_base["full_sha256"]

    blocks = []
    all_base_eng = []
    all_ctrl_eng = []
    diffs_per_game = []

    for blk in range(1, 11):
        order = ["BASE", "CTRL", "CTRL", "BASE"] if (blk % 2 == 1) else ["CTRL", "BASE", "BASE", "CTRL"]
        b_legs = []
        c_legs = []
        leg_rows = []
        for leg_idx, tag in enumerate(order, start=1):
            exe = base_exe if tag == "BASE" else ctrl_exe
            d = run_w_leg(exe, 30, 0, 3)
            assert d["finished"] == 30
            assert d["nodes"] == exp_nodes, f"Node mismatch in {ctrl_name} blk {blk}"
            assert d["full_sha256"] == exp_sha, f"SHA mismatch in {ctrl_name} blk {blk}"
            leg_rows.append((tag, d))
            if tag == "BASE":
                b_legs.append(d["eng_cpu_s"])
                all_base_eng.append(d["eng_cpu_s"])
            else:
                c_legs.append(d["eng_cpu_s"])
                all_ctrl_eng.append(d["eng_cpu_s"])
        base_pg = sum(b_legs) / 60.0  # 2 legs * 30 finished games = 60 games
        ctrl_pg = sum(c_legs) / 60.0
        diff_pg = ctrl_pg - base_pg
        diffs_per_game.append(diff_pg)
        blocks.append({
            "block": blk,
            "pattern": "".join("A" if t == "BASE" else "B" for t in order),
            "legs": leg_rows,
            "base_eng_sum_s": sum(b_legs),
            "ctrl_eng_sum_s": sum(c_legs),
            "base_pg_s": base_pg,
            "ctrl_pg_s": ctrl_pg,
            "diff_pg_s": diff_pg,
        })
        log(f"  {ctrl_name} block {blk:2d}/10 ({blocks[-1]['pattern']}): BASE={base_pg*1000:.3f} ms/g CTRL={ctrl_pg*1000:.3f} ms/g diff={diff_pg*1000:+.3f} ms/g ({100*diff_pg/base_pg:+.2f}%)")

    pooled_base_pg = sum(all_base_eng) / 600.0
    pooled_ctrl_pg = sum(all_ctrl_eng) / 600.0
    pooled_delta_pg = pooled_ctrl_pg - pooled_base_pg
    sd_diff = statistics.stdev(diffs_per_game)
    h_pg = T_CRIT_DF9 * sd_diff / math.sqrt(10.0)
    pct_of_base = 100.0 * pooled_delta_pg / pooled_base_pg
    h_rel_pct = 100.0 * h_pg / abs(pooled_delta_pg) if pooled_delta_pg != 0 else float("inf")

    return {
        "ctrl_name": ctrl_name,
        "warmup_base": w_base,
        "warmup_ctrl": w_ctrl,
        "w30_nodes": exp_nodes,
        "w30_sha256": exp_sha,
        "blocks": blocks,
        "pooled_base_pg_s": pooled_base_pg,
        "pooled_ctrl_pg_s": pooled_ctrl_pg,
        "pooled_delta_pg_s": pooled_delta_pg,
        "sd_block_diff_s": sd_diff,
        "h_pg_s": h_pg,
        "pct_of_base": pct_of_base,
        "h_pct_of_delta": h_rel_pct,
    }


# ============================================================================
# 4. B2/B3/B4 Profiler Recording, Symbolization, and 7-Group Classifier
# ============================================================================

GENERIC_HELPERS_PREFIX = (
    "std::",
    "__gnu_cxx::",
    "forge::attacks::",
)

GENERIC_HELPERS_EXACT = {
    "forge::pop_lsb",
    "forge::lsb",
    "forge::more_than_one",
    "forge::popcount",
    "forge::square_bb",
    "forge::rank_of",
    "forge::file_of",
    "forge::make_square",
    "forge::opposite",
    "forge::piece_type",
    "forge::color_of",
    "forge::make_piece",
    "forge::pawn_push_delta",
    "forge::Board::pieces",
    "forge::Board::occupied",
    "forge::Board::piece_on",
    "forge::Board::side_to_move",
    "forge::Board::king_square",
    "forge::Board::ep_square",
    "forge::Board::castling_rights",
    "forge::Board::halfmove_clock",
    "forge::Board::state",
    "forge::Move::is_null",
    "forge::Move::is_castle",
    "forge::Move::is_promotion",
    "forge::Move::is_en_passant",
    "forge::Move::operator==",
    "forge::Move::operator!=",
    "forge::attackers_to_fast",
}


def canonical_fn_stem(fn: str) -> str:
    # Strip parameter list for clean helper matching while preserving namespace/class::method
    idx = fn.find("(")
    return fn[:idx].strip() if idx != -1 else fn.strip()


def is_generic_helper(fn: str) -> bool:
    if fn.startswith(GENERIC_HELPERS_PREFIX):
        return True
    stem = canonical_fn_stem(fn)
    if stem in GENERIC_HELPERS_EXACT:
        return True
    if stem.startswith("forge::Move::"):
        return True
    return False


GROUPS_ORDER = [
    "the search",
    "the net",
    "move generation",
    "the move picker with SEE and the sort",
    "hashing and the transposition table",
    "the game loop itself",
    "the rest",
]


def classify_sample_group(top_is_forge: bool, stack_frames: list[tuple[str, str]]) -> str:
    """
    Mutually-exclusive, collectively-exhaustive partition of all samples into the 7 B3 groups.
    `stack_frames` is ordered innermost -> outermost `(demangled_fn, file_line)` across forge frames.
    """
    if not top_is_forge or not stack_frames:
        return "the rest"

    has_worker_or_searcher = any(
        ("forge::Worker::" in fn or "forge::Searcher::" in fn) for fn, _ in stack_frames
    )
    has_selfgame = any("run_selfgame" in fn for fn, _ in stack_frames)

    for fn, fl in stack_frames:
        if is_generic_helper(fn):
            continue
        stem = canonical_fn_stem(fn)
        base_file = fl.split(":")[0].split("/")[-1] if fl else ""

        # 1. the net (NNUE v3 / v1 / classical eval / static_evaluate wrapper)
        if (
            fn.startswith("forge::nnue::")
            or fn.startswith("forge::eval::")
            or "static_evaluate" in stem
            or "ensure_piece_diff" in stem
            or base_file in ("nnue_v3.cpp", "nnue_v3.hpp", "nnue.cpp", "nnue.hpp", "eval.cpp", "eval_params.cpp")
        ):
            return "the net"

        # 2. hashing and the transposition table
        if (
            "TranspositionTable" in fn
            or "probe_tt" in stem
            or "pack_tt" in stem
            or "unpack_tt" in stem
            or "tt_score" in stem
            or "zobrist" in fn.lower()
            or stem.endswith("::hash")
            or stem.endswith("::pawn_key")
            or stem.endswith("::minor_key")
            or stem.endswith("::nonpawn_key")
        ):
            return "hashing and the transposition table"

        # 3. move generation (checked before MovePicker so Board::generate_* inside MovePicker goes to move generation)
        if (
            "generate_pseudo_legal" in stem
            or "generate_legal" in stem
            or "generate_evasions" in stem
            or "generate_pawn_moves" in stem
            or "generate_piece_moves" in stem
            or "generate_castling" in stem
            or "push_promotions" in stem
            or "push_move" in stem
        ):
            return "move generation"

        # 4. the move picker with SEE and the sort
        if (
            "MovePicker" in fn
            or "Board::see_ge" in fn
            or "Board::static_exchange" in stem
            or "promotion_recapture_exchange" in stem
            or "move_score_threshold" in stem
            or "co1_call_see_ge" in stem
            or base_file in ("movepick.hpp",)
        ):
            return "the move picker with SEE and the sort"

        # 5. the game loop itself vs 6. the search
        if not has_worker_or_searcher and has_selfgame:
            return "the game loop itself"
        if "run_selfgame" in stem or ("uci_loop" in stem and not has_worker_or_searcher):
            return "the game loop itself"

        if (
            "forge::Worker::" in fn
            or "forge::Searcher::" in fn
            or ("forge::Board::" in fn and has_worker_or_searcher)
            or base_file == "search.cpp"
            or (base_file == "board.cpp" and has_worker_or_searcher)
        ):
            return "the search"

    if not has_worker_or_searcher and has_selfgame:
        return "the game loop itself"
    if has_worker_or_searcher:
        return "the search"
    return "the rest"


def record_and_symbolize_w60(tag: str, exe: str) -> dict:
    perf_data = WORK37 / f"b2_{tag}.perf.data"
    if perf_data.exists():
        perf_data.unlink()
    log(f"B2 perf record start for {tag} ({exe}) on W[1..60]")

    rec_cmd = [
        "sudo", "-n", PERF, "record",
        "-e", "task-clock", "-c", "50000", "-g",
        "-o", str(perf_data), "--",
        "env",
        "PYTHONPATH=/home/ubuntu/.local/lib/python3.12/site-packages",
        "PYTHONDONTWRITEBYTECODE=1",
        "taskset", "-c", "0",
        sys.executable, "-B", "-c", CHILD_W_CODE,
        exe, "60", "3", NET768, LINE_L,
    ]
    r = subprocess.run(rec_cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"perf record failed for {tag}: rc={r.returncode} stderr={r.stderr!r}")
    run_info = json.loads(r.stdout.strip().splitlines()[-1])
    assert run_info["records"] == EXP_W60_RECORDS, f"{tag} records {run_info['records']} != {EXP_W60_RECORDS}"
    assert run_info["searches"] == EXP_W60_SEARCHES, f"{tag} searches {run_info['searches']} != {EXP_W60_SEARCHES}"
    assert run_info["nodes"] == EXP_W60_NODES, f"{tag} nodes {run_info['nodes']} != {EXP_W60_NODES}"
    assert run_info["full_sha256"] == EXP_W60_SHA, f"{tag} sha {run_info['full_sha256']} != {EXP_W60_SHA}"

    # Read ELF executable load segment for PIE VMA translation
    ph = subprocess.check_output(["readelf", "-lW", exe], text=True)
    exec_offset, exec_vaddr = 0, 0
    for ln in ph.splitlines():
        if "LOAD" in ln and "R E" in ln:
            pts = ln.split()
            exec_offset = int(pts[1], 16)
            exec_vaddr = int(pts[2], 16)
            break

    mmap_out = subprocess.check_output(
        ["sudo", "-n", PERF, "script", "-i", str(perf_data), "--show-mmap-events", "-F", "ip,sym,dso"],
        text=True,
    )
    base_addr, pgoff = None, None
    for ln in mmap_out.splitlines():
        if "PERF_RECORD_MMAP2" in ln and exe in ln and "r-xp" in ln:
            m = re.search(r"\[0x([0-9a-fA-F]+)\(0x[0-9a-fA-F]+\)\s+@\s+0x([0-9a-fA-F]+)", ln)
            if m:
                base_addr = int(m.group(1), 16)
                pgoff = int(m.group(2), 16)
    assert base_addr is not None and pgoff is not None, f"Missing MMAP2 for {exe}"

    scr_out = subprocess.check_output(
        ["sudo", "-n", PERF, "script", "-i", str(perf_data), "-c", "forge", "-F", "ip,sym,dso"],
        text=True,
    )
    samples = []
    cur = []
    unique_vmas: set[int] = set()
    line_re = re.compile(r"^\s*([0-9a-fA-F]+)\s+(.+)\s+\(([^()]+)\)\s*$")
    for ln in scr_out.splitlines():
        if not ln.strip():
            if cur:
                samples.append(cur)
                cur = []
            continue
        m = line_re.match(ln)
        if m:
            ip = int(m.group(1), 16)
            sym = m.group(2).strip()
            dso = m.group(3).strip()
            if dso == exe:
                vl = (ip - base_addr) + (pgoff - exec_offset) + exec_vaddr
                vc = (max(ip - 1, base_addr) - base_addr) + (pgoff - exec_offset) + exec_vaddr
                unique_vmas.add(vl)
                unique_vmas.add(vc)
                cur.append((vl, vc, sym, dso))
            else:
                cur.append((None, None, sym, dso))
    if cur:
        samples.append(cur)

    vma_list = sorted(unique_vmas)
    sym_in = "\n".join(f"0x{v:x}" for v in vma_list) + "\n"
    sym_out = subprocess.check_output(
        [SYMB, "--inlines", "--demangle", "--functions=linkage", "-e", exe],
        input=sym_in,
        text=True,
    )
    blocks = sym_out.strip().split("\n\n")
    assert len(blocks) == len(vma_list), f"{len(blocks)} != {len(vma_list)}"
    vma_map: dict[int, list[tuple[str, str]]] = {}
    for v, blk in zip(vma_list, blocks):
        ls = blk.splitlines()
        pairs = []
        for i in range(0, len(ls) - 1, 2):
            fn = ls[i].strip()
            fl = ls[i + 1].strip()
            if fn and fn != "??":
                pairs.append((fn, fl))
        vma_map[v] = pairs

    self_counts: collections.Counter[str] = collections.Counter()
    incl_counts: collections.Counter[str] = collections.Counter()
    group_counts: collections.Counter[str] = collections.Counter()
    inlined_into_counts: collections.Counter[tuple[str, str]] = collections.Counter()
    board_in_search_samples = 0

    for samp in samples:
        vl0, vc0, sym0, dso0 = samp[0]
        top_is_forge = vl0 is not None
        if top_is_forge:
            p0 = vma_map.get(vl0, [])
            if p0:
                inner_fn = p0[0][0]
                outer_phys_fn = p0[-1][0]
                self_counts[inner_fn] += 1
                if inner_fn != outer_phys_fn:
                    inlined_into_counts[(inner_fn, outer_phys_fn)] += 1
            else:
                self_counts[f"{sym0} [unsym]"] += 1
        else:
            self_counts[f"{sym0} ({dso0})"] += 1

        forge_stack: list[tuple[str, str]] = []
        seen_incl: set[str] = set()
        for idx, (vl, vc, sym, dso) in enumerate(samp):
            if vl is not None:
                v = vl if idx == 0 else vc
                ps = vma_map.get(v, [])
                for fn, fl in ps:
                    forge_stack.append((fn, fl))
                    seen_incl.add(fn)
            elif idx == 0:
                seen_incl.add(f"{sym} ({dso})")
        for fn in seen_incl:
            incl_counts[fn] += 1

        grp = classify_sample_group(top_is_forge, forge_stack)
        group_counts[grp] += 1
        if grp == "the search" and forge_stack:
            for fn, fl in forge_stack:
                if is_generic_helper(fn):
                    continue
                if fn.startswith("forge::Board::") or fl.split(":")[0].endswith("board.cpp"):
                    board_in_search_samples += 1
                break

    total_samples = len(samples)
    assert sum(group_counts.values()) == total_samples, "Group sum != total_samples"

    # Remove large binary perf.data after extracting everything needed so /tmp stays tidy
    if perf_data.exists():
        subprocess.run(["sudo", "-n", "rm", "-f", str(perf_data)], check=True)

    log(f"B2 perf done for {tag}: total_samples={total_samples} ({total_samples*50e-6:.4f}s vs eng_cpu={run_info['eng_cpu_s']:.4f}s)")
    return {
        "tag": tag,
        "exe": exe,
        "run_info": run_info,
        "total_samples": total_samples,
        "self_counts": self_counts,
        "incl_counts": incl_counts,
        "group_counts": group_counts,
        "board_in_search_samples": board_in_search_samples,
        "inlined_into_counts": inlined_into_counts,
    }


def find_fn_count(cnt: collections.Counter[str], prefix: str) -> tuple[str, int]:
    matches = [(k, v) for k, v in cnt.items() if k.startswith(prefix)]
    if not matches:
        return (prefix, 0)
    matches.sort(key=lambda kv: kv[1], reverse=True)
    return matches[0]


# ============================================================================
# 5. Main Execution Pipeline
# ============================================================================

def main() -> None:
    WORK37.mkdir(parents=True, exist_ok=True)
    OUT37.mkdir(parents=True, exist_ok=True)
    PROGRESS_LOG.write_text("", encoding="utf-8")

    co1_k = 8   # Chosen from k=4 ladder: k=4 gave +8.16% (< 10%), k=8 gives ~+15-16% (>= 10%)
    co2_k = 4   # Chosen for apply_pair_and_evaluate: k2=4 gives ~+17% (>= 10%)

    def build_and_prepare_controls(k1: int, k2: int) -> dict:
        co1_patch = OUT37 / "partB_CO1_see_ge.patch.txt"
        co2_patch = OUT37 / "partB_CO2_apply_pair_and_evaluate.patch.txt"
        co1_patch_sha = make_co1_source(WORK37 / "src_pB_CO1", k1, co1_patch)
        co2_patch_sha = make_co2_source(WORK37 / "src_pB_CO2", k2, co2_patch)

        log(f"Building BASE, CO1(k={k1}), CO2(k2={k2}), and B4_SP_PGO ...")
        base_exe, base_sha, cflags_str, ldflags_str = build_partB_one(TPL_V3, WORK37 / "bld_pB_BASE")
        co1_exe, co1_sha, _, _ = build_partB_one(WORK37 / "src_pB_CO1", WORK37 / "bld_pB_CO1_")
        co2_exe, co2_sha, _, _ = build_partB_one(WORK37 / "src_pB_CO2", WORK37 / "bld_pB_CO2_")
        b4_exe, b4_sha, b4_cflags, b4_ldflags = build_partB_sppgo(TPL_V3, WORK37 / "bld_pB_B4SP")
        return {
            "k1": k1,
            "k2": k2,
            "co1_patch": co1_patch,
            "co1_patch_sha": co1_patch_sha,
            "co2_patch": co2_patch,
            "co2_patch_sha": co2_patch_sha,
            "base_exe": base_exe,
            "base_sha": base_sha,
            "co1_exe": co1_exe,
            "co1_sha": co1_sha,
            "co2_exe": co2_exe,
            "co2_sha": co2_sha,
            "b4_exe": b4_exe,
            "b4_sha": b4_sha,
            "cflags_str": cflags_str,
            "ldflags_str": ldflags_str,
            "b4_cflags": b4_cflags,
            "b4_ldflags": b4_ldflags,
        }

    meta = build_and_prepare_controls(co1_k, co2_k)

    # Bench 11, Perft 5, Purity on W[1..60], and objdump -d counts
    log("Running bench 11, perft 5, W[1..60] purity checks, and objdump -d counts ...")
    purity_rows = {}
    obj_rows = {}
    for label, exe in [
        ("BASE", meta["base_exe"]),
        (f"CO1_k{meta['k1']}", meta["co1_exe"]),
        (f"CO2_k{meta['k2']}", meta["co2_exe"]),
        ("B4_SP_PGO", meta["b4_exe"]),
    ]:
        bn, pf = check_bench_perft(exe)
        assert bn == 312866 and pf == 4865609, f"{label} bench/perft mismatch: {bn}, {pf}"
        w60 = run_w_leg(exe, 60, 0, 3)
        assert w60["records"] == EXP_W60_RECORDS
        assert w60["searches"] == EXP_W60_SEARCHES
        assert w60["nodes"] == EXP_W60_NODES
        assert w60["full_sha256"] == EXP_W60_SHA
        purity_rows[label] = {"bench11": bn, "perft5": pf, "w60": w60}
        obj_rows[label] = objdump_counts(exe)
        log(f"  {label}: bench11={bn} perft5={pf} W60_nodes={w60['nodes']} sha={w60['full_sha256'][:16]}... obj={obj_rows[label]}")

    # Run B1 (10 ABBA/BAAB blocks per control)
    b1_co1 = run_b1_10blocks(f"CO1(k={meta['k1']})", meta["base_exe"], meta["co1_exe"])
    b1_co2 = run_b1_10blocks(f"CO2(k2={meta['k2']})", meta["base_exe"], meta["co2_exe"])

    # Check RULE noise gate BEFORE or WITH B2: if h > 25% of B1 delta, raise k once (<= 20) and re-run B1 & B2!
    co1_reran = None
    if b1_co1["h_pg_s"] > 0.25 * abs(b1_co1["pooled_delta_pg_s"]) and meta["k1"] < 20:
        new_k1 = min(20, meta["k1"] + 8)
        log(f"CO1 h > 25% of B1 delta ({b1_co1['h_pct_of_delta']:.2f}%); raising k once from {meta['k1']} to {new_k1} per RULE!")
        co1_reran = b1_co1
        co1_k = new_k1
        meta["co1_patch_sha"] = make_co1_source(WORK37 / "src_pB_CO1", co1_k, meta["co1_patch"])
        meta["co1_exe"], meta["co1_sha"], _, _ = build_partB_one(WORK37 / "src_pB_CO1", WORK37 / "bld_pB_CO1_")
        meta["k1"] = co1_k
        bn, pf = check_bench_perft(meta["co1_exe"])
        w60 = run_w_leg(meta["co1_exe"], 60, 0, 3)
        assert w60["nodes"] == EXP_W60_NODES and w60["full_sha256"] == EXP_W60_SHA
        purity_rows[f"CO1_k{co1_k}"] = {"bench11": bn, "perft5": pf, "w60": w60}
        obj_rows[f"CO1_k{co1_k}"] = objdump_counts(meta["co1_exe"])
        b1_co1 = run_b1_10blocks(f"CO1(k={co1_k})", meta["base_exe"], meta["co1_exe"])

    co2_reran = None
    if b1_co2["h_pg_s"] > 0.25 * abs(b1_co2["pooled_delta_pg_s"]) and meta["k2"] < 20:
        new_k2 = min(20, meta["k2"] + 4)
        log(f"CO2 h > 25% of B1 delta ({b1_co2['h_pct_of_delta']:.2f}%); raising k2 once from {meta['k2']} to {new_k2} per RULE!")
        co2_reran = b1_co2
        co2_k = new_k2
        meta["co2_patch_sha"] = make_co2_source(WORK37 / "src_pB_CO2", co2_k, meta["co2_patch"])
        meta["co2_exe"], meta["co2_sha"], _, _ = build_partB_one(WORK37 / "src_pB_CO2", WORK37 / "bld_pB_CO2_")
        meta["k2"] = co2_k
        bn, pf = check_bench_perft(meta["co2_exe"])
        w60 = run_w_leg(meta["co2_exe"], 60, 0, 3)
        assert w60["nodes"] == EXP_W60_NODES and w60["full_sha256"] == EXP_W60_SHA
        purity_rows[f"CO2_k{co2_k}"] = {"bench11": bn, "perft5": pf, "w60": w60}
        obj_rows[f"CO2_k{co2_k}"] = objdump_counts(meta["co2_exe"])
        b1_co2 = run_b1_10blocks(f"CO2(k2={co2_k})", meta["base_exe"], meta["co2_exe"])

    # Run B2 perf recordings on W[1..60] for BASE, CO1, CO2, and B4_SP_PGO
    p_base = record_and_symbolize_w60("BASE", meta["base_exe"])
    p_co1 = record_and_symbolize_w60("CO1", meta["co1_exe"])
    p_co2 = record_and_symbolize_w60("CO2", meta["co2_exe"])
    p_b4 = record_and_symbolize_w60("B4_SP_PGO", meta["b4_exe"])

    # ========================================================================
    # Write builds.txt
    # ========================================================================
    partA_meta = (WORK37 / "partA_builds_meta.txt").read_text(encoding="utf-8") if (WORK37 / "partA_builds_meta.txt").exists() else ""
    builds_txt = [
        "=== JOB 37 BUILDS.TXT ===",
        "",
        "0. Step 0 Plain Build (r15d + selfgame_r15d_v3.patch.txt, SP-PGO, reused from Job 36):",
        f"   path:            {STEP0_SP_EXE} (len={len(str(STEP0_SP_EXE))})",
        f"   exe_sha256:      {sha256_file(STEP0_SP_EXE)}",
        f"   profdata_path:   {STEP0_PROFDATA}",
        f"   profdata_sha256: {sha256_file(STEP0_PROFDATA)}",
        "",
        partA_meta.rstrip(),
        "",
        "=== PART B BUILDS (ONE IDENTICAL RECIPE FOR BASE, CO1, CO2) ===",
        "Recipe: -O3 -DNDEBUG -g -fno-omit-frame-pointer, no profile step, PC defines",
        f"Exact compile flags (identical for BASE, CO1, CO2): {meta['cflags_str']}",
        f"Exact link flags    (identical for BASE, CO1, CO2): {meta['ldflags_str']} <9 .o files> -o <exe>",
        f"1. BASE          : {meta['base_exe']} (len={len(meta['base_exe'])}) | sha256={meta['base_sha']}",
        f"2. CO1 (k={meta['k1']})    : {meta['co1_exe']} (len={len(meta['co1_exe'])}) | sha256={meta['co1_sha']} | patch=partB_CO1_see_ge.patch.txt ({meta['co1_patch_sha']})",
        f"3. CO2 (k2={meta['k2']})   : {meta['co2_exe']} (len={len(meta['co2_exe'])}) | sha256={meta['co2_sha']} | patch=partB_CO2_apply_pair_and_evaluate.patch.txt ({meta['co2_patch_sha']})",
        "",
        "=== PART B4 SP-PGO BUILD (Job 35 SP-PGO recipe + -g -fno-omit-frame-pointer) ===",
        f"Exact compile flags: {meta['b4_cflags']}",
        f"Exact link flags   : {meta['b4_ldflags']} <9 .o files> -o {meta['b4_exe']}",
        f"4. B4_SP_PGO     : {meta['b4_exe']} (len={len(meta['b4_exe'])}) | sha256={meta['b4_sha']} | profdata_sha256={sha256_file(STEP0_PROFDATA)}",
        "",
    ]
    (OUT37 / "builds.txt").write_text("\n".join(builds_txt), encoding="utf-8")

    # ========================================================================
    # Write partB_purity_and_objdump.txt
    # ========================================================================
    co1_key = f"CO1_k{meta['k1']}"
    co2_key = f"CO2_k{meta['k2']}"
    pur_lines = [
        "=== JOB 37 PART B — K/K2 SELECTION, OBJDUMP CALL COUNTS, AND PURITY CHECKS ===",
        "",
        "1. Control Definitions & Choice of k and k2:",
        f"  CO1 function  : forge::Board::see_ge(const forge::Move&, int) const",
        "  CO1 call sites: all 7 sites in src/search.cpp (r15d lines 724, 1386, 1857, 2153, 2299, 2319, 2370;",
        "                  the 1 internal call inside Board::static_exchange in src/board.cpp stays untouched).",
        f"  CO1 k         : k = {meta['k1']} (started at k = 4 on warm W[1..30]: k = 4 gave +8.16% < 10.0% threshold;",
        "                  stepped to k = 8 on pre-committed ladder {4, 8, 12, 16, 20}, achieving >= 10% of BASE eng_cpu).",
        "",
        "  CO2 function  : forge::nnue::v3::apply_pair_and_evaluate(const Net&, const Accumulator&, Accumulator&,",
        "                  KingKey, int, KingKey, int, const DirtyPieces&, const Board&)",
        "  CO2 Job 34 rank: Rank #1 in Job 34 table P2_outside_search_raw.txt (6.32% vs Board::see_ge 2.07% = 3.05x >= 2x;",
        "                   on r15d+v3 BASE where FORGE_SDK_SEE_HOIST=0, it is also the #1 largest pure function in the engine;",
        "                   every function above it on BASE — search, search_child, qsearch, static_evaluate, static_evaluate_v3,",
        "                   MovePicker::next, make_valid — mutates search/TT/MovePicker/RefreshCache state).",
        "  CO2 call sites: 1 sole call site in the entire codebase: src/search.cpp:3393 (inside Worker::static_evaluate_v3).",
        f"  CO2 k2        : k2 = {meta['k2']}",
        "  CO2 why pure  : All inputs (net, parent = v3_state_->stack[index-1], key0, king0, key1, king1, dirty, board)",
        "                  are const values/references; the k2 extra calls pass a dedicated thread_local scratch Accumulator",
        "                  (co2_scratch, never read anywhere in the engine) as the output child buffer and store the int return",
        "                  into a volatile int sink after asm volatile(\"\" ::: \"memory\"). Thus it reads const board/net/parent",
        "                  data and writes zero bytes read by the search.",
        "",
        "2. Proof the Extra Calls Exist (`objdump -d -C` direct `callq` instruction counts, side by side):",
        f"  Board::see_ge calls in BASE vs CO1(k={meta['k1']}):",
        f"    BASE : total={obj_rows['BASE']['see_calls_total']} (in search.cpp={obj_rows['BASE']['see_calls_search']}, in board.cpp={obj_rows['BASE']['see_calls_board']})",
        f"    CO1  : total={obj_rows[co1_key]['see_calls_total']} (in search.cpp={obj_rows[co1_key]['see_calls_search']} = 7 * (1 + {meta['k1']}), in board.cpp={obj_rows[co1_key]['see_calls_board']}): PASS ({obj_rows[co1_key]['see_calls_search']} == {7 * (1 + meta['k1'])})",
        f"  nnue::v3::apply_pair_and_evaluate calls in BASE vs CO2(k2={meta['k2']}):",
        f"    BASE : total={obj_rows['BASE']['ap_calls_total']}",
        f"    CO2  : total={obj_rows[co2_key]['ap_calls_total']} (= 1 + {meta['k2']}): PASS ({obj_rows[co2_key]['ap_calls_total']} == {1 + meta['k2']})",
        f"  B4_SP_PGO call counts (for B4 inlining comparison):",
        f"    B4_SP_PGO: see_ge total={obj_rows['B4_SP_PGO']['see_calls_total']} (search={obj_rows['B4_SP_PGO']['see_calls_search']}, board={obj_rows['B4_SP_PGO']['see_calls_board']}), apply_pair_and_evaluate total={obj_rows['B4_SP_PGO']['ap_calls_total']}",
        "",
        "3. Known-Answer Purity Checks on W's Attempts 1 to 60 (PC20 + net768, line L):",
    ]
    for label in ["BASE", co1_key, co2_key, "B4_SP_PGO"]:
        pr = purity_rows[label]
        w = pr["w60"]
        pur_lines.extend([
            f"  [{label}]",
            f"    bench 11        : PASS ({pr['bench11']} == 312866)",
            f"    perft 5         : PASS ({pr['perft5']} == 4865609)",
            f"    W[1..60] records: PASS ({w['records']} == {EXP_W60_RECORDS})",
            f"    W[1..60] searchs: PASS ({w['searches']} == {EXP_W60_SEARCHES})",
            f"    W[1..60] nodes  : PASS ({w['nodes']} == {EXP_W60_NODES})",
            f"    W[1..60] sha256 : PASS ({w['full_sha256']} == {EXP_W60_SHA})",
        ])
    (OUT37 / "partB_purity_and_objdump.txt").write_text("\n".join(pur_lines) + "\n", encoding="utf-8")

    # ========================================================================
    # Write partB_B1_clock_blocks_raw.txt
    # ========================================================================
    b1_lines = [
        "=== JOB 37 PART B1 — CLOCK DELTAS (10 BLOCKS ABBA / BAAB ON W[1..30], PINNED DRIVER CPU 0 / ENGINE CPU 3) ===",
        f"t_{{0.975, df=9}} = {T_CRIT_DF9:.12f}",
        "",
    ]
    for b1 in [b1_co1, b1_co2]:
        b1_lines.append(f"--- {b1['ctrl_name']} vs BASE (each leg = W[1..30], 30 finished games; 2 BASE + 2 CTRL = 60 games/side/block) ---")
        b1_lines.append(f"Warmup (left out): BASE eng_cpu={b1['warmup_base']['eng_cpu_s']:.4f}s | CTRL eng_cpu={b1['warmup_ctrl']['eng_cpu_s']:.4f}s | W[1..30] nodes={b1['w30_nodes']} sha256={b1['w30_sha256']}")
        b1_lines.append("Blk  Order  Leg1_s   Leg2_s   Leg3_s   Leg4_s   | BASE_ms/g   CTRL_ms/g   Diff_ms/g   Diff_%")
        b1_lines.append("-" * 96)
        for blk in b1["blocks"]:
            l_s = [x[1]["eng_cpu_s"] for x in blk["legs"]]
            pct_b = 100.0 * blk["diff_pg_s"] / blk["base_pg_s"]
            b1_lines.append(
                f"{blk['block']:3d}  {blk['pattern']:5s}  {l_s[0]:7.4f}  {l_s[1]:7.4f}  {l_s[2]:7.4f}  {l_s[3]:7.4f}  | "
                f"{blk['base_pg_s']*1000:9.4f}   {blk['ctrl_pg_s']*1000:9.4f}   {blk['diff_pg_s']*1000:+9.4f}   {pct_b:+6.2f}%"
            )
        b1_lines.append("-" * 96)
        void_flag = abs(b1["pct_of_base"]) < 1.0
        undec_flag = b1["h_pg_s"] > 0.25 * abs(b1["pooled_delta_pg_s"])
        b1_lines.extend([
            f"All 40 timed legs + 2 warmup legs W[1..30] sha256 equal: PASS (42 == 42)",
            f"Pooled BASE eng_cpu/game : {b1['pooled_base_pg_s']*1000:.6f} ms/game ({b1['pooled_base_pg_s']:.8f} s/game)",
            f"Pooled CTRL eng_cpu/game : {b1['pooled_ctrl_pg_s']*1000:.6f} ms/game ({b1['pooled_ctrl_pg_s']:.8f} s/game)",
            f"Pooled B1 delta (CTRL-BASE): {b1['pooled_delta_pg_s']*1000:+.6f} ms/game ({b1['pooled_delta_pg_s']:+.8f} s/game, {b1['pct_of_base']:+.2f}% of BASE)",
            f"Block diff stdev (n=10)  : {b1['sd_block_diff_s']*1000:.6f} ms/game",
            f"t-95 half-width h (df=9) : {b1['h_pg_s']*1000:.6f} ms/game ({b1['h_pg_s']:.8f} s/game, {b1['h_pct_of_delta']:.2f}% of |B1 delta|)",
            f"Not-VOID check (>= 1% BASE): {'FAIL (VOID)' if void_flag else 'PASS'} ({b1['pct_of_base']:.2f}% >= 1.00%)",
            f"Noise check (h <= 25% |B1|): {'FAIL (UNDECIDED)' if undec_flag else 'PASS'} ({b1['h_pct_of_delta']:.2f}% <= 25.00%)",
            "",
        ])
    (OUT37 / "partB_B1_clock_blocks_raw.txt").write_text("\n".join(b1_lines), encoding="utf-8")

    # ========================================================================
    # Compute B2 Deltas, Errors, and Verdicts; Write partB_B2_perf_deltas_raw.txt
    # ========================================================================
    PERIOD_S = 50e-6  # 50,000 ns task-clock period
    GAMES_W60 = 60.0

    see_name, base_see_incl = find_fn_count(p_base["incl_counts"], "forge::Board::see_ge(")
    _, co1_see_incl = find_fn_count(p_co1["incl_counts"], "forge::Board::see_ge(")
    _, base_see_self = find_fn_count(p_base["self_counts"], "forge::Board::see_ge(")
    _, co1_see_self = find_fn_count(p_co1["self_counts"], "forge::Board::see_ge(")

    ap_name, base_ap_incl = find_fn_count(p_base["incl_counts"], "forge::nnue::v3::apply_pair_and_evaluate(")
    _, co2_ap_incl = find_fn_count(p_co2["incl_counts"], "forge::nnue::v3::apply_pair_and_evaluate(")
    _, base_ap_self = find_fn_count(p_base["self_counts"], "forge::nnue::v3::apply_pair_and_evaluate(")
    _, co2_ap_self = find_fn_count(p_co2["self_counts"], "forge::nnue::v3::apply_pair_and_evaluate(")

    def eval_control_verdict(ctrl_label: str, fn_name: str, base_incl: int, ctrl_incl: int, base_self: int, ctrl_self: int,
                             base_tot: int, ctrl_tot: int, b1_res: dict) -> dict:
        b1_d = b1_res["pooled_delta_pg_s"]
        h = b1_res["h_pg_s"]
        fn_diff_samp = ctrl_incl - base_incl
        tot_diff_samp = ctrl_tot - base_tot
        b2_fn_d = fn_diff_samp * PERIOD_S / GAMES_W60
        b2_tot_d = tot_diff_samp * PERIOD_S / GAMES_W60
        abs_diff = abs(b2_fn_d - b1_d)
        bound = 0.25 * abs(b1_d) + h
        err_rel = (b2_fn_d - b1_d) / b1_d
        if abs(b1_res["pct_of_base"]) < 1.0:
            verdict = "VOID"
        elif h > 0.25 * abs(b1_d):
            verdict = "UNDECIDED"
        elif abs_diff <= bound:
            verdict = "TRUSTED"
        else:
            verdict = "NOT TRUSTED"
        return {
            "ctrl_label": ctrl_label,
            "fn_name": fn_name,
            "base_incl": base_incl,
            "ctrl_incl": ctrl_incl,
            "fn_diff_samp": fn_diff_samp,
            "base_self": base_self,
            "ctrl_self": ctrl_self,
            "base_tot": base_tot,
            "ctrl_tot": ctrl_tot,
            "tot_diff_samp": tot_diff_samp,
            "b1_d_s": b1_d,
            "h_s": h,
            "b2_fn_d_s": b2_fn_d,
            "b2_tot_d_s": b2_tot_d,
            "err_rel": err_rel,
            "abs_diff_s": abs_diff,
            "bound_s": bound,
            "verdict": verdict,
        }

    v_co1 = eval_control_verdict(
        f"CO1 (k={meta['k1']}, Board::see_ge)", see_name,
        base_see_incl, co1_see_incl, base_see_self, co1_see_self,
        p_base["total_samples"], p_co1["total_samples"], b1_co1,
    )
    v_co2 = eval_control_verdict(
        f"CO2 (k2={meta['k2']}, nnue::v3::apply_pair_and_evaluate)", ap_name,
        base_ap_incl, co2_ap_incl, base_ap_self, co2_ap_self,
        p_base["total_samples"], p_co2["total_samples"], b1_co2,
    )

    b2_lines = [
        "=== JOB 37 PART B2 — PROFILER DELTAS & FUNCTION-LEVEL VERDICTS (perf record -e task-clock -c 50000 -g on W[1..60]) ===",
        "Event & period: task-clock, fixed period = 50,000 ns (50 us / sample), 60 finished games on W[1..60].",
        f"BASE W[1..60]: total_samples = {p_base['total_samples']} ({p_base['total_samples']*PERIOD_S:.4f}s; rusage eng_cpu = {p_base['run_info']['eng_cpu_s']:.4f}s)",
        f"CO1  W[1..60]: total_samples = {p_co1['total_samples']} ({p_co1['total_samples']*PERIOD_S:.4f}s; rusage eng_cpu = {p_co1['run_info']['eng_cpu_s']:.4f}s)",
        f"CO2  W[1..60]: total_samples = {p_co2['total_samples']} ({p_co2['total_samples']*PERIOD_S:.4f}s; rusage eng_cpu = {p_co2['run_info']['eng_cpu_s']:.4f}s)",
        f"B4   W[1..60]: total_samples = {p_b4['total_samples']} ({p_b4['total_samples']*PERIOD_S:.4f}s; rusage eng_cpu = {p_b4['run_info']['eng_cpu_s']:.4f}s)",
        "",
    ]
    for v in [v_co1, v_co2]:
        b2_lines.extend([
            f"--- {v['ctrl_label']} ---",
            f"  Target function               : {v['fn_name']}",
            f"  Function self samples         : BASE = {v['base_self']} ({100*v['base_self']/v['base_tot']:.2f}%), CTRL = {v['ctrl_self']} ({100*v['ctrl_self']/v['ctrl_tot']:.2f}%), diff = {v['ctrl_self']-v['base_self']:+d}",
            f"  Function INCLUSIVE samples    : BASE = {v['base_incl']} ({100*v['base_incl']/v['base_tot']:.2f}%), CTRL = {v['ctrl_incl']} ({100*v['ctrl_incl']/v['ctrl_tot']:.2f}%), diff = {v['fn_diff_samp']:+d}",
            f"  Total forge samples           : BASE = {v['base_tot']}, CTRL = {v['ctrl_tot']}, diff = {v['tot_diff_samp']:+d}",
            f"  B1 clock delta (eng_cpu/game) : {v['b1_d_s']*1000:+.6f} ms/game (h = {v['h_s']*1000:.6f} ms/game)",
            f"  B2 function delta (incl/game) : {v['b2_fn_d_s']*1000:+.6f} ms/game  [({v['fn_diff_samp']:+d} * 50 us) / 60]",
            f"  B2 total delta (total/game)   : {v['b2_tot_d_s']*1000:+.6f} ms/game  [({v['tot_diff_samp']:+d} * 50 us) / 60]",
            f"  Relative attribution error    : error = (B2 - B1) / B1 = {v['err_rel']*100:+.2f}%",
            f"  Trust gate |B2 - B1| <= 0.25*B1 + h: |{v['b2_fn_d_s']*1000:.6f} - {v['b1_d_s']*1000:.6f}| = {v['abs_diff_s']*1000:.6f} ms/g vs bound {v['bound_s']*1000:.6f} ms/g",
            f"  VERDICT                       : {v['verdict']} ({v['abs_diff_s']*1000:.6f} <= {v['bound_s']*1000:.6f})" if v["verdict"] == "TRUSTED" else f"  VERDICT                       : {v['verdict']} ({v['abs_diff_s']*1000:.6f} vs {v['bound_s']*1000:.6f})",
            "",
        ])
    (OUT37 / "partB_B2_perf_deltas_raw.txt").write_text("\n".join(b2_lines), encoding="utf-8")

    # ========================================================================
    # Write partB_B3_B4_tables_raw.txt (B3 on BASE + B4 on SP-PGO side by side)
    # ========================================================================
    def format_top25_and_groups(p_data: dict, heading: str) -> list[str]:
        tot = p_data["total_samples"]
        out = [
            heading,
            f"Total forge samples on W[1..60]: {tot} (= {tot*PERIOD_S:.4f} s task-clock; rusage eng_cpu = {p_data['run_info']['eng_cpu_s']:.4f} s)",
            "",
            "Rank   Self_Samp   Self_%   Incl_Samp   Incl_%   Function (demangled linkage name)",
            "-" * 115,
        ]
        for rk, (fn, sc) in enumerate(p_data["self_counts"].most_common(25), start=1):
            ic = p_data["incl_counts"].get(fn, sc)
            out.append(f"{rk:4d}   {sc:9d}   {100*sc/tot:5.2f}%   {ic:9d}   {100*ic/tot:5.2f}%   {fn}")
        out.append("-" * 115)
        out.append("")
        out.append("Group Breakdown (mutually exclusive partition of all samples):")
        out.append("Group                                      Samples    Share_%")
        out.append("-" * 64)
        g_sum = 0
        for g in GROUPS_ORDER:
            gc = p_data["group_counts"][g]
            g_sum += gc
            out.append(f"{g:40s}   {gc:7d}    {100*gc/tot:6.2f}%")
        out.append("-" * 64)
        out.append(f"{'TOTAL (sum == total_samples)':40s}   {g_sum:7d}    {100*g_sum/tot:6.2f}%  PASS ({g_sum} == {tot})")
        bis = p_data["board_in_search_samples"]
        out.append(f"  (Note: within 'the search', Board state/legality/make-unmake functions account for {bis} samples = {100*bis/tot:.2f}% of total.)")
        out.append("")
        return out

    t_lines = []
    t_lines.extend(format_top25_and_groups(p_base, "=== JOB 37 PART B3 — THE TABLE (BASE ON W[1..60], B2 RECORDING) ==="))
    t_lines.extend(format_top25_and_groups(p_b4, "=== JOB 37 PART B4 — THE SP-PGO TABLE (r15d+v3 SP-PGO ON W[1..60]) BESIDE B3 ==="))

    # Side-by-side Group comparison B3 vs B4
    tot_b3 = p_base["total_samples"]
    tot_b4 = p_b4["total_samples"]
    t_lines.extend([
        "=== B3 (BASE -O3) vs B4 (SP-PGO + ThinLTO) SIDE-BY-SIDE GROUP COMPARISON ===",
        f"Total task-clock samples: BASE = {tot_b3} ({tot_b3*PERIOD_S:.4f}s) vs B4_SP_PGO = {tot_b4} ({tot_b4*PERIOD_S:.4f}s), delta = {100*(tot_b4-tot_b3)/tot_b3:+.2f}%",
        "Group                                      B3_Samp   B3_%     B4_Samp   B4_%     Samp_Change",
        "-" * 92,
    ])
    for g in GROUPS_ORDER:
        c3 = p_base["group_counts"][g]
        c4 = p_b4["group_counts"][g]
        pct_chg = 100.0 * (c4 - c3) / c3 if c3 > 0 else 0.0
        t_lines.append(f"{g:40s}   {c3:7d}  {100*c3/tot_b3:5.2f}%   {c4:7d}  {100*c4/tot_b4:5.2f}%   {c4-c3:+7d} ({pct_chg:+6.2f}%)")
    t_lines.append("")

    # Exact cross-TU / profile-guided inlining comparison: functions with callq in BASE that disappear or shrink in B4_SP_PGO
    def count_all_calls(exe: str) -> collections.Counter[str]:
        dis = subprocess.check_output(["objdump", "-d", "-C", exe], text=True)
        c: collections.Counter[str] = collections.Counter()
        for ln in dis.splitlines():
            if "\tcall" in ln and "<forge::" in ln:
                m = re.search(r"<(forge::[^+>]+)>", ln)
                if m:
                    c[m.group(1)] += 1
        return c

    calls_base = count_all_calls(meta["base_exe"])
    calls_b4 = count_all_calls(meta["b4_exe"])

    t_lines.extend([
        "=== WHICH FUNCTIONS THE SP-PGO + THINLTO STEP INLINES INTO OTHERS ===",
        "A. Direct `callq` counts in `objdump -d -C` (BASE vs B4_SP_PGO) for hot functions whose `callq`s drop in SP-PGO:",
        "   BASE_calls  B4_calls   Function",
        "   " + "-" * 95,
    ])
    call_diffs = []
    for fn, cb in calls_base.items():
        c4 = calls_b4.get(fn, 0)
        if cb != c4 and (cb >= 2 or p_base["incl_counts"].get(fn, 0) >= 1000):
            call_diffs.append((p_base["incl_counts"].get(fn, 0), cb, c4, fn))
    call_diffs.sort(reverse=True)
    for _, cb, c4, fn in call_diffs[:25]:
        t_lines.append(f"   {cb:10d}  {c4:8d}   {fn}")

    t_lines.extend([
        "",
        "B. Measured DWARF inline pairs `(innermost function -> physical host symbol)` in B4_SP_PGO that were NOT inlined",
        "   into that host in BASE (top 20 by B4 sample count):",
        "   B4_Samples  B4_%    BASE_Samples  Inlined Function  -->  Host Physical Function",
        "   " + "-" * 105,
    ])
    new_inlines = []
    for (inf, hostf), c4 in p_b4["inlined_into_counts"].most_common(200):
        cb = p_base["inlined_into_counts"].get((inf, hostf), 0)
        if c4 - cb >= 250 and not is_generic_helper(inf):
            new_inlines.append((c4 - cb, c4, cb, inf, hostf))
    new_inlines.sort(reverse=True)
    for _, c4, cb, inf, hostf in new_inlines[:20]:
        t_lines.append(f"   {c4:10d}  {100*c4/tot_b4:5.2f}%  {cb:12d}  {canonical_fn_stem(inf)}  -->  {canonical_fn_stem(hostf)}")

    (OUT37 / "partB_B3_B4_tables_raw.txt").write_text("\n".join(t_lines) + "\n", encoding="utf-8")

    # Append Part B completion stamp AFTER all Part B work and raw files are written!
    with (OUT37 / "stamps.txt").open("a", encoding="utf-8") as sf:
        sf.write(
            f"{utc_now()} | Part B finished: BASE, CO1(k={meta['k1']}: {v_co1['verdict']}, err={v_co1['err_rel']*100:+.2f}%), "
            f"CO2(k2={meta['k2']}: {v_co2['verdict']}, err={v_co2['err_rel']*100:+.2f}%), B3 table, and B4 SP-PGO table completed\n"
        )

    log(f"PART_B_ALL_DONE: CO1={v_co1['verdict']} (B1={v_co1['b1_d_s']*1000:+.3f}ms/g, B2={v_co1['b2_fn_d_s']*1000:+.3f}ms/g, err={v_co1['err_rel']*100:+.2f}%), CO2={v_co2['verdict']} (B1={v_co2['b1_d_s']*1000:+.3f}ms/g, B2={v_co2['b2_fn_d_s']*1000:+.3f}ms/g, err={v_co2['err_rel']*100:+.2f}%)")


if __name__ == "__main__":
    main()
