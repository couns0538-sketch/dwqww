"""Verify all Wave 1-6 patches dynamically across all patch roots via `git apply --check`
and isolated temp-copy checks (all transient temp dirs live under scratch\\teamwork_tmp
and are deleted unconditionally in `finally:`).

Strictly read-only on C:\\nnue-lab\\forge\\r15dsg, C:\\nnue-lab\\pipeline, and all source files.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

LAB = Path(r"C:\nnue-lab")
R15_ROOT = LAB / "forge" / "r15dsg"
FF_ROOT = LAB / "neon" / "forge_fixes"
FQ_ROOT = LAB / "neon" / "filter_quest"
HERE = Path(__file__).resolve().parent
DEFAULT_TEMP_ROOT = Path(r"C:\Users\Administrator\.gemini\antigravity\scratch\teamwork_tmp")

SCAN_ROOTS: list[tuple[str, Path]] = [
    ("forge_fixes/patches", FF_ROOT / "patches"),
    ("filter_quest/patches", FQ_ROOT / "patches"),
    ("teamwork_wave2", FF_ROOT / "teamwork_wave2"),
    ("teamwork_wave3", FF_ROOT / "teamwork_wave3"),
    ("teamwork_wave4", FF_ROOT / "teamwork_wave4"),
    ("teamwork_wave5", FF_ROOT / "teamwork_wave5"),
]

STACK_SPECS: dict[str, list[Path]] = {
    "superstack_6": [
        FF_ROOT / "patches" / "V3P_pairwise_psqt_fused_v3.patch",
        FF_ROOT / "patches" / "SF33_qs_overhaul_SF13_plus_SF32.patch",
        FF_ROOT / "patches" / "SF8_conthist_6ply.patch",
        FF_ROOT / "teamwork_wave2" / "streamA_search" / "patches" / "proto_1_corrhist_minor.patch",
        FF_ROOT / "patches" / "SF15_rfp_failsoft_blend.patch",
        FF_ROOT / "patches" / "SF27_goodcap_caphist_see_threshold.patch",
    ],
    "v3p_round12_14_sf38": [
        FF_ROOT / "patches" / "V3P_pairwise_psqt_fused_v3.patch",
        FF_ROOT / "patches" / "SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch",
        FF_ROOT / "patches" / "SF35_razoring_d3_quadratic_and_nmp_minply.patch",
        FF_ROOT / "patches" / "SF36_threat_quiet_move_ordering.patch",
        FF_ROOT / "patches" / "SF38_corrhist_major.patch",
        FF_ROOT / "patches" / "SF40_tt_recency_pv_admit_and_pv_conthist.patch",
    ],
    "v3p_round12_14_sf39": [
        FF_ROOT / "patches" / "V3P_pairwise_psqt_fused_v3.patch",
        FF_ROOT / "patches" / "SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch",
        FF_ROOT / "patches" / "SF35_razoring_d3_quadratic_and_nmp_minply.patch",
        FF_ROOT / "patches" / "SF36_threat_quiet_move_ordering.patch",
        FF_ROOT / "patches" / "SF39_corrhist_minor_plus_major.patch",
        FF_ROOT / "patches" / "SF40_tt_recency_pv_admit_and_pv_conthist.patch",
    ],
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_sub_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["HIP_VISIBLE_DEVICES"] = ""
    env["ROCR_VISIBLE_DEVICES"] = ""
    return env


def parse_target_files(patch_text: str) -> list[str]:
    targets: list[str] = []
    seen: set[str] = set()
    for line in patch_text.splitlines():
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            rel = m.group(1).strip()
            if rel not in seen:
                seen.add(rel)
                targets.append(rel)
    if not targets:
        for line in patch_text.splitlines():
            m = re.match(r"^--- a/(.+)$", line)
            if m:
                rel = m.group(1).strip()
                if rel not in seen:
                    seen.add(rel)
                    targets.append(rel)
    return targets


def enumerate_patches() -> list[tuple[str, Path]]:
    seen: set[Path] = set()
    found: list[tuple[str, Path]] = []
    for group_name, root in SCAN_ROOTS:
        if not root.exists():
            continue
        candidates = sorted(root.rglob("*.patch"))
        for p in candidates:
            if any(
                part.startswith("_work_") or part in ("__pycache__", ".pytest_cache")
                for part in p.parts
            ):
                continue
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            found.append((group_name, rp))
    return found


def classify_patch(patch_path: Path, targets: list[str]) -> str:
    if any(t.startswith("pipeline/") for t in targets):
        return "pipeline_temp"
    if any(t.startswith("forge/r15dsg/") for t in targets):
        return "r15dsg_prefixed_temp"
    if targets == ["train_v3p.py"] or patch_path.name == "train_v3p_g3_flags.patch":
        return "forge_fixes_temp"
    return "r15dsg_direct"


def check_patch_routed(group_name: str, patch_path: Path, run_tmp: Path) -> dict:
    text = patch_path.read_text(encoding="utf-8", errors="replace")
    lines = len(text.splitlines())
    bytes_len = patch_path.stat().st_size
    sha = sha256_file(patch_path)
    targets = parse_target_files(text)
    route = classify_patch(patch_path, targets)
    env = clean_sub_env()

    if route == "r15dsg_direct":
        proc = subprocess.run(
            ["git", "-C", str(R15_ROOT), "apply", "--check", str(patch_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        return {
            "group": group_name,
            "name": patch_path.name,
            "path": str(patch_path),
            "route": route,
            "git_root": str(R15_ROOT),
            "bytes": bytes_len,
            "lines": lines,
            "target_files": targets,
            "sha256": sha,
            "rc": proc.returncode,
            "ast_ok": None,
            "passed": proc.returncode == 0,
            "stderr": proc.stderr.strip(),
        }

    # Isolated temp-copy check & apply for pipeline/, forge/r15dsg/-prefixed, and neon/forge_fixes/
    work_dir = run_tmp / f"chk_{route}_{patch_path.stem}_{uuid.uuid4().hex[:6]}"
    work_dir.mkdir(parents=True, exist_ok=True)
    src_base = FF_ROOT if route == "forge_fixes_temp" else LAB
    for rel in targets:
        src = src_base / rel
        if not src.exists():
            raise FileNotFoundError(f"Missing target file for {patch_path.name}: {src}")
        dst = work_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    r_chk = subprocess.run(
        ["git", "-C", str(work_dir), "apply", "--check", str(patch_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    r_app = subprocess.run(
        ["git", "-C", str(work_dir), "apply", str(patch_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    ast_ok: bool | None = None
    ast_err = ""
    py_targets = [work_dir / rel for rel in targets if rel.endswith(".py")]
    if py_targets and r_chk.returncode == 0 and r_app.returncode == 0:
        ast_ok = True
        for pyf in py_targets:
            try:
                src_text = pyf.read_text(encoding="utf-8")
                ast.parse(src_text, filename=str(pyf))
                compile(src_text, str(pyf), "exec")
            except Exception as exc:
                ast_ok = False
                ast_err = f"{pyf.name}: {exc}"
                break

    passed = (r_chk.returncode == 0) and (r_app.returncode == 0) and (ast_ok in (None, True))
    stderr = (r_chk.stderr or r_app.stderr or ast_err).strip()
    return {
        "group": group_name,
        "name": patch_path.name,
        "path": str(patch_path),
        "route": route,
        "git_root": f"temp_copy({src_base})",
        "bytes": bytes_len,
        "lines": lines,
        "target_files": targets,
        "sha256": sha,
        "rc": r_chk.returncode if r_chk.returncode != 0 else r_app.returncode,
        "ast_ok": ast_ok,
        "passed": passed,
        "stderr": stderr,
    }


def _load_tmp_datagen(work_dir: Path, patch_path: Path, env: dict[str, str]):
    nnloop_dir = work_dir / "pipeline" / "nnloop"
    nnloop_dir.mkdir(parents=True, exist_ok=True)
    for fname in ("__init__.py", "common.py", "engine.py", "datagen_uci.py"):
        shutil.copy2(LAB / "pipeline" / "nnloop" / fname, nnloop_dir / fname)

    r_chk = subprocess.run(
        ["git", "-C", str(work_dir), "apply", "--check", str(patch_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    if r_chk.returncode != 0:
        raise AssertionError(f"Temp-copy git apply --check failed rc={r_chk.returncode}: {r_chk.stderr}")

    r_app = subprocess.run(
        ["git", "-C", str(work_dir), "apply", str(patch_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    if r_app.returncode != 0:
        raise AssertionError(f"Temp-copy git apply failed rc={r_app.returncode}: {r_app.stderr}")

    patched_file = nnloop_dir / "datagen_uci.py"
    src_text = patched_file.read_text(encoding="utf-8")
    ast.parse(src_text, filename=str(patched_file))
    compile(src_text, str(patched_file), "exec")

    pkg_name = f"_tmp_pipeline_{uuid.uuid4().hex[:8]}"
    pkg_spec = importlib.util.spec_from_file_location(
        pkg_name,
        str(nnloop_dir / "__init__.py"),
        submodule_search_locations=[str(nnloop_dir)],
    )
    assert pkg_spec is not None and pkg_spec.loader is not None
    pkg_mod = importlib.util.module_from_spec(pkg_spec)
    sys.modules[pkg_name] = pkg_mod
    pkg_spec.loader.exec_module(pkg_mod)

    mod_name = f"{pkg_name}.datagen_uci"
    spec = importlib.util.spec_from_file_location(mod_name, str(patched_file))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = pkg_name
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod, pkg_name, r_chk.returncode, r_app.returncode


def run_datagen_startpos_temp_test(run_tmp: Path) -> dict:
    """Apply datagen_uci_startpos_only.patch in <run_tmp> and verify sp_k=4, zero RNG drift, selfgame_ok."""
    patch_path = FF_ROOT / "patches" / "datagen_uci_startpos_only.patch"
    work_dir = run_tmp / f"fn_startpos_{uuid.uuid4().hex[:6]}"
    pkg_name = ""
    try:
        mod, pkg_name, rc_chk, rc_app = _load_tmp_datagen(work_dir, patch_path, clean_sub_env())
        book = [
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
            "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
        ]

        sp_k_counts_default: dict[int, int] = {}
        sp_k_counts_explicit: dict[int, int] = {}
        sp_hits_default = 0
        sp_hits_explicit = 0

        g_sp_default = {
            "random_move_min_ply": 0,
            "random_move_max_ply": 1,
            "random_move_count": 2,
            "write_min_ply": 2,
            "startpos_frac": 0.10,
            "startpos_write_min_ply": 0,
        }
        g_sp_explicit = {**g_sp_default, "startpos_random_move_count": 4}

        rng1 = random.Random(20261128)
        for _ in range(2000):
            _b, prefix, rplies, wmp = mod._game_opening(rng1, g_sp_default, book)
            if prefix == "position startpos":
                sp_hits_default += 1
                assert wmp == 0
                assert rplies in ({0, 1, 2}, {0, 1, 2, 3})
                sp_k_counts_default[len(rplies)] = sp_k_counts_default.get(len(rplies), 0) + 1
            else:
                assert wmp == 2 and rplies == {0, 1}

        rng2 = random.Random(20261128)
        for _ in range(2000):
            _b, prefix, rplies, wmp = mod._game_opening(rng2, g_sp_explicit, book)
            if prefix == "position startpos":
                sp_hits_explicit += 1
                assert wmp == 0
                assert rplies == {0, 1, 2, 3}
                sp_k_counts_explicit[len(rplies)] = sp_k_counts_explicit.get(len(rplies), 0) + 1

        assert 150 <= sp_hits_default <= 260
        assert set(sp_k_counts_default.keys()).issubset({3, 4}) and 0 not in sp_k_counts_default
        assert sp_k_counts_explicit == {4: sp_hits_explicit}

        for label, leg_g in [
            ("legacy_k8", {"random_move_min_ply": 0, "random_move_max_ply": 7, "random_move_count": 8, "write_min_ply": 8, "startpos_frac": 0.0}),
            ("cc0_k2_sp0", {"random_move_min_ply": 0, "random_move_max_ply": 1, "random_move_count": 2, "write_min_ply": 2, "startpos_frac": 0.0}),
            ("legacy_k8_omitted", {"random_move_min_ply": 0, "random_move_max_ply": 7, "random_move_count": 8, "write_min_ply": 8}),
        ]:
            ra = random.Random(123456)
            rb = random.Random(123456)
            for _ in range(100):
                fen_a = ra.choice(book)
                lo, hi = int(leg_g["random_move_min_ply"]), int(leg_g["random_move_max_ply"])
                k = min(int(leg_g["random_move_count"]), max(0, hi - lo + 1))
                rp_a = set(ra.sample(range(lo, hi + 1), k)) if k > 0 else set()
                _b, pref_b, rp_b, wmp_b = mod._game_opening(rb, leg_g, book)
                assert pref_b == f"position fen {fen_a}"
                assert rp_b == rp_a
                assert wmp_b == int(leg_g["write_min_ply"])
                assert ra.getstate() == rb.getstate(), f"{label} RNG drifted"

        cc0_cfg = {
            "engine": {"score": {"unit": "raw", "multiplier": 1.0}},
            "datagen": {
                "soft_nodes": 4000,
                "random_multi_pv": 0,
                "random_move_min_ply": 0,
                "random_move_max_ply": 1,
                "random_move_count": 2,
                "write_min_ply": 2,
                "startpos_frac": 0.10,
                "startpos_write_min_ply": 0,
                "startpos_random_move_count": 4,
            },
        }
        sg_ok_cc0 = mod.selfgame_ok(cc0_cfg)
        assert sg_ok_cc0 == ""
        assert mod.selfgame_ok({"engine": cc0_cfg["engine"], "datagen": {**cc0_cfg["datagen"], "random_move_max_ply": 3}}) != ""
        assert mod.selfgame_ok({"engine": cc0_cfg["engine"], "datagen": {**cc0_cfg["datagen"], "random_multi_pv": 2}}) != ""

        return {
            "passed": True,
            "patch": str(patch_path),
            "temp_git_apply_check_rc": rc_chk,
            "temp_git_apply_rc": rc_app,
            "sp_k4_default": {"startpos_games": sp_hits_default, "k_counts": sp_k_counts_default},
            "sp_k4_explicit": {"startpos_games": sp_hits_explicit, "k_counts": sp_k_counts_explicit},
            "zero_rng_drift": True,
            "selfgame_ok_fixed_k2_cc0": sg_ok_cc0,
        }
    finally:
        if pkg_name:
            for k in [m for m in sys.modules if m == pkg_name or m.startswith(pkg_name + ".")]:
                sys.modules.pop(k, None)
        shutil.rmtree(work_dir, ignore_errors=True)


def run_datagen_parity_7_8_temp_test(run_tmp: Path) -> dict:
    """Apply datagen_uci_parity_7_8_minimal.patch in <run_tmp> and verify alternating 8/7 & write_min_ply."""
    patch_path = FF_ROOT / "patches" / "datagen_uci_parity_7_8_minimal.patch"
    work_dir = run_tmp / f"fn_parity78_{uuid.uuid4().hex[:6]}"
    pkg_name = ""
    try:
        mod, pkg_name, rc_chk, rc_app = _load_tmp_datagen(work_dir, patch_path, clean_sub_env())

        g_alt = {
            "nodes": 0,
            "soft_nodes": 4000,
            "random_multi_pv": 0,
            "random_move_min_ply": 0,
            "random_move_max_ply": 7,
            "random_move_count": 8,
            "random_move_count_alt": 7,
            "write_min_ply": 8,
            "eval_limit": 2000,
            "max_ply": 200,
            "draw_adj_ply": 80,
            "draw_adj_score": 5,
            "draw_adj_count": 8,
        }
        g_no_alt = {k: v for k, v in g_alt.items() if k != "random_move_count_alt"}

        assert mod._random_count_for_game(g_alt, 0) == (8, True)
        assert mod._random_count_for_game(g_alt, 1) == (7, True)
        assert mod._random_count_for_game(g_alt, 2) == (8, True)
        assert mod._random_count_for_game(g_alt, 3) == (7, True)
        assert mod._random_count_for_game(g_no_alt, 1) == (8, False)
        assert mod._random_count_for_game({**g_alt, "random_move_count_alt": -1}, 1) == (8, False)

        cfg_ok = {"engine": {"score": {"unit": "raw", "multiplier": 1.0}}, "datagen": g_alt}
        cfg_bad = {"engine": cfg_ok["engine"], "datagen": {**g_alt, "random_move_count_alt": 9}}
        assert mod.selfgame_ok(cfg_ok) == ""
        bad_msg = mod.selfgame_ok(cfg_bad)
        assert "random_move_count_alt" in bad_msg

        # Verify write_min_ply alternation end-to-end inside play_game_sg with a mock engine
        class _MockSgEngine:
            def __init__(self) -> None:
                self.cmds: list[str] = []

            def new_game(self) -> None:
                self.cmds.append("ucinewgame")

            def send(self, line: str) -> None:
                self.cmds.append(line)

            def _get(self, deadline: float) -> str:
                return "sgend result 0 reason drawadj plies 12 run 0 searches 0 nodes 0 moves"

        sg_writemin: list[int] = []
        sg_random_plies_counts: list[int] = []
        rng = random.Random(20261128)
        for gidx in (0, 1):
            eng = _MockSgEngine()
            mod.play_game_sg(eng, rng, g_alt, book=[], game_idx=gidx)
            pos_cmd = [c for c in eng.cmds if c.startswith("position ")][0]
            mv_cnt = len(pos_cmd.split(" moves ")[1].split()) if " moves " in pos_cmd else 0
            sg_cmd = [c for c in eng.cmds if c.startswith("selfgame ")][0]
            m = re.search(r"writeminply (\d+)", sg_cmd)
            assert m is not None
            sg_random_plies_counts.append(mv_cnt)
            sg_writemin.append(int(m.group(1)))
        assert sg_random_plies_counts == [8, 7], f"Unexpected random move counts: {sg_random_plies_counts}"
        assert sg_writemin == [8, 7], f"Unexpected writeminply alternation: {sg_writemin}"

        # Also verify explicit custom write_min_ply (e.g. 10 != 8) stays pinned to 10
        eng_pin = _MockSgEngine()
        mod.play_game_sg(eng_pin, rng, {**g_alt, "write_min_ply": 10}, book=[], game_idx=1)
        sg_pin = [c for c in eng_pin.cmds if c.startswith("selfgame ")][0]
        assert "writeminply 10" in sg_pin

        return {
            "passed": True,
            "patch": str(patch_path),
            "temp_git_apply_check_rc": rc_chk,
            "temp_git_apply_rc": rc_app,
            "random_count_g0": [8, True],
            "random_count_g1": [7, True],
            "selfgame_ok_alt7": "",
            "selfgame_ok_alt9_rejected": bad_msg,
            "play_game_sg_writeminply_alt": sg_writemin,
            "play_game_sg_pinned_writeminply_10": True,
        }
    finally:
        if pkg_name:
            for k in [m for m in sys.modules if m == pkg_name or m.startswith(pkg_name + ".")]:
                sys.modules.pop(k, None)
        shutil.rmtree(work_dir, ignore_errors=True)


def run_v3p_surface4_temp_test(run_tmp: Path) -> dict:
    """Verify v3p_surface4a_v3_parity.patch and v3p_surface4b_v3_model_check.patch in <run_tmp>."""
    p4a = FF_ROOT / "patches" / "v3p_surface4a_v3_parity.patch"
    p4b = FF_ROOT / "patches" / "v3p_surface4b_v3_model_check.patch"
    work_dir = run_tmp / f"fn_s4_{uuid.uuid4().hex[:6]}"
    tools_dir = work_dir / "pipeline" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    env = clean_sub_env()
    try:
        shutil.copy2(LAB / "pipeline" / "tools" / "v3_parity.py", tools_dir / "v3_parity.py")
        shutil.copy2(LAB / "pipeline" / "tools" / "v3_model_check.py", tools_dir / "v3_model_check.py")

        for p in (p4a, p4b):
            rc_c = subprocess.run(["git", "-C", str(work_dir), "apply", "--check", str(p)], capture_output=True, text=True, env=env, timeout=30)
            assert rc_c.returncode == 0, f"{p.name} check failed: {rc_c.stderr}"
            rc_a = subprocess.run(["git", "-C", str(work_dir), "apply", str(p)], capture_output=True, text=True, env=env, timeout=30)
            assert rc_a.returncode == 0, f"{p.name} apply failed: {rc_a.stderr}"

        s4a_src = (tools_dir / "v3_parity.py").read_text(encoding="utf-8")
        s4b_src = (tools_dir / "v3_model_check.py").read_text(encoding="utf-8")
        ast.parse(s4a_src, filename="v3_parity.py")
        compile(s4a_src, "v3_parity.py", "exec")
        ast.parse(s4b_src, filename="v3_model_check.py")
        compile(s4b_src, "v3_model_check.py", "exec")

        assert "import forge_v3p as forge_v3" in s4a_src
        assert "import forge_v3p as forge_v3" in s4b_src
        assert "import forge_train_v3p as v3p" in s4b_src
        assert "ckpt_hdr.get('arch') == 'v3p'" in s4b_src
        assert "v3p.load_model(model_path)" in s4b_src

        return {
            "passed": True,
            "patch_4a": str(p4a),
            "patch_4b": str(p4b),
            "ast_and_compile_ok": True,
            "v3_parity_forge_v3p_fallback": True,
            "v3_model_check_v3p_arch_dispatch": True,
        }
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def run_stack_check(stack_name: str, patches: list[Path], run_tmp: Path) -> dict:
    missing = [str(p) for p in patches if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing patches for {stack_name}: {missing}")
    env = clean_sub_env()

    r_direct = subprocess.run(
        ["git", "-C", str(R15_ROOT), "apply", "--check", *(str(p) for p in patches)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    touched_rels: list[str] = []
    seen: set[str] = set()
    for p in patches:
        for rel in parse_target_files(p.read_text(encoding="utf-8", errors="replace")):
            if rel not in seen:
                seen.add(rel)
                touched_rels.append(rel)

    work_dir = run_tmp / f"stack_{stack_name}_{uuid.uuid4().hex[:6]}"
    work_dir.mkdir(parents=True, exist_ok=True)
    seq_steps: list[dict] = []
    try:
        for rel in touched_rels:
            src = R15_ROOT / rel
            dst = work_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        for p in patches:
            rc_chk = subprocess.run(
                ["git", "-C", str(work_dir), "apply", "--check", str(p)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            rc_app = subprocess.run(
                ["git", "-C", str(work_dir), "apply", str(p)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            seq_steps.append(
                {
                    "patch": p.name,
                    "sha256": sha256_file(p),
                    "check_rc": rc_chk.returncode,
                    "apply_rc": rc_app.returncode,
                    "stderr": (rc_chk.stderr or rc_app.stderr).strip(),
                }
            )
            if rc_chk.returncode != 0 or rc_app.returncode != 0:
                break
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    seq_ok = len(seq_steps) == len(patches) and all(s["check_rc"] == 0 and s["apply_rc"] == 0 for s in seq_steps)
    return {
        "name": stack_name,
        "patches": [p.name for p in patches],
        "touched_files": touched_rels,
        "direct_apply_check_rc": r_direct.returncode,
        "direct_apply_check_stderr": r_direct.stderr.strip(),
        "sequential_isolated_steps": seq_steps,
        "passed": (r_direct.returncode == 0 and seq_ok),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Verify all Wave 1-6 patches dynamically, run isolated temp-copy functional checks, and verify combined stacks."
    )
    ap.add_argument(
        "--temp-root",
        type=str,
        default=str(DEFAULT_TEMP_ROOT),
        help="Root directory for transient temp copies (never inside C:\\nnue-lab).",
    )
    ap.add_argument(
        "--json-out",
        type=str,
        default=str(HERE / "verify_all_patches_w6_report.json"),
        help="Path to write JSON verification report.",
    )
    args = ap.parse_args()

    temp_root = Path(args.temp_root).resolve()
    if str(temp_root).lower().startswith(str(LAB).lower()):
        raise ValueError(f"--temp-root must NOT be inside {LAB}: {temp_root}")
    run_tmp = temp_root / f"verify_w6_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    run_tmp.mkdir(parents=True, exist_ok=True)

    try:
        discovered = enumerate_patches()
        results: list[dict] = []
        group_counts: dict[str, dict[str, int]] = {}

        for gname, p in discovered:
            rec = check_patch_routed(gname, p, run_tmp)
            results.append(rec)
            gc = group_counts.setdefault(gname, {"total": 0, "passed": 0, "failed": 0})
            gc["total"] += 1
            if rec["passed"]:
                gc["passed"] += 1
            else:
                gc["failed"] += 1
            status = "PASS" if rec["passed"] else "FAIL"
            print(
                f"[{status}] {gname}/{rec['name']} | route={rec['route']} | rc={rec['rc']} | "
                f"sha256={rec['sha256'][:16]} | targets={','.join(rec['target_files'])}"
            )
            if not rec["passed"] and rec["stderr"]:
                print(f"       stderr: {rec['stderr']}")

        total_patches = len(results)
        total_passed = sum(1 for r in results if r["passed"])
        print(f"\nPATCH_SUMMARY: {total_passed}/{total_patches} passed (RC=0)")
        for gname, counts in group_counts.items():
            print(f"  - {gname}: {counts['passed']}/{counts['total']} PASS")

        print("\nRUNNING ISOLATED FUNCTIONAL TESTS ...")
        t_startpos = run_datagen_startpos_temp_test(run_tmp)
        print(f"  - datagen_startpos_temp_test: {'PASS' if t_startpos['passed'] else 'FAIL'} | sp_k4_explicit={t_startpos['sp_k4_explicit']}")
        t_parity78 = run_datagen_parity_7_8_temp_test(run_tmp)
        print(f"  - datagen_parity_7_8_temp_test: {'PASS' if t_parity78['passed'] else 'FAIL'} | writeminply_alt={t_parity78['play_game_sg_writeminply_alt']}")
        t_surface4 = run_v3p_surface4_temp_test(run_tmp)
        print(f"  - v3p_surface4_temp_test: {'PASS' if t_surface4['passed'] else 'FAIL'} | ast_ok={t_surface4['ast_and_compile_ok']}")

        all_functional_passed = t_startpos["passed"] and t_parity78["passed"] and t_surface4["passed"]

        print("\nRUNNING ISOLATED COMBINED STACK CHECKS ...")
        stack_results: dict[str, dict] = {}
        for sname, spaths in STACK_SPECS.items():
            sres = run_stack_check(sname, spaths, run_tmp)
            stack_results[sname] = sres
            print(
                f"  - {sname}: {'PASS' if sres['passed'] else 'FAIL'} | "
                f"direct_rc={sres['direct_apply_check_rc']} | "
                f"sequential={len(sres['sequential_isolated_steps'])}/{len(spaths)} RC=0"
            )
        all_stacks_passed = all(s["passed"] for s in stack_results.values())

        payload = {
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_patches": total_patches,
            "total_passed": total_passed,
            "all_functional_passed": all_functional_passed,
            "all_stacks_passed": all_stacks_passed,
            "group_counts": group_counts,
            "patches": results,
            "functional_tests": {
                "datagen_startpos_temp_test": t_startpos,
                "datagen_parity_7_8_temp_test": t_parity78,
                "v3p_surface4_temp_test": t_surface4,
            },
            "stack_checks": stack_results,
        }
        if args.json_out:
            out_p = Path(args.json_out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"\nWROTE_JSON: {out_p} ({out_p.stat().st_size} B)")

        ok = (total_patches > 0 and total_passed == total_patches and all_functional_passed and all_stacks_passed)
        return 0 if ok else 1
    finally:
        shutil.rmtree(run_tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
