# Hand-off: exact pack to Code Review, then QA

This job queues nothing. Code Review reads first; QA alone schedules gates and publishes locks.

**Blocker: no channel.** This session reaches no Code Review or QA session or queue, and the job's prompt forbids queueing here. Couns forwards the exact pack: this folder, on branch `opus-syzygy-gaps-20261107`, at the commit named in `STATUS.md`.

## Check the pack first
```
git clone --filter=blob:none --no-checkout --branch opus-syzygy-gaps-20261107 https://github.com/couns0538-sketch/dwqww pack
cd pack && git config core.autocrlf false && git sparse-checkout set opus_syzygy_gaps opus_r13/p6 && git checkout
cd opus_syzygy_gaps && md5sum -c --quiet MANIFEST.md5 && sha256sum -c --quiet MANIFEST.sha256
```
Read `REPORT.md`, then `GAP_LEDGER.md`, `README.md`, `BENCH.md`, `REVIEW_LOG.md`.

## Code Review
- The patch to read: `patches/syzygy_gaps_after_p6.patch`. `patches/syzygy_gaps_after_w6p6.patch` has the same changed lines; one hunk has other context. `patches/syzygy_port_and_gaps_after_w6.patch` is P6 port + this change on the trial_w6 source, as one patch.
- The reviews in `REVIEW_LOG.md` were this job's own and are not Code Review: three by one Opus subagent, one bug hunt by a Fable subagent. Each was independent of the main agent's reasoning, but none had the role or the authority of Code Review.
- Judgement calls to look at:
  1. Store-side rule of `SyzygyRule50` bit 1: not at a root, not in qsearch. No failing scenario found, but the argument is by test, not by proof (`GAP_LEDGER.md`, Limits).
  2. Boundary walk inside `go`: budget 1000 moves, about 35 ms at worst on this PC. 919 of the 4569 purpose-built boundary rows stay undecided, mostly at clocks 60-89 (`GAP_LEDGER.md`, Limits). No false claim there, but the move may be worse. A higher budget costs latency at every such root.
  3. The deviation from the common rank convention at dtz + counter = 100 (`README.md`, Root ranks).
  4. WDL-only move filter: only the report is corrected.
  5. Cost of `SyzygyRule50` bit 1: a few true warm claims are withheld (`BENCH.md`).
  6. Unconfirmed, by reading only (bug hunter, `review/H1.md`): a mate score read from the hash at a much deeper ply than it was stored at can drift below the mate band into the TB band. It needs mates at a root ply above about 120. It is P6's behaviour, not this patch's, and was not tested.
  7. The claim harness judges a mate-band claim by the table's result at the node's clock (DTZ + clock), not by the mate distance. A mate claimed too long for the clock counts only when the result itself is wrong, so the counts at the two mate sites are lower bounds (`review/H1.md`, finding 2).

## QA
- Status of every on-path: **SEARCH/EVAL CHANGE, UNPROVEN.** No Elo claim. A QA SPRT is required; none was run or queued here.
- P6's own gates (USYZP, USYZPD4 and their confirms, idx 230-233 in the current `forge_gates.json`) have no results, so P6 itself is unproven as well. Ordering is QA's decision.
- Which exe: the live lock line is trial_w6, so the patch for a gate is `patches/syzygy_port_and_gaps_after_w6.patch` on the trial_w6 source, with the six trial_w6 defines and `FORGE_SYZYGY_TB_BOUNDS=1 FORGE_SYZYGY_ROOT_EXACT=1 FORGE_SYZYGY_RULE50=1`. This job built it with the kit v2.3 recipe (`tools/after_w6.sh`, hashes in `BENCH.md`), not with the clang recipe of `forge_clang_combo29_trial_w6.exe`, which is QA's.
- Options for the on-side: `SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3`, tables loaded. Defaults stay 0, so the same exe with the options at 0 is the P6 path.
- Expected pins are in `BENCH.md`: lock pins without tables at every option value; the P6 path with tables at options 0.
- `SyzygyProbeDepth` is not changed by this job. All fixtures use its default (1); only the option churn run (`tools/uci_churn.py`) sets other values.

