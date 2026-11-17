# Evidence index

Everything in this folder backs a specific claim in `../FINDINGS.md`. Nothing here is
hand-typed; every file is the direct output of a script in `../scripts/`.

## `logs/`

| file | what it shows | finding |
|---|---|---|
| `pins-all-builds.txt` | all 11 LOCK.md pins + perft 5, exact, on native / v2 / v3 at depths 11/13/16/20/22, net on and off | §1 |
| `build_all.txt` | the 4 successful builds and the **2 expected compile failures** with their `#error` text | §2 |
| `identity-sweep.txt` | 120 positions × 5 fields (bestmove, nodes, score, score-kind, depth), 3 builds, 0 mismatches | §3 |
| `final-table.txt` | the slot-corrected ratio table with CI95, direction share, and per-pair implied slot bias | §4 |
| `switch-decomposition.txt` | direct A/B of the two switches OFF vs ON, plus the arithmetic showing subtraction does **not** telescope | §4 |
| `bail.txt` | 8 drawn-root bail cases across 3 builds, all identical, with the twofold and FEN controls | §5 |
| `isa-disassembly.txt` | ymm/zmm/k-reg/pext/popcnt counts per binary, with an existence guard so a failed disassembly cannot read as zero | §7 |
| `qemu-execution.txt` | emulated-CPU execution: v2 on Nehalem produces every pin; the AVX-512 limitation of qemu stated first | §7 |
| `cpu-levels.txt` | what each emulated CPU actually advertises, so the ISA labels are measured rather than assumed | §7 |

## `timing/`

`arms/` holds both ABBA arms for every comparison as raw per-position JSON
(`A_med`, `B_med`, all four wall times, node counts and bestmoves per side).
`final-table.txt` and `final-timing.json` are the derived summary.

The pairs, each with a forward arm (`A,B`) and a reverse arm (`B,A`):

| comparison | forward | reverse |
|---|---|---|
| A/A control (native vs native) | `abba-AA.json` | — |
| v2 vs native | `abba-native-v2.json` | `abba-rev-v2.json` |
| v3 vs native | `abba-native-v3.json` | `abba-rev-v3.json` |
| v3+PEXT vs native | `abba-v3pext.json` | `abba-rev-v3pext.json` |
| v4 both-on vs native | `abba-v4both.json` | `abba-rev-v4both.json` |
| v4 both-off vs native | `abba-v4-avx2-nopext-nopext.json` | `abba-rev-v4-avx2-nopext-nopext.json` |
| v4 PEXT-only vs native | `abba-v4-avx2-pext.json` | `abba-rev-v4-avx2-pext.json` |
| v4 ZMM-only vs native | `abba-v4-zmm-nopext.json` | `abba-rev-v4-zmm-nopext.json` |
| switches OFF vs ON (direct) | `abba-sw-fwd.json` | `abba-sw-rev.json` |
| **v2 forward repeat** (drift check) | `abba-v2-repeat.json` | — |

`abba-v2-repeat.json` is the evidence for the between-run drift limit in §4: the same
comparison, re-run, gives 1.1299 where the first run gave 1.1453.

## `bail.json`, `identity-sweep.json`

Machine-readable versions of the two logs, so the claims can be re-derived without
re-running the engine.

## `pos120.fens`

The 120-position corpus used for all timing and identity work — the first 120 lines of
`forge-combo29/tests_kimi5_job3/first200.fens` from branch
`origin/for-fable-and-opus/kimi5-work`, deduplicated (120 unique). Named here so the
numbers cannot be separated from the set that produced them.
