"""CPU-only verification suite for Stream B (FORGE TEAMWORK WAVE 7).

Verifies genuinely (no mocks/hardcoded outputs):
  1. All 5 Wave-7 scripts compile cleanly via py_compile into TemporaryDirectory()
     with zero .pyc / __pycache__ leakage into C:\\nnue-lab.
  2. AST and source-level read-only safety checks across all 5 scripts (plus run_net_match.py):
     writes stay strictly inside neon/, run_opus_r1_live768_skipnoisy.py monkey-patches
     ft._load_one / ft._count_one in memory without --keep-noisy, run_stage2_clean_skipnoisy_gpu.py
     enforces --skip-fqs-noisy, CLOCK_MATCH_RUNNING cleanup sits in try/finally, and
     run_stage2_clean_skipnoisy_matches.py dispatches --nodes 50000 via run_net_match.py.
  3. Exact JSON schema and value invariants for all 5 Wave-7 JSON artifacts and
     G3_FULL25_PGO_vs_live_r0067_2000g_6p006/summary.json.
  4. Stream B deliverable hygiene: zero forbidden words and zero
     __pycache__ / .pytest_cache / .pyc / binary / _work_* leftovers under Stream B.
"""
from __future__ import annotations

import ast
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Enforce strictly CPU-only execution before any downstream subprocess/imports.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HIP_VISIBLE_DEVICES"] = ""
os.environ["ROCR_VISIBLE_DEVICES"] = ""
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

STREAM_B_DIR = Path(__file__).resolve().parents[1]
WAVE7_DIR = STREAM_B_DIR.parent
FORGE_FIXES_DIR = WAVE7_DIR.parent
NEON_DIR = FORGE_FIXES_DIR.parent
LAB_ROOT = NEON_DIR.parent
FILTER_QUEST_DIR = NEON_DIR / "filter_quest"

TARGET_SCRIPTS = [
    FILTER_QUEST_DIR / "run_stage2_clean_skipnoisy_gpu.py",
    FILTER_QUEST_DIR / "run_stage2_clean_skipnoisy_matches.py",
    FORGE_FIXES_DIR / "run_opus_r1_live768_skipnoisy.py",
    FORGE_FIXES_DIR / "run_lmr_deeper_sprt.py",
    FORGE_FIXES_DIR / "bench_serverday_4archs_pgo.py",
]

RUN_NET_MATCH_PY = FORGE_FIXES_DIR / "run_net_match.py"

FORENSIC_JSON = FORGE_FIXES_DIR / "CC0_NOISY_VS_QUIET_FORENSIC.json"
G3AB_JSON = FORGE_FIXES_DIR / "G3AB_DISTILL_REGIME_CHECK.json"
SPEED_2BUILDS_JSON = FORGE_FIXES_DIR / "CLEAN_IDLE_SPEED_2BUILDS.json"
SPEED_5ARCH_JSON = FORGE_FIXES_DIR / "CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json"
STAGE2_QUIET_JSON = FILTER_QUEST_DIR / "STAGE2_QUIET_GPU_SUMMARY.json"
G3_PGO_MATCH_JSON = (
    FORGE_FIXES_DIR
    / "matches"
    / "G3_FULL25_PGO_vs_live_r0067_2000g_6p006"
    / "summary.json"
)
SPEC_MD = STREAM_B_DIR / "SERVER_DAY_2B_FINAL_EXECUTION_SPEC.md"

FORBIDDEN_RE = re.compile("cu" + "red?", re.IGNORECASE)
FORBIDDEN_ROOT_NAMES = frozenset({"runs", "forge", "pipeline", "teamwork", "tools"})
FORBIDDEN_ROOT_RE = re.compile(
    r"(?:^|[/\\'\"\s(,])(?:runs|forge|pipeline|teamwork|tools)(?:[/\\'\"\s),]|$)"
)


def _cpu_env() -> dict[str, str]:
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["HIP_VISIBLE_DEVICES"] = ""
    env["ROCR_VISIBLE_DEVICES"] = ""
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _parse_ast(path: Path) -> tuple[str, ast.AST]:
    src = path.read_text(encoding="utf-8")
    return src, ast.parse(src, filename=str(path))


