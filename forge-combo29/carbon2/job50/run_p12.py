#!/usr/bin/env python3
"""
Job 50 Part P12 (`run_p12.py`):
1. Verifies `/tmp/carbon2_job36/tpl_r15d_v3` source hashes (`0 == 0` CRLF), `SeePieceValue[Pawn] == 100`
   in `include/forge/eval.hpp`, and `bundle9` (`/tmp/carbon2_job44/bld_bundle9/forge`).
2. Creates a clean `bundle9` source tree in `/tmp/carbon2_job50/src_bundle12` (`tpl_r15d_v3` +
   `bundle_grok7.patch.txt` + `P8_S13_hoist.patch.txt` + `P9_B8_fast.patch.txt`), checks `0 == 0` CRLF
   on `forge-combo29/carbon2/job50/P12_hd_lower.patch.txt`, verifies `git apply --check -p1`, and applies it.
3. Builds `/tmp/carbon2_job50/bld_bundle12/forge` (`bundle12 = bundle9 + P12`) with `build_release_v3`
   and writes `forge-combo29/carbon2/job50/builds.txt` and `forge-combo29/carbon2/job50/p12_summary.txt`.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j50_lib import (  # noqa: E402
    BUNDLE7_PATCH,
    EXP_BUNDLE9_SHA,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    JOB50,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    P12_PATCH_PATH,
    TPL_V3,
    UHO_BOOK,
    WORK50,
    apply_bundle9_to_fresh_v3,
    build_release_v3,
    ensure_bundle9_exe,
    fmt_cmp,
    get_id_name_strict,
    sha256_file,
    utc_now,
)


def main() -> None:
    WORK50.mkdir(parents=True, exist_ok=True)
    JOB50.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    all_ok = True

    def rec(ok: bool, msg: str) -> None:
        nonlocal all_ok
        if not ok:
            all_ok = False
        lines.append(msg)
        print(msg, flush=True)

    lines.append(f"=== JOB 50 PART P12 BUILD & PATCH VERIFICATION ({utc_now()}) ===")

    # 1. Check base r15d+v3 source tree hashes + CRLF + SeePieceValue[Pawn]
    for rel, exp_sha in EXP_TREE_SHAS.items():
        fp = TPL_V3 / rel
        raw = fp.read_bytes()
        rec(*fmt_cmp(f"{rel} CRLF count", raw.count(b"\r\n"), 0))
        rec(*fmt_cmp(f"tree file sha256({fp})", sha256_file(fp), exp_sha))

    eval_hpp = TPL_V3 / "include/forge/eval.hpp"
    eval_txt = eval_hpp.read_text(encoding="utf-8")
    m_spv = re.search(r"SeePieceValue\{([^}]+)\}", eval_txt)
    if not m_spv:
        raise RuntimeError(f"Could not find SeePieceValue in {eval_hpp}")
    spv_vals = [int(x.strip()) for x in m_spv.group(1).split(",")]
    pawn_spv = spv_vals[1]
    rec(*fmt_cmp("eval.hpp SeePieceValue[Pawn] (index 1)", pawn_spv, 100))

    # 2. Verify bundle9 exe
    b9_exe, b9_sha, b9_prov = ensure_bundle9_exe()
    rec(*fmt_cmp(f"bundle9 exe sha256({b9_exe})", b9_sha, EXP_BUNDLE9_SHA))
    b9_id = get_id_name_strict(b9_exe)

    # 3. Verify P12_hd_lower.patch.txt CRLF == 0 and apply on fresh bundle9 tree
    p12_bytes = P12_PATCH_PATH.read_bytes()
    rec(*fmt_cmp("P12_hd_lower.patch.txt CRLF count", p12_bytes.count(b"\r\n"), 0))
    p12_sha = sha256_file(P12_PATCH_PATH)
    lines.append(f"  patch sha256({P12_PATCH_PATH}): {p12_sha}")

    src_b12 = WORK50 / "src_bundle12"
    apply_bundle9_to_fresh_v3(src_b12)
    chk = subprocess.run(
        ["git", "apply", "--check", "-p1", str(P12_PATCH_PATH)],
        cwd=str(src_b12),
        capture_output=True,
        text=True,
    )
    rec(*fmt_cmp("git apply --check -p1 P12_hd_lower.patch.txt on bundle9", chk.returncode, 0))
    if chk.returncode != 0:
        raise RuntimeError(f"git apply --check failed: {chk.stderr}")

    ap = subprocess.run(
        ["git", "apply", "-p1", str(P12_PATCH_PATH)],
        cwd=str(src_b12),
        capture_output=True,
        text=True,
        check=True,
    )
    rec(*fmt_cmp("git apply -p1 P12_hd_lower.patch.txt on bundle9", ap.returncode, 0))

    # Check CRLF on patched files
    for rel in ("include/forge/search.hpp", "src/search.cpp"):
        pf = src_b12 / rel
        rec(*fmt_cmp(f"bundle12 {rel} CRLF count", pf.read_bytes().count(b"\r\n"), 0))

    # 4. Build bundle12 Release executable
    bld_b12 = WORK50 / "bld_bundle12"
    b12_exe, b12_sha, b12_cflags, b12_lflags = build_release_v3(src_b12, bld_b12)
    b12_id = get_id_name_strict(b12_exe)
    lines.append(f"  bundle12 exe path: {b12_exe}")
    lines.append(f"  bundle12 exe sha256({b12_exe}): {b12_sha}")
    lines.append(f"  bundle12 id_name: {b12_id}")

    rec(*fmt_cmp("PART P12 OVERALL", 1 if all_ok else 0, 1))
    (JOB50 / "p12_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    fc_repo = pathlib.Path("/tmp/carbon2_job40/fastchess_repo")
    fc_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(fc_repo), check=True, capture_output=True, text=True
    ).stdout.strip()

    builds_lines = [
        "=== JOB 50 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {sha256_file(TPL_V3 / rel)}" for rel in EXP_TREE_SHAS],
        f"   eval.hpp SeePieceValue[Pawn] = {pawn_spv} (SeePieceValue{{{m_spv.group(1)}}})",
        "",
        f"2. Base bundle9 executable (same as Jobs 44, 46, 48, 49): {b9_exe}",
        f"   provenance = {b9_prov}",
        f"   exe sha256({b9_exe}) = {b9_sha}",
        f"   id_name = {b9_id}",
        f"   patch 1 sha256({BUNDLE7_PATCH}) = {sha256_file(BUNDLE7_PATCH)} (expected b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146)",
        f"   patch 2 sha256({P8_HOIST_PATCH}) = {sha256_file(P8_HOIST_PATCH)} (expected {EXP_P8_HOIST_SHA})",
        f"   patch 3 sha256({P9_B8_FAST_PATCH}) = {sha256_file(P9_B8_FAST_PATCH)} (expected {EXP_P9_B8_FAST_SHA})",
        "",
        f"3. Patched bundle12 executable (bundle12 = bundle9 + P12_hd_lower.patch.txt): {b12_exe}",
        f"   how_built = fresh copy of {TPL_V3} into {src_b12}, git apply -p1 of bundle_grok7 + P8_S13_hoist + P9_B8_fast + {P12_PATCH_PATH}, compiled with Release SapphireRapids ThinLTO clang++-18/lld-18",
        f"   patch 4 sha256({P12_PATCH_PATH}) = {p12_sha}",
        f"   exe sha256({b12_exe}) = {b12_sha}",
        f"   id_name = {b12_id}",
        f"   compile_flags = {b12_cflags}",
        f"   link_flags    = {b12_lflags}",
        "",
        f"4. Official fastchess executable: {FASTCHESS_BIN}",
        f"   git_commit({fc_repo}) = {fc_head}",
        f"   exe sha256({FASTCHESS_BIN}) = {sha256_file(FASTCHESS_BIN)}",
        "",
        f"5. Official opening book: {UHO_BOOK}",
        f"   lines({UHO_BOOK}) = {EXP_UHO_LINES}",
        f"   book sha256({UHO_BOOK}) = {sha256_file(UHO_BOOK)} (expected {EXP_UHO_SHA})",
    ]
    (JOB50 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")
    if not all_ok:
        raise RuntimeError("Part P12 failed!")


if __name__ == "__main__":
    main()
