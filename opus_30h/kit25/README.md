# kit v2.5 (Opus 30-h job) = kit v2.4 (Opus R12, branch opus-r12-pgo-net `opus_r12/kit_v24`) + workload v2n

Why: kit v2.3 (QA's, the lock's kit) trains the PGO profile with every option OFF, so a code path that only an option
reaches (EvalFileV2) is optimised as cold code: the v2 path of kit v2.3 exe df1f140b ran at 0.71x the lock's speed on
the very same search tree (ABBA, `D:\o30\speed\abba_v2lock_d20`). Kit v2.4 `-PartialTraining` (never-executed
functions get normal -O3) brought it to 0.959x (CI 0.929-0.990, `D:\o30\speed\abba_kit24_v2lock_d20`).
v2.5 adds `-Workload v2n`: the frozen v1 workload (uci, bench 11 / 13 / 16) and then the same three benches with
`setoption name EvalFileV2 value {NET:lockv2}` = the lock net written as a v2 file (king buckets 4 by rank, output
buckets 8, every bucket a copy - `o30_v2net.py from-lock --kb-map rank4 --ob 8`, sha256 adc53b04...). That net is the
same function as the compiled-in net, so the second half replays exactly the v1 search trees through the v2 code: the
search profile keeps its shape (counts doubled) and the v2 evaluation, king-bucket refresh and output-bucket code get a
real profile.

Files here: `frozen_train_cmds_v2n.txt` (sha256 57C8CF2E...), `nets_v2n.txt` (sha256 6DE8D8B4...),
`kit25_vs_kit24.patch` (build_ltopgo.ps1: ValidateSet v2n, -NetV2, manifest / workload sha per workload, EvalFileV2
allowed in v2 workloads, driver args, 6 bench lines; tools/train_driver.py: EvalFileV2 allowed, its "loaded" line
counted). Working copy `D:\o30\kit25`; wrapper `tools/kit25_build_o30.sh <repo> <tag>` (-Expose -PartialTraining
-Workload v2n, pc1 + pc2, pc1 = pc2 binding).
