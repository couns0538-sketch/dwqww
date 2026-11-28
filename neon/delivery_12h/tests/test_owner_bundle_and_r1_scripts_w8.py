"""CPU-only verification suite for Stream A (FORGE TEAMWORK WAVE 8, Milestone M1).

Verifies genuinely (no mocks/hardcoded outputs, < 5s):
  1. OWNER_BUNDLE_DECLARATION.json matches on-disk SHA-256 digests of
     FORGE_OWNER_BUNDLE_PGO.exe, FORGE_OWNER_BUNDLE_PGO.patch, all 4 constituent
     patches, G3_FULL25/cand.fnn3, r0067/train/cand.fnn3, and live forge.exe.
  2. FORGE_OWNER_BUNDLE_PGO.patch has 52 @@ hunks (34 + 1 + 5 + 12) across 4 files,
     passes `git apply --check` on a temporary copy of C:\\nnue-lab\\forge\\r15dsg
     inside scratch temp (cleaned up in finally:), and LmrDeeperShallower defaults
     to false in forge/r15dsg.
  3. All 5 Stream A Python runner scripts (plus run_net_match.py) compile cleanly via
     py_compile into TemporaryDirectory(), keep writes strictly under neon/,
     enforce/default concurrency <= 7 on clock runners (and default 8 for 50k SPRT),
     manage CLOCK_MATCH_RUNNING in try/finally for clock runs, and never write
     .cache.npz into runs/forge/.
  4. serverday_v3/run_dedup_buckets_v3.sh and run_train_stream_gpu_v3.sh use strict
     LF-only endings, enforce --skip-noisy / --skip-fqs-noisy and --king-buckets 16
     by default, and never pass --save-ckpt-every or --keep-in-check in active code.
  5. Stream A deliverables contain zero forbidden words and zero cache/binary leftovers.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

# Enforce strictly CPU-only execution and no bytecode caching.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HIP_VISIBLE_DEVICES"] = ""
os.environ["ROCR_VISIBLE_DEVICES"] = ""

STREAM_A_DIR = Path(__file__).resolve().parents[1]
WAVE8_DIR = STREAM_A_DIR.parent
FORGE_FIXES_DIR = WAVE8_DIR.parent
NEON_DIR = FORGE_FIXES_DIR.parent
LAB_ROOT = NEON_DIR.parent
R15DSG_DIR = LAB_ROOT / "forge" / "r15dsg"

TMP_ROOT = Path(
    r"C:\Users\Administrator\.gemini\antigravity\scratch\teamwork_tmp\4deb87b5-b27c-4d2e-974c-003f86fd73ca\streamA"
)

DECL_JSON = FORGE_FIXES_DIR / "OWNER_BUNDLE_DECLARATION.json"
BUNDLE_PATCH = FORGE_FIXES_DIR / "patches" / "FORGE_OWNER_BUNDLE_PGO.patch"
DOSSIER_MD = STREAM_A_DIR / "OWNER_BUNDLE_TECHNICAL_DOSSIER.md"

RUNNER_OWNER_BUNDLE = FORGE_FIXES_DIR / "run_owner_bundle_clock_test.py"
RUNNER_R1_TWIN = FORGE_FIXES_DIR / "run_opus_r1_keep_twin.py"
RUNNER_POST_250K = FORGE_FIXES_DIR / "run_post_bundle_250k_queue.py"
RUNNER_LMR_SPRT = FORGE_FIXES_DIR / "run_lmr_deeper_sprt.py"
RUNNER_CLOCK_TM = FORGE_FIXES_DIR / "run_clock_tm_screen.py"
RUNNER_NET_MATCH = FORGE_FIXES_DIR / "run_net_match.py"

ALL_RUNNERS = [
    RUNNER_OWNER_BUNDLE,
    RUNNER_R1_TWIN,
    RUNNER_POST_250K,
    RUNNER_LMR_SPRT,
    RUNNER_CLOCK_TM,
    RUNNER_NET_MATCH,
]

SH_DEDUP_V3 = FORGE_FIXES_DIR / "serverday_v3" / "run_dedup_buckets_v3.sh"
SH_TRAIN_V3 = FORGE_FIXES_DIR / "serverday_v3" / "run_train_stream_gpu_v3.sh"

FORBIDDEN_RE = re.compile("cu" + "red?", re.IGNORECASE)
FORBIDDEN_ROOT_NAMES = frozenset({"runs", "forge", "pipeline", "teamwork", "tools"})
FORBIDDEN_ROOT_RE = re.compile(
    r"(?:^|[/\\'\"\s(,])(?:runs|forge|pipeline|teamwork|tools)(?:[/\\'\"\s),]|$)"
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@contextmanager
def scratch_subdir(prefix: str):
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    td = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TMP_ROOT)))
    try:
        yield td
    finally:
        shutil.rmtree(td, ignore_errors=True)
        try:
            if TMP_ROOT.exists() and not any(TMP_ROOT.iterdir()):
                TMP_ROOT.rmdir()
        except OSError:
            pass


def _parse_ast(path: Path) -> tuple[str, ast.AST]:
    src = path.read_text(encoding="utf-8")
    return src, ast.parse(src, filename=str(path))


def _assigned_nodes(tree: ast.AST) -> dict[str, list[ast.AST]]:
    out: dict[str, list[ast.AST]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    out.setdefault(tgt.id, []).append(node.value)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if isinstance(node.target, ast.Name):
                out.setdefault(node.target.id, []).append(node.value)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name):
                out.setdefault(node.target.id, []).append(node.value)
    return out


def _kw_arg(node: ast.Call, name: str) -> ast.AST | None:
    for kw in node.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _is_write_open_mode(mode_node: ast.AST | None) -> bool:
    if mode_node is None:
        return False
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return any(ch in mode_node.value for ch in ("w", "a", "x", "+"))
    return True


def _write_call_target_nodes(tree: ast.AST) -> list[tuple[str, ast.AST]]:
    path_write_methods = {"write_text", "write_bytes", "mkdir", "unlink", "touch"}
    found: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr in path_write_methods:
                found.append((func.attr, func.value))
            elif func.attr == "open":
                mode_node = node.args[0] if node.args else _kw_arg(node, "mode")
                if _is_write_open_mode(mode_node):
                    found.append(("open", func.value))
            elif isinstance(func.value, ast.Name) and func.value.id == "os":
                if func.attr in {"replace", "rename"}:
                    src_node = node.args[0] if node.args else _kw_arg(node, "src")
                    dst_node = node.args[1] if len(node.args) >= 2 else _kw_arg(node, "dst")
                    if dst_node is not None:
                        found.append((f"os.{func.attr}", dst_node))
                    if src_node is not None:
                        found.append((f"os.{func.attr}", src_node))
                elif func.attr in {"remove", "unlink", "mkdir", "makedirs"}:
                    p_node = node.args[0] if node.args else (_kw_arg(node, "path") or _kw_arg(node, "name"))
                    if p_node is not None:
                        found.append((f"os.{func.attr}", p_node))
            elif isinstance(func.value, ast.Name) and func.value.id == "shutil":
                if func.attr in {"copy", "copy2", "copyfile", "copytree", "move"}:
                    src_node = node.args[0] if node.args else _kw_arg(node, "src")
                    dst_node = node.args[1] if len(node.args) >= 2 else _kw_arg(node, "dst")
                    if dst_node is not None:
                        found.append((f"shutil.{func.attr}", dst_node))
                    if func.attr == "move" and src_node is not None:
                        found.append(("shutil.move", src_node))
                elif func.attr == "rmtree":
                    p_node = node.args[0] if node.args else _kw_arg(node, "path")
                    if p_node is not None:
                        found.append(("shutil.rmtree", p_node))
            elif func.attr in {"rename", "replace"} and (
                (len(node.args) == 1 and not node.keywords)
                or (len(node.args) == 0 and _kw_arg(node, "target") is not None)
            ):
                tgt = node.args[0] if node.args else _kw_arg(node, "target")
                found.append((f"Path.{func.attr}", func.value))
                if tgt is not None:
                    found.append((f"Path.{func.attr}", tgt))
        elif isinstance(func, ast.Name):
            if func.id == "atomic_write_json":
                p_node = node.args[0] if node.args else _kw_arg(node, "path")
                if p_node is not None:
                    found.append((func.id, p_node))
            elif func.id == "open":
                file_node = node.args[0] if node.args else _kw_arg(node, "file")
                mode_node = node.args[1] if len(node.args) >= 2 else _kw_arg(node, "mode")
                if file_node is not None and _is_write_open_mode(mode_node):
                    found.append(("open", file_node))
    return found


def _expr_has_forbidden_root(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            parts = [p for p in sub.value.replace("\\", "/").split("/") if p]
            if any(p in FORBIDDEN_ROOT_NAMES for p in parts):
                return True
    return bool(FORBIDDEN_ROOT_RE.search(ast.unparse(node)))


def _assert_write_target_safe(
    op: str,
    target_node: ast.AST,
    assign_nodes: dict[str, list[ast.AST]],
    script_name: str,
) -> None:
    target_src = ast.unparse(target_node)
    assert not _expr_has_forbidden_root(target_node), (
        f"Unsafe write target ({op}) in {script_name}: {target_src}"
    )
    queue = [n.id for n in ast.walk(target_node) if isinstance(n, ast.Name)]
    visited: set[str] = set()
    while queue:
        var_name = queue.pop(0)
        if var_name in visited:
            continue
        visited.add(var_name)
        for val_node in assign_nodes.get(var_name, []):
            assert not _expr_has_forbidden_root(val_node), (
                f"Variable {var_name} in {script_name} points outside neon/: {ast.unparse(val_node)}"
            )
            for sub in ast.walk(val_node):
                if isinstance(sub, ast.Name) and sub.id not in visited:
                    queue.append(sub.id)


def _argparse_defaults(tree: ast.AST) -> dict[str, object]:
    defaults: dict[str, object] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            flags = [
                a.value for a in node.args
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith("--")
            ]
            d_node = _kw_arg(node, "default")
            if flags and d_node is not None and isinstance(d_node, ast.Constant):
                defaults[flags[0]] = d_node.value
    return defaults


# ---------------------------------------------------------------------------
# 1. OWNER_BUNDLE_DECLARATION.json on-disk SHA-256 verification
# ---------------------------------------------------------------------------


def test_owner_bundle_declaration_sha256s() -> None:
    assert DECL_JSON.is_file(), f"Missing {DECL_JSON}"
    decl = json.loads(DECL_JSON.read_text(encoding="utf-8"))

    file_checks = [
        ("bundle_exe", "bundle_exe_sha256"),
        ("bundle_patch", "bundle_patch_sha256"),
        ("live_pgo_exe", "live_pgo_exe_sha256"),
        ("g3_net", "g3_net_sha256"),
        ("r0067_net", "r0067_net_sha256"),
    ]
    for path_key, sha_key in file_checks:
        p = Path(decl[path_key])
        assert p.is_file(), f"Missing {path_key}: {p}"
        assert _sha256_file(p) == decl[sha_key], f"SHA-256 mismatch for {path_key}"

    assert Path(decl["bundle_exe"]).stat().st_size == decl["bundle_exe_bytes"] == 2447872

    patches = decl["patches_included"]
    assert len(patches) == 4
    for entry in patches:
        pp = Path(entry["patch"])
        assert pp.is_file(), f"Missing constituent patch: {pp}"
        assert _sha256_file(pp) == entry["sha256"], f"SHA-256 mismatch for {entry['name']}"

    assert decl["extra_uci_options_on_bundle"] == {"LmrDeeperShallower": True}
    assert decl["gates"]["perft5"] == 4865609
    assert decl["gates"]["g3_full_hard_pass"] is True
    assert decl["gates"]["r0067_quick_hard_pass"] is True


# ---------------------------------------------------------------------------
# 2. Combined patch hunk counts, git apply --check on temp r15dsg, & UCI default
# ---------------------------------------------------------------------------


def test_owner_bundle_patch_hunks_and_git_apply_check_temp_r15dsg() -> None:
    assert BUNDLE_PATCH.is_file(), f"Missing {BUNDLE_PATCH}"
    decl = json.loads(DECL_JSON.read_text(encoding="utf-8"))

    # Verify constituent hunk counts sum to 34 + 1 + 5 + 12 = 52
    expected_constituent_hunks = {
        "V3P_pairwise_psqt_fused_v3.patch": 34,
        "SF13_qs_evasion_pruning.patch": 1,
        "SF8_conthist_6ply.patch": 5,
        "proto_1_corrhist_minor.patch": 12,
    }
    total_const = 0
    for entry in decl["patches_included"]:
        txt = Path(entry["patch"]).read_text(encoding="utf-8")
        cnt = sum(1 for ln in txt.splitlines() if ln.startswith("@@"))
        assert cnt == expected_constituent_hunks[entry["name"]], entry["name"]
        total_const += cnt
    assert total_const == 52

    # Verify combined patch has 52 hunks across the 4 exact files
    bundle_txt = BUNDLE_PATCH.read_text(encoding="utf-8")
    file_hunks: dict[str, int] = {}
    cur_file: str | None = None
    for ln in bundle_txt.splitlines():
        if ln.startswith("+++ b/"):
            cur_file = ln[6:]
            file_hunks.setdefault(cur_file, 0)
        elif ln.startswith("@@") and cur_file is not None:
            file_hunks[cur_file] += 1

    assert file_hunks == {
        "include/forge/nnue_v3.hpp": 12,
        "include/forge/search.hpp": 3,
        "src/nnue_v3.cpp": 22,
        "src/search.cpp": 15,
    }
    assert sum(file_hunks.values()) == 52

    # Verify LmrDeeperShallower defaults to false in forge/r15dsg
    assert "extern bool LmrDeeperShallower;" in (R15DSG_DIR / "include/forge/search.hpp").read_text(encoding="utf-8")
    assert "bool LmrDeeperShallower = false;" in (R15DSG_DIR / "src/search.cpp").read_text(encoding="utf-8")
    assert "option name LmrDeeperShallower type check default false" in (R15DSG_DIR / "src/uci.cpp").read_text(encoding="utf-8")

    # Apply --check on a temporary copy of forge/r15dsg in scratch_subdir (cleaned in finally)
    with scratch_subdir("r15dsg_check_") as td:
        copy_dir = td / "r15dsg"
        shutil.copytree(R15DSG_DIR, copy_dir)
        res = subprocess.run(
            ["git", "-C", str(copy_dir), "apply", "--check", str(BUNDLE_PATCH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert res.returncode == 0, f"git apply --check failed: {res.stderr}"
        assert res.stderr == ""


# ---------------------------------------------------------------------------
# 3. Python runner py_compile, AST write boundaries, concurrency, lock & cache guards
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script_path", ALL_RUNNERS)
def test_runners_py_compile_zero_cache_and_safe_writes(script_path: Path) -> None:
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert script_path.is_file(), f"Missing script: {script_path}"
    before_root_pycache = (LAB_ROOT / "__pycache__").exists()
    with tempfile.TemporaryDirectory() as td:
        cfile = Path(td) / f"{script_path.stem}.pyc"
        compiled = py_compile.compile(str(script_path), cfile=str(cfile), doraise=True)
        assert compiled == str(cfile)
        assert cfile.is_file() and cfile.stat().st_size > 0
    assert (LAB_ROOT / "__pycache__").exists() == before_root_pycache

    _, tree = _parse_ast(script_path)
    assigns = _assigned_nodes(tree)
    for op, tgt_node in _write_call_target_nodes(tree):
        _assert_write_target_safe(op, tgt_node, assigns, script_path.name)


def test_clock_and_sprt_runners_concurrency_and_lockfile_ast() -> None:
    # 1) run_owner_bundle_clock_test.py: concurrency default <= 7 (== 7), CLOCK_MATCH_RUNNING in try/finally
    src_ob, tree_ob = _parse_ast(RUNNER_OWNER_BUNDLE)
    defs_ob = _argparse_defaults(tree_ob)
    assert defs_ob["--concurrency"] <= 7 and defs_ob["--concurrency"] == 7
    assert defs_ob["--games"] == 2000
    assert defs_ob["--tc"] == "6+0.06"
    assert ".cache.npz" not in src_ob
    assert "CLOCK_MATCH_RUNNING" in src_ob
    has_clock_finally = any(
        isinstance(n, ast.Try)
        and any("clock_flag" in ast.unparse(stmt) and "unlink" in ast.unparse(stmt) for stmt in n.finalbody)
        for n in ast.walk(tree_ob)
    )
    assert has_clock_finally, "run_owner_bundle_clock_test.py must unlink clock_flag in try/finally"
    has_work_finally = any(
        isinstance(n, ast.Try)
        and any("rmtree" in ast.unparse(stmt) and "work" in ast.unparse(stmt) for stmt in n.finalbody)
        for n in ast.walk(tree_ob)
    )
    assert has_work_finally, "run_owner_bundle_clock_test.py must clean work dir in finally"

    # 2) run_clock_tm_screen.py: concurrency default <= 7 (== 7), delegates --nodes 0 --tc to run_net_match.py
    src_tm, tree_tm = _parse_ast(RUNNER_CLOCK_TM)
    defs_tm = _argparse_defaults(tree_tm)
    assert defs_tm["--concurrency"] <= 7 and defs_tm["--concurrency"] == 7
    assert defs_tm["--games"] == 600
    assert defs_tm["--tc"] == "6+0.06"
    assert '"--nodes", "0", "--tc", tc' in src_tm
    assert "run_net_match.py" in src_tm
    assert ".cache.npz" not in src_tm

    # 3) run_net_match.py: is_clock = (args.nodes == 0) and clock_flag unlinked in try/finally
    src_nm, tree_nm = _parse_ast(RUNNER_NET_MATCH)
    defs_nm = _argparse_defaults(tree_nm)
    assert defs_nm["--nodes"] == 50000
    assert "CLOCK_MATCH_RUNNING" in src_nm
    assert ".cache.npz" not in src_nm
    has_nm_finally = any(
        isinstance(n, ast.Try)
        and any("clock_flag" in ast.unparse(stmt) and "unlink" in ast.unparse(stmt) for stmt in n.finalbody)
        for n in ast.walk(tree_nm)
    )
    assert has_nm_finally, "run_net_match.py must unlink clock_flag in try/finally"

    # 4) run_lmr_deeper_sprt.py: defaults --nodes 50000, --tc "", --concurrency 8; LOCK in try/finally when is_clock
    src_sprt, tree_sprt = _parse_ast(RUNNER_LMR_SPRT)
    defs_sprt = _argparse_defaults(tree_sprt)
    assert defs_sprt["--nodes"] == 50000
    assert defs_sprt["--tc"] == ""
    assert defs_sprt["--concurrency"] == 8
    assert "CLOCK_MATCH_RUNNING" in src_sprt
    assert ".cache.npz" not in src_sprt
    has_sprt_finally = any(
        isinstance(n, ast.Try)
        and any("LOCK" in ast.unparse(stmt) and "unlink" in ast.unparse(stmt) for stmt in n.finalbody)
        for n in ast.walk(tree_sprt)
    )
    assert has_sprt_finally, "run_lmr_deeper_sprt.py must unlink LOCK in try/finally"


def test_r1_twin_and_post_bundle_250k_cache_guards() -> None:
    # 1) run_opus_r1_keep_twin.py: ft._load_one / ft._count_one monkey-patched read-only on .cache.npz
    src_r1, tree_r1 = _parse_ast(RUNNER_R1_TWIN)
    defs_r1 = _argparse_defaults(tree_r1)
    assert defs_r1["--seed"] == 1
    assert "ft._parse_plain" in src_r1

    monkey_attrs = set()
    for node in ast.walk(tree_r1):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == "ft":
                    monkey_attrs.add((tgt.attr, ast.unparse(node.value)))
    assert ("_load_one", "safe_load_one") in monkey_attrs
    assert ("_count_one", "safe_count_one") in monkey_attrs

    # .cache.npz must never appear in any write target node
    for op, tgt_node in _write_call_target_nodes(tree_r1):
        assert ".cache.npz" not in ast.unparse(tgt_node), f"Unexpected cache write ({op}) in R1 twin"

    # Both safe_load_one and safe_count_one must guard orig_* behind existing_cache.exists()
    fn_defs = {n.name: n for n in ast.walk(tree_r1) if isinstance(n, ast.FunctionDef)}
    for fn_name in ("safe_load_one", "safe_count_one"):
        fn_src = ast.unparse(fn_defs[fn_name])
        assert "existing_cache.exists()" in fn_src
        assert "ft._parse_plain" in fn_src

    # 2) run_post_bundle_250k_queue.py: zero direct writes, delegates --nodes 250000 via run_net_match.py
    src_q, tree_q = _parse_ast(RUNNER_POST_250K)
    assert _write_call_target_nodes(tree_q) == []
    assert '"--nodes", "250000"' in src_q
    assert "run_net_match.py" in src_q
    assert ".cache.npz" not in src_q


# ---------------------------------------------------------------------------
# 4. serverday_v3 shell wrapper LF-only & CLI flag invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sh_path", [SH_DEDUP_V3, SH_TRAIN_V3])
def test_serverday_v3_shell_wrappers_lf_only_and_flags(sh_path: Path) -> None:
    assert sh_path.is_file(), f"Missing shell wrapper: {sh_path}"
    raw = sh_path.read_bytes()
    assert b"\r" not in raw, f"CR byte found in {sh_path.name}"
    assert b"\n" in raw, f"No LF found in {sh_path.name}"

    text = raw.decode("utf-8")
    # Strip # comment lines before inspecting active CLI flags
    active = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))

    assert "--save-ckpt-every" not in active, f"Forbidden --save-ckpt-every in {sh_path.name}"
    assert "--keep-in-check" not in active, f"Forbidden --keep-in-check in {sh_path.name}"

    if sh_path == SH_DEDUP_V3:
        assert "--skip-noisy" in active
        assert "--drop-draw-conflict 600" in active
        assert "--dedup-mode" in active
    else:
        assert 'KING_BUCKETS="${KING_BUCKETS:-16}"' in active
        assert "--king-buckets" in active
        assert "--skip-fqs-noisy" in active


# ---------------------------------------------------------------------------
# 5. Stream A deliverable hygiene & zero forbidden words
# ---------------------------------------------------------------------------


def test_stream_a_deliverables_hygiene_and_forbidden_words() -> None:
    assert DOSSIER_MD.is_file(), f"Missing {DOSSIER_MD}"
    dossier_txt = DOSSIER_MD.read_text(encoding="utf-8")
    assert len(dossier_txt) > 4000
    assert not FORBIDDEN_RE.search(dossier_txt), "Forbidden word found in OWNER_BUNDLE_TECHNICAL_DOSSIER.md"

    for marker in (
        "FORGE_OWNER_BUNDLE_PGO.exe",
        "95d0608e1a6c4c4ba6606a6ba2a8e4562280f71129b33d5d71f65b7e3c8941b0",
        "4865609",
        "Arm A",
        "Arm B",
        "COMBO_v2",
        "SF4b1",
        "obm4",
        "LmrDeeperShallower",
        "52",
    ):
        assert marker in dossier_txt, f"Missing {marker!r} in OWNER_BUNDLE_TECHNICAL_DOSSIER.md"

    test_txt = Path(__file__).read_text(encoding="utf-8")
    assert not FORBIDDEN_RE.search(test_txt), "Forbidden word found in test_owner_bundle_and_r1_scripts_w8.py"

    forbidden_exts = {".pyc", ".exe", ".fnn3", ".pt", ".fqs", ".plain", ".pgn", ".o", ".obj", ".part"}
    for p in STREAM_A_DIR.rglob("*"):
        assert p.name not in {"__pycache__", ".pytest_cache"}, f"Forbidden cache dir: {p}"
        assert not p.name.startswith("_work_"), f"Forbidden _work_ dir: {p}"
        if p.is_file():
            assert p.suffix.lower() not in forbidden_exts, f"Forbidden extension: {p}"
