# verify_done.py - before the final manifest: re-read every log that DONE_head.md names and check that the file
# exists and carries the verdict the table claims (Python standard library only). A name with '*' must match at
# least one file and every match must carry the verdict. Prints one line per log and a total; exit 0 only if all hold.
#   python -I -B verify_done.py --log L
import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

ROOT = U.REPO + r'\fable_cpu_speed'
# log name pattern -> text that must be present
EXPECT = [
    ('freeze.log', 'VERDICT FREEZE PASS'),
    ('pins_c29ctl.log', 'planned 13 completed 13 mismatches 0 errors 0'),
    ('bytecmp_lock_vs_c29ctl_r2.log', 'VERDICT BYTECMP CODE-AND-DATA-IDENTICAL'),
    ('profile_bench22_neton_quiet.log', 'VERDICT PROFILE DONE'),
    ('profile_bench22_neton.log', 'VERDICT PROFILE DONE'),
    ('san_fixtures.log', 'planned 8 completed 8 as expected 8'),
    ('san_fixtures_r2.log', 'planned 8 completed 8 as expected 8'),
    ('san_fixtures_r2.log', 'ThreadSanitizer available: NO'),
    ('san_build_asan_r2.log', 'VERDICT SANBUILD DONE'),
    ('san_build_ubsan.log', 'VERDICT SANBUILD DONE'),
    ('san_bench_asan_r2.log', 'planned 10 completed 10 node mismatches 0 sanitizer report lines 0 lane failures 0'),
    ('san_bench_ubsan.log', 'planned 10 completed 10 node mismatches 0 sanitizer report lines 0 lane failures 0'),
    ('cmp_det_*.log', 'VERDICT ROWCMP PASS'),
    ('cmp_tt_lock_*.log', 'planned 240 completed 240 mismatches 0'),
    ('mt_asan_r2.log', 'planned 200 completed 200 illegal best moves 0 sanitizer report lines 0 exit code 0'),
    ('mt_ubsan.log', 'planned 200 completed 200 illegal best moves 0 sanitizer report lines 0 exit code 0'),
    ('mt_release_lock.log', 'planned 200 completed 200 illegal best moves 0 sanitizer report lines 0 exit code 0'),
    ('selftest_checkers.log', 'planned 10 completed 10 as expected 10'),
    ('patch_*_apply.log', 'VERDICT PATCH PASS'),
    ('pins_fuse_*.log', 'planned 13 completed 13 mismatches 0 errors 0'),
    ('pins_pick_*.log', 'planned 13 completed 13 mismatches 0 errors 0'),
    ('pins_pipe_*.log', 'planned 13 completed 13 mismatches 0 errors 0'),
    ('pins_wpf_*.log', 'planned 13 completed 13 mismatches 0 errors 0'),
    ('bytecmp_c29ctl_vs_fuse_off.log', 'CODE-AND-DATA-IDENTICAL'),
    ('bytecmp_c29ctl_vs_pick_off.log', 'CODE-AND-DATA-IDENTICAL'),
    ('bytecmp_c29ctl_vs_pipe_off.log', 'CODE-AND-DATA-IDENTICAL'),
    ('bytecmp_c29ctl_vs_wpf_off_r2.log', 'CODE-AND-DATA-IDENTICAL'),
    ('cmp_harness_fuse_*.log', 'planned 12000 completed 12000 mismatches 0'),
    ('cmp_harness_pick_*.log', 'planned 12000 completed 12000 mismatches 0'),
    ('cmp_harness_pipe_*.log', 'planned 12000 completed 12000 mismatches 0'),
    ('cmp_harness_wpf_*.log', 'planned 12000 completed 12000 mismatches 0'),
    ('cmp_harness_mutant_capture_column_vs_ctl_neton.log', 'mismatches 9619'),
    ('timing_null_1.log', 'RESULT median -0.30 %, min -5.19 %, max +7.68 %'),
    ('timing_fuse_1.log', 'RESULT median +0.93 %, min -0.99 %, max +4.60 %'),
    ('timing_fuse_2_followup.log', 'RESULT median +1.46 %, min -1.62 %, max +6.13 %'),
    ('timing_pick_1.log', 'RESULT median +0.72 %, min -2.17 %, max +4.57 %'),
    ('timing_pipe_1.log', 'RESULT median -1.53 %, min -3.47 %, max +1.12 %'),
    ('timing_wpf16_1.log', 'RESULT median -4.42 %, min -9.18 %, max -2.21 %'),
    ('cmp_release_lock_exe_vs_NNUE_FUSE_EVAL_*.log', 'planned 12000 completed 12000 mismatches 0'),
    ('cmp_release_lock_exe_vs_PREFETCH_PICK_*.log', 'planned 12000 completed 12000 mismatches 0'),
    ('bughunt_uci_battery.log', 'planned 390 runs completed 390; cases with at least one flag: 7'),
    ('bughunt_uci_battery_hard.log', 'planned 130 runs completed 130; cases with at least one flag: 7'),
    ('bughunt_book_and_moves.log', 'planned 30 runs completed 30; cases with at least one flag: 0'),
    ('san_build_hard.log', 'VERDICT SANBUILD DONE'),
    ('san_bench_hard.log', 'planned 10 completed 10 node mismatches 0 sanitizer report lines 0 lane failures 0'),
    ('mt_hard.log', 'planned 200 completed 200 illegal best moves 0 sanitizer report lines 0 exit code 0'),
    ('cmp_lock_vs_hard_cold_*.log', 'planned 2000 completed 2000 mismatches 0'),
    ('cmp_lock_exe_vs_hardened_build_wide_*.log', 'VERDICT ROWCMP PASS'),
    ('bughunt_latency_threads1.log', 'planned 380 completed 380'),
]
COUNTS = {'cmp_det_*.log': 8, 'cmp_tt_lock_*.log': 2, 'patch_*_apply.log': 4, 'cmp_harness_fuse_*.log': 4, 'cmp_harness_pick_*.log': 4,
          'cmp_harness_pipe_*.log': 4, 'cmp_harness_wpf_*.log': 4, 'cmp_release_lock_exe_vs_NNUE_FUSE_EVAL_*.log': 4,
          'cmp_release_lock_exe_vs_PREFETCH_PICK_*.log': 4, 'cmp_lock_vs_hard_cold_*.log': 2,
          'cmp_lock_exe_vs_hardened_build_wide_*.log': 6, 'pins_fuse_*.log': 2, 'pins_pick_*.log': 2, 'pins_pipe_*.log': 2, 'pins_wpf_*.log': 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    a = ap.parse_args()
    U.require_lane()
    L = U.header('VERIFY DONE: every verdict log re-read from disk', [os.path.abspath(__file__), U.__file__], [], ['planned %d checks' % len(EXPECT)])
    ok = 0
    for pat, text in EXPECT:
        files = sorted(glob.glob(os.path.join(U.LOGS, pat)))
        want = COUNTS.get(pat, 1)
        good = len(files) == want and all(text in open(f, 'r', encoding='ascii', errors='replace').read() for f in files)
        ok += 1 if good else 0
        L.append('%s %-52s files %d of %d  wants "%s"' % ('OK  ' if good else 'MISS', pat, len(files), want, text))
    # every log named in DONE_head.md with a plain file name must exist
    head = open(os.path.join(ROOT, 'DONE_head.md'), 'r', encoding='utf-8').read()
    names = sorted(set(re.findall(r'`([A-Za-z0-9_.]+\.(?:log|txt|tsv|json))`', head)))
    missing = [n for n in names if not (os.path.exists(os.path.join(U.LOGS, n)) or os.path.exists(os.path.join(ROOT, n)))]
    L.append('log names in DONE_head.md: %d, missing on disk: %d %s' % (len(names), len(missing), ' '.join(missing)))
    L.append('planned %d completed %d as claimed %d' % (len(EXPECT), len(EXPECT), ok))
    verdict = 'PASS' if (ok == len(EXPECT) and not missing) else 'FAIL'
    L.append('VERDICT VERIFYDONE %s; end %s' % (verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(l for l in L if l.startswith(('MISS', 'log names', 'planned', 'VERDICT'))))
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
