# R12 idea sources

- QA's R11 speed check (`QA_R11_SPEEDCHECK_20261030.md` md5 3bec98e6 on the box; PC copy
  `grok-pc\forge_push\qa_r11h2h\speed4_summary.txt`): LTO+PGO HalfKA exe 9E5CB644 12.1-12.4% slower than plain D8D90B68
  with a net loaded, 5-6% faster with no net; cause named by QA: the PGO profile never runs the net path.
- GCC manual, `-fprofile-use` / `-fprofile-partial-training` (GCC 10+): code not executed in the training run is optimized
  for size; partial training compiles never-executed functions as without profile feedback. The user asked for the
  partial-training variant (R12 item 2b).
- GCC manual, `-fprofile-update=single` / `-fprofile-correction`: multi-threaded training gives racy, inconsistent counts
  that -fprofile-correction smooths; this is why the Threads=2 part of workload v2 is not node-deterministic.
- Kit v2.3 (Engine Coder + CR + QA, `qa_ltopgo_al1_stage\kit_v23`): frozen workload v1, pc1 = pc2 exe sha256 rule,
  lp_check.py identity; v2.4 only adds a workload and two switches on top of it.
- Forge source r10fix1 (7f79c349): `bench` runs its own one-thread `Searcher(16)` with an exclusive TT lease, so the
  SMP code (shared-TT `lock_stripe` locking, helper threads) only runs in `go` with Threads >= 2.
- R5B lesson (byte copies of one exe can time differently on this PC): the A/A pairs use a byte copy of the exe.
