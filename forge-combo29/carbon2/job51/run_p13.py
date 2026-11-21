#!/usr/bin/env python3
"""
Job 51 Part P13 (`run_p13.py`):
1. Verifies `/tmp/carbon2_job36/tpl_r15d_v3` source hashes (`0 == 0` CRLF) and `bundle9`
   (`/tmp/carbon2_job44/bld_bundle9/forge`).
2. Prepares a clean `bundle9` source tree in `/tmp/carbon2_job51/src_bundle9_ref`, runs and classifies
   every `tune::HistRework` occurrence across `src_bundle9_ref` (`14` reads on `13` lines in `src/search.cpp`,
   `1` write in `src/uci.cpp`), stopping if any read touches neither `TWIN` nor `JOINT CORRECTION`.
3. Applies the split (`HistReworkQuiet`, `HistReworkCorrection`, `rework_quiet_level()`,
   `rework_correction_level()`) in `/tmp/carbon2_job51/src_bundle13_gen`, writes
   `forge-combo29/carbon2/job51/P13_histrework_split.patch.txt` (`0 == 0` CRLF), verifies
   `git apply --check -p1` and applies it onto a fresh `bundle9` tree `/tmp/carbon2_job51/src_bundle13`,
   records the before/after `grep` with every line's class into `p13_grep_classification.json` and
   `p13_summary.txt`, builds `/tmp/carbon2_job51/bld_bundle13/forge`, and writes `builds.txt`.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from j51_lib import (  # noqa: E402
    BUNDLE7_PATCH,
    EXP_BUNDLE9_SHA,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    JOB51,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    P13_PATCH_PATH,
    TPL_V3,
    UHO_BOOK,
    WORK51,
    apply_bundle9_to_fresh_v3,
    build_release_v3,
    ensure_bundle9_exe,
    fmt_cmp,
    get_id_name_strict,
    sha256_file,
    utc_now,
)


def classify_before_line(rel_file: str, lineno: int, code: str, prev_lines: list[str], next_lines: list[str]) -> tuple[str, int, str]:
    """
    Returns (mechanism_class, count_on_line, reason).
    mechanism_class in {"TWIN", "JOINT_CORRECTION", "UCI_SET"}.
    Raises RuntimeError if any `tune::HistRework` read touches neither TWIN nor JOINT_CORRECTION!
    """
    cnt = code.count("tune::HistRework")
    if rel_file == "src/uci.cpp":
        if "forge::tune::HistRework = clamped;" in code:
            return "UCI_SET", cnt, "UCI setoption write (`forge::tune::HistRework = clamped;`), left unchanged"
        raise RuntimeError(f"Unexpected tune::HistRework in {rel_file}:{lineno}: {code}")

    window = "\n".join(prev_lines + [code] + next_lines)
    touches_joint = ("joint_correction_" in window) or ("joint_weight" in window)
    touches_twin = (
        ("rework_history_" in window)
        or ("threat_maps_" in window)
        or ("threat_quarters" in window)
        or ("rework_entry" in window)
        or ("update_rework_history" in window)
        or ("rework(" in code)
    )
    if touches_joint and not touches_twin:
        return "JOINT_CORRECTION", cnt, "touches `joint_correction_` / `b4::joint_weight`"
    if touches_twin and not touches_joint:
        return "TWIN", cnt, "touches `rework_history_` / `threat_maps_` / `b4::threat_quarters` / `rework_entry`"
    raise RuntimeError(
        f"STOP: unclassified or ambiguous `tune::HistRework` read at {rel_file}:{lineno}: {code}\nWindow:\n{window}"
    )


def apply_split_edits_to_tree(tree_dir: pathlib.Path) -> None:
    # 1. include/forge/search.hpp
    shpp = tree_dir / "include/forge/search.hpp"
    shpp_txt = shpp.read_text(encoding="utf-8")
    old_decl = "extern int HistRework;               // 0 = off; 1..3: threat-keyed quiet history twin + pawn x material correction\n"
    new_decl = (
        old_decl
        + "extern int HistReworkQuiet;          // -1 = follow HistRework; 0..3: threat-keyed quiet history twin level\n"
        + "extern int HistReworkCorrection;     // -1 = follow HistRework; 0..3: pawn x non-pawn-material correction level\n"
        + "int rework_quiet_level();\n"
        + "int rework_correction_level();\n"
    )
    if shpp_txt.count(old_decl) != 1:
        raise RuntimeError("Expected exactly 1 extern int HistRework declaration in search.hpp")
    shpp.write_text(shpp_txt.replace(old_decl, new_decl, 1), encoding="utf-8")

    # 2. src/search.cpp
    scpp = tree_dir / "src/search.cpp"
    scpp_txt = scpp.read_text(encoding="utf-8")

    old_def = "int HistRework = 0;\n"
    new_def = (
        "int HistRework = 0;\n"
        "int HistReworkQuiet = -1;\n"
        "int HistReworkCorrection = -1;\n"
        "int rework_quiet_level() { return HistReworkQuiet < 0 ? HistRework : HistReworkQuiet; }\n"
        "int rework_correction_level() { return HistReworkCorrection < 0 ? HistRework : HistReworkCorrection; }\n"
    )
    if scpp_txt.count(old_def) != 1:
        raise RuntimeError("Expected exactly 1 `int HistRework = 0;` in search.cpp")
    scpp_txt = scpp_txt.replace(old_def, new_def, 1)

    old_param = '        {"IdeaB8b_Swing", &IdeaB8b_Swing, 0, 500},\n'
    new_param = (
        old_param
        + '        {"HistReworkQuiet", &HistReworkQuiet, -1, 3},\n'
        + '        {"HistReworkCorrection", &HistReworkCorrection, -1, 3},\n'
    )
    if scpp_txt.count(old_param) != 1:
        raise RuntimeError("Expected exactly 1 `IdeaB8b_Swing` parameter entry in search.cpp")
    scpp_txt = scpp_txt.replace(old_param, new_param, 1)

    # Replace the 2 JOINT_CORRECTION blocks first (using exact unique multi-line blocks), then all remaining 12 TWIN reads
    old_joint_read = (
        "    // B4 HistRework: pawn structure x non-pawn material. |entry| <= 8192, weight <= 100: |term| <= 8192.\n"
        "    if (const int level = tune::HistRework; level != 0) {"
    )
    new_joint_read = (
        "    // B4 HistRework: pawn structure x non-pawn material. |entry| <= 8192, weight <= 100: |term| <= 8192.\n"
        "    if (const int level = tune::rework_correction_level(); level != 0) {"
    )
    if scpp_txt.count(old_joint_read) != 1:
        raise RuntimeError("Expected exactly 1 joint read block in search.cpp")
    scpp_txt = scpp_txt.replace(old_joint_read, new_joint_read, 1)

    old_joint_upd = (
        "    // B4 HistRework: the joint table learns the same residual step (|step| <= 2048 * 16 / 256 = 128) with a\n"
        "    // self-damping update instead of the add-and-clamp above.\n"
        "    if (tune::HistRework != 0) {"
    )
    new_joint_upd = (
        "    // B4 HistRework: the joint table learns the same residual step (|step| <= 2048 * 16 / 256 = 128) with a\n"
        "    // self-damping update instead of the add-and-clamp above.\n"
        "    if (tune::rework_correction_level() != 0) {"
    )
    if scpp_txt.count(old_joint_upd) != 1:
        raise RuntimeError("Expected exactly 1 joint update block in search.cpp")
    scpp_txt = scpp_txt.replace(old_joint_upd, new_joint_upd, 1)

    rem_twin = scpp_txt.count("tune::HistRework")
    if rem_twin != 12:
        raise RuntimeError(f"Expected 12 remaining TWIN reads of tune::HistRework, got {rem_twin}")
    scpp_txt = scpp_txt.replace("tune::HistRework", "tune::rework_quiet_level()")
    scpp.write_text(scpp_txt, encoding="utf-8")


def collect_grep_records(tree_dir: pathlib.Path, pattern: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for rel in ("include/forge/search.hpp", "src/search.cpp", "src/uci.cpp"):
        fp = tree_dir / rel
        all_lns = fp.read_text(encoding="utf-8").splitlines()
        for idx, ln in enumerate(all_lns):
            if pattern in ln:
                out.append(
                    {
                        "file": rel,
                        "line": idx + 1,
                        "code": ln,
                        "prev": all_lns[max(0, idx - 4) : idx],
                        "next": all_lns[idx + 1 : min(len(all_lns), idx + 14)],
                    }
                )
    return out


def main() -> None:
    WORK51.mkdir(parents=True, exist_ok=True)
    JOB51.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    all_ok = True

    def rec(ok: bool, msg: str) -> None:
        nonlocal all_ok
        if not ok:
            all_ok = False
        lines.append(msg)
        print(msg, flush=True)

    lines.append(f"=== JOB 51 PART P13 HISTREWORK SPLIT PATCH & BUILD ({utc_now()}) ===")

    for rel, exp_sha in EXP_TREE_SHAS.items():
        fp = TPL_V3 / rel
        raw = fp.read_bytes()
        rec(*fmt_cmp(f"{rel} CRLF count", raw.count(b"\r\n"), 0))
        rec(*fmt_cmp(f"tree file sha256({fp})", sha256_file(fp), exp_sha))

    b9_exe, b9_sha, b9_prov = ensure_bundle9_exe()
    rec(*fmt_cmp(f"bundle9 exe sha256({b9_exe})", b9_sha, EXP_BUNDLE9_SHA))
    b9_id = get_id_name_strict(b9_exe)

    # Create clean reference bundle9 tree and classify every `tune::HistRework`
    src_b9_ref = WORK51 / "src_bundle9_ref"
    apply_bundle9_to_fresh_v3(src_b9_ref)

    before_raw = collect_grep_records(src_b9_ref, "tune::HistRework")
    before_classified: list[dict[str, object]] = []
    search_read_occ = 0
    search_read_lines = 0
    twin_occ = 0
    twin_lines = 0
    joint_occ = 0
    joint_lines = 0
    for item in before_raw:
        m_cls, cnt, reason = classify_before_line(
            str(item["file"]),
            int(item["line"]),
            str(item["code"]),
            list(item["prev"]),
            list(item["next"]),
        )
        if item["file"] == "src/search.cpp":
            search_read_occ += cnt
            search_read_lines += 1
            if m_cls == "TWIN":
                twin_occ += cnt
                twin_lines += 1
            elif m_cls == "JOINT_CORRECTION":
                joint_occ += cnt
                joint_lines += 1
        before_classified.append(
            {
                "file": item["file"],
                "line": item["line"],
                "occurrences_on_line": cnt,
                "class": m_cls,
                "reason": reason,
                "code": item["code"],
            }
        )

    rec(*fmt_cmp("K1 bundle9 search.cpp tune::HistRework read occurrences", search_read_occ, 14))
    rec(*fmt_cmp("K1 bundle9 search.cpp tune::HistRework read lines", search_read_lines, 13))
    rec(*fmt_cmp("K1 bundle9 TWIN read occurrences", twin_occ, 12))
    rec(*fmt_cmp("K1 bundle9 TWIN read lines", twin_lines, 11))
    rec(*fmt_cmp("K1 bundle9 JOINT_CORRECTION read occurrences", joint_occ, 2))
    rec(*fmt_cmp("K1 bundle9 JOINT_CORRECTION read lines", joint_lines, 2))

    # Generate clean unified diff P13_histrework_split.patch.txt from git diff
    src_gen = WORK51 / "src_bundle13_gen"
    apply_bundle9_to_fresh_v3(src_gen)
    subprocess.run(["git", "init", "-q"], cwd=str(src_gen), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(src_gen), check=True)
    subprocess.run(
        ["git", "-c", "user.name=tmp", "-c", "user.email=tmp@local", "commit", "-q", "-m", "bundle9"],
        cwd=str(src_gen),
        check=True,
    )
    apply_split_edits_to_tree(src_gen)
    diff_out = subprocess.run(
        ["git", "diff", "--no-color", "HEAD"],
        cwd=str(src_gen),
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    P13_PATCH_PATH.write_text(diff_out, encoding="utf-8")
    p13_bytes = P13_PATCH_PATH.read_bytes()
    rec(*fmt_cmp("P13_histrework_split.patch.txt CRLF count", p13_bytes.count(b"\r\n"), 0))
    p13_sha = sha256_file(P13_PATCH_PATH)
    lines.append(f"  patch sha256({P13_PATCH_PATH}): {p13_sha}")

    # Apply P13_histrework_split.patch.txt onto a fresh bundle9 tree src_bundle13
    src_b13 = WORK51 / "src_bundle13"
    apply_bundle9_to_fresh_v3(src_b13)
    chk = subprocess.run(
        ["git", "apply", "--check", "-p1", str(P13_PATCH_PATH)],
        cwd=str(src_b13),
        capture_output=True,
        text=True,
    )
    rec(*fmt_cmp("git apply --check -p1 P13_histrework_split.patch.txt on bundle9", chk.returncode, 0))
    if chk.returncode != 0:
        raise RuntimeError(f"git apply --check failed: {chk.stderr}")
    ap = subprocess.run(
        ["git", "apply", "-p1", str(P13_PATCH_PATH)],
        cwd=str(src_b13),
        capture_output=True,
        text=True,
        check=True,
    )
    rec(*fmt_cmp("git apply -p1 P13_histrework_split.patch.txt on bundle9", ap.returncode, 0))

    for rel in ("include/forge/search.hpp", "src/search.cpp"):
        rec(*fmt_cmp(f"bundle13 {rel} CRLF count", (src_b13 / rel).read_bytes().count(b"\r\n"), 0))

    # Collect AFTER grep of `tune::HistRework` and `tune::rework_`
    after_histrework = collect_grep_records(src_b13, "tune::HistRework")
    after_rework_fn = collect_grep_records(src_b13, "tune::rework_")
    rec(*fmt_cmp("after P13: search.cpp remaining `tune::HistRework` reads", sum(1 for x in after_histrework if x["file"] == "src/search.cpp"), 0))
    rec(*fmt_cmp("after P13: uci.cpp `tune::HistRework` set lines", sum(1 for x in after_histrework if x["file"] == "src/uci.cpp"), 1))

    after_classified: list[dict[str, object]] = []
    after_q_occ = 0
    after_c_occ = 0
    for item in after_histrework:
        after_classified.append(
            {
                "file": item["file"],
                "line": item["line"],
                "class": "UCI_SET",
                "code": item["code"],
            }
        )
    for item in after_rework_fn:
        cd = str(item["code"])
        nq = cd.count("tune::rework_quiet_level()")
        nc = cd.count("tune::rework_correction_level()")
        after_q_occ += nq
        after_c_occ += nc
        after_classified.append(
            {
                "file": item["file"],
                "line": item["line"],
                "class": "TWIN (`rework_quiet_level`)" if nq > 0 else "JOINT_CORRECTION (`rework_correction_level`)",
                "occurrences_on_line": nq + nc,
                "code": cd,
            }
        )
    rec(*fmt_cmp("after P13: `tune::rework_quiet_level()` occurrences in search.cpp", after_q_occ, 12))
    rec(*fmt_cmp("after P13: `tune::rework_correction_level()` occurrences in search.cpp", after_c_occ, 2))

    # Build bundle13
    bld_b13 = WORK51 / "bld_bundle13"
    b13_exe, b13_sha, b13_cflags, b13_lflags = build_release_v3(src_b13, bld_b13)
    b13_id = get_id_name_strict(b13_exe)
    lines.append(f"  bundle13 exe path: {b13_exe}")
    lines.append(f"  bundle13 exe sha256({b13_exe}): {b13_sha}")
    lines.append(f"  bundle13 id_name: {b13_id}")

    rec(*fmt_cmp("PART P13 OVERALL", 1 if all_ok else 0, 1))
    (JOB51 / "p13_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (JOB51 / "p13_grep_classification.json").write_text(
        json.dumps(
            {
                "before_tune_HistRework": before_classified,
                "after_tune_HistRework_and_rework_levels": after_classified,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    fc_repo = pathlib.Path("/tmp/carbon2_job40/fastchess_repo")
    fc_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(fc_repo), check=True, capture_output=True, text=True
    ).stdout.strip()

    builds_lines = [
        "=== JOB 51 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {sha256_file(TPL_V3 / rel)}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Base bundle9 executable (same as Jobs 44, 46, 48, 49, 50): {b9_exe}",
        f"   provenance = {b9_prov}",
        f"   exe sha256({b9_exe}) = {b9_sha}",
        f"   id_name = {b9_id}",
        f"   patch 1 sha256({BUNDLE7_PATCH}) = {sha256_file(BUNDLE7_PATCH)} (expected b5ae73776326495977125ac7712ecb0832473dcd5f748db2a398b8afc5b41146)",
        f"   patch 2 sha256({P8_HOIST_PATCH}) = {sha256_file(P8_HOIST_PATCH)} (expected {EXP_P8_HOIST_SHA})",
        f"   patch 3 sha256({P9_B8_FAST_PATCH}) = {sha256_file(P9_B8_FAST_PATCH)} (expected {EXP_P9_B8_FAST_SHA})",
        "",
        f"3. Patched bundle13 executable (bundle13 = bundle9 + P13_histrework_split.patch.txt, independent of bundle12): {b13_exe}",
        f"   how_built = fresh copy of {TPL_V3} into {src_b13}, git apply -p1 of bundle_grok7 + P8_S13_hoist + P9_B8_fast + {P13_PATCH_PATH}, compiled with Release SapphireRapids ThinLTO clang++-18/lld-18",
        f"   patch 4 sha256({P13_PATCH_PATH}) = {p13_sha}",
        f"   exe sha256({b13_exe}) = {b13_sha}",
        f"   id_name = {b13_id}",
        f"   compile_flags = {b13_cflags}",
        f"   link_flags    = {b13_lflags}",
        "",
        f"4. Official fastchess executable: {FASTCHESS_BIN}",
        f"   git_commit({fc_repo}) = {fc_head}",
        f"   exe sha256({FASTCHESS_BIN}) = {sha256_file(FASTCHESS_BIN)}",
        "",
        f"5. Official opening book: {UHO_BOOK}",
        f"   lines({UHO_BOOK}) = {EXP_UHO_LINES}",
        f"   book sha256({UHO_BOOK}) = {sha256_file(UHO_BOOK)} (expected {EXP_UHO_SHA})",
    ]
    (JOB51 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")
    if not all_ok:
        raise RuntimeError("Part P13 failed!")


if __name__ == "__main__":
    main()
