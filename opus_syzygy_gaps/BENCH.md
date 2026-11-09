# BENCH - opus-syzygy-gaps-20261107, frozen head 989399b

**Label: SEARCH/EVAL CHANGE, UNPROVEN.** With an option on, the search changes. No games were played and there is no Elo claim: QA's SPRT decides. Nothing is queued. NPS was not measured (the prompt forbids quiet ABBA runs here, and NPS is not Elo).

Compact logs are in `logs/`. Row files stay in the job root under `out/`, paths below.

## What was measured
| item | value |
|---|---|
| candidate | `out/src/cand`, commit 989399ba6a7f, parent ded9684 (the P6 tree) |
| `patches/syzygy_gaps_after_p6.patch` | md5 de4da16a5be55242422942de3b3e18de, sha256 7ebe07148ea336eb2d4d6e30571e14959c98ee27605b42b697bcb7bfe0fb4f29 |
| `patches/syzygy_gaps_after_w6p6.patch` | md5 bac6d5a57d016cd55397d4052253afaa, sha256 84443a828f90be4f4e1323f68ed2990ae5d3c29408cf62f077203d0262947e7c |
| `patches/syzygy_port_and_gaps_after_w6.patch` | PENDING |
| parent | lock source d4f43124 + `opus_r13/p6/syzygy_port.patch` (md5 4342d24f) = kit exe sha256 150374ff4b9132b99b48e9ba6a51b36b89e22014c61cec3053d1f4f17b87d99f |
| Build A (macros off) | sha256 150374ff... = the parent, byte for byte |
| Build B (macros on, options 0) | sha256 db91700e745281a525b17d1553de40874da94185f1941a027dad85699132da46, md5 4730b028572373c172b65561ea8a8e80, pc1 = pc2 |
| compiler | g++ 15.2.0 (MSYS2 Rev14) |
| recipe | QA kit v2.3 lines, frozen workload v1 (sha256 checked by `tools/kit_build.ps1`): `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin`, then PGO |
| tables | `D:\syzygy345`, 145 WDL + 145 DTZ, all 290 file hashes = the project's list (`fixtures/TABLES.sha256`) |
| all on | `SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3` |
| placement | every run Idle on CPUs 12-15 (0xF000), Threads 1 unless a line says otherwise |

## OFF identity: frozen head against the parent
All IDENTICAL or EQUAL. Log: `logs/final_989399b.txt`, `logs/identity_buildB_c989399b.txt`.

| check | result |
|---|---|
| preprocessed source, macros off | ALL EQUAL. With macros on, 2 units differ (search, uci): expected |
| Build A against the parent exe | byte-identical (OFF verdict at compile time) |
| Build B pc1 against pc2 | byte-identical |
| macro combinations (each macro alone and together) | all compile, `logs/macro_combos_989399b.txt` |
| clean-room lint on the patch | CLEAN, `logs/lint_989399b.txt` |
| Build B pins, no tables, net on and off, perft | PINS ALL EQUAL: on 312866 / 862329 / 3024920 / 12389307 / 34048354, off 375354 / 907205 / 2448617 / 13573040 / 24506465, perft 4865609 / 193690690 |
| Build B pins, tables | PINS ALL EQUAL, P6 path: 313631 / 866959 / 2460490 / 11465604 / 31972996 |
| warm identity, no tables | IDENTICAL, 25,717 lines, 2000 searches, 80 state changes |
| warm identity, tables, 12k FENs | IDENTICAL, 25,988 lines, 2000 searches |
| warm identity, tables, clock fixture | IDENTICAL, 43,642 lines, 2000 searches |

Cold identity of Build B against the parent, depth as in `tools/identity_runs.ps1`:

| set | rows | different | nodes on both |
|---|---|---|---|
| net_on (12k FENs, depth 13) | 12000 | 0 | 1,534,521,761 |
| net_off | 12000 | 0 | 1,578,228,148 |
| tb_12k | 12000 | 0 | 1,464,257,271 |
| tb_roots (5-man, 3-4 piece tables, depth 10) | 30000 | 0 | 378,022,151 |
| tb_clock (depth 6) | 19905 | 0 | 16,672,350 |
| tb_promo | 4000 | 0 | 3,127,020 |
| tb_ep | 2000 | 0 | 1,107,330 |
| tb_rep | 2000 | 0 | 1,076,108 |
| tb_castle | 499 | 0 | 849,810 |
| tb_clock100 | 500 | 0 | 0 (the root reports a draw and does not search) |

**Reproduction from the pack** (`tools/repro_from_pack.sh`, `logs/repro_989399b.txt`): lock source + P6 patch + pack patch, both with `-F0`: fresh tree = `out/src/cand` HEAD; macros off and macros on rebuild the same exe hashes.

## Bench per option, Build B, depths 11 / 13 / 16 / 20 / 22
Without tables, every option value below gives the lock pins at all five depths. With `D:\syzygy345`:

| option | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|
| all 0 (P6 path) | 313631 | 866959 | 2460490 | 11465604 | 31972996 |
| SyzygyTbBounds=1 | 313659 | 867107 | 2458296 | 11661537 | 31281025 |
| SyzygyTbBounds=2 | 313632 | 866960 | 2469380 | 10687206 | 27772621 |
| SyzygyTbBounds=4 | 313631 | 866962 | 2461660 | 11820857 | 27639447 |
| SyzygyTbBounds=7 | 313659 | 867107 | 2458296 | 10663626 | 26408664 |
| SyzygyRootExact=1, 2 or 3 | 313631 | 866959 | 2460490 | 11465604 | 31972996 |
| SyzygyRule50=1 or 3 | 313631 | 866959 | 2460490 | 11195442 | 33899273 |
| SyzygyRule50=2 | 313631 | 866959 | 2460490 | 11465604 | 31972996 |
| all on | 313659 | 867107 | 2458296 | 10663627 | 26324444 |

Liveness: `SyzygyRootExact` never shows in the bench, because no bench root sits inside the tables, and `SyzygyRule50` bit 2 only acts when the rule option changes. Their evidence is the fixtures below, not the bench. These numbers are node counts, not strength: a lower count says nothing about Elo.

## Fixtures: parent against all on
Oracles: python-chess and Fathom for table values; `tools/oracle_exact.py` for the 50-move boundary, which does not use the DTZ rounding flag. The parent numbers are plain builds with the same nodes as kit exe 150374ff. The all-on numbers are the plain build of the frozen head, sha256 b5ce3df3969536890ca3c7eac1ca7b56030a411e97ae2964f0e84fb0cad2b509. Logs: `logs/suite_parent.txt`, `logs/suite_v9on.txt`, `logs/suite_v9on_special2.txt`.

PENDING: suite table.

## Per bit (information, no verdict)
PENDING

## Warm table, moves played
PENDING

## Move quality
PENDING

## Stress
PENDING

## trial_w6 line
PENDING

## Not measured
- Strength. No games, no SPRT, no tuning.
- Speed. No ABBA. The kit profile is trained with the options off, so on-paths are cold-optimised: say so in any comparison.
- 6-piece tables: none on this PC. The interior fixtures use 5-man roots with 3-4 piece tables loaded as the same situation one piece lower.
- The clang recipe of the live lock exe (`forge_clang_combo29_trial_w6.exe`, E1284F7F): see the trial_w6 line.

## Evidence paths (job root `D:\forge_jobs_20261107\opus1`)
PENDING
