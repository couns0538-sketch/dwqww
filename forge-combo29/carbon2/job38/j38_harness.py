#!/usr/bin/env python3
"""
Job 38 UCI & Build Harness (`j38_harness.py`):
- Enforces strict UCI handshake: after EVERY `setoption`, `ucinewgame`, and `position`,
  sends `isready` and reads every line to `readyok`, raising immediately on
  "unknown option", "invalid value", "invalid FEN", or non-empty stderr / unexpected EOF.
- Writes `<rows_path>` (`index\tdepth\tnodes`) and `<rows_path>.meta` (`exe`, `sha256`,
  `id name`, every `setoption` line sent, `positions`, `count`, `depth`, `sum`, `exit`)
  beside every rows file.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Sequence

sys.dont_write_bytecode = True

BASE_COMMIT = "6b98f2170a3210e71beed04bbd2553972c253ed7"
REPO = pathlib.Path("/agent/repos/dwqww")
OUT38 = REPO / "forge-combo29/carbon2/job38"
WORK38 = pathlib.Path("/tmp/carbon2_job38")
FENS_O = WORK38 / "inputs/first200.fens"
FENS_G = WORK38 / "inputs/set_G.epd"

S14_OPTIONS: list[tuple[str, str]] = [
    ("Threads", "1"),
    ("Hash", "16"),
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
]

EXP_BENCH11 = 312866
EXP_BENCH13 = 862329
EXP_BENCH16 = 3024920
EXP_PERFT5 = 4865609
EXP_O_SUM = 9500069
EXP_O_FIRST3 = [41311, 24872, 28574]
EXP_G_SUM = 18466239

BAD_MARKERS = ("unknown option", "invalid value", "invalid fen")


def utc_now() -> str:
    return subprocess.check_output(["date", "-u"], text=True).strip()


def sha256_file(p: pathlib.Path | str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_pass(label: str, got: object, exp: object) -> tuple[bool, str]:
    ok = got == exp
    tag = "PASS" if ok else "FAIL"
    op = "==" if ok else "!="
    return ok, f"{label}: {tag} ({got} {op} {exp})"


def load_fens(path: pathlib.Path) -> list[str]:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return lines


def check_line_no_error(line: str, context: str) -> None:
    low = line.lower()
    for bm in BAD_MARKERS:
        if bm in low:
            raise RuntimeError(f"UCI error marker {bm!r} during {context}: {line!r}")


def run_fresh_bench(exe: str, depth: int) -> int:
    stdin = f"uci\nisready\nbench {depth}\nisready\nquit\n"
    r = subprocess.run([exe], input=stdin, text=True, capture_output=True)
    if r.returncode != 0 or r.stderr:
        raise RuntimeError(f"bench {depth} failed on {exe}: rc={r.returncode} stderr={r.stderr!r}")
    prefix = f"info string bench depth {depth} nodes "
    for ln in r.stdout.splitlines():
        check_line_no_error(ln, f"bench {depth}")
        if ln.startswith(prefix):
            return int(ln[len(prefix):].split()[0])
    raise RuntimeError(f"Missing '{prefix}' in {exe} stdout:\n{r.stdout[-400:]}")


def run_fresh_perft5(exe: str) -> int:
    stdin = "uci\nisready\nposition startpos\nisready\ngo perft 5\nisready\nquit\n"
    r = subprocess.run([exe], input=stdin, text=True, capture_output=True)
    if r.returncode != 0 or r.stderr:
        raise RuntimeError(f"perft 5 failed on {exe}: rc={r.returncode} stderr={r.stderr!r}")
    for ln in r.stdout.splitlines():
        check_line_no_error(ln, "perft 5")
    for ln in reversed(r.stdout.splitlines()):
        if ln.startswith("nodes "):
            return int(ln.split()[1])
    raise RuntimeError(f"Missing 'nodes <N>' in perft 5 stdout:\n{r.stdout[-400:]}")


def check_four_numbers(exe: str) -> dict[str, int]:
    return {
        "bench11": run_fresh_bench(exe, 11),
        "bench13": run_fresh_bench(exe, 13),
        "bench16": run_fresh_bench(exe, 16),
        "perft5": run_fresh_perft5(exe),
    }


def measure_depth_set(
    exe: str,
    fens_path: pathlib.Path,
    depth: int,
    extra_options: Sequence[tuple[str, str]],
    rows_out: pathlib.Path,
) -> list[int]:
    """
    One fresh process for `(exe, fens_path)`.
    Sends `uci`, then S14 + `extra_options` (with `isready` -> `readyok` after EVERY setoption),
    then for every FEN: `ucinewgame` + `isready` -> `readyok`, `position fen <FEN>` + `isready` -> `readyok`,
    `go depth <depth>` -> `bestmove`.
    Writes `rows_out` and `rows_out.with_name(rows_out.name + '.meta')`.
    """
    fens = load_fens(fens_path)
    exe_sha = sha256_file(exe)
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None and proc.stderr is not None

    def send(cmd: str) -> None:
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    def read_until(target_token: str, ctx: str) -> list[str]:
        collected: list[str] = []
        while True:
            ln = proc.stdout.readline()
            if ln == "":
                err_txt = proc.stderr.read()
                raise RuntimeError(f"EOF waiting for {target_token!r} in {ctx}; stderr={err_txt!r}")
            s = ln.rstrip("\r\n")
            check_line_no_error(s, ctx)
            collected.append(s)
            if s == target_token or (target_token == "bestmove " and s.startswith("bestmove ")):
                return collected

    send("uci")
    uci_lines = read_until("uciok", "uci")
    id_name = ""
    for uln in uci_lines:
        if uln.startswith("id name "):
            id_name = uln
            break
    if not id_name:
        raise RuntimeError(f"Missing 'id name' in uci output of {exe}")

    sent_option_lines: list[str] = []
    for k, v in list(S14_OPTIONS) + list(extra_options):
        opt_cmd = f"setoption name {k} value {v}"
        sent_option_lines.append(opt_cmd)
        send(opt_cmd)
        send("isready")
        read_until("readyok", opt_cmd)

    nodes_list: list[int] = []
    nodes_re = re.compile(r"\bnodes\s+(\d+)\b")
    depth_re = re.compile(r"\bdepth\s+(\d+)\b")

    for idx, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until("readyok", f"ucinewgame #{idx}")

        pos_cmd = f"position fen {fen}"
        send(pos_cmd)
        send("isready")
        read_until("readyok", f"position #{idx}")

        send(f"go depth {depth}")
        go_lines = read_until("bestmove ", f"go depth {depth} #{idx}")
        last_nodes: int | None = None
        for gl in go_lines:
            if gl.startswith("info "):
                mn = nodes_re.search(gl)
                md = depth_re.search(gl)
                if mn and md:
                    last_nodes = int(mn.group(1))
        if last_nodes is None:
            raise RuntimeError(f"No info depth/nodes line on position #{idx} ({fen!r}): {go_lines[-5:]}")
        nodes_list.append(last_nodes)

    send("quit")
    _, stderr_txt = proc.communicate(timeout=15)
    rc = proc.returncode
    if rc != 0 or stderr_txt:
        raise RuntimeError(f"Engine exited rc={rc} stderr={stderr_txt!r}")

    rows_out.parent.mkdir(parents=True, exist_ok=True)
    row_lines = ["index\tdepth\tnodes"] + [f"{i}\t{depth}\t{n}" for i, n in enumerate(nodes_list, start=1)]
    rows_out.write_text("\n".join(row_lines) + "\n", encoding="utf-8")

    meta_path = rows_out.with_name(rows_out.name + ".meta")
    meta_lines = [
        f"exe {exe}",
        f"sha256 {exe_sha}",
        id_name,
        "options",
        *sent_option_lines,
        f"positions {fens_path}",
        f"count {len(nodes_list)}",
        f"depth {depth}",
        f"sum {sum(nodes_list)}",
        f"exit {rc}",
    ]
    meta_path.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")
    return nodes_list


def parse_seat_nodes_file(path: pathlib.Path) -> list[int]:
    out: list[int] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("index") or s.startswith("#"):
            continue
        pts = s.split()
        out.append(int(pts[-1]))
    return out


def build_worktree_patch(
    tag: str,
    patch_path: pathlib.Path | None,
) -> tuple[bool, str, str, str]:
    """
    Creates a fresh detached worktree of 6b98f217 at `/tmp/carbon2_job38/wt_<tag>`
    (sparse-checked-out to `forge-combo29/` for speed!), runs `git apply --check`
    then `git apply` if `patch_path` is provided, and builds Release with `g++`.
    Returns `(ok, msg, exe_path, exe_sha256)`.
    """
    wt_dir = WORK38 / f"wt_{tag}"
    bld_dir = WORK38 / f"bld_{tag}"
    if wt_dir.exists():
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(wt_dir)], capture_output=True)
        if wt_dir.exists():
            shutil.rmtree(wt_dir)
    if bld_dir.exists():
        shutil.rmtree(bld_dir)

    subprocess.run(
        ["git", "-C", str(REPO), "worktree", "add", "--no-checkout", "--detach", str(wt_dir), BASE_COMMIT],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(["git", "-C", str(wt_dir), "sparse-checkout", "init", "--cone"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(wt_dir), "sparse-checkout", "set", "forge-combo29"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(wt_dir), "checkout", BASE_COMMIT], check=True, capture_output=True)

    apply_msg = "base (no patch)"
    if patch_path is not None:
        # Try repo-root git apply --check first; if paths lack `forge-combo29/` prefix, try -p1 in forge-combo29
        chk = subprocess.run(
            ["git", "-C", str(wt_dir), "apply", "--check", str(patch_path)],
            capture_output=True,
            text=True,
        )
        if chk.returncode == 0:
            subprocess.run(["git", "-C", str(wt_dir), "apply", str(patch_path)], check=True)
            apply_msg = "git apply --check PASS (repo root)"
        else:
            chk2 = subprocess.run(
                ["git", "-C", str(wt_dir / "forge-combo29"), "apply", "--check", str(patch_path)],
                capture_output=True,
                text=True,
            )
            if chk2.returncode == 0:
                subprocess.run(["git", "-C", str(wt_dir / "forge-combo29"), "apply", str(patch_path)], check=True)
                apply_msg = "git apply --check PASS (forge-combo29 subdir)"
            else:
                return False, f"git apply --check FAIL: {chk.stderr.strip()} | {chk2.stderr.strip()}", "", ""

    cfg = subprocess.run(
        [
            "cmake",
            "-S", str(wt_dir / "forge-combo29"),
            "-B", str(bld_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_CXX_COMPILER=g++",
        ],
        capture_output=True,
        text=True,
    )
    if cfg.returncode != 0:
        return False, f"cmake configure FAIL: {cfg.stderr[-400:]}", "", ""

    bld = subprocess.run(["cmake", "--build", str(bld_dir), "-j4"], capture_output=True, text=True)
    if bld.returncode != 0:
        return False, f"cmake build FAIL: {bld.stderr[-400:]}\n{bld.stdout[-400:]}", "", ""

    exe = bld_dir / "forge"
    return True, apply_msg, str(exe), sha256_file(exe)
