#!/usr/bin/env python3
"""
Job 36 Part C Runner (`run_partC_kf_v3.py`):
1. Applies `selfgame_r15d_v3.patch.txt` to clean `kF` (`/tmp/carbon2_work/src_kF`)
   with `patch -p1 --fuzz=0`.
2. Builds `kF_v3` via SP-PGO (`/tmp/carbon2_job36/bld_sp_sgkFv3/forge`, len=38).
3. Verifies Step 0's seven numbers in fresh processes (+ Job 20).
4. Runs Sets A, B, C, and n on `kF_v3` and compares every `sha256`, every `sg` line,
   every `sgend` line (including `KF`'s `fen` field), and every `sgerror` line against
   `r15d_v3` (`r15d + v3`), plus `builds.txt`.
"""
from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import chess

JOB36 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job36")
JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")
WORK = pathlib.Path("/tmp/carbon2_job36")
KF_SRC = pathlib.Path("/tmp/carbon2_work/src_kF")
R15D_V3_EXE = "/tmp/carbon2_job36/bld_sp_sgr15v/forge"

sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))
sys.path.insert(0, "/tmp/carbon2_job28")

from loop_v3_driver import V3SuiteRun, run_loop_detailed, write_v2_v3_rows
from run_suite_compare import SUITES
from sp_tools import build_sp_pgo
from verify_seven import sha256_file, verify_exe


def fmt_cmp(label: str, got: object, exp: object) -> tuple[bool, str]:
    ok = got == exp
    status = "PASS" if ok else "FAIL"
    op = "==" if ok else "!="
    return ok, f"  {label:<46s}: {status} ({got} {op} {exp})"


def write_builds_txt() -> None:
    entries = [
        (
            "plain_r15d (REUSED from Job 11/31/33/35)",
            "/tmp/carbon2_job11/bld_sp_r15d_1/forge",
            "/tmp/carbon2_job11/bld_sp_r15d_1/forge.profdata",
        ),
        (
            "r15d_v2 (REUSED from Job 35)",
            "/tmp/carbon2_job35/bld_sp_sgr15v/forge",
            "/tmp/carbon2_job35/bld_sp_sgr15v/forge.profdata",
        ),
        (
            "kK (REUSED from Job 32/34)",
            "/tmp/carbon2_job32/bld_sp_stkK_1/forge",
            "/tmp/carbon2_job32/bld_sp_stkK_1/forge.profdata",
        ),
        (
            "plain_kF (REUSED from Job 17/28/30/31/35)",
            "/tmp/carbon2_job17/bld_sp_tidy_1/forge",
            "/tmp/carbon2_job17/bld_sp_tidy_1/forge.profdata",
        ),
        (
            "r15d_v3 (SP-PGO, Job 36 Part A)",
            "/tmp/carbon2_job36/bld_sp_sgr15v/forge",
            "/tmp/carbon2_job36/bld_sp_sgr15v/forge.profdata",
        ),
        (
            "kK_cp (fast -O3 ThinLTO counter build, Job 36 Part B)",
            "/tmp/carbon2_job36/bld_kk_cp_fast/forge",
            None,
        ),
        (
            "kK_plant (fast -O3 ThinLTO planted build, Job 36 Part B)",
            "/tmp/carbon2_job36/bld_kk_pl_fast/forge",
            None,
        ),
        (
            "kF_cp (fast -O3 ThinLTO counter build, Job 36 Part B)",
            "/tmp/carbon2_job36/bld_kf_cp_fast/forge",
            None,
        ),
        (
            "kF_v3 (SP-PGO, Job 36 Part C)",
            "/tmp/carbon2_job36/bld_sp_sgkFv3/forge",
            "/tmp/carbon2_job36/bld_sp_sgkFv3/forge.profdata",
        ),
    ]
    out = ["=== JOB 36 BUILDS ==="]
    for idx, (lbl, epath, ppath) in enumerate(entries, 1):
        out.append(f"{idx}. {lbl}:")
        out.append(f"   path:            {epath} (len={len(epath)})")
        out.append(f"   exe_sha256:      {sha256_file(epath)}")
        if ppath is not None and pathlib.Path(ppath).exists():
            out.append(f"   profdata_sha256: {sha256_file(ppath)}")
        out.append("")
    (JOB36 / "builds.txt").write_text("\n".join(out))