## Where everything is
Paths are relative to this folder (`opus_syzygy_gaps/` on branch `opus-syzygy-gaps-20261107`, online at https://github.com/couns0538-sketch/dwqww/tree/opus-syzygy-gaps-20261107/opus_syzygy_gaps), except paths that start with `D:\`, which exist only on grok-pc.

### Read first
| file | what it is |
|---|---|
| [REPORT.md](REPORT.md) | the result on one page: gaps, costs, limits, proof that off means off |
| [GAP_LEDGER.md](GAP_LEDGER.md) | each gap with its evidence on the parent and with the switch; limits; rejected candidates |
| [README.md](README.md) | switches, semantics (WDL, rule 50, root ranks, score bands), and what each tool does |
| [BENCH.md](BENCH.md) | every number, hash and pin, each with the log behind it |
| [REVIEW_LOG.md](REVIEW_LOG.md) | reviews R1-R3, own checks B1-B6, bug hunt H1: each finding and its action |
| [STATUS.md](STATUS.md) | final state, rulings, jobs still running |
| [IDEA_SOURCE.md](IDEA_SOURCE.md), [tools/THIRD_PARTY_NOTICES.md](tools/THIRD_PARTY_NOTICES.md) | where ideas and oracles come from, licences |
| [MANIFEST.md5](MANIFEST.md5), [MANIFEST.sha256](MANIFEST.sha256) | checksums of every file in the pack |

### Patches, reviews, fixtures, tools
| folder | contents |
|---|---|
| `patches/` | `syzygy_gaps_after_p6.patch`: the change to review, on the P6 tree. `syzygy_gaps_after_w6p6.patch`: the same changed lines on trial_w6 + P6 port. `syzygy_port_and_gaps_after_w6.patch`: P6 port + this change on the trial_w6 source in one patch, the one for a gate build |
| `review/` | `R1.md`, `R2.md`, `R3.md`: the reviewer's three reports. `H1.md`: the bug hunter's report |
| `fixtures/` | input rows of every fixture: `clock.fens`, `f1.clock.tsv`, `f1.toggle.fens`, `s1.*.fens` (castling, clock 100, en passant, promotion, repetition), `zz2roots.fens` and `zz_found.tsv` (zugzwang), `review7.fens`, `read.k0.tsv` and `read.mate.tsv` (read-side rows, H1). `TABLES.sha256`: hashes of all 290 table files |
| `tools/` | every script, 80 files; README.md, "Test tools", says what each one does |

### Logs (`logs/`: compact results; the row files behind them are under `D:\forge_jobs_20261107\opus1\out\`)
| topic | files |
|---|---|
| frozen head, off means off | `final_chain_989399b.txt` (the final chain, one line per step), `final_989399b.txt` (freeze proof), `kit_buildA_c989399b.txt`, `kit_buildB_c989399b_pc1.txt`, `kit_p6_parent_pc1.txt` (kit builds and hashes), `identity_buildB_c989399b.txt` (node identity), `macro_combos_989399b.txt`, `lint_989399b.txt`, `repro_989399b.txt` (tree rebuilt from the pack alone), `pins_p6_plain_off.json` and `pins_p6_plain_tb.json` (parent pins without and with tables) |
| trial_w6 line | `after_w6_989399b2.txt` (ALL CHECKS PASS), `after_w6_989399b2.arms.txt` (changed lines against the speed switches), `kit_w6p6_parent_989399b2.txt`, `kit_w6p6_B_989399b2.txt`, `after_w6_989399b_rejected.txt` and `after_w6_989399b_rejected.patch.log` (the first attempt, rightly stopped: REVIEW_LOG.md B3) |
| suite, frozen head all on against the parent | `suite_v9on.txt`, `suite_parent.txt`, `suite_v9on_special2.txt`, `suite_v9on_move_quality.json`, `suite_v9on_root_boundary_full.json`, `suite_v9on_uci_boundary_full.json`, `suite_parent_root_boundary_full.json`, `suite_parent_uci_boundary_full.json` (all 4569 boundary rows), `partial_v9on.txt` (partial and damaged table sets), `info_v8.txt` (per-bit numbers) |
| the gaps on the parent | `claims_p6_d10_3k.txt` (interior claims, 3000 roots, depth 10), `root_p6_clock.txt` and `root_p6_clock.json` (root checks on the clock fixture, 19,905 roots), `e1_p6_d8.json` and `e1_p6_d10.json` (move quality, 200,000 roots), `c1_full.txt` (P6's own table tests: 36,825 checks, 0 failures) |
| stress | `san_v9.txt` (UBSan and ASan), `flips_v9.txt` (damaged tables under ASan), `green_v8.txt` (missing child tables), `churn_v9.txt` (option churn), `pred1_v9.log` and `pred2_v9.log` (a root's entry read later at another clock) |
| bug hunt, read-side rows | `read_side_runs.txt` (one line per run), `read_side_m8_k0_wrong.txt` and `read_side_m7_mate_wrong.txt` (sample wrong claims of the two mutants), `read_side_harness_r300.txt` (harness unchanged), `read_side_r1_partial.txt` (the full 1500-row run, unfinished) |

### Only on grok-pc (too large for git)
Tables: `D:\syzygy345` (hashes in `fixtures/TABLES.sha256`). Job root: `D:\forge_jobs_20261107\opus1\out\`:

| folder | contents |
|---|---|
| `src\cand` | the candidate source tree (git, head 989399b, parent ded9684 = the P6 tree); `src\p6_port` is the parent tree, `src\w6p6g_989399b2` trial_w6 + port |
| `builds\` | kit builds (Build A, Build B pc1 and pc2, trial_w6 line) with their `SUMMARY.txt` and exes |
| `exe\` | test exes: claim harness builds, root tools, plain builds, mutants |
| `qual\` | suite runs: `v9on` = frozen head all on, `p6` = parent, `info_v8` = per bit |
| `exp\` | experiments: `claims`, `warm`, `exact` (oracle rows), `partial`, `read` (read-side rows and runs), `hunt` (churn, missing child tables) |
| `ident\`, `san\` | identity row files; sanitizer builds and runs |
| `tb\`, `oracle\` | damaged and partial table folders; Fathom builds (oracle only) |
| `review\`, `hunt_agent\` | the reviewer's and the bug hunter's working folders |
| `logs\` | full logs of every chain |
