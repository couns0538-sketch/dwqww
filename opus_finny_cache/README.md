# opus_finny_cache — Finny-table-style lazy accumulator refresh cache on trial_w6

**Verdict: NOT APPLICABLE on trial_w6 — no engine code, by measurement, not by assumption.**

| item | value |
|---|---|
| branch | `opus-finny-cache-20261107`, based on parent **P** = `7ce10a05` (trial_w6 source). Independent of the SMP pack and of int8 |
| parent identity | P kit build pc1 = pc2 = `4181a589…6b6fb0` = trial_w6 byte for byte (`logs/parent/`) |
| reserved names | `FORGE_NNUE_FINNY` (compile-time, default 0), UCI `NnueFinnyCache` (default false). Fixed in SPEC §1; **used nowhere** |
| why no code | trial_w6's network has 768 king-independent inputs. Accumulators refresh only at search roots (searches × workers); the instrumented count found **0 in-tree refreshes** in bench 16, 300 FENs at depth 13 and 20 FENs at Threads 4. Refresh share ≈ 0.01-0.02 % of accumulator work (BENCH.md) |
| builds | none: compile-time 0 would be P itself (4181a589); there is nothing to put behind a compile-time 1 |
| cache identity verdict | **N/A**: no cache exists, so no bit-exactness or node-identity claim is made. The exactness rule a future implementation must meet is SPEC §3.3 |
| where the idea does pay | HalfKA K32H3^ (r10fix1 `7f79c349`, `EvalFileHalfKA`): king-bucketed with int16 accumulators and no refresh cache. The v3 branch (FB1) already has one. Owner decisions, INVENTORY.md |

## Files
- `SPEC.md`: names; the measured gate; the design for a king-dependent network (key, entry, exactness rule, full event table: king moves, captures, promotions, en passant, castling, null moves, make/unmake, newgame, net reload, Threads, thread isolation, discard); qualification list.
- `BENCH.md`: the refresh-count measurement (scratch exe sha256, FEN md5, counts, histogram).
- `INVENTORY.md`: parent, the existing caches and their owners, untouched packs (int8 2760434c, skipped NNUE packs).
- `IDEA_SOURCE.md`, `COMMANDS.md` (EXECUTED vs PREPARED-ONLY), `STATUS.md`, `REVIEW_LOG.md`, `MD5SUMS`, `SHA256SUMS`.
- `refresh_count_scratch_after_w6.patch`: the measurement-only instrumentation (never a candidate).
- `tools/`: `rc_make.ps1`, `rc_measure.ps1`, `o2_uci_lib.ps1`, `run_pinned.ps1`, `kit_build.ps1`.
- `logs/`: `refresh_count/` and `parent/`.

## Handoff
Code Review reads this pack as an evidence and decision record. No gate exe exists and none is to be queued. Next steps belong to the owners (INVENTORY.md).