def main() -> None:
    utc0 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    patch_path = JOB36 / "selfgame_r15d_v3.patch.txt"
    patch_txt = patch_path.read_text()
    patch_sha = hashlib.sha256(patch_path.read_bytes()).hexdigest()

    tpl_kf_v3 = WORK / "tpl_kF_v3"
    if tpl_kf_v3.exists():
        shutil.rmtree(tpl_kf_v3)
    shutil.copytree(KF_SRC, tpl_kf_v3)

    apply_res = subprocess.run(
        ["patch", "-d", str(tpl_kf_v3), "-p1", "--fuzz=0"],
        input=patch_txt,
        text=True,
        capture_output=True,
    )
    ok_apply, s_apply = fmt_cmp("patch -p1 --fuzz=0 exit_code on kF", apply_res.returncode, 0)
    step0_lines = [
        f"UTC start: {utc0}",
        "=== PART C: Apply `selfgame_r15d_v3.patch.txt` to `kF` (`patch -p1 --fuzz=0`) ===",
        f"Patch sha256: {patch_sha}",
        f"APPLIES: {'YES' if ok_apply else 'NO'}",
        s_apply,
        "--- patch stdout ---",
        apply_res.stdout.rstrip("\n"),
    ]
    if apply_res.stderr:
        step0_lines.extend(["--- patch stderr ---", apply_res.stderr.rstrip("\n")])
    step0_lines.append("")

    if not ok_apply:
        (JOB36 / "partC_apply_and_step0_raw.txt").write_text("\n".join(step0_lines) + "\n")
        print("\n".join(step0_lines), flush=True)
        raise SystemExit(1)

    sp_res = build_sp_pgo(
        str(tpl_kf_v3),
        "/tmp/carbon2_job36/src_sp_sgkFv3",
        "/tmp/carbon2_job36/bld_sp_sgkFv3",
        cpu_pin=3,
    )
    kf_v3_exe = sp_res["exe"]
    assert len(kf_v3_exe) == 38

    ok_v7, v7_lines = verify_exe(
        "kF_v3 (bld_sp_sgkFv3)",
        kf_v3_exe,
        profdata_path="/tmp/carbon2_job36/bld_sp_sgkFv3/forge.profdata",
        with_job20=True,
    )
    utc1 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    step0_lines.extend(v7_lines)
    step0_lines.append(f"UTC end: {utc1}")
    step0_lines.append(f"PART C APPLY + STEP 0 OVERALL: {'PASS' if (ok_apply and ok_v7) else 'FAIL'} ({int(ok_apply and ok_v7)} == 1)")
    (JOB36 / "partC_apply_and_step0_raw.txt").write_text("\n".join(step0_lines) + "\n")
    print("\n".join(step0_lines), flush=True)
    if not ok_v7:
        raise SystemExit(1)

    # Run A, B, C, n on both r15d_v3 and kF_v3 and compare every sha256, sg, sgend (incl. fen), and sgerror
    set_order = ["A", "B", "C", "n"]
    tasks = []
    for idx, sname in enumerate(set_order):
        seed, n_att, settings, _ka = SUITES[sname]
        tasks.append((sname, "r15d_v3", R15D_V3_EXE, seed, n_att, settings, idx % 4))
        tasks.append((sname, "kF_v3", kf_v3_exe, seed, n_att, settings, (idx + 2) % 4))

    runs: dict[tuple[str, str], V3SuiteRun] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = {
            pool.submit(run_loop_detailed, exe, 3, seed, n_att, settings, cpu): (sname, tag)
            for sname, tag, exe, seed, n_att, settings, cpu in tasks
        }
        for fut in concurrent.futures.as_completed(futs):
            runs[futs[fut]] = fut.result()

    utc2 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    all_ok = True
    sum_lines = [
        f"UTC: {utc2}",
        "=== PART C: Known-Answer Comparison `kF + v3` vs `r15d + v3` Across Sets A, B, C, and n ===",
        f"r15d_v3 exe: {R15D_V3_EXE}",
        f"kF_v3   exe: {kf_v3_exe}",
        "",
    ]

    total_kf_fen_eq = 0
    total_kf_fen_cmp = 0

    for sname in set_order:
        _seed, _n_att, _settings, ka = SUITES[sname]
        rd = runs[(sname, "r15d_v3")]
        rk = runs[(sname, "kF_v3")]
        write_v2_v3_rows(JOB36 / f"partC_kF_v3_{sname}_rows.txt", f"partC kF_v3 Set {sname}", rk)

        sg_eq = sum(
            sum(1 for a, b in zip(dd.sg_lines, dk.sg_lines) if a == b)
            for dd, dk in zip(rd.details, rk.details)
            if len(dd.sg_lines) == len(dk.sg_lines)
        )
        sg_tot = sum(len(dd.sg_lines) for dd in rd.details)

        sgend_eq = sum(
            1
            for dd, dk in zip(rd.details, rk.details)
            if dd.sgend_line is not None and dd.sgend_line == dk.sgend_line
        )
        sgend_tot = sum(1 for dd in rd.details if dd.sgend_line is not None)

        fen_eq_r15d = sum(
            1
            for dd, dk in zip(rd.details, rk.details)
            if dd.final_fen is not None and dd.final_fen == dk.final_fen
        )
        fen_eq_py = 0
        for dk in rk.details:
            if dk.finished and dk.sgend_line is not None:
                b = chess.Board()
                for u in dk.opening_moves + dk.loop_moves:
                    b.push_uci(u)
                total_kf_fen_cmp += 1
                if dk.final_fen == b.fen():
                    fen_eq_py += 1
                    total_kf_fen_eq += 1

        sgerr_eq = sum(
            1
            for dd, dk in zip(rd.details, rk.details)
            if dd.sgerror_line is not None and dd.sgerror_line == dk.sgerror_line
        )
        sgerr_tot = sum(1 for dd in rd.details if dd.sgerror_line is not None)

        sum_lines.append(f"[Set {sname}] attempts={rk.attempts} finished={rk.finished} thrown={rk.thrown_away}")
        for lbl, got, exp in [
            ("kF_v3 full_sha256 vs r15d_v3 (== KA3)", rk.full_sha256, rd.full_sha256),
            ("kF_v3 full_sha256 vs KA", rk.full_sha256, ka["full_sha256"]),
            ("kF_v3 searches vs r15d_v3", rk.total_searches, rd.total_searches),
            ("kF_v3 nodes vs r15d_v3", rk.total_nodes, rd.total_nodes),
            ("kF_v3 sg lines equal r15d_v3", sg_eq, sg_tot),
            ("kF_v3 sgend lines (incl. fen) equal r15d_v3", sgend_eq, sgend_tot),
            ("kF_v3 final fen equal r15d_v3", fen_eq_r15d, sgend_tot),
            ("kF_v3 final fen equal python-chess", fen_eq_py, sgend_tot),
            ("kF_v3 sgerror lines equal r15d_v3", sgerr_eq, sgerr_tot),
        ]:
            ok, s = fmt_cmp(lbl, got, exp)
            all_ok = all_ok and ok
            sum_lines.append(s)
        sum_lines.append("")

    ok_tot_fen, s_tot_fen = fmt_cmp("Total kF_v3 finished games fen == python-chess", total_kf_fen_eq, total_kf_fen_cmp)
    all_ok = all_ok and ok_tot_fen
    sum_lines.append(s_tot_fen)
    sum_lines.append(f"PART C OVERALL: {'PASS' if all_ok else 'FAIL'} ({int(all_ok)} == 1)")

    out_txt = "\n".join(sum_lines) + "\n"
    (JOB36 / "partC_kF_v3_summary.txt").write_text(out_txt)
    print(out_txt, flush=True)

    write_builds_txt()
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
