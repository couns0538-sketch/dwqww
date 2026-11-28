"""CPU-only verification suite for Stream C (FORGE TEAMWORK WAVE 9, Milestone M3).

Verifies genuinely (no mocks/hardcoded outputs, < 3s runtime, zero cache):
  1. R1_TWIN_DECLARATION.json & STAGE2_250K_CONFIRMATIONS_DECLARATION.json:
     schema validity, SHA-256 digests of all existing referenced files, graceful
     handling of pending OPUS_R1_live768_keepnoisy_twin\\cand.fnn3, heat rule
     (concurrency <= 12), no_pooling_rule, and fresh non-overlapping seeds across
     R1_TWIN, STAGE2_250K, and OWNER_BUNDLE declarations.
  2. OWNER_BUNDLE_RESULTS.json, OWNER_BUNDLE_ARMA_PGN_FORENSICS.json (nested),
     OWNER_BUNDLE_ARMB_PGN_FORENSICS.json (flat root), and Arm A / Arm B /
     G3-alone summary.json files: 2,000 games each, 0 TL/IL/DC, PGN totals
     matching summary.json W-D-L exactly (449-1059-492, 439-1144-417,
     480-1038-482), ptnml sum & point equivalence, and PGN file existence.
  3. bench_per_patch_nps.py & audit_owner_bundle_arma_pgn.py: valid AST and
     py_compile into TemporaryDirectory(), AST verification of
     CLOCK_MATCH_RUNNING try/finally unlink in bench_per_patch_nps.py,
     build_single_pgo try/finally shutil.rmtree cleanup, neon/-only write
     boundaries, SINGLE_PATCHES & top-level asset existence.
  4. PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md & pipeline/config.forge.toml:
     existence, zero forbidden words, valid datagen_uci_parity_7_8_minimal.patch
     & packet artifacts, and exact 1-based lines (214, 274, 357, 433) cross-checked
     with tomllib.
  5. Wave 9 directory hygiene, <= 3 MiB cap, and zero forbidden words.
"""
from __future__ import annotations

import ast
import functools
import hashlib
import json
import os
import py_compile
import re
import sys
import tempfile
import tomllib
from pathlib import Path

import pytest

# Strictly CPU-only execution and zero bytecode caching.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HIP_VISIBLE_DEVICES"] = ""
os.environ["ROCR_VISIBLE_DEVICES"] = ""

STREAM_C_DIR = Path(__file__).resolve().parents[1]
WAVE9_DIR = STREAM_C_DIR.parent
FORGE_FIXES_DIR = WAVE9_DIR.parent
NEON_DIR = FORGE_FIXES_DIR.parent
LAB_ROOT = NEON_DIR.parent
PIPELINE_DIR = LAB_ROOT / "pipeline"
FILTER_QUEST_DIR = NEON_DIR / "filter_quest"
MATCHES_DIR = FORGE_FIXES_DIR / "matches"

R1_TWIN_DECL = FORGE_FIXES_DIR / "R1_TWIN_DECLARATION.json"
STAGE2_DECL = FORGE_FIXES_DIR / "STAGE2_250K_CONFIRMATIONS_DECLARATION.json"
OWNER_DECL = FORGE_FIXES_DIR / "OWNER_BUNDLE_DECLARATION.json"
OWNER_RESULTS = FORGE_FIXES_DIR / "OWNER_BUNDLE_RESULTS.json"
ARMA_FORENSICS = FORGE_FIXES_DIR / "OWNER_BUNDLE_ARMA_PGN_FORENSICS.json"
ARMB_FORENSICS = FORGE_FIXES_DIR / "OWNER_BUNDLE_ARMB_PGN_FORENSICS.json"

ARMA_SUMMARY = MATCHES_DIR / "OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006" / "summary.json"
ARMB_SUMMARY = MATCHES_DIR / "OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006" / "summary.json"
G3_SUMMARY = MATCHES_DIR / "G3_FULL25_PGO_vs_live_r0067_2000g_6p006" / "summary.json"

BENCH_SCRIPT = FORGE_FIXES_DIR / "bench_per_patch_nps.py"
AUDIT_SCRIPT = FORGE_FIXES_DIR / "audit_owner_bundle_arma_pgn.py"

