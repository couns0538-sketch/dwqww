# INVENTORY — reconciliation before coding (opus2, 2026-11-09, Vienna)

Read-only sources only: GitHub (gh api / ls-remote), the local repo `D:\grok-pc-data\dwqww` (git show only, no fetch or
write), QA's lock records under `C:\Users\Administrator\grok-pc\forge_push` (read only) and `D:\forge-qa` (grep only).
`F:\ospd` and `C:\ospd_hunt` were not read.

## Parent (recorded, verified)
| item | value |
|---|---|
| lock source | git `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (FD3A5190's source). Its `include/`+`src/` (20 files) match the lock's `SOURCES.sha256` 20/20; the on-disk lock copy is CRLF, same content |
| trial_w6 patch | `opus_speed/patches/trial_w6.patch` @ opus-speed-20261105 `1ad0d295`, md5 `5786e9b87a0c3cec4707af521cec85bc`. GNU patch -p1 -F0 applied cleanly |
| src_kit flips | TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SEARCH_SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1, NNUE_ZMM=1 (one `#define N 0` line each) |
| **parent P** | commit `7ce10a05cf8704d5b43b84e214657a492f5ae690` on this branch |
| P kit build | QA kit v2.3 `-Expose` (Idle copy, see BENCH.md): **pc1 = pc2 = `4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = trial_w6 byte for byte**, md5 331EA9BF… Pins net on, perft and node identity: ALL OK |
| baseline exe | `C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`, same sha256, hashed before use |

Newer lock note (not used as parent): CURRENT_LOCK.json moved on 2026-11-08 to `forge_clang_combo29_trial_w6.exe` (E1284F7F…, clang LTO+PGO). It is bit-exact vs trial_w6 with the same pins and is not byte-reproducible (PDB paths). Per the job prompt the parent is trial_w6. A port to combo29 is out of scope; QA decides.

## Shared-TT / SMP history and branches
| branch / item | finding | relation to this pack |
|---|---|---|
| `forge/audit-tt-race-20261019` (439f2103) | "isolated ThreadSanitizer probe for Forge 6.4 shared TT races" | the plain shared TT had TSan races, which is the origin of today's design |
| `forge/tt-coherence-20261019` (ec6a8dff), `tests/tt_coherence_tests.cpp` in the lock | striped locks (1024 alignas(64) mutexes), opaque TTProbe handle with epoch, ExclusiveLease, 12 coherence groups with torn-tuple detectors | the lock's TT is race-free **because it locks**. A lockless variant does not exist anywhere and is this pack's job |
| `research/grokchess-tt-smp-seqlock-*`, `investigator/tt-smp-publication-*`, `forge/candidate-tt-smp-snapshot-*` | October research and snapshot branches on the older grokchess/Forge 6.x line | ideas only; the seqlock route is not taken (payloads would have to be atomic anyway, see SPEC) |
| trial_w6 `FORGE_SPD_TT_NOTLS` | `tt_owned_` + probe_owned/store_owned skip lock_stripe on the lease thread (Threads 1) | kept unchanged; the lockless dispatch is a third branch in front of it |
| `opus-tt-replace-cache-20261106` (87bf3c7e) | TtReplaceCache: default-OFF `FORGE_SPD_TT_REPLACE_CACHE` on trial_w6, patch md5 aba037b2, gate ec1cb55e, ON node-identical, "ready for Code Review" | **textual overlap**: same probe replacement loop in search.cpp, plus search.hpp and uci.cpp. Independent packs; a later stack needs a hand merge (not done here) |
| `opus-tt-cut-node-20261105`, `opus-nmp-tt-capture-20261105` | search changes using TT data (CR_PASS receipts exist) | no overlap in TT storage code |
| SmpV2 (FB2 J5 `fable-fb2-j5`, `astra2-smpv2-mate`, `astra3-smp-mate-rootcause`; Astra owns its mate selection) | helper diversity + deepest-result selection | **not present in trial_w6** (no `SmpV2`/`Smp*` option in P). Untouched |
| `opus-r3-smp`, `opus-r3-smpq` | SmpHelpersPastDepth: no time-to-depth gain | ideas only; not in trial_w6 |

## Int8 pack 2760434c (identified; not touched)
- Receipt `C:\Users\Administrator\grok-pc\forge_push\CR_PASS_nnue_int8_vnni_pgo_on_19ed0385.ok` reads "PIN-MATCH RECORD after CR APPROVE":
  - pack `crew-nnue-int8-vnni-pgo-on-20261106`, tip `e57f8f61`, **CR=2760434c**;
  - exe `forge_nnue_int8_vnni_gate_19ed0385.exe`, sha256 19ED0385…2497;
  - OFF pins = lock pins; ON pins (NnueInt8Vnni=1) 326976/760289/3282449/11638305/27267033, i.e. an eval change;
  - UCI smoke PASS. Engine QA int8-vnni2 2026-11-06.
- Branch `opus-nnue-int8-vnni-20261106`, `opus_nnue_int8_vnni/STATUS.md` (last update 2026-11-06), "Unproven / not claimed": **Threads > 1 not tested with NnueInt8Vnni=1 (no Threads 2-4 soak)**. Its BENCH.md also has a CR/QA item about plain -O3 ON speed.
- These are gaps for the int8 owner. They are not needed for this handoff and were not closed (job rule). This pack does not stack on int8.

## Skipped as instructed
The FT-accum AVX2, skip-zero L1 and int16 vpdpwssd packs are not touched. They were not found under those names in `forge_push` queue/QA files or in `D:\forge-qa` (grep only).

## Name reservations
`FORGE_SMP_LAYOUT`, `TtLockless`, "lockless" and "SMP_LAYOUT" have no matches in QA files (`forge_push` queue/QA docs, `D:\forge-qa`) and none in the trial_w6 source. The names are free and fixed in SPEC.md.

## Job-wide facts used by the plan
- PC: Ryzen 7 9850X3D, 16 logical CPUs with SMT pairs (0,1)…(14,15).
  - At 18:3x Vienna, CPUs 0-3 were 100 % busy and 4-15 nearly idle.
  - No process was pinned to 12-15; this job uses 12-15 at Idle (user instruction).
- No local TSan: MinGW g++ 15.2 and MSVC have none. The lock tree's `.github/workflows/opus-ci.yml` runs `opus_round1/ci/run_ci.sh {release,asan,tsan}` on ubuntu-24.04 for `opus-*` pushes, so TSan evidence comes from CI.
- The trial_w6 tree cannot build at `-march=x86-64-v3` with its defaults, because `FORGE_SPD_NNUE_ZMM=1` has `#error` without AVX-512F. CI on this branch therefore passes `-DFORGE_SPD_NNUE_ZMM=0` (CI only; the switch touches no TT/SMP code).