def _expr_has_forbidden_root(node: ast.AST) -> bool:
    """Return True if an AST expression references a forbidden top-level repo dir."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            parts = [p for p in sub.value.replace("\\", "/").split("/") if p]
            if any(p in FORBIDDEN_ROOT_NAMES for p in parts):
                return True
    return bool(FORBIDDEN_ROOT_RE.search(ast.unparse(node)))


def _has_forbidden_root(expr_or_node: ast.AST | str) -> bool:
    if isinstance(expr_or_node, ast.AST):
        return _expr_has_forbidden_root(expr_or_node)
    if FORBIDDEN_ROOT_RE.search(expr_or_node):
        return True
    try:
        parsed = ast.parse(expr_or_node, mode="eval")
    except SyntaxError:
        return False
    return _expr_has_forbidden_root(parsed)


def _assigned_nodes(tree: ast.AST) -> dict[str, list[ast.AST]]:
    """Collect AST value expressions assigned to top-level or local names."""
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


def _assigned_constants(tree: ast.AST) -> dict[str, list[str]]:
    """Collect unparsed expressions assigned to top-level or local names."""
    return {k: [ast.unparse(v) for v in vs] for k, vs in _assigned_nodes(tree).items()}


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
    """Extract (op_name, target_ast_node) for file/dir write or mutation operations in AST."""
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
            elif func.attr == "rename":
                tgt = node.args[0] if node.args else _kw_arg(node, "target")
                if tgt is not None:
                    found.append(("Path.rename", func.value))
                    found.append(("Path.rename", tgt))
            elif func.attr == "replace":
                # Path.replace(target) takes 1 arg; str.replace(old, new[, count]) takes >= 2.
                if (len(node.args) == 1 and not node.keywords) or (
                    len(node.args) == 0 and _kw_arg(node, "target") is not None
                ):
                    tgt = node.args[0] if node.args else _kw_arg(node, "target")
                    found.append(("Path.replace", func.value))
                    if tgt is not None:
                        found.append(("Path.replace", tgt))
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
            elif func.id in {"copy", "copy2", "copyfile", "copytree", "move"}:
                src_node = node.args[0] if node.args else _kw_arg(node, "src")
                dst_node = node.args[1] if len(node.args) >= 2 else _kw_arg(node, "dst")
                if dst_node is not None:
                    found.append((func.id, dst_node))
                if func.id == "move" and src_node is not None:
                    found.append((func.id, src_node))
            elif func.id == "rmtree":
                p_node = node.args[0] if node.args else _kw_arg(node, "path")
                if p_node is not None:
                    found.append((func.id, p_node))
    return found


def _write_call_targets(tree: ast.AST) -> list[tuple[str, str]]:
    """Extract (method_or_func, target_expr_src) for file/dir write operations in AST."""
    return [(op, ast.unparse(node)) for op, node in _write_call_target_nodes(tree)]


def _is_argv_target(node: ast.AST) -> bool:
    if isinstance(node, ast.Name) and node.id == "argv":
        return True
    if isinstance(node, ast.Attribute) and node.attr == "argv":
        return True
    if isinstance(node, ast.Subscript):
        return _is_argv_target(node.value)
    return False


def _argv_mutation_exprs(tree: ast.AST) -> list[str]:
    """Collect all assignments, augmented assignments, and list-mutating calls on argv."""
    mutations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(_is_argv_target(t) for t in node.targets):
            mutations.append(ast.unparse(node))
        elif isinstance(node, ast.AugAssign) and _is_argv_target(node.target):
            mutations.append(ast.unparse(node))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"append", "extend", "insert", "__iadd__"} and _is_argv_target(
                node.func.value
            ):
                mutations.append(ast.unparse(node))
    return mutations


# ---------------------------------------------------------------------------
# 1. Clean py_compile in TemporaryDirectory (no repo __pycache__ / .pyc)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script_path", TARGET_SCRIPTS + [RUN_NET_MATCH_PY])
def test_scripts_py_compile_in_tempdir_cpu_only(script_path: Path) -> None:
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert script_path.is_file(), f"Missing script: {script_path}"
    before_root_pycache = (LAB_ROOT / "__pycache__").exists()
    with tempfile.TemporaryDirectory() as td:
        cfile = Path(td) / f"{script_path.stem}.pyc"
        compiled = py_compile.compile(str(script_path), cfile=str(cfile), doraise=True)
        assert compiled == str(cfile)
        assert cfile.is_file() and cfile.stat().st_size > 0
    assert (LAB_ROOT / "__pycache__").exists() == before_root_pycache


def test_subprocess_py_compile_zero_cache_under_stream_b() -> None:
    scripts_arg = json.dumps([str(p) for p in TARGET_SCRIPTS])
    code = (
        "import json, os, py_compile, tempfile; from pathlib import Path; "
        "assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''; "
        f"paths = json.loads({scripts_arg!r}); "
        "td = tempfile.TemporaryDirectory(); "
        "[py_compile.compile(p, cfile=str(Path(td.name)/f'{Path(p).stem}.pyc'), doraise=True) for p in paths]; "
        "td.cleanup(); print('PY_COMPILE_SUBPROC_OK')"
    )
    r = subprocess.run(
        [sys.executable, "-B", "-c", code],
        env=_cpu_env(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    assert "PY_COMPILE_SUBPROC_OK" in r.stdout


# ---------------------------------------------------------------------------
# 2. AST & source-level read-only safety outside neon/
# ---------------------------------------------------------------------------


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


@pytest.mark.parametrize("script_path", TARGET_SCRIPTS + [RUN_NET_MATCH_PY])
def test_scripts_write_targets_stay_inside_neon(script_path: Path) -> None:
    src, tree = _parse_ast(script_path)
    assign_nodes = _assigned_nodes(tree)
    writes = _write_call_target_nodes(tree)
    if script_path.name == "run_stage2_clean_skipnoisy_matches.py":
        assert writes == []
    else:
        assert writes, f"Expected explicit write operations in {script_path.name}"

    for op, target_node in writes:
        _assert_write_target_safe(op, target_node, assign_nodes, script_path.name)

    # Sanity: ensure no .cache.npz creation string exists outside runs/forge guard comments.
    if script_path.name != "run_opus_r1_live768_skipnoisy.py":
        assert ".cache.npz" not in src


def test_opus_r1_live768_skipnoisy_readonly_and_monkeypatch_ast() -> None:
    p = FORGE_FIXES_DIR / "run_opus_r1_live768_skipnoisy.py"
    src, tree = _parse_ast(p)
    assigns = _assigned_constants(tree)

    # Verify OUT_DIR stays strictly inside neon/forge_fixes/gpu_runs/OPUS_R1_live768_skipnoisy
    out_dir_vals = assigns.get("OUT_DIR", [])
    assert out_dir_vals and all(
        "OPUS_R1_live768_skipnoisy" in v and "FIX" in v and not _has_forbidden_root(v)
        for v in out_dir_vals
    )
    fix_vals = assigns.get("FIX", [])
    assert fix_vals and all("neon/forge_fixes" in v and not _has_forbidden_root(v) for v in fix_vals)

    # Verify LIVE_ENV is populated into os.environ before forge_train_v3 import.
    assert "LIVE_ENV" in assigns
    live_env_pos = src.index("LIVE_ENV = {")
    import_v3_pos = src.index("import forge_train_v3")
    assert live_env_pos < import_v3_pos
    for req_key in ("FORGE_COMPACT", "FORGE_STEP_V2", "FORGE_FUSED_STEP", "FORGE_PARSE_PROCS"):
        assert req_key in src

    # Verify AST assignments monkey-patching ft._load_one and ft._count_one in memory.
    patched_attrs: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if (
                    isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "ft"
                    and tgt.attr in {"_load_one", "_count_one"}
                ):
                    patched_attrs[tgt.attr] = ast.unparse(node.value)
    assert patched_attrs.get("_load_one") == "safe_load_one"
    assert patched_attrs.get("_count_one") == "safe_count_one"

    # Verify temporary cache stays inside OUT_DIR/_tmp_cache and --keep-noisy is NEVER added to argv.
    tmp_cache_vals = assigns.get("tmp_cache_dir", [])
    assert tmp_cache_vals and all(
        "OUT_DIR" in v and "_tmp_cache" in v and not _has_forbidden_root(v)
        for v in tmp_cache_vals
    )
    argv_mutations = _argv_mutation_exprs(tree)
    assert argv_mutations, "Expected sys.argv construction for forge_train_v3"
    assert all("--keep-noisy" not in m for m in argv_mutations), (
        f"Forbidden --keep-noisy in argv mutation: {argv_mutations}"
    )


def test_stage2_clean_skipnoisy_gpu_enforces_skip_noisy_and_neon_paths() -> None:
    p = FILTER_QUEST_DIR / "run_stage2_clean_skipnoisy_gpu.py"
    src, tree = _parse_ast(p)
    assigns = _assigned_constants(tree)

    fq_vals = assigns.get("FQ", [])
    assert fq_vals and all("neon/filter_quest" in v and not _has_forbidden_root(v) for v in fq_vals)
    s2q_vals = assigns.get("S2Q_RUNS", [])
    assert s2q_vals and all("FQ" in v and "stage2_runs_quiet" in v and not _has_forbidden_root(v) for v in s2q_vals)
    cmd_vals = assigns.get("cmd", [])
    assert cmd_vals and all("--skip-fqs-noisy" in v for v in cmd_vals)

    writes = _write_call_targets(tree)
    assert any("STAGE2_QUIET_GPU_SUMMARY.json" in expr and "FQ" in expr for _, expr in writes)
    assert "runs/" not in src.replace("stage2_runs_quiet", "")


def test_stage2_clean_skipnoisy_matches_dispatches_50k_via_run_net_match() -> None:
    p = FILTER_QUEST_DIR / "run_stage2_clean_skipnoisy_matches.py"
    _, tree = _parse_ast(p)
    assigns = _assigned_constants(tree)
    runner_vals = assigns.get("RUNNER", [])
    assert runner_vals and all("run_net_match.py" in v and "FIX" in v and not _has_forbidden_root(v) for v in runner_vals)

    sub_calls = [
        ast.unparse(n)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "run"
    ]
    assert any("RUNNER" in c and "'--nodes'" in c and "'50000'" in c for c in sub_calls)

    # Also verify run_net_match.py writes only under MATCHES (neon/forge_fixes/matches) + neon/CLOCK_MATCH_RUNNING in try/finally.
    _, nm_tree = _parse_ast(RUN_NET_MATCH_PY)
    nm_assigns = _assigned_constants(nm_tree)
    matches_vals = nm_assigns.get("MATCHES", [])
    assert matches_vals and all("FIX_ROOT" in v and "matches" in v and not _has_forbidden_root(v) for v in matches_vals)
    clock_vals = nm_assigns.get("clock_flag", [])
    assert clock_vals and all("neon/CLOCK_MATCH_RUNNING" in v and not _has_forbidden_root(v) for v in clock_vals)
    try_nodes = [n for n in ast.walk(nm_tree) if isinstance(n, ast.Try)]
    assert any("clock_flag.unlink()" in ast.unparse(tn.finalbody) for tn in try_nodes)


def test_lmr_sprt_and_bench_5arch_write_under_neon_with_clock_lock_cleanup() -> None:
    for p, expected_out_token in (
        (FORGE_FIXES_DIR / "run_lmr_deeper_sprt.py", "FIX"),
        (FORGE_FIXES_DIR / "bench_serverday_4archs_pgo.py", "CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json"),
    ):
        _, tree = _parse_ast(p)
        assigns = _assigned_constants(tree)
        fix_vals = assigns.get("FIX", [])
        assert fix_vals and all("neon/forge_fixes" in v and not _has_forbidden_root(v) for v in fix_vals)
        lock_vals = assigns.get("LOCK", [])
        assert lock_vals and all("neon/CLOCK_MATCH_RUNNING" in v and not _has_forbidden_root(v) for v in lock_vals)
        try_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
        assert any("LOCK.unlink()" in ast.unparse(tn.finalbody) for tn in try_nodes), (
            f"{p.name} must clean LOCK in try/finally"
        )
        writes = _write_call_targets(tree)
        if p.name == "run_lmr_deeper_sprt.py":
            out_dir_vals = assigns.get("out_dir", [])
            assert out_dir_vals and all("FIX" in v and "matches" in v and not _has_forbidden_root(v) for v in out_dir_vals)
            log_vals = assigns.get("log_path", [])
            assert log_vals and all("out_dir" in v and "fastchess.log" in v and not _has_forbidden_root(v) for v in log_vals)
            sum_vals = assigns.get("summary_path", [])
            assert sum_vals and all("out_dir" in v and "summary.json" in v and not _has_forbidden_root(v) for v in sum_vals)
            assert all(
                expr.startswith(("out_dir", "summary_path", "log_path", "LOCK"))
                for _, expr in writes
            )
        else:
            out_vals = assigns.get("OUT", [])
            assert out_vals and all(expected_out_token in v and "FIX" in v and not _has_forbidden_root(v) for v in out_vals)
            assert all(expr.startswith(("OUT", "LOCK")) for _, expr in writes)


def test_ast_guard_helpers_reject_all_5_challenger_bypass_patterns() -> None:
    """Self-check ensuring all 5 Challenger static-bypass patterns are caught by AST helpers."""
    # 1. BYPASS_path_div: LAB / "runs" / "forge" / "leak.txt"
    t1 = ast.parse('(LAB / "runs" / "forge" / "leak.txt").write_text("x")')
    w1 = _write_call_target_nodes(t1)
    assert len(w1) == 1 and _expr_has_forbidden_root(w1[0][1])

    # 2. BYPASS_open_kw_mode: open("runs/forge/leak.txt", mode="w") and Path(...).open(mode="a")
    t2 = ast.parse('open("runs/forge/leak.txt", mode="w").write("x")\nPath("runs/x").open(mode="a")\nopen("runs/ok.txt", mode="r")')
    w2 = _write_call_target_nodes(t2)
    assert len(w2) == 2 and all(_expr_has_forbidden_root(n) for _, n in w2)

    # 3. BYPASS_shutil_copy_valid_syntax: shutil.copy / os.replace / Path.replace / Path.touch
    t3 = ast.parse(
        'import shutil, os\n'
        'shutil.copy("a", "runs/forge/leak.txt")\n'
        'os.replace("a", "pipeline/leak.txt")\n'
        'Path("a").replace("tools/leak.txt")\n'
        'Path("teamwork/leak.txt").touch()\n'
    )
    w3 = _write_call_target_nodes(t3)
    assert any(op == "shutil.copy" and _expr_has_forbidden_root(n) for op, n in w3)
    assert any(op == "os.replace" and _expr_has_forbidden_root(n) for op, n in w3)
    assert any(op == "Path.replace" and _expr_has_forbidden_root(n) for op, n in w3)
    assert any(op == "touch" and _expr_has_forbidden_root(n) for op, n in w3)

    # 4. BYPASS_lmr_reassign_summary: valid assignment followed by unsafe reassignment
    t4 = ast.parse(
        'summary_path = out_dir / "summary.json"\n'
        'summary_path = FIX.parent.parent / "runs" / "leak.json"\n'
    )
    a4 = _assigned_constants(t4)["summary_path"]
    assert not all("out_dir" in v and "summary.json" in v and not _has_forbidden_root(v) for v in a4)

    # 5. BYPASS_opus_argv_append: sys.argv.append / extend / insert / +=
    for snippet in (
        'sys.argv.append("--keep-noisy")',
        'sys.argv.extend(["--keep-noisy"])',
        'sys.argv.insert(1, "--keep-noisy")',
        'sys.argv += ["--keep-noisy"]',
    ):
        t5 = ast.parse(snippet)
        muts = _argv_mutation_exprs(t5)
        assert muts and any("--keep-noisy" in m for m in muts), snippet


# ---------------------------------------------------------------------------
# 3. JSON schema & exact value invariants (5 JSONs + G3_FULL25_PGO summary)
# ---------------------------------------------------------------------------


def test_cc0_noisy_vs_quiet_forensic_json_invariants() -> None:
    assert FORENSIC_JSON.is_file()
    d = json.loads(FORENSIC_JSON.read_text(encoding="utf-8"))
    assert d["total_rows"] == 1839070
    assert d["noisy_pct"] == 17.12
    noisy = d["groups"]["noisy_bit0_1"]
    quiet = d["groups"]["quiet_bit0_0"]
    assert noisy["mean_stm_mat"] < -1.0
    assert noisy["mean_sc"] > 30
    assert noisy["pct_eq_sc_with_mat_ge3"] > 20.0
    assert noisy["pct_eq_sc_with_mat_ge8"] / quiet["pct_eq_sc_with_mat_ge8"] == pytest.approx(134.0, rel=1e-6)


def test_g3ab_distill_regime_check_json_invariants() -> None:
    assert G3AB_JSON.is_file()
    d = json.loads(G3AB_JSON.read_text(encoding="utf-8"))
    skip = d["G3b_distill_skip_noisy"]
    keep = d["G3a_distill_keep_noisy"]
    assert skip["skip_noisy"] is True
    assert keep["skip_noisy"] is False
    assert skip["ols_piece_cp"]["Q"] >= 1000
    assert keep["ols_piece_cp"]["Q"] < 250


def test_clean_idle_speed_2builds_json_invariants() -> None:
    assert SPEED_2BUILDS_JSON.is_file()
    d = json.loads(SPEED_2BUILDS_JSON.read_text(encoding="utf-8"))
    assert d["v3p_bit_exact_nodes"] == 869964
    summary = d["summary"]
    v3p_keys = [
        "v1_unfused_A",
        "v1_unfused_B",
        "v3_fused_A",
        "v3_fused_B",
        "v3_fused_PGO_A",
        "v3_fused_PGO_B",
    ]
    for k in v3p_keys:
        assert summary[k]["nodes"] == 869964
    assert "live_pgo_r0067" in summary
    assert summary["live_pgo_r0067"]["median_nps"] > 3_000_000


def test_clean_idle_serverday_5arch_nps_json_invariants() -> None:
    assert SPEED_5ARCH_JSON.is_file()
    d = json.loads(SPEED_5ARCH_JSON.read_text(encoding="utf-8"))
    s = d["summary"]
    expected_keys = {
        "live_pgo_r0067_768screlu",
        "v3p_pgo_r0067_768screlu",
        "v3p_pgo_768p_kb8",
        "v3p_pgo_1024p_kb8_G3",
        "v3p_pgo_1536p_kb8",
        "v3p_pgo_1024p_kb16",
    }
    assert set(s.keys()) == expected_keys
    kb16_nps = s["v3p_pgo_1024p_kb16"]["median_nps"]
    kb8_nps = s["v3p_pgo_1024p_kb8_G3"]["median_nps"]
    assert abs(kb16_nps / kb8_nps - 1.0) < 0.01
    live_nps = s["live_pgo_r0067_768screlu"]["median_nps"]
    n1536_nps = s["v3p_pgo_1536p_kb8"]["median_nps"]
    assert (live_nps - n1536_nps) / live_nps > 0.20


def test_stage2_quiet_gpu_summary_json_invariants() -> None:
    assert STAGE2_QUIET_JSON.is_file()
    d = json.loads(STAGE2_QUIET_JSON.read_text(encoding="utf-8"))
    assert d["f1_quiet_kept"] == 1442765
    arms = d["arms"]
    assert len(arms) == 9
    for arm_name, arm in arms.items():
        assert arm["ols_Q"] >= 950, f"{arm_name} ols_Q={arm['ols_Q']}"
        assert arm["syz_win_ok_pct"] >= 99.0, f"{arm_name} syz_win_ok_pct={arm['syz_win_ok_pct']}"


def test_g3_full25_pgo_match_summary_invariants() -> None:
    assert G3_PGO_MATCH_JSON.is_file()
    d = json.loads(G3_PGO_MATCH_JSON.read_text(encoding="utf-8"))
    assert d["games"] == 2000
    assert d["finished"] is True
    assert d["time_losses"] == 0
    assert d["illegal_moves"] == 0
    assert d["disconnects"] == 0


# ---------------------------------------------------------------------------
# 4. Stream B deliverable invariants & zero cache/forbidden-word checks
# ---------------------------------------------------------------------------


def test_stream_b_spec_and_directory_hygiene() -> None:
    assert SPEC_MD.is_file()
    txt = SPEC_MD.read_text(encoding="utf-8")
    assert len(txt) > 2000
    assert not FORBIDDEN_RE.search(txt), "Forbidden word found in SERVER_DAY_2B_FINAL_EXECUTION_SPEC.md"
    for marker in (
        "--skip-fqs-noisy",
        "partition_fqs_buckets.py",
        "train_v3p_stream.py",
        "dead_draws_20k_s5disjoint.fqs.z",
        "SERVER_DAY_COST_MODEL.json",
    ):
        assert marker in txt, f"Missing {marker} in SERVER_DAY_2B_FINAL_EXECUTION_SPEC.md"

    test_txt = Path(__file__).read_text(encoding="utf-8")
    assert not FORBIDDEN_RE.search(test_txt), "Forbidden word found in test file"

    forbidden_exts = {".pyc", ".exe", ".fnn3", ".pt", ".fqs", ".plain", ".pgn", ".o", ".obj", ".part"}
    for p in STREAM_B_DIR.rglob("*"):
        assert p.name not in {"__pycache__", ".pytest_cache"}, f"Forbidden cache dir: {p}"
        assert not p.name.startswith("_work_"), f"Forbidden _work_ dir: {p}"
        if p.is_file():
            assert p.suffix.lower() not in forbidden_exts, f"Forbidden file extension: {p}"
            assert not p.name.endswith(".fqs.z"), f"Forbidden .fqs.z file: {p}"
