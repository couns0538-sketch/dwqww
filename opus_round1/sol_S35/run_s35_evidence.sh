#!/usr/bin/env bash
# run_s35_evidence.sh (S35, opus 2026-10-27): regenerate every S35 log. Writes logs/ in this folder and scratch under $S (F:).
# Reads the lock archive and (sha256 only) the live PC watcher files; runs nothing on the PC. BelowNormal/idle via nice.
set -u
J=$(cd "$(dirname "$0")" && pwd); cd "$J"
S=${S35_SCRATCH:-/f/opus_scratch/sol_s35}; SW=$(cygpath -w "$S")
LA=/d/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039/6_gate/pc_autonomy_scripts_copy
L=/c/Users/Administrator/grok-pc/forge_push
export TMP="$SW\\tmp" TEMP="$SW\\tmp"; mkdir -p "$S/tmp" logs
H=forge_sol_S35_test_watcher_locked_log_20261027.ps1
{ echo "# step1 provenance (S35, $(date '+%Y-%m-%d %H:%M:%S %z')); all sources read-only"
  echo "## lock-archive copies (LA = 6_gate/pc_autonomy_scripts_copy)"
  (cd $LA && sha256sum driver_r7/conc7_watch.v2_conc8_20261025.ps1 al_vote_20261025/netgate_watch.AL.ps1 autonomy_20261025/netgate_watch.ps1 al_vote_20261025/race_pr/Zfix/autopromote.ps1.staged_ZH)
  echo "## live PC files (sha256 only, never run)"
  sha256sum $L/qa_conc7/conc7_watch.ps1 $L/qa_conc7/conc7_watch.ps1.bak_conc8_20261025_132539 $L/qa_conc7/conc7_watch.ps1.bak_sharedread_20261025 $L/autonomy/netgate_watch.ps1 $L/autonomy/autopromote.ps1
  echo "## committed fixtures"; sha256sum fixtures/watchers/*.ps1 fixtures/functions/*.ps1
  echo "## extract (harness -ExtractFrom) regenerated into scratch and compared"
  nice -n 19 pwsh -NoProfile -NonInteractive -File $H -ExtractFrom "$(cygpath -w $LA/al_vote_20261025/race_pr/Zfix/autopromote.ps1.staged_ZH)" -Names Read-Shared,Log-TLCrash -OutFile "$SW\\regen_extract.ps1" 2>&1
  cmp "$S/regen_extract.ps1" fixtures/functions/autopromote_896663b0_tl_functions.ps1 && echo "regenerated extract == committed extract (cmp: identical)"
  echo "## variants regenerated (make_s35_variants.py; must print the committed hashes)"; python -I -B make_s35_variants.py
  echo "## pwsh version"; pwsh -NoProfile -Command '$PSVersionTable.PSVersion.ToString()'
} > logs/step1_provenance.log 2>&1
for R in A B; do
  { echo "# step2 suite run $R: nice -n 19 pwsh -NoProfile -NonInteractive -File $H -Targets fixtures/targets.json -WorkDir $SW\\work -OutJson $SW\\suite_$R.json"
    nice -n 19 pwsh -NoProfile -NonInteractive -File $H -Targets fixtures/targets.json -WorkDir "$SW\\work" -OutJson "$SW\\suite_$R.json" 2>&1; echo "exit code: $?"
  } > logs/step2_suite_run_$R.log
  grep -E '^(conc7|autopromote|negative|all targets|exit code)' logs/step2_suite_run_$R.log > "$S/table$R.txt"
done
{ cmp "$S/tableA.txt" "$S/tableB.txt" && echo "run A and run B result tables identical (cmp)"; (cd "$S" && sha256sum tableA.txt tableB.txt); } > logs/step2_determinism.log 2>&1
(cd "$S" && tar -czf "$J/logs/step2_suite_evidence.tar.gz" suite_A.json suite_B.json)
{ echo "# step3 safety self-test: nice -n 19 pwsh -NoProfile -NonInteractive -File s35_safety_selftest.ps1 -WorkDir $SW\\safety_$$"
  nice -n 19 pwsh -NoProfile -NonInteractive -File s35_safety_selftest.ps1 -WorkDir "$SW\\safety_$$" 2>&1; echo "exit code: $?"; } > logs/step3_safety_selftest.log
{ echo "# step4 lock-semantics probe: nice -n 19 pwsh -NoProfile -NonInteractive -File s35_probe_lock_semantics.ps1 -OutDir $SW\\probe_$$"
  nice -n 19 pwsh -NoProfile -NonInteractive -File s35_probe_lock_semantics.ps1 -OutDir "$SW\\probe_$$" 2>&1; echo "exit code: $?"; } > logs/step4_lock_semantics_probe.log
cat logs/step2_determinism.log; tail -1 logs/step3_safety_selftest.log; ls -l logs/step2_suite_evidence.tar.gz
