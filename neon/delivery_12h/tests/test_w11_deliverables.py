"""CPU-only verification suite for Forge Wave 11 deliverables (zero GPU, zero matches, zero cache)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HIP_VISIBLE_DEVICES"] = ""
os.environ["ROCR_VISIBLE_DEVICES"] = ""

WAVE11_DIR = Path(__file__).resolve().parent
FORGE_FIXES_DIR = WAVE11_DIR.parent
NEON_DIR = FORGE_FIXES_DIR.parent
LAB_ROOT = NEON_DIR.parent
LOOP_PLACE_DIR = FORGE_FIXES_DIR / "loop_place"

STAGER_PY = WAVE11_DIR / "stage_teamwork_delivery_w11.py"
MANIFEST_JSON = WAVE11_DIR / "DELIVERY_MANIFEST_W11.json"
SEARCH_LEDGER_MD = WAVE11_DIR / "SEARCH_ONE_BY_ONE_PLACEMENT_LEDGER.md"

DIFF_MD = LOOP_PLACE_DIR / "R0202_VS_R1_KEEP_FORENSIC_DIFF.md"
DIFF_JSON = LOOP_PLACE_DIR / "R0202_VS_R1_KEEP_FORENSIC_DIFF.json"
DRAFT_PATCH = LOOP_PLACE_DIR / "config_forge_skipnoisy_DRAFT.patch"
VERIFY_LP_PY = LOOP_PLACE_DIR / "verify_skipnoisy_loop_placement.py"
CACHE_SWAP_PY = LOOP_PLACE_DIR / "cache_swap_skipnoisy.py"
TEST_CACHE_SWAP_PY = LOOP_PLACE_DIR / "test_cache_swap_skipnoisy.py"

W10_MANIFEST_JSON = (
    FORGE_FIXES_DIR
    / "teamwork_wave10"
    / "streamC_delivery_stager_w10"
    / "DELIVERY_MANIFEST_W10.json"
)
LIVE_DEST = LAB_ROOT / "teamwork" / "neon_12h_quest_delivery"

MAX_BUNDLE_BYTES = 4_194_304
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
BANNED_WORD_RE = re.compile(r"\b" + "".join(["c", "u", "r", "e"]) + r"d?\b", re.IGNORECASE)

FORBIDDEN_SUFFIXES = {
    ".binpack", ".dll", ".epd", ".exe", ".fnn3", ".fqs", ".lib", ".log",
    ".npz", ".o", ".obj", ".out", ".part", ".pgn", ".plain", ".pt", ".pyc", ".z",
}
FORBIDDEN_DIR_NAMES = {"__pycache__", ".pytest_cache", "_tmp_cache", "_pytest_tmp"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_stager(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["HIP_VISIBLE_DEVICES"] = ""
    env["ROCR_VISIBLE_DEVICES"] = ""
    return subprocess.run(
        [sys.executable, "-B", str(STAGER_PY), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=20,
    )


def test_deliverable1_r0202_vs_r1_keep_forensic_diff() -> None:
    assert DIFF_MD.is_file()
    assert DIFF_JSON.is_file()
    data = json.loads(DIFF_JSON.read_text(encoding="utf-8"))
    sbs = data["side_by_side"]
    assert sbs["train_rows_used"]["r0202"] == 346_931_328
    assert sbs["train_rows_used"]["r1_keep"] == 346_931_328
    assert sbs["train_rows_used"]["r1_skip_ref"] == 281_241_466
    assert sbs["filter_kept_total"]["r0202"] == 378_856_831
    assert sbs["epochs"]["r0202"] == sbs["epochs"]["r1_keep"] == 40
    assert sbs["batch_size"]["r0202"] == sbs["batch_size"]["r1_keep"] == 8192
    assert sbs["mix"]["r0202"] == sbs["mix"]["r1_keep"] == 0.75
    assert sbs["w1_decay"]["r0202"] == sbs["w1_decay"]["r1_keep"] == 0.3
    assert sbs["init_actual_vs_state_json"]["subtle_metadata_diff_flagged"] is True
    assert sbs["live_env_triton_and_parser_flags"]["r0202_FORGE_PARSE_PROCS"].startswith("4")
    assert sbs["live_env_triton_and_parser_flags"]["r1_keep_FORGE_PARSE_PROCS"].startswith("8")
    assert sbs["thermal_pauses_and_wall_time"]["r0202_cooling_pauses"] == 22
    assert sbs["thermal_pauses_and_wall_time"]["r1_keep_cooling_pauses"] == 0

    ep_rows = data["trajectories"]["r0202_train_log_epochs"]
    assert len(ep_rows) == 40
    assert ep_rows[0]["loss"] == pytest.approx(0.010121, abs=1e-7)
    assert ep_rows[-1]["loss"] == pytest.approx(0.006358, abs=1e-7)
    assert ep_rows[-1]["fit_holdout"] == pytest.approx(0.009218, abs=1e-7)

    fm = data["trajectories"]["final_metrics"]
    assert fm["r0202"]["val"] == pytest.approx(0.009218, abs=1e-7)
    assert fm["r1_keep"]["final_loss"] == pytest.approx(0.006366, abs=1e-7)
    assert fm["r1_keep"]["val"] == pytest.approx(0.009190, abs=1e-7)

    arts = data["artifacts_and_weight_stats"]
    for key in ("r0202", "r1_keep", "r1_skip"):
        assert _sha256_file(Path(arts[key]["pt_path"])) == arts[key]["pt_sha256"]
        assert _sha256_file(Path(arts[key]["fnn3_path"])) == arts[key]["fnn3_sha256"]

    flag_ids = {f["id"] for f in data["flagged_differences"]}
    assert {
        "DIFF-1-STATE-JSON-INIT-MISREPORT",
        "DIFF-2-FORGE-PARSE-PROCS",
        "DIFF-3-THERMAL-PAUSES",
        "DIFF-4-TRITON-ATOMIC-NONDETERMINISM",
    } <= flag_ids

    md_txt = DIFF_MD.read_text(encoding="utf-8")
    assert "NOT CONFIRMED" in md_txt
    assert "breaks V3P nets on CC0 data" in md_txt
    assert "early-stopping upward bias" in md_txt
    assert not BANNED_WORD_RE.search(md_txt)
    assert not BANNED_WORD_RE.search(DIFF_JSON.read_text(encoding="utf-8"))


def test_deliverable2_skipnoisy_draft_patch_and_verifier() -> None:
    assert DRAFT_PATCH.is_file()
    assert VERIFY_LP_PY.is_file()
    # Pre-existing W10/Opus loop_place files must remain byte-for-byte untouched
    assert _sha256_file(CACHE_SWAP_PY) == "7a19c65efd4b72771495dbcb541ed4be4cd054ef4da86c0110ad075ebaa0ce68"
    assert _sha256_file(TEST_CACHE_SWAP_PY) == "e082131ae02a4d55ea905ba18ee17910eb65adb535c899300eccc52f10a41b3c"

    vmod = _load_module("verify_skipnoisy_loop_placement", VERIFY_LP_PY)
    res = vmod.verify_all()
    assert res["status"] == "PASS"
    assert res["patch_applies_in_memory"] is True
    assert res["patched_toml_valid"] is True
    assert res["keep_noisy_removed_from_train_cmd"] is True
    assert res["max_window_positions"] == 388_000_000
    assert res["selected_rounds_count"] == 25
    assert res["selected_rounds_range"] == "r0178..r0202"
    assert res["kept_recorded_total"] == 378_856_831
    assert res["verified_hashes_count"] == 10


def test_deliverable3_search_one_by_one_placement_ledger() -> None:
    assert SEARCH_LEDGER_MD.is_file()
    txt = SEARCH_LEDGER_MD.read_text(encoding="utf-8")
    for token in (
        "V3Pv3_alone_r0067_pgo",
        "0.9922x",
        "1,373,184",
        "LmrDeeperShallower=true",
        "0.9698x",
        "381",
        "SF13_alone_pgo",
        "0.9737x",
        "W2_proto_1_alone_pgo",
        "0.9724x",
        "SF8_alone_pgo",
        "0.9100x",
        "-9.00%",
        "SF4b1",
        "SF15",
        "UCI_EvasionOrdering",
        "OWNER_BUNDLE",
        "-7.47",
        "+3.82",
    ):
        assert token in txt, f"Missing expected search ledger token: {token}"
    assert not BANNED_WORD_RE.search(txt)


def test_deliverable4_w11_stager_manifest_and_safety_gates() -> None:
    with tempfile.TemporaryDirectory() as td:
        cfile = Path(td) / "stage_teamwork_delivery_w11.pyc"
        compiled = py_compile.compile(str(STAGER_PY), cfile=str(cfile), doraise=True)
        assert Path(compiled).is_file()

    stager = _load_module("stage_teamwork_delivery_w11", STAGER_PY)
    assert stager.MAX_BUNDLE_BYTES == MAX_BUNDLE_BYTES
    assert stager.CONFIRM_TOKEN == "YES_COPY_TO_TEAMWORK"

    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "w11.1"
    assert manifest["wave"] == 11
    assert manifest["max_bundle_bytes"] == MAX_BUNDLE_BYTES

    errs, dup_d, dup_s, _, _ = stager.validate_manifest_schema(manifest)
    assert errs == []
    assert dup_d == 0
    assert dup_s == 0

    w10 = json.loads(W10_MANIFEST_JSON.read_text(encoding="utf-8"))
    w11_by_src = {
        os.path.normcase(os.path.normpath(e["source"])): e for e in manifest["files"]
    }
    for w10_e in w10["files"]:
        sk = os.path.normcase(os.path.normpath(w10_e["source"]))
        assert sk in w11_by_src, f"Missing W10 entry in W11: {w10_e['source']}"
        if w10_e.get("wave10_sibling"):
            assert w11_by_src[sk]["status"] == "frozen"
            assert w11_by_src[sk]["freeze_mutable"] is False

    # OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k summary promoted to frozen
    r1_sprt_key = os.path.normcase(
        os.path.normpath(
            str(FORGE_FIXES_DIR / "matches" / "OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k" / "summary.json")
        )
    )
    assert w11_by_src[r1_sprt_key]["status"] == "frozen"
    assert w11_by_src[r1_sprt_key]["pending_until_freeze"] is False

    # All W11 siblings marked living + wave11_sibling + sha256=null
    w11_sibs = [e for e in manifest["files"] if e["wave11_sibling"]]
    assert len(w11_sibs) == 8
    assert all(
        e["status"] == "living"
        and e["freeze_mutable"] is True
        and e["pending_until_freeze"] is False
        and e["sha256"] is None
        and e["wave_origin"] == "W11"
        for e in w11_sibs
    )

    # Negative schema checks
    bad_m = json.loads(json.dumps(manifest))
    f_idx = next(i for i, e in enumerate(bad_m["files"]) if e["status"] == "frozen")
    bad_m["files"][f_idx]["status"] = "living"
    bad_errs, _, _, _, _ = stager.validate_manifest_schema(bad_m)
    assert len(bad_errs) > 0

    # Synthetic freeze check: passes when clean HANDOFF + valid JSON dict, fails on banned word
    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        clean_handoff = td_p / "HANDOFF.md"
        clean_handoff.write_text("# Clean Handoff\nAll matches complete.\n", encoding="utf-8")
        good_json = td_p / "summary.json"
        good_json.write_text('{"elo": "+10.0"}', encoding="utf-8")
        ok_f = stager.check_freeze_state(clean_handoff, [{"source": str(good_json)}])
        assert ok_f["freeze_ok"] is True

        bad_handoff = td_p / "HANDOFF_BAD.md"
        bad_handoff.write_text(f"# Bad\nThis {''.join(['c','u','r','e','d'])} it.\n", encoding="utf-8")
        bad_f = stager.check_freeze_state(bad_handoff, [{"source": str(good_json)}])
        assert bad_f["freeze_ok"] is False
        assert len(bad_f["handoff_banned_hits"]) == 1

    # CLI checks: --dry-run, --verify-manifest, and dual-lock --live refusal
    r_dry = _run_stager("--dry-run", "--require-siblings")
    assert r_dry.returncode == 0, r_dry.stderr + "\n" + r_dry.stdout
    assert "DRY_RUN_SUMMARY:" in r_dry.stdout

    r_ver = _run_stager("--verify-manifest", "--require-siblings")
    assert r_ver.returncode == 0, r_ver.stderr + "\n" + r_ver.stdout
    assert "status=PASS" in r_ver.stdout
    m_bytes = re.search(r"total_bytes=(\d+)\+(\d+)=(\d+)/(\d+)", r_ver.stdout)
    assert m_bytes is not None
    assert int(m_bytes.group(3)) <= MAX_BUNDLE_BYTES

    assert _run_stager("--live").returncode == 2
    assert _run_stager("--live", "--allow-unfrozen").returncode == 2
    assert _run_stager("--live", "--confirm-quest-complete", "YES_COPY_TO_TEAMWORK").returncode == 2
    assert not LIVE_DEST.exists()


def test_w11_hygiene_and_wording_rules() -> None:
    for d in (WAVE11_DIR, LOOP_PLACE_DIR):
        for root, dirs, files in os.walk(d):
            for sub in dirs:
                assert sub.lower() not in FORBIDDEN_DIR_NAMES, f"Forbidden dir {sub} in {root}"
            for fn in files:
                fp = Path(root) / fn
                bad_sufs = [s for s in fp.suffixes if s.lower() in FORBIDDEN_SUFFIXES]
                assert not bad_sufs, f"Forbidden suffix {bad_sufs} in {fp}"
                txt = fp.read_text(encoding="utf-8", errors="replace")
                hits = BANNED_WORD_RE.findall(txt)
                assert not hits, f"Banned word {hits} in {fp}"