PACKET_MD = FORGE_FIXES_DIR / "PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md"
CONFIG_TOML = PIPELINE_DIR / "config.forge.toml"
PARITY_PATCH = FORGE_FIXES_DIR / "patches" / "datagen_uci_parity_7_8_minimal.patch"

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_RE = re.compile("cu" + "red?", re.IGNORECASE)
FORBIDDEN_ROOT_NAMES = frozenset({"runs", "forge", "pipeline", "teamwork", "tools"})
FORBIDDEN_ROOT_RE = re.compile(
    r"(?:^|[/\\'\"\s(,])(?:runs|forge|pipeline|teamwork|tools)(?:[/\\'\"\s),]|$)"
)


def _is_int(val: object) -> bool:
    return isinstance(val, int) and not isinstance(val, bool)


def _is_num(val: object) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


@functools.lru_cache(maxsize=None)
def _sha256_resolved(resolved_path: Path) -> str:
    h = hashlib.sha256()
    with resolved_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_resolved(path.resolve())


def _load_json(path: Path) -> dict:
    assert path.is_file(), f"Missing JSON file: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Expected JSON object in {path}"
    return data


def _parse_ast(path: Path) -> tuple[str, ast.AST]:
    assert path.is_file(), f"Missing Python file: {path}"
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


