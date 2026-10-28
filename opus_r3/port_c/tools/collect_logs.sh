#!/usr/bin/env bash
# Copy the R3 port C evidence logs from scratch into the job folder (text logs only; dumps, exes and nets stay in
# F:\opus_scratch with sha256 in the logs).
S=/f/opus_scratch/r3/port_c/logs
J=/f/opus_scratch/worktrees/opus_r3_port_c/opus_r3/port_c/logs
mkdir -p $J
cd $S
for f in build_base_2432670b.log build_base_2432670b_o2.log build_sa2merge_default.log build_sa2merge_int16.log \
         build_final_default.log build_final_o2.log build_final_int16.log build_final_int16_o2.log build_h512.log \
         byte_identity_default_and_o2.log inputs_sha256.log v2_replicas.log \
         uci_check_full_sa2merge_default.log uci_check_full_sa2merge_int16_off.log bench_sa2merge_int16_on.log \
         uci_check_full_final_default.log uci_check_full_final_o2.log uci_check_full_final_int16.log uci_check_full_final_int16_o2.log \
         bench_on_final_int16.log bench_on_final_int16_o2.log \
         nnue_int16_regression_final_int16.log nnue_int16_regression_final_int16_o2.log \
         nnue_int16_regression_absent_final_default.log nnue_int16_regression_absent_final_o2.log \
         bench_v2replica_int16on_final_int16.log bench_v2replica_int16on_final_int16_o2.log \
         bench_h512.log v2_h512.log parity_dumps.log \
         cmake_default.configure.log cmake_default.build.log cmake_default_build_driver.log cmake_default_warnings_vs_base.log \
         cmake_binaries_vs_base.log ctest_default.log known_failures_default.log ctest_default_run2.log known_failures_default_run2.log \
         ctest_default_run3.log known_failures_default_run3.log ctest_hard_deadline_rerun_default.log ctest_smp_rerun_default.log \
         cmake_o2.configure.log cmake_o2.build.log cmake_o2.summary.log ctest_o2.log \
         cmake_int16.configure.log cmake_int16.build.log cmake_int16.summary.log ctest_int16.log \
         cmake_o2_int16.configure.log cmake_o2_int16.build.log cmake_o2_int16.summary.log ctest_o2_int16.log \
         cmake_variants_warnings.log \
         mutation_port_c_o2off.log mutation_port_c_o2on.log mutation_port_c_o2off.json mutation_port_c_o2on.json \
         ci_watch_a4fa82bb.log; do
  if [ -f "$f" ]; then cp "$f" "$J/$f"; else echo "missing: $f"; fi
done
[ -d ci_40570018288 ] && mkdir -p $J/ci_40570018288 && cp ci_40570018288/*.log ci_40570018288/*.txt $J/ci_40570018288/ 2>/dev/null
ls $J | wc -l
