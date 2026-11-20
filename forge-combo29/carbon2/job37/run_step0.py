#!/usr/bin/env python3
"""
Job 37 Step 0 Verifier (`run_step0.py`):
Verifies reused SP-PGO `r15d + v3` (`/tmp/carbon2_job36/bld_sp_sgr15v/forge`) against
its recorded Job 36 sha256, all 7 fresh-process Step 0 numbers, and Set n attempts 1..60
through the `selfgame` driver with the PC's line L.
Every PASS/FAIL line prints the two compared values side by side.
"""
from __future__ import annotations

import datetime
import pathlib
import sys

sys.dont_write_bytecode = True

JOB37 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job37")
JOB36 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job36")
JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")

sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from loop_v3_driver import run_loop_detailed
from ref_driver import RunSettings
from verify_seven import fmt_cmp, sha256_file, verify_exe

R15D_V3_EXE = "/tmp/carbon2_job36/bld_sp_sgr15v/forge"
R15D_V3_PROF = "/tmp/carbon2_job36/bld_sp_sgr15v/forge.profdata"
REC_EXE_SHA = "bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810"
REC_PROF_SHA = "e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc"

LINE_L_ARGS = "softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"
EXP_N60_RECORDS = 8449
EXP_N60_SEARCHES = 8482
EXP_N60_NODES = 36688357
EXP_N60_SHA = "b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15"


def main() -> None:
    ok7, lines7 = verify_exe(
        "r15d_v3 (reused /tmp/carbon2_job36/bld_sp_sgr15v/forge, recorded in job36/builds.txt)",
        R15D_V3_EXE,
        expected_sha256=REC_EXE_SHA,
        profdata_path=R15D_V3_PROF,
        expected_prof_sha256=REC_PROF_SHA,
    )

    settings_n = RunSettings(net_path="/tmp/carbon2_work/net768.fnn3")
    res_n60 = run_loop_detailed(
        R15D_V3_EXE,
        3,
        "carbon2-job33-n",
        60,
        settings_n,
        cpu_pin=3,
        custom_sg_cmd=f"selfgame {LINE_L_ARGS}",
    )

    checks = [
        ("n[1..60] line L records", res_n60.total_records, EXP_N60_RECORDS),
        ("n[1..60] line L searches", res_n60.total_searches, EXP_N60_SEARCHES),
        ("n[1..60] line L nodes", res_n60.total_nodes, EXP_N60_NODES),
        ("n[1..60] line L record text sha256", res_n60.full_sha256, EXP_N60_SHA),
    ]
    all_ok = ok7
    n60_lines = [
        "",
        f"[Set n attempts 1..60 through selfgame driver with PC line L ('selfgame {LINE_L_ARGS}')]",
    ]
    for lbl, got, exp in checks:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        n60_lines.append(s)

    utc_end = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    out_lines = [
        "=== JOB 37 STEP 0: r15d + v3 Verification (7 Fresh Processes + Set n[1..60] with Line L) ===",
        *lines7,
        *n60_lines,
        "",
        f"STEP 0 OVERALL: {'PASS' if all_ok else 'FAIL'} ({int(all_ok)} == 1)",
        f"UTC finished: {utc_end}",
    ]
    out_txt = "\n".join(out_lines) + "\n"
    (JOB37 / "step0_raw.txt").write_text(out_txt)
    print(out_txt, flush=True)
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
