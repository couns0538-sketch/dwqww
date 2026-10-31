# R12 - LTO+PGO profile that includes the HalfKA net path

Branch `opus-r12-pgo-net` (base 7f79c349 = r10fix1, the engine source of 9E5CB644 / D8D90B68; no engine change).
Report: `REPORT.md`. Kit: `kit_v24/` (= kit v2.3 + workload v2, `-PartialTraining`, `-CheckOptPins`; see its README).

## Run (PC, BelowNormal, only on a CPU pair QA freed for R12)
Builds (each: plain + instrumented + training + LTO+PGO + identity; the kit pins itself to the pair):

    python -I -B opus_r12/tools/r12_build_chain.py --work F:/opus_scratch/r12/builds --src F:/opus_scratch/r12/src_r10fix1 \
      --log F:/opus_scratch/r12/logs/chain.log --build r10fix1_w2_pc1:full --build r10fix1_w2_pc2 \
      --build r10fix1_w2pt_pc1:pt:full --build r10fix1_w2pt_pc2:pt [--pair 0x3 --ignore-idle]

`:pt` = `-PartialTraining`, `:full` = identity also with both nets (pins = D8D90B68's counts). Without `--pair` the
chain waits until no gate / trainer / self-play / QA process holds a pair; `--pair 0x3 --ignore-idle` is for a pair QA
freed without changing the trainer mask (Idle trainer threads then yield). The chain never kills or deletes.

Same-engine checks: kit identity (OFF = lock pins, nets = pins, plain = LTO+PGO), and

    python -I -B opus_r12/tools/r12_fens12k.py --out <dir> --cpu 0 --net <net> --fens opus_r10/parity/fens_12k.txt \
      --depth 2 --exe D8=<plain d8d90b68> --exe NEW=<new exe>

Speed (palindromic ABBA blocks, fresh process per run, A/A against a byte copy):

    python -I -B opus_r12/tools/r12_speed.py --out <dir> --cpu 0 --net <net> --pairs 7 --aa-pairs 3 --depths 16 20 \
      --exe A=<new> --exe B=<new pt> --exe D8=<d8d90b68> --exe L9=<9e5cb644> --ref D8 --ref L9 --ref B \
      --aa A=<copy of new> --aa B=<copy of new pt>

Scratch: `F:\opus_scratch\r12\` (builds, exes, logs). CR patches: `D:\grok-pc-data\r12_pgo\cr_patches`.