def _eval_lab_path_expr(node: ast.AST, env: dict[str, Path]) -> Path:
    if isinstance(node, ast.Name):
        assert node.id in env, f"Unknown path base {node.id!r}"
        return env[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return Path(node.value)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "Path" and len(node.args) == 1:
            arg = node.args[0]
            assert isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            return Path(arg.value)
        if isinstance(node.func, ast.Name) and node.func.id == "str" and len(node.args) == 1:
            return _eval_lab_path_expr(node.args[0], env)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _eval_lab_path_expr(node.left, env)
        assert isinstance(node.right, ast.Constant) and isinstance(node.right.value, str)
        return left / node.right.value
    raise AssertionError(f"Unsupported path AST expression: {ast.dump(node)}")


def _extract_module_path_env(tree: ast.Module) -> dict[str, Path]:
    env: dict[str, Path] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            name = stmt.targets[0].id
            if name in {
                "LAB", "FIX", "FQ", "MATCHES", "SRC_BASE", "PY", "LIVE_PGO_EXE",
                "BUNDLE_EXE", "R0067", "OUT_JSON", "BASE_EXE", "V3P_EXE", "R1_SKIP", "BOOK",
            }:
                env[name] = _eval_lab_path_expr(stmt.value, env)
    return env


def _is_attr_call(node: ast.AST, obj_name: str, attr_name: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == obj_name
        and node.func.attr == attr_name
    )


# ---------------------------------------------------------------------------
# 1. R1_TWIN_DECLARATION.json & STAGE2_250K_CONFIRMATIONS_DECLARATION.json
# ---------------------------------------------------------------------------


def test_r1_twin_declaration_schema_sha256_and_pending_twin_handling() -> None:
    decl = _load_json(R1_TWIN_DECL)
    assert set(decl.keys()) == {
        "written",
        "request_ref",
        "training_twin",
        "r1_skip_completed_net",
        "matches_declared",
    }
    assert isinstance(decl["written"], str) and decl["written"].strip()
    assert isinstance(decl["request_ref"], str) and decl["request_ref"].strip()

    twin = decl["training_twin"]
    assert isinstance(twin, dict)
    assert set(twin.keys()) == {
        "script",
        "runner",
        "window",
        "params",
        "single_variable_diff_vs_R1_skip",
        "out_net",
    }
    for k in ("script", "runner", "window", "single_variable_diff_vs_R1_skip", "out_net"):
        assert isinstance(twin[k], str) and twin[k].strip(), k

    script_path = Path(twin["script"])
    assert script_path.is_file() and script_path.stat().st_size == 7427
    assert _sha256_file(script_path) == "3336d8c95a02e96968af5ee8e0991b74895f17bdc11240d95ed30478d2b8ab4b"

    params = twin["params"]
    assert isinstance(params, dict)
    assert set(params.keys()) == {
        "hidden",
        "epochs",
        "lr",
        "batch_size",
        "lr_cycles",
        "w1_decay",
        "mix",
        "distill_net",
        "distill_weight",
        "teacher_once",
        "seed",
        "keep_noisy",
    }
    assert _is_int(params["hidden"]) and params["hidden"] == 768
    assert _is_int(params["epochs"]) and params["epochs"] == 40
    assert isinstance(params["lr"], float) and params["lr"] == pytest.approx(0.0005)
    assert _is_int(params["batch_size"]) and params["batch_size"] == 8192
    assert params["lr_cycles"] == "auto"
    assert isinstance(params["w1_decay"], float) and params["w1_decay"] == pytest.approx(0.3)
    assert isinstance(params["mix"], float) and params["mix"] == pytest.approx(0.75)
    assert isinstance(params["distill_weight"], float) and params["distill_weight"] == pytest.approx(0.2)
    assert params["teacher_once"] is True
    assert _is_int(params["seed"]) and params["seed"] == 1
    assert params["keep_noisy"] is True

    distill_path = Path(params["distill_net"])
    assert distill_path.is_file() and distill_path.stat().st_size == 791911
    assert _sha256_file(distill_path) == "52be981d04cc92cadbabb12d84b82c19b0ac3299557a9179968dc7d872039430"

    r1_skip = decl["r1_skip_completed_net"]
    assert isinstance(r1_skip, dict) and set(r1_skip.keys()) == {"path", "bytes", "sha256"}
    r1_skip_path = Path(r1_skip["path"])
    assert r1_skip_path.is_file()
    assert _is_int(r1_skip["bytes"]) and r1_skip_path.stat().st_size == r1_skip["bytes"] == 9463528
    assert HEX64_RE.match(r1_skip["sha256"])
    assert _sha256_file(r1_skip_path) == r1_skip["sha256"]

    out_net = Path(twin["out_net"])
    assert out_net.parent.is_dir(), f"Missing twin output directory: {out_net.parent}"

    matches = decl["matches_declared"]
    assert isinstance(matches, list) and len(matches) == 2
    for idx, m in enumerate(matches):
        assert isinstance(m, dict)
        required = {
            "name",
            "exe_both",
            "exe_sha256",
            "cand_net",
            "base_net",
            "book",
            "book_sha256",
            "games",
            "nodes",
            "seed",
            "concurrency",
            "decision_rule",
        }
        assert required.issubset(m.keys()), f"Match {idx} missing keys"
        assert isinstance(m["name"], str) and m["name"].strip()
        assert isinstance(m["decision_rule"], str) and m["decision_rule"].strip()
        assert _is_int(m["games"]) and m["games"] == 1000
        assert _is_int(m["nodes"]) and m["nodes"] == 250000
        assert _is_int(m["seed"]) and m["seed"] > 0
        assert _is_int(m["concurrency"]) and 1 <= m["concurrency"] <= 12

        exe_path = Path(m["exe_both"])
        assert exe_path.is_file() and HEX64_RE.match(m["exe_sha256"])
        assert _sha256_file(exe_path) == m["exe_sha256"]

        cand_path = Path(m["cand_net"])
        assert cand_path.resolve() == r1_skip_path.resolve()
        if "cand_net_sha256" in m:
            assert _sha256_file(cand_path) == m["cand_net_sha256"]

        book_path = Path(m["book"])
        assert book_path.is_file() and HEX64_RE.match(m["book_sha256"])
        assert _sha256_file(book_path) == m["book_sha256"]

    # Match 0 targets the pending R1-keep twin output net.
    m0 = matches[0]
    assert Path(m0["base_net"]).resolve() == out_net.resolve()
    if out_net.is_file():
        assert out_net.stat().st_size > 0
        digest = _sha256_file(out_net)
        assert HEX64_RE.match(digest)
        if "base_net_sha256" in m0:
            assert digest == m0["base_net_sha256"]

    # Match 1 targets r0067 with an explicit base_net_sha256.
    m1 = matches[1]
    assert "base_net_sha256" in m1 and HEX64_RE.match(m1["base_net_sha256"])
    r0067_path = Path(m1["base_net"])
    assert r0067_path.is_file()
    assert _sha256_file(r0067_path) == m1["base_net_sha256"]


def test_stage2_250k_confirmations_declaration_schema_sha256_and_rules() -> None:
    decl = _load_json(STAGE2_DECL)
    assert set(decl.keys()) == {
        "written",
        "request_ref",
        "exe_both",
        "exe_sha256",
        "book",
        "book_sha256",
        "concurrency",
        "max_threads_beside_gpu",
        "no_pooling_rule",
        "confirmations",
    }
    assert isinstance(decl["written"], str) and decl["written"].strip()
    assert isinstance(decl["request_ref"], str) and decl["request_ref"].strip()

    exe_path = Path(decl["exe_both"])
    assert exe_path.is_file() and HEX64_RE.match(decl["exe_sha256"])
    assert _sha256_file(exe_path) == decl["exe_sha256"]

    book_path = Path(decl["book"])
    assert book_path.is_file() and HEX64_RE.match(decl["book_sha256"])
    assert _sha256_file(book_path) == decl["book_sha256"]

    conc = decl["concurrency"]
    max_t = decl["max_threads_beside_gpu"]
    assert _is_int(conc) and _is_int(max_t)
    assert 1 <= conc <= max_t <= 12

    rule = decl["no_pooling_rule"]
    assert isinstance(rule, str) and rule.strip()
    assert "NEVER pooled" in rule and "50k" in rule and "250k" in rule

    confs = decl["confirmations"]
    assert isinstance(confs, list) and len(confs) == 3
    for item in confs:
        assert isinstance(item, dict)
        assert set(item.keys()) == {
            "name",
            "origin_50k_filter",
            "origin_50k_result",
            "cand_net",
            "cand_net_sha256",
            "base_net",
            "base_net_sha256",
            "games",
            "nodes",
            "seed",
            "decision_rule",
        }
        for sk in ("name", "origin_50k_filter", "origin_50k_result", "decision_rule"):
            assert isinstance(item[sk], str) and item[sk].strip(), sk
        assert _is_int(item["games"]) and item["games"] == 600
        assert _is_int(item["nodes"]) and item["nodes"] == 250000
        assert _is_int(item["seed"]) and item["seed"] > 0

        cand_p = Path(item["cand_net"])
        base_p = Path(item["base_net"])
        assert cand_p.is_file() and cand_p.stat().st_size > 0
        assert base_p.is_file() and base_p.stat().st_size > 0
        assert HEX64_RE.match(item["cand_net_sha256"]) and HEX64_RE.match(item["base_net_sha256"])
        assert _sha256_file(cand_p) == item["cand_net_sha256"]
        assert _sha256_file(base_p) == item["base_net_sha256"]


def test_fresh_non_overlapping_seeds_across_all_declarations() -> None:
    r1 = _load_json(R1_TWIN_DECL)
    s2 = _load_json(STAGE2_DECL)
    ob = _load_json(OWNER_DECL)
    ob_res = _load_json(OWNER_RESULTS)

    r1_seeds = [m["seed"] for m in r1["matches_declared"]]
    s2_seeds = [c["seed"] for c in s2["confirmations"]]
    ob_seeds = [
        ob["arms"]["ARM_A_owners"]["seed"],
        ob["arms"]["ARM_B_control"]["seed"],
    ]

    assert r1_seeds == [202611951, 202611952]
    assert s2_seeds == [202611960, 202611961, 202611962]
    assert ob_seeds == [202611901, 202611902]
    assert ob_res["arms"]["ARM_A_owners"]["declaration"]["seed"] == ob_seeds[0]
    assert ob_res["arms"]["ARM_B_control"]["declaration"]["seed"] == ob_seeds[1]

    all_seeds = r1_seeds + s2_seeds + ob_seeds
    assert all(_is_int(s) and s > 0 for s in all_seeds)
    assert len(all_seeds) == len(set(all_seeds)) == 7

    g3_seed = _load_json(G3_SUMMARY)["declaration"]["seed"]
    assert _is_int(g3_seed) and g3_seed not in set(all_seeds)


# ---------------------------------------------------------------------------
# 2. OWNER_BUNDLE_RESULTS.json & Arm A / Arm B / G3-alone PGN Forensics Parity
# ---------------------------------------------------------------------------


def _assert_forensics_matches_summary(
    forensics: dict,
    summary: dict,
    expected_wdl: tuple[int, int, int],
) -> None:
    assert set(forensics.keys()) == {
        "pgn",
        "games",
        "cand_as_white",
        "cand_as_black",
        "by_ply_bucket",
        "avg_plies",
    }
    assert _is_int(forensics["games"]) and forensics["games"] == 2000
    assert _is_num(forensics["avg_plies"]) and forensics["avg_plies"] > 0

    pgn_path = Path(forensics["pgn"])
    assert pgn_path.resolve() == Path(summary["pgn"]).resolve()
    assert pgn_path.is_file() and pgn_path.stat().st_size > 0

    exp_w, exp_d, exp_l = expected_wdl
    assert summary["games"] == 2000 and _is_int(summary["games"])
    assert (summary["wins"], summary["draws"], summary["losses"]) == expected_wdl
    assert all(_is_int(summary[k]) for k in ("wins", "draws", "losses"))
    assert exp_w + exp_d + exp_l == 2000

    assert _is_int(summary["time_losses"]) and summary["time_losses"] == 0
    assert _is_int(summary["illegal_moves"]) and summary["illegal_moves"] == 0
    assert _is_int(summary["disconnects"]) and summary["disconnects"] == 0
    assert summary["time_forfeits_by_engine"] == {}
    assert summary["finished"] is True
    assert _is_int(summary["exit_code"]) and summary["exit_code"] == 0

    heat = summary["heat"]
    assert heat["stopped_for_heat"] is False
    assert heat["stopped_without_reading"] is False

    conc = summary["declaration"]["concurrency"]
    assert _is_int(conc) and 1 <= conc <= 12

    ptnml = summary["ptnml"]
    assert isinstance(ptnml, list) and len(ptnml) == 5 and all(_is_int(x) and x >= 0 for x in ptnml)
    assert sum(ptnml) == 1000
    ptnml_pts = 0.0 * ptnml[0] + 0.5 * ptnml[1] + 1.0 * ptnml[2] + 1.5 * ptnml[3] + 2.0 * ptnml[4]
    assert ptnml_pts == pytest.approx(exp_w + 0.5 * exp_d)

    # Color split parity
    cw = forensics["cand_as_white"]
    cb = forensics["cand_as_black"]
    for sub in (cw, cb):
        assert set(sub.keys()) == {"W", "D", "L", "net"}
        assert all(_is_int(sub[k]) for k in ("W", "D", "L", "net"))
        assert sub["net"] == sub["W"] - sub["L"]
        assert sub["W"] + sub["D"] + sub["L"] == 1000
    assert (cw["W"] + cb["W"], cw["D"] + cb["D"], cw["L"] + cb["L"]) == expected_wdl

    # Ply-bucket parity
    buckets = forensics["by_ply_bucket"]
    assert set(buckets.keys()) == {"short_le80", "mid_81_140", "long_gt140"}
    bw = bd = bl = 0
    for bk in ("short_le80", "mid_81_140", "long_gt140"):
        b = buckets[bk]
        assert set(b.keys()) == {"W", "D", "L", "net"}
        assert all(_is_int(b[k]) for k in ("W", "D", "L", "net"))
        assert b["net"] == b["W"] - b["L"]
        bw += b["W"]
        bd += b["D"]
        bl += b["L"]
    assert (bw, bd, bl) == expected_wdl
    assert bw + bd + bl == 2000


def test_owner_bundle_results_summaries_and_pgn_forensics_parity() -> None:
    ob_decl = _load_json(OWNER_DECL)
    ob_res = _load_json(OWNER_RESULTS)
    arma_sum = _load_json(ARMA_SUMMARY)
    armb_sum = _load_json(ARMB_SUMMARY)
    g3_sum = _load_json(G3_SUMMARY)

    assert set(ob_res.keys()) == {"declaration", "arms"}
    assert ob_res["declaration"] == ob_decl
    assert set(ob_res["arms"].keys()) == {"ARM_A_owners", "ARM_B_control"}
    assert ob_res["arms"]["ARM_A_owners"] == arma_sum
    assert ob_res["arms"]["ARM_B_control"] == armb_sum

    arma_for = _load_json(ARMA_FORENSICS)
    armb_for = _load_json(ARMB_FORENSICS)

    # Nesting asymmetry: Arm A forensics is nested; Arm B forensics is flat at root.
    assert set(arma_for.keys()) == {"written", "ARMA_bundleG3_vs_liveR0067", "G3alone_vs_liveR0067"}
    assert "written" not in armb_for

    _assert_forensics_matches_summary(
        arma_for["ARMA_bundleG3_vs_liveR0067"], arma_sum, (449, 1059, 492)
    )
    _assert_forensics_matches_summary(
        arma_for["G3alone_vs_liveR0067"], g3_sum, (480, 1038, 482)
    )
    _assert_forensics_matches_summary(
        armb_for, armb_sum, (439, 1144, 417)
    )


# ---------------------------------------------------------------------------
# 3. bench_per_patch_nps.py & audit_owner_bundle_arma_pgn.py AST, Safety & Assets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script_path", [BENCH_SCRIPT, AUDIT_SCRIPT])
def test_scripts_ast_py_compile_zero_cache_and_neon_writes(script_path: Path) -> None:
    before_root_pycache = (LAB_ROOT / "__pycache__").exists()
    fix_pycache = FORGE_FIXES_DIR / "__pycache__"
    before_fix_pyc = {p.name for p in fix_pycache.glob("*")} if fix_pycache.is_dir() else set()

    with tempfile.TemporaryDirectory() as td:
        cfile = Path(td) / f"{script_path.stem}.pyc"
        compiled = py_compile.compile(str(script_path), cfile=str(cfile), doraise=True)
        assert compiled == str(cfile)
        assert cfile.is_file() and cfile.stat().st_size > 0

    assert (LAB_ROOT / "__pycache__").exists() == before_root_pycache
    after_fix_pyc = {p.name for p in fix_pycache.glob("*")} if fix_pycache.is_dir() else set()
    assert after_fix_pyc == before_fix_pyc

    src, tree = _parse_ast(script_path)
    assert not FORBIDDEN_RE.search(src), f"Forbidden word in {script_path.name}"
    assigns = _assigned_nodes(tree)
    for op, tgt_node in _write_call_target_nodes(tree):
        _assert_write_target_safe(op, tgt_node, assigns, script_path.name)


def test_bench_per_patch_nps_ast_clock_flag_cleanup_and_assets() -> None:
    _, tree = _parse_ast(BENCH_SCRIPT)
    assert isinstance(tree, ast.Module)

    fn_defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert {"sha256_file", "load_v3_opts", "build_single_pgo", "bench_once", "main"}.issubset(fn_defs)

    # 1) AST inspection of main() for clock_flag = LAB / "neon/CLOCK_MATCH_RUNNING" & try/finally unlink
    main_fn = fn_defs["main"]
    has_clock_assign = False
    for stmt in main_fn.body:
        if (
            isinstance(stmt, ast.Assign)
            and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id == "clock_flag"
            and isinstance(stmt.value, ast.BinOp)
            and isinstance(stmt.value.op, ast.Div)
            and isinstance(stmt.value.left, ast.Name)
            and stmt.value.left.id == "LAB"
            and isinstance(stmt.value.right, ast.Constant)
            and stmt.value.right.value == "neon/CLOCK_MATCH_RUNNING"
        ):
            has_clock_assign = True
    assert has_clock_assign, "main() must assign clock_flag = LAB / 'neon/CLOCK_MATCH_RUNNING'"

    try_nodes = [n for n in ast.walk(main_fn) if isinstance(n, ast.Try)]
    clock_try_ok = False
    for tr in try_nodes:
        body_calls_write = any(_is_attr_call(n, "clock_flag", "write_text") for s in tr.body for n in ast.walk(s))
        body_has_bench_loop = any(
            isinstance(s, ast.For)
            and any(
                isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "bench_once"
                for c in ast.walk(s)
            )
            for s in tr.body
        )
        finally_unlinks = any(
            isinstance(s, ast.If)
            and _is_attr_call(s.test, "clock_flag", "exists")
            and any(_is_attr_call(bs, "clock_flag", "unlink") for bs in s.body for bs in ast.walk(bs))
            for s in tr.finalbody
        )
        if body_calls_write and body_has_bench_loop and finally_unlinks:
            clock_try_ok = True
            break
    assert clock_try_ok, "main() must set clock_flag.write_text around bench loop and unlink in try/finally"

    # 2) AST inspection of build_single_pgo() try/finally shutil.rmtree(work, ignore_errors=True)
    bsp_fn = fn_defs["build_single_pgo"]
    bsp_try_ok = False
    for tr in (n for n in ast.walk(bsp_fn) if isinstance(n, ast.Try)):
        for s in tr.finalbody:
            for c in ast.walk(s):
                if (
                    _is_attr_call(c, "shutil", "rmtree")
                    and len(c.args) >= 1
                    and isinstance(c.args[0], ast.Name)
                    and c.args[0].id == "work"
                    and isinstance(_kw_arg(c, "ignore_errors"), ast.Constant)
                    and _kw_arg(c, "ignore_errors").value is True
                ):
                    bsp_try_ok = True
    assert bsp_try_ok, "build_single_pgo() must clean work dir via shutil.rmtree(work, ignore_errors=True) in finally"

    # 3) AST extraction of SINGLE_PATCHES & top-level input constants (excluding unrun OUT_JSON)
    env = _extract_module_path_env(tree)
    for key in ("SRC_BASE", "PY", "LIVE_PGO_EXE", "BUNDLE_EXE", "R0067"):
        assert env[key].exists(), f"Missing asset {key}: {env[key]}"
    assert env["SRC_BASE"].is_dir()
    for key in ("PY", "LIVE_PGO_EXE", "BUNDLE_EXE", "R0067"):
        assert env[key].is_file()
    assert (FORGE_FIXES_DIR / "build_fast.py").is_file()
    assert CONFIG_TOML.is_file()

    sp_assign = next(
        s for s in tree.body
        if isinstance(s, ast.Assign)
        and len(s.targets) == 1
        and isinstance(s.targets[0], ast.Name)
        and s.targets[0].id == "SINGLE_PATCHES"
    )
    assert isinstance(sp_assign.value, ast.List) and len(sp_assign.value.elts) == 4
    extracted_patches: list[tuple[str, Path]] = []
    for elt in sp_assign.value.elts:
        assert isinstance(elt, ast.Tuple) and len(elt.elts) == 2
        assert isinstance(elt.elts[0], ast.Constant) and isinstance(elt.elts[0].value, str)
        p = _eval_lab_path_expr(elt.elts[1], env)
        assert p.is_file() and p.suffix == ".patch", f"Missing patch from SINGLE_PATCHES: {p}"
        extracted_patches.append((elt.elts[0].value, p))
    assert [nm for nm, _ in extracted_patches] == [
        "SF13_alone_pgo",
        "SF8_alone_pgo",
        "W2_proto_1_alone_pgo",
        "V3Pv3_alone_r0067_pgo",
    ]


def test_audit_owner_bundle_arma_pgn_ast_targets_and_assets() -> None:
    _, tree = _parse_ast(AUDIT_SCRIPT)
    assert isinstance(tree, ast.Module)

    fn_names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert {"sha256_file", "write_declarations", "parse_pgn_stats", "main"}.issubset(fn_names)

    env = _extract_module_path_env(tree)
    for key in ("BASE_EXE", "V3P_EXE", "LIVE_PGO_EXE", "R0067", "R1_SKIP", "BOOK"):
        assert env[key].is_file(), f"Missing asset {key}: {env[key]}"

    # Verify all write_text targets stay strictly inside neon/forge_fixes/ (scoped per function)
    fn_defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    non_fn_body = [s for s in tree.body if not isinstance(s, ast.FunctionDef)]
    assert _write_call_target_nodes(ast.Module(body=non_fn_body, type_ignores=[])) == []

    resolved_targets: list[str] = []
    for fn_node in fn_defs.values():
        fn_assigns = _assigned_nodes(fn_node)
        for op, tgt_node in _write_call_target_nodes(fn_node):
            assert op == "write_text"
            if isinstance(tgt_node, ast.Name):
                vals = fn_assigns.get(tgt_node.id, [])
                assert len(vals) == 1, f"Ambiguous assignment for {tgt_node.id} in {fn_node.name}"
                p = _eval_lab_path_expr(vals[0], env)
            else:
                p = _eval_lab_path_expr(tgt_node, env)
            assert p.resolve().is_relative_to(FORGE_FIXES_DIR.resolve()), f"Write outside FIX: {p}"
            resolved_targets.append(p.name)

    assert len(resolved_targets) == 3
    assert set(resolved_targets) == {
        "R1_TWIN_DECLARATION.json",
        "STAGE2_250K_CONFIRMATIONS_DECLARATION.json",
        "OWNER_BUNDLE_ARMA_PGN_FORENSICS.json",
    }

    arma_pgn = MATCHES_DIR / "OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006" / "games_20261128_024459.pgn"
    g3_dir = MATCHES_DIR / "G3_FULL25_PGO_vs_live_r0067_2000g_6p006"
    assert arma_pgn.is_file()
    assert g3_dir.is_dir() and any(g3_dir.glob("games_*.pgn"))


# ---------------------------------------------------------------------------
# 4. PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md & pipeline/config.forge.toml
# ---------------------------------------------------------------------------


def test_packet_immediate_loop_and_config_forge_toml_lines() -> None:
    assert PACKET_MD.is_file() and PACKET_MD.stat().st_size > 4000
    packet_txt = PACKET_MD.read_text(encoding="utf-8")
    assert not FORBIDDEN_RE.search(packet_txt), "Forbidden word found in PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md"

    for i in range(1, 6):
        assert f"## Packet {i}" in packet_txt

    assert PARITY_PATCH.is_file()
    patch_txt = PARITY_PATCH.read_text(encoding="utf-8")
    patch_lines = patch_txt.splitlines()
    assert len(patch_lines) == 111
    patch_sha = _sha256_file(PARITY_PATCH)
    assert patch_sha.startswith("184c6d2b")
    assert "184c6d2b..." in packet_txt
    assert "--- a/pipeline/nnloop/datagen_uci.py" in patch_txt
    assert "+++ b/pipeline/nnloop/datagen_uci.py" in patch_txt
    assert (PIPELINE_DIR / "nnloop" / "datagen_uci.py").is_file()

    for artifact in (
        FILTER_QUEST_DIR / "LIVE_LOOP_PARITY_BIAS_AUDIT.json",
        FORGE_FIXES_DIR / "pilot_datagen_parity_7_8_G3_R4.json",
        FORGE_FIXES_DIR / "run_lmr_deeper_sprt.py",
        FORGE_FIXES_DIR / "serverday_v3" / "run_dedup_buckets_v3.sh",
        FORGE_FIXES_DIR / "serverday_v3" / "run_train_stream_gpu_v3.sh",
    ):
        assert artifact.is_file(), f"Missing packet-referenced artifact: {artifact}"

    assert CONFIG_TOML.is_file()
    cfg_txt = CONFIG_TOML.read_text(encoding="utf-8")
    lines = cfg_txt.splitlines()

    # Exact 1-based line assertions cited in Packet 1-3
    assert "v3_uci_options" in lines[213] and "EvalSwingMult = 15" in lines[213]
    assert "random_move_count" in lines[273] and "= 8" in lines[273]
    assert "train_cmd" in lines[356] and "--keep-noisy" in lines[356]
    assert "keep_noisy" in lines[432] and lines[432].strip() == "keep_noisy = true"

    # Cross-check with tomllib
    cfg = tomllib.loads(cfg_txt)
    assert isinstance(cfg["engine"]["v3_uci_options"], dict)
    assert cfg["engine"]["v3_uci_options"]["EvalSwingMult"] == 15
    assert cfg["datagen"]["random_move_count"] == 8
    assert "--keep-noisy" in cfg["train"]["train_cmd"]
    assert cfg["train"]["keep_noisy"] is True


# ---------------------------------------------------------------------------
# 5. Wave 9 Hygiene, Size Cap & Forbidden-Word Self-Test
# ---------------------------------------------------------------------------


def test_wave9_hygiene_size_cap_and_forbidden_words() -> None:
    self_txt = Path(__file__).read_text(encoding="utf-8")
    assert not FORBIDDEN_RE.search(self_txt), "Forbidden word found in test_wave9_declarations_and_packets.py"

    assert not (LAB_ROOT / "__pycache__").exists(), "Unexpected __pycache__ at C:\\nnue-lab"

    forbidden_exts = {".pyc", ".pyo", ".exe", ".fnn3", ".pt", ".fqs", ".plain", ".pgn", ".o", ".obj", ".part"}
    text_exts = {".md", ".py", ".txt", ".json", ".toml", ".sh", ".patch"}
    total_bytes = 0

    for p in WAVE9_DIR.rglob("*"):
        assert p.name not in {"__pycache__", ".pytest_cache"}, f"Forbidden cache dir: {p}"
        assert not p.name.startswith("_work_"), f"Forbidden _work_ path: {p}"
        if p.is_file():
            assert p.suffix.lower() not in forbidden_exts, f"Forbidden binary/cache file: {p}"
            total_bytes += p.stat().st_size
            if p.suffix.lower() in text_exts:
                txt = p.read_text(encoding="utf-8")
                assert not FORBIDDEN_RE.search(txt), f"Forbidden word found in {p}"

    assert total_bytes <= 3 * 1024 * 1024, f"teamwork_wave9 exceeds 3 MiB: {total_bytes} bytes"
