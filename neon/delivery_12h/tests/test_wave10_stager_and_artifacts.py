"""CPU-only verification suite for Stream C (FORGE TEAMWORK WAVE 10).

Verifies genuinely (no mocks/hardcoded outputs, < 3s runtime, zero cache):
  1. CLEAN_IDLE_PER_PATCH_NPS.json: all 7 summary rows, exact nodes, median_ms (381 ms
     for live_pgo_r0067 & live_pgo_LmrDeeper), median_nps, ratios, pct deltas, EXE
     SHA-256s, and consistency with the 5 interleaved raw runs.
  2. SERVERDAY_ARCH_SUITE_QUIET_SUMMARY.json & 24-net OLS_SCALEFREE_COMPARISON.json:
     G5a/G5b/G5c master_gate_hard_pass=True, Q/P > 10.5, exact 24 rows, and cross-check
     between both files plus quiet vs collapsed regimes.
  3. All 3 S2Q_*_600g_250k_CONFIRM/summary.json files: games==600, finished=True,
     0 time_losses/illegal_moves/disconnects, exact pentanomial_exact Elo/CIs
     (-5.21, -12.75, -16.23), W-D-L, ptnml, and seeds 202611960..202611962.
  4. stage_teamwork_delivery_w10.py & DELIVERY_MANIFEST_W10.json:
     py_compile into TemporaryDirectory(), schema w10.1 / wave 10 / 4.0 MiB cap,
     strict status invariants, negative schema/CLI safety checks,
     --dry-run --require-siblings RC=0, --verify-manifest --require-siblings RC=0,
     --live without token RC=2, --live with token while unfrozen RC=2,
     C:\\nnue-lab\\teamwork\\neon_12h_quest_delivery untouched, total staged <= 4.0 MiB.
  5. Hygiene & wording rules across teamwork_wave10\\: zero __pycache__, .pytest_cache,
     forbidden binary/temp suffixes, <= 3.0 MiB dir cap, zero banned terms, and
     Stream B uses "NOT CONFIRMED" (never "REJECTED") for all 3 600g @ 250k arms.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import py_compile
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Strictly CPU-only execution and zero bytecode caching.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HIP_VISIBLE_DEVICES"] = ""
os.environ["ROCR_VISIBLE_DEVICES"] = ""

STREAM_C_DIR = Path(__file__).resolve().parents[1]
WAVE10_DIR = STREAM_C_DIR.parent
FORGE_FIXES_DIR = WAVE10_DIR.parent
NEON_DIR = FORGE_FIXES_DIR.parent
LAB_ROOT = NEON_DIR.parent
MATCHES_DIR = FORGE_FIXES_DIR / "matches"

STAGER_PY = STREAM_C_DIR / "stage_teamwork_delivery_w10.py"
MANIFEST_JSON = STREAM_C_DIR / "DELIVERY_MANIFEST_W10.json"
MANIFEST_MD = STREAM_C_DIR / "DELIVERY_MANIFEST_W10.md"
STREAM_A_MD = WAVE10_DIR / "streamA_per_patch_nps_and_search" / "PER_PATCH_NPS_AND_SEARCH_ROADMAP.md"
STREAM_B_MD = (
    WAVE10_DIR
    / "streamB_stage2_250k_postmortem"
    / "STAGE2_250K_VERIFICATION_AND_SERVERDAY_FINAL_LOCK.md"
)

NPS_JSON = FORGE_FIXES_DIR / "CLEAN_IDLE_PER_PATCH_NPS.json"
ARCH_SUITE_JSON = FORGE_FIXES_DIR / "SERVERDAY_ARCH_SUITE_QUIET_SUMMARY.json"
OLS_JSON = FORGE_FIXES_DIR / "OLS_SCALEFREE_COMPARISON.json"
W8_MANIFEST_JSON = (
    FORGE_FIXES_DIR
    / "teamwork_wave8"
    / "streamC_delivery_stager_w8"
    / "DELIVERY_MANIFEST_W8.json"
)
LIVE_DEST = LAB_ROOT / "teamwork" / "neon_12h_quest_delivery"

S2Q_CONFIRM_SUMMARIES = {
    "S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM": (
        MATCHES_DIR / "S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM" / "summary.json"
    ),
    "S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM": (
        MATCHES_DIR
        / "S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM"
        / "summary.json"
    ),
    "S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM": (
        MATCHES_DIR / "S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM" / "summary.json"
    ),
}

MAX_BUNDLE_BYTES = 4_194_304
MAX_WAVE10_DIR_BYTES = 3_145_728
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
BANNED_WORD_RE = re.compile(r"\b" + "".join(["c", "u", "r", "e"]) + r"d?\b", re.IGNORECASE)

FORBIDDEN_SUFFIXES = {
    ".binpack",
    ".dll",
    ".epd",
    ".exe",
    ".fnn3",
    ".fqs",
    ".lib",
    ".log",
    ".npz",
    ".o",
    ".obj",
    ".out",
    ".part",
    ".pgn",
    ".plain",
    ".pt",
    ".pyc",
    ".z",
}
FORBIDDEN_DIR_NAMES = {"__pycache__", ".pytest_cache", "_tmp_cache"}


def _load_json(path: Path) -> dict:
    assert path.is_file(), f"Missing JSON file: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Expected JSON object in {path}"
    return data


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_stager_module():
    spec = importlib.util.spec_from_file_location("stage_teamwork_delivery_w10", STAGER_PY)
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
        timeout=15,
    )


def test_clean_idle_per_patch_nps_json() -> None:
    data = _load_json(NPS_JSON)
    assert data["depth"] == 15
    assert data["rounds"] == 5
    assert data["net"] == r"C:\nnue-lab\runs\forge\r0067\train\cand.fnn3"

    expected = {
        "live_pgo_r0067": (
            "cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d",
            1373184,
            381,
            3604157,
            1.0,
            0.0,
        ),
        "V3Pv3_alone_r0067_pgo": (
            "6d5443e8088b6617ce0a266bb4336db05bf363ae672442895cdbd60f8a3369c7",
            1373184,
            384,
            3576000,
            0.9922,
            -0.78,
        ),
        "SF13_alone_pgo": (
            "796ef50e534b892453de3401bc4e65e3661f9d11b911146e7807bb95600ae1c1",
            1393274,
            397,
            3509506,
            0.9737,
            -2.63,
        ),
        "W2_proto_1_alone_pgo": (
            "56882b9be1032bd5cddafff3c9a5e7b60a61301db32068e5a6e73148b83bbc06",
            1412411,
            403,
            3504741,
            0.9724,
            -2.76,
        ),
        "live_pgo_LmrDeeper": (
            "cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d",
            1331742,
            381,
            3495385,
            0.9698,
            -3.02,
        ),
        "SF8_alone_pgo": (
            "28e803a8d0b6e88d12dcf42bd37d57b0fe177476666cb1bbe3bdde17cc5f3905",
            1200340,
            366,
            3279617,
            0.91,
            -9.0,
        ),
        "FORGE_OWNER_BUNDLE_PGO": (
            "95d0608e1a6c4c4ba6606a6ba2a8e4562280f71129b33d5d71f65b7e3c8941b0",
            1490428,
            445,
            3349276,
            0.9293,
            -7.07,
        ),
    }

    summary = data["summary"]
    runs = data["runs"]
    assert set(summary.keys()) == set(expected.keys())
    assert set(runs.keys()) == set(expected.keys())

    verified_exe_hashes: dict[str, str] = {}
    for key, (sha, nodes, med_ms, med_nps, ratio, delta) in expected.items():
        row = summary[key]
        assert HEX64_RE.match(row["exe_sha256"])
        assert row["exe_sha256"] == sha
        assert row["nodes"] == nodes
        assert row["median_ms"] == med_ms
        assert row["median_nps"] == med_nps
        assert row["ratio_vs_live_pgo"] == pytest.approx(ratio, abs=1e-6)
        assert row["pct_delta_vs_live_pgo"] == pytest.approx(delta, abs=1e-6)

        exe_p = Path(row["exe"])
        assert exe_p.is_file(), f"Missing benchmark exe: {exe_p}"
        if str(exe_p) not in verified_exe_hashes:
            verified_exe_hashes[str(exe_p)] = _sha256_file(exe_p)
        assert verified_exe_hashes[str(exe_p)] == sha

        round_rows = runs[key]
        assert len(round_rows) == 5
        assert all(r["nodes"] == nodes for r in round_rows)
        assert statistics.median([r["time_ms"] for r in round_rows]) == med_ms
        assert statistics.median([r["nps"] for r in round_rows]) == med_nps

    # Bit-exact nodes for V3Pv3 alone vs live baseline, and identical wall time for LmrDeeper
    assert summary["V3Pv3_alone_r0067_pgo"]["nodes"] == summary["live_pgo_r0067"]["nodes"]
    assert summary["live_pgo_LmrDeeper"]["median_ms"] == summary["live_pgo_r0067"]["median_ms"] == 381


def test_serverday_arch_suite_and_ols_24_nets() -> None:
    arch = _load_json(ARCH_SUITE_JSON)
    ols = _load_json(OLS_JSON)

    expected_archs = {
        "G5a_quiet_768p_kb8": (768, 8, 9647848, 10.69, 5.357),
        "G5b_quiet_1536p_kb8": (1536, 8, 19098856, 10.59, 5.542),
        "G5c_quiet_1024p_kb16": (1024, 16, 25577704, 10.661, 5.505),
    }
    assert set(arch.keys()) == set(expected_archs.keys())

    for name, (hid, kb, nbytes, q_p, r_p) in expected_archs.items():
        entry = arch[name]
        assert entry["hidden"] == hid
        assert entry["king_buckets"] == kb
        assert entry["net_bytes"] == nbytes
        assert entry["master_gate_hard_pass"] is True
        assert entry["ols_Q_over_P"] > 10.5
        assert entry["ols_Q_over_P"] == pytest.approx(q_p, abs=1e-4)
        assert entry["ols_R_over_P"] == pytest.approx(r_p, abs=1e-4)

    rows = ols["rows"]
    assert isinstance(rows, list) and len(rows) == 24
    by_name = {r["net"]: r for r in rows}
    assert len(by_name) == 24

    for name, (_, _, _, q_p, r_p) in expected_archs.items():
        assert name in by_name
        ratios = by_name[name]["ratios_vs_P"]
        assert ratios["Q_P"] > 10.5
        assert ratios["Q_P"] == pytest.approx(q_p, abs=1e-3)
        assert ratios["R_P"] == pytest.approx(r_p, abs=1e-3)

    # All 5 pre-quiet CC0 nets collapsed (Q/P < 4.0); all 14 quiet CC0 nets have Q/P > 10.0
    collapsed_names = {
        "G3a_cc0_keep_noisy (scratch V3P)",
        "G3a_distill_keep_noisy (r0067 w=0.2)",
        "G5a_cc0_768p_kb8",
        "G5b_cc0_1536p_kb8",
        "G5c_cc0_1024p_kb16",
    }
    collapsed = [r for r in rows if r["net"] in collapsed_names]
    quiet_cc0 = [
        r
        for r in rows
        if r["net"].startswith("S2Q/")
        or "skip_noisy" in r["net"]
        or r["net"].endswith("_quiet_768p_kb8")
        or r["net"].endswith("_quiet_1536p_kb8")
        or r["net"].endswith("_quiet_1024p_kb16")
    ]
    assert len(collapsed) == 5
    assert len(quiet_cc0) == 14
    assert all(r["ratios_vs_P"]["Q_P"] < 4.0 for r in collapsed)
    assert all(r["ratios_vs_P"]["Q_P"] > 10.0 for r in quiet_cc0)


def test_stage2_250k_confirmations_summaries() -> None:
    expected = {
        "S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM": {
            "seed": 202611960,
            "wdl": (168, 255, 177),
            "elo": -5.21,
            "lo": -24.09,
            "hi": 13.64,
            "los": 29.39,
        },
        "S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM": {
            "seed": 202611961,
            "wdl": (161, 256, 183),
            "elo": -12.75,
            "lo": -31.52,
            "hi": 5.95,
            "los": 9.08,
        },
        "S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM": {
            "seed": 202611962,
            "wdl": (158, 256, 186),
            "elo": -16.23,
            "lo": -35.75,
            "hi": 3.19,
            "los": 5.08,
        },
    }

    for name, path in S2Q_CONFIRM_SUMMARIES.items():
        data = _load_json(path)
        exp = expected[name]
        assert data["finished"] is True
        assert data["games"] == 600
        assert data["time_losses"] == 0
        assert data["illegal_moves"] == 0
        assert data["disconnects"] == 0
        assert data["exit_code"] == 0
        assert (data["wins"], data["draws"], data["losses"]) == exp["wdl"]
        assert data["wins"] + data["draws"] + data["losses"] == 600
        assert sum(data["ptnml"]) == 300

        decl = data["declaration"]
        assert decl["name"] == name
        assert decl["games"] == 600
        assert decl["nodes"] == 250000
        assert decl["seed"] == exp["seed"]

        ptn = data["pentanomial_exact"]
        assert ptn["games"] == 600
        assert ptn["pairs"] == 300
        assert ptn["elo"] == pytest.approx(exp["elo"], abs=1e-6)
        assert ptn["elo_ci95_lo"] == pytest.approx(exp["lo"], abs=1e-6)
        assert ptn["elo_ci95_hi"] == pytest.approx(exp["hi"], abs=1e-6)
        assert ptn["los_pct"] == pytest.approx(exp["los"], abs=1e-6)
        # All 3 CIs straddle zero -> NOT CONFIRMED
        assert ptn["elo_ci95_lo"] < 0 < ptn["elo_ci95_hi"]


def test_stager_py_compile_schema_and_safety_gates() -> None:
    with tempfile.TemporaryDirectory() as td:
        cfile = Path(td) / "stage_teamwork_delivery_w10.pyc"
        compiled = py_compile.compile(str(STAGER_PY), cfile=str(cfile), doraise=True)
        assert Path(compiled).is_file()

    stager = _load_stager_module()
    assert stager.MAX_BUNDLE_BYTES == MAX_BUNDLE_BYTES
    assert stager.CONFIRM_TOKEN == "YES_COPY_TO_TEAMWORK"

    manifest = _load_json(MANIFEST_JSON)
    assert manifest["schema_version"] == "w10.1"
    assert manifest["wave"] == 10
    assert manifest["max_bundle_bytes"] == MAX_BUNDLE_BYTES

    errs, dup_d, dup_s, _, _ = stager.validate_manifest_schema(manifest)
    assert errs == []
    assert dup_d == 0
    assert dup_s == 0

    # Verify all 377 W8 entries are preserved in W10
    w8 = _load_json(W8_MANIFEST_JSON)
    w10_by_src = {
        os.path.normcase(os.path.normpath(e["source"])): e for e in manifest["files"]
    }
    for w8_e in w8["files"]:
        sk = os.path.normcase(os.path.normpath(w8_e["source"]))
        assert sk in w10_by_src, f"Missing W8 entry in W10: {w8_e['source']}"
        if w8_e.get("wave8_sibling"):
            assert w10_by_src[sk]["status"] == "frozen"
            assert w10_by_src[sk]["freeze_mutable"] is False

    # Verify OWNER_BUNDLE_RESULTS.json promoted to frozen
    obr_key = os.path.normcase(os.path.normpath(str(FORGE_FIXES_DIR / "OWNER_BUNDLE_RESULTS.json")))
    assert w10_by_src[obr_key]["status"] == "frozen"
    assert w10_by_src[obr_key]["pending_until_freeze"] is False

    # Verify all 6 W10 siblings are marked living + wave10_sibling + sha256=null
    w10_sibs = [e for e in manifest["files"] if e["wave10_sibling"]]
    assert len(w10_sibs) == 6
    assert all(
        e["status"] == "living"
        and e["freeze_mutable"] is True
        and e["pending_until_freeze"] is False
        and e["sha256"] is None
        and e["wave_origin"] == "W10"
        for e in w10_sibs
    )

    # Negative in-memory schema invariant checks
    bad_manifest = json.loads(json.dumps(manifest))
    frozen_idx = next(i for i, e in enumerate(bad_manifest["files"]) if e["status"] == "frozen")
    bad_manifest["files"][frozen_idx]["status"] = "living"  # mismatch with freeze_mutable=False
    bad_errs, _, _, _, _ = stager.validate_manifest_schema(bad_manifest)
    assert len(bad_errs) > 0

    bad_manifest2 = json.loads(json.dumps(manifest))
    living_idx = next(i for i, e in enumerate(bad_manifest2["files"]) if e["status"] == "living")
    bad_manifest2["files"][living_idx]["status"] = "frozen"  # mismatch with freeze_mutable=True
    bad_errs2, _, _, _, _ = stager.validate_manifest_schema(bad_manifest2)
    assert len(bad_errs2) > 0

    assert not stager.is_safe_dest_rel("../escape.txt")
    assert not stager.is_safe_dest_rel("/abs/path.txt")
    assert not stager.is_safe_dest_rel("C:\\abs\\path.txt")
    assert stager.has_forbidden_suffix(Path("foo.fnn3"), stager.FORBIDDEN_SUFFIXES)
    assert stager.has_forbidden_suffix(Path("foo.fqs.z"), stager.FORBIDDEN_SUFFIXES)

    # Reject unknown --allow-unfrozen flag (no escape hatch exists)
    r_esc = _run_stager("--live", "--allow-unfrozen")
    assert r_esc.returncode == 2

    # Dry-run & verify-manifest with --require-siblings must pass RC=0
    r_dry = _run_stager("--dry-run", "--require-siblings")
    assert r_dry.returncode == 0, r_dry.stderr + "\n" + r_dry.stdout
    assert "DRY_RUN_SUMMARY:" in r_dry.stdout

    r_ver = _run_stager("--verify-manifest", "--require-siblings")
    assert r_ver.returncode == 0, r_ver.stderr + "\n" + r_ver.stdout
    assert "status=PASS" in r_ver.stdout
    m_bytes = re.search(r"total_bytes=(\d+)\+(\d+)=(\d+)/(\d+)", r_ver.stdout)
    assert m_bytes is not None
    staged_bytes = int(m_bytes.group(3))
    assert staged_bytes <= MAX_BUNDLE_BYTES

    # Dual-lock --live refusal tests (NEVER actually stages!)
    r_notok = _run_stager("--live")
    assert r_notok.returncode == 2

    r_unfrozen = _run_stager("--live", "--confirm-quest-complete", "YES_COPY_TO_TEAMWORK")
    assert r_unfrozen.returncode == 2
    assert not LIVE_DEST.exists(), "C:\\nnue-lab\\teamwork\\neon_12h_quest_delivery must remain untouched!"


def test_wave10_hygiene_cap_and_mandatory_wording() -> None:
    assert MANIFEST_MD.is_file()
    assert STREAM_A_MD.is_file()
    assert STREAM_B_MD.is_file()

    total_bytes = 0
    for root, dirs, files in os.walk(WAVE10_DIR):
        for d in dirs:
            dl = d.lower()
            assert dl not in FORBIDDEN_DIR_NAMES, f"Forbidden cache dir in wave10: {Path(root) / d}"
            assert not dl.startswith("_work_"), f"Forbidden _work_ dir in wave10: {Path(root) / d}"
        for fname in files:
            fp = Path(root) / fname
            bad_sufs = [s for s in fp.suffixes if s.lower() in FORBIDDEN_SUFFIXES]
            assert not bad_sufs, f"Forbidden suffix {bad_sufs} in {fp}"
            total_bytes += fp.stat().st_size
            txt = fp.read_text(encoding="utf-8", errors="replace")
            hits = BANNED_WORD_RE.findall(txt)
            assert not hits, f"Banned word {hits} found in {fp}"

    assert total_bytes <= MAX_WAVE10_DIR_BYTES, (
        f"teamwork_wave10 size {total_bytes} exceeds {MAX_WAVE10_DIR_BYTES}"
    )

    # Stream B must classify all 3 600g @ 250k arms as NOT CONFIRMED and NEVER use REJECTED
    sb_text = STREAM_B_MD.read_text(encoding="utf-8")
    assert len(re.findall(r"NOT CONFIRMED", sb_text)) >= 3
    for arm in (
        "S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM",
        "S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM",
        "S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM",
    ):
        arm_lines = [ln for ln in sb_text.splitlines() if arm in ln]
        assert any("NOT CONFIRMED" in ln for ln in arm_lines), f"Missing NOT CONFIRMED for {arm}"
    assert not re.search(r"\brejected\b", sb_text, re.IGNORECASE), (
        "Stream B must never apply REJECTED to the 600g @ 250k confirmation arms"
    )
