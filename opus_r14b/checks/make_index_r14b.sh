#!/usr/bin/env bash
# make_index_r14b.sh - Opus R14-B: FILES.txt + SHA256SUMS for the two item folders (forge-job-workflow "Finish"),
# with the shared helpers in F:/opus_scratch/tools (read-only use). Re-run after any edit in a folder; then
# `sha256sum -c --quiet SHA256SUMS` in each folder must print nothing.
set -euo pipefail
W=/d/grok-pc-data/dwqww/.claude/worktrees
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
MK=F:/opus_scratch/tools/make_files_index.py
FIN=/f/opus_scratch/tools/finish_report.sh
"$PY" -I -B "$MK" "$W/o14b-l1/opus_r14b/item1" --title "R14-B item 1 fast npt loader, branch opus-r14b-fast-loader" \
  --header "candidate b5: forge_fastloader.dll sha256 9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935 (built by fastloader/build_fastloader.sh, not committed)" \
  --desc "HANDOFF.md=adoption steps for Engine NNUE / QA (start here)" \
  --desc "RESULTS.md=all checks, numbers and review records (chronological)" \
  --desc "GPU_REQUEST.md=the GPU window request: commands, what to measure, done criteria" \
  --desc "LOADER_SPEC.md=what the old loader does and what the fast loader reproduces" \
  --desc "IDEA_SOURCE.md=sources: GPL loader read for behaviour only, own code" \
  --desc "fastloader/forge_fastloader.cpp=fast loader DLL source (candidate b5)" \
  --desc "fastloader/forge_fastloader.py=Python side: FastStream + FastSparseBatchDataset (sha256 39af47b0...)" \
  --desc "fastloader/build_fastloader.sh=build of the DLL (pc1 = pc2 byte-identical)" \
  --desc "fastloader/ffl_selftest.cpp=self-test (CI: ASan+UBSan, TSan)" \
  --desc "patches/0005-fast-loader-switch.patch=the trainer switch --fast-loader (default off)" \
  --desc "patches/0006-seed-before-model-OPTIONAL.patch=optional: seed before the model is built (Engine NNUE decides)" \
  --desc "trainer_manifest_b2614500.sha256=sha256 of the 264 trainer files the installer's anchors were written for" \
  --desc "tools/install_fast_loader.py=installer for a trainer COPY (--check, --loader-dll)" \
  --desc "tools/test_installer.sh=installer exit codes and file effects on copies of the live config.py + train.py (25 cases; the live-folder guard tested on a stand-in)" \
  --desc "tools/test_scope.py=the fail-closed scope: every out-of-scope setting refused with a clear message (20 cases, bug hunt #7)" \
  --desc "tools/fl_acceptance.sh=one-command CPU acceptance check on a switched trainer copy" \
  --desc "tools/fl_equal.py=raw C API batch hashing and timing (old / fast)" \
  --desc "tools/fl_dataset_equal.py=equality through the trainer's own Dataset path" \
  --desc "tools/fl_abba.py=palindromic loader ABBA" \
  --desc "tools/fl_distribution.py=old w4 vs fast as distributions" \
  --desc "tools/fl_fuzz.py=damaged-file fuzzing (bug hunt #4)" \
  --desc "tools/lm_det.py=deterministic CPU loss-match driver" \
  --desc "tools/lm_run.sh=loss-match run script" \
  --desc "tools/b5_checks.sh=b5 check script (config matrix, spanning batches)" \
  --desc "tools/lowrun.ps1=run one program at low priority on a CPU mask (exit 127 if it cannot start)"
"$PY" -I -B "$MK" "$W/o14b-r2/opus_r14b/item2" --title "R14-B item 2 resumable relabel, branch opus-r14b-relabel" \
  --header "relabel2.py FROZEN at sha256 e01caaf1cf8814771033b3deb71727fd0d2eb45f39ee9b27ae54c7d2970f1602" \
  --desc "RELABEL_HANDOFF.md=handoff for Engine NNUE: state, commands, rules, 50M runbook, costs (start here)" \
  --desc "RESULTS.md=all checks, numbers and review records (chronological)" \
  --desc "relabel2.py=the relabel tool: prepare / run / assemble / status (FROZEN)" \
  --desc "test_relabel2.sh=test suite: exit codes with reasons, --jobs 2, game across files, disk floor, kill / resume" \
  --desc "job_damage.py=damaged job state x run / assemble / status: 105 runs, exit 4 / 3 / 2 with a reason or 0 (a case of test_relabel2.sh)" \
  --desc "prove_resume.sh=the 1M kill / resume proof driver" \
  --desc "bridge_check.sh=post-proof code vs the proof's outputs" \
  --desc "fn_diff.py=function-level diff of two relabel2.py versions" \
  --desc "measure_rates.sh=rate measurements next to the crew load" \
  --desc "build_probe_opt.sh=LTO / LTO+PGO builds of the R13 probe from the lock source in git" \
  --desc "probe_bench.py=probe reference runs, answer compare, probe ABBA" \
  --desc "probe_ref_500.tsv=500 reference requests (rows 900,000-900,499 of the proof sample)" \
  --desc "probe_ref_500_r13.jsonl=the R13 probe's answers to them (20k nodes, Hash 1 MB)" \
  --desc "pgo_train_2k.tsv=PGO training requests (rows 0-1,999 of the proof sample)" \
  --desc "label_stats.py=descriptive label statistics" \
  --desc "sort_normalized.py=sort Astra's normalized JSONL by (source, source_row), with a RAM check" \
  --desc "forge_probe.py=R13 probe client (unchanged copy)" \
  --desc "astra/records.py=Astra's record parser (unchanged copy)" \
  --desc "patches/post_proof_changes.patch=relabel2.py changes after the proof code" \
  --desc "lowrun.ps1=run one program at low priority on a CPU mask (exit 127 if it cannot start)"
for d in "$W/o14b-l1/opus_r14b/item1" "$W/o14b-r2/opus_r14b/item2"; do
  bash "$FIN" "$d"
  (cd "$d" && sha256sum -c --quiet SHA256SUMS && echo "$d: SHA256SUMS verify OK")
  echo "unfilled index lines: $(grep -c '| - |' "$d/FILES.txt" || true)"
done
