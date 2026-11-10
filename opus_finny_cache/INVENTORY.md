# opus_finny_cache — INVENTORY (ownership and implementations checked before any code; read-only)

## Parent (same recorded parent as the SMP pack; this branch is independent of it)
- Parent **P** = `7ce10a05cf8704d5b43b84e214657a492f5ae690`: lock source `d4f43124` + `opus_speed/patches/trial_w6.patch` (md5 `5786e9b87a0c3cec4707af521cec85bc`, opus-speed-20261105@1ad0d295), with the six src_kit default flips.
- Kit v2.3 `-Expose` build of P: pc1 = pc2 = `4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0`, which is trial_w6 byte for byte (`logs/parent/SUMMARY_p*.txt`).
- d4f4312's `include/`+`src/` match the lock's SOURCES.sha256 20/20.

## Refresh caches that already exist (owners)
| implementation | where | status | relation |
|---|---|---|---|
| NNUE v3 refresh cache: `refresh_from_pieces`, keyed (perspective, bucket, flip), with 12 piece bitboards | branch `fable-nnue-arch` (FB1, Fable), `src/nnue_v3.cpp`, option `NNUEArch` | exists; v3 architecture only | not in trial_w6. Owner FB1 |
| HalfKA K32H3^ (32 mirrored king buckets × 3 material states; int16 accumulators) | r10fix1 = git `7f79c349` (`src/nnue_halfka.cpp`, option `EvalFileHalfKA`; exes 9E5CB644 / D8D90B68) | `refresh(board, perspective, out)` + incremental `apply`; **no refresh cache** (no cache / finny in the source) | king-bucketed: bucket changes (king moves across buckets, the opponent's queen gained or lost) force refreshes. **This is where a Finny cache would pay** (SPEC §3). Not trial_w6-based, so it needs its owner's decision (Opus R10 / R11 NNUE pipeline) |
| trial_w6 default net (768 → H256, float, residual on HCE) | parent P `src/nnue.cpp`, `src/search.cpp` | lazy incremental updates; refresh only at search roots | Finny cache not applicable (SPEC §2, BENCH.md) |

## Packs not touched (job instructions)
- Int8 pack: `crew-nnue-int8-vnni-pgo-on-20261106`, tip `e57f8f61`, **CR=2760434c**, exe `forge_nnue_int8_vnni_gate_19ed0385.exe`. Receipt: `C:\Users\Administrator\grok-pc\forge_push\CR_PASS_nnue_int8_vnni_pgo_on_19ed0385.ok`.
  - ON is an eval change (ON pins differ).
  - The owner's STATUS lists as unproven: "Threads > 1 not tested with NnueInt8Vnni=1".
  - Recorded for the owner; not closed here.
- The FT-accum AVX2, skip-zero L1 and int16 vpdpwssd packs are skipped as instructed; they are not touched and not stacked.
- The SMP pack `opus-smp-layout-20261107` is independent: this branch starts from P, not from it.

## Names
`FORGE_NNUE_FINNY` and `NnueFinnyCache` have no matches in QA's files (`forge_push` queue/QA docs, `D:\forge-qa`) and none in the trial_w6 source. They are reserved in SPEC.md §1 and used nowhere.
