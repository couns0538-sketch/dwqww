# R12 - LTO+PGO profile with the HalfKA net path — IN PROGRESS (checkpoint)

Branch `opus-r12-pgo-net` = 7f79c349 (r10fix1, engine unchanged) + R12 commits (kit, tools, report, skill). No Elo or
gate claim; QA gates. Machine exclusive: no (gates, NNUE trainer w4_s4 and self-play kept running). Cores: QA freed
CPUs 0/1 at 20:14 PC clock (trainer mask 0x000F -> 0x000C); every R12 build ran pinned to 0x3, every timing run on
CPU 0 (CPU 1 = its SMT sibling, idle except our own builds, which never overlapped timing), all BelowNormal.

## Results so far
### Workload v2 as specified (nets + Threads=2) does not reproduce
| build | workload | LTO+PGO exe sha256 | identity (OFF pins, e19 pins, e9 pins) |
|---|---|---|---|
| r10fix1_w2_pc1 | v2 | 8f162985ac76683092c304dba734d789c8d885d57b6a735026addb45ee240492 | ALL OK |
| r10fix1_w2_pc2 | v2 | 18503c4dae56d55e696d918770b34b68c081f27e5be4b36326a6ef745ba12ea1 | OFF ALL OK |
| r10fix1_w2pt_pc1 | v2 + -fprofile-partial-training | 63ae405f75eaa46885449486e7b16dd9b1f725eef094ee9428854ae618a80382 | ALL OK |
| r10fix1_w2pt_pc2 | v2 + -fprofile-partial-training | ee5c8beaa5153d2b68bfd83139b850a538dcb22b9460fafc92e27167f77614fc | OFF ALL OK |

- pc1 != pc2 for both variants: the binding check FAILS, so no speed run was made with these exes (rule).
- Cause (logs/funcdiff_*.txt, `tools/exe_func_diff.py`): 12 of 4686 (v2) and 23 of 4674 (v2 + pt) functions differ,
  all hot: Worker::search, qsearch, evaluate_position, static_evaluate, MovePicker::next, halfka::evaluate_raw (v2),
  generate_pseudo_legal, see_ge, ... The 24 Threads=2 `go nodes 200000` searches share the TT between two threads, so
  their node split and tree shape depend on timing; those counts land in exactly the code PGO optimizes hardest.
- `bench` cannot profile SMP: it runs its own one-thread `Searcher(16)` with an exclusive TT lease whatever Threads is.
  So "bench at Threads=2" would be reproducible but would profile no SMP code; real SMP profiling needs `go` with
  2 threads, which is not reproducible. The binding pc1 = pc2 rule and an SMP profile cannot both hold.
- Decision: the gated net workload is **v2t1** = v2 without the Threads=2 part (node-deterministic bench only:
  no net, e19, e9 at Threads=1; sha256 dca15f66...). Workload v2 stays in the kit as the documented SMP experiment.

### Workload v2t1 (reproducible net profile)
| build | workload | LTO+PGO exe sha256 | identity |
|---|---|---|---|
| r10fix1_v2t1_pc1 | v2t1 | e06e0348da4c6d4756cde5984f5c395c1b2055cca40489bf0630db5f6c75cd7a | OFF = lock pins, e19 + e9 = D8D90B68 pins d11..d22, plain = LTO+PGO: ALL OK |
| r10fix1_v2t1_pc2 | v2t1 | e06e0348da4c6d4756cde5984f5c395c1b2055cca40489bf0630db5f6c75cd7a (byte-identical) | OFF ALL OK |

Binding check v2t1: **PASS** (pc1 = pc2). Partial-training variant, 12k identity and speed: running.
