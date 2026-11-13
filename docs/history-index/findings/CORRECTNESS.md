# Correctness findings

Full reads behind this note are the lock record, the H512 rules paragraph, the fair-eval arithmetic section, and the security note. Per-position dumps, pin logs, and perft logs were inventoried and not read.

## Lock identity

`lock/combo29-20261110` @ `16833ecc03b425586f91f4c8834dea8807bf4c22`.

Pins and hashes: `forge-combo29/LOCK.md` (blob `4ae6a095ee3bbd2383c7c1c6049a2edde41ef58e`). The same blob is on the H512 tip. Net on bench nodes 312866 / 862329 / 3024920 / 12389307 / 34048354 at depths 11/13/16/20/22. Net off 375354 / 907205 / 2448617 / 13573040 / 24506465. Perft 5 = 4865609. Exe md5 `c0051c99695f48bf93272d96fe7548c3`, sha256 `E1284F7FC492C8FE1285797FDAE8988CF2F2926B33FCFEE7023D284D67D8802E`. Net md5 `22B4B9E2C61B37C0450F13A3A92C19B3`.

The lock note says a Linux GCC build reproduced those ten pins and perft, including a portable x86-64-v3 build, and that those binaries are not the lock exe. Sanitizers were not run. Source manifest `windows_build/SOURCE_INPUTS.sha256` is claimed to match 20 of 20 files. This index did not recompute the hashes.

`BADCAP_PREFIX` is present and not enabled. The note says clang_four is not this lock.

## Fair-eval arithmetic

From `fair_eval/REPORT.md`, on 12,000 FENs, against a diagnostic build of the lock source rather than the shipped exe:

- GCC plain diagnostic vs the clang diagnostic reference: 12,000/12,000, max error 0. Evaluation on this set did not depend on compiler or PGO.
- INT8 option off, and the v2 KB8 replica (ported, hot, and scalar): exact.
- INT8 on: 1,269/12,000 exact, max 29 cp, mean 3.207 cp, 64 sign flips. Hand-crafted term equal on all 12,000. Passed bounds that were fixed before the run.
- U8 and run 5 differ from s198 by design (mean 17.7 cp and 14.7 cp). That is not an error. SIMD equals scalar on 12,000/12,000.

The report's remaining gap: agreement on ten bench searches plus 12,000 positions is finite evidence, not a proof for every position. The shipped exe was not queried for static eval because it has no such command.

H512 parity and rules: 14,000/14,000 integer agreement and a short rules list (perft, mates, insufficient material, 50-move) equal to the lock. Not a substitute for the unread pin logs. Threads above 1 and sanitizers were not run on that path.

## Alias tips that look like correctness work and are not a new commit

These names are newer than their commit and point at work that is already on another branch. Read the commit once.

| Looks like | Actually is |
|---|---|
| `investigator/hourly-20261021-1000-no-new-finding`, `...-1100-qsearch-candidate-native`, `...-1200-terminal-zero-nodes-native` | `5101c2529d386b7c3a04ba9156a69ee34df6bb43`, OwnBook regression, 2026-10-20 |
| `investigator/hourly-20261020-1000`, `1100`, `1500-dedup`, `null-rule50-20261020-1200`, `ownbook-native-confirmation-20261020-1800`, and 24 `forge/*` names | `356e863dbd86d2ce24b8ee9486d7406f1d525480`, native CI pin of a pre-fix commit |
| `research/grokchess-tt-smp-seqlock-20261020-0505` and five other `research/grokchess-*` names from 2026-10-21 | `main` @ `5176ddf79ae15b76c08c4485d90ee5600ba30a1a`, the ten-file upload |

`investigator/qsearch-horizon-stalemate-20261020-1400` (`ab9c56000235bfbf3c1aaa1814111d264d3f0823`) and `investigator/terminal-zero-node-20261020-1300` (`7d4974f3ba613b8e50290ff6db05a3d9a98831f3`) have their own commits. They were not read. Their subjects claim a horizon-stalemate probe and a terminal `go nodes 0` handoff. Those two are real separate tips and belong in the next correctness batch, ahead of the aliases.

## Fix already recorded, not re-tested

The 2026-11-12 removal of `instrument_refresh_stats.py` and the tablebase path check are in `SECURITY.md`. History still contains the old files. Correctness work that checks out an old commit should expect `src` and `include` to be deletable by that script if something runs it.
