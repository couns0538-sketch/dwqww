# T05-02: One hot eval path for the v2 gate exe (the profile trains the code games run); BOLT is not an option
Status: COMPLETE

## Source
- Own: D:/o30/FINAL_REPORT.md (kit v2.3 makes the v2 path 0.71x, v2.4 -PartialTraining 0.959x, v2.5 workload v2n ~1.0x
  on the bench; v2p4 on game positions OFF 0.933, KB1 0.980; BH-8 per-file effect), D:/o30/wt/opus_30h/a/RESULTS.md
  (probe: kit v2.5 OFF vs lock 0.964, CI 0.942-0.986; without noinline 0.875 before the root fix), skill forge-ltopgo-pgo
  (MSYS2 g++ 15.2.0, -flto=1 -fprofile-generate / -fprofile-use; workload v1 never runs an option-only net path).
- BOLT: https://github.com/llvm/llvm-project/blob/b53763029964ff42b806ede881612fc391344327/bolt/README.md line 12.

## Licence
Own records. llvm-project b537630299: Apache-2.0 WITH LLVM-exception (README read only; tool row corrected in
notes/T05/licences.md).

## Mechanism
GCC's profile-guided build optimises what the training run executes; code that the run never reaches is compiled as
cold (size-optimised, moved away), unless -fprofile-partial-training gives it plain -O3. The v2 eval sits behind a
runtime option, in its own noinline function and section, so its speed depends on which kit and workload built the
exe (0.71x -> 0.959x -> ~1.0x), and the v2.5 build moved the shared code too (its OFF path 0.933-0.964 of the lock).
Fix by construction: let the compiled-in net be loaded into the v2 structures (one king bucket, one output bucket) at
start-up and evaluate it through the v2 code, so there is ONE eval path. The lock's frozen workload then trains the
code that games run, the lock's own kit can build the gate exe, and the noinline / section split can go.
Trained v2 nets add king-bucket refreshes, which KB1 never runs: keep -fprofile-partial-training, or add one bench with
a KB8 net to the workload.
BOLT (post-link block / function layout from a profile) cannot help here: "BOLT operates on X86-64 and AArch64 ELF
binaries"; our exes are PE/COFF from MSYS2 g++ on Windows, and its profiles come from Linux perf or its own ELF
instrumentation. Answer: BOLT on MSYS2 / Windows = NO (source above).

## Forge fit
Lock: src/search.cpp:599-621 static_evaluate (compiled-in path), :1367 root refresh; src/nnue.cpp:53-68 weights().
v2 (v2port.patch): src/search.cpp static_evaluate_v2 with `__attribute__((section(".text.forge_v2"), noinline))`,
a `[[unlikely]]` branch at the top of static_evaluate, the root branch in Worker::search. The lock net written as v2 is
proven to give the lock pins d11-d22 (KB1 / OB1, KB1 / OB8, KB4 replicas), so the one-path build is node-identical.

## Expected gain
Source numbers (own): profile coverage alone moved the v2 path 0.71x -> 0.959x -> ~1.0x (bench); what is left on game
positions is P1 = 0.980 on the v2 path and 0.933-0.964 on v2p4's OFF path (V2P4_GAP.md), partly per-file noise.
Forge estimate: +2-5 % nps for the v2 gate exe, 0 for the lock path **UNPROVEN** (first strip the per-file term with
fresh copies; if P1 vanishes there, this card shrinks to the BOLT answer).

## Effort
Crew 4-8 h (loader from the compiled-in arrays into a v2 Net, the one-path switch, kit build pc1 = pc2, identity).
CPU ~2 h (pins, 12k-FEN identity, nps ABBA). No GPU.

## Test plan
Pre-gate: lock pins (bench d11-d22, perft) with the switch on; trained nets' ON benches = packed counts; parity /
walk unchanged (same kernels); `uci` output identical. Gate route: node-identical = nps ABBA only, vs the lock exe on
game positions (depth_probe_ab.py), several fresh copies per exe (R5B --copies) and an identical-command A/A first.

## OFF-by-default design
Build switch `FORGE_ONE_EVAL_PATH` (default 0 = today's two paths, the lock's code); 1 routes the compiled-in net
through the v2 code. Node-identical (pins equal), so no UCI option; EvalFileV2 keeps its meaning.
