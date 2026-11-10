# opus_smp_layout — BENCH (evidence: everything here was EXECUTED; prepared-only commands are in COMMANDS.md / SCALING_PLAN.md)

Machine: AMD Ryzen 7 9850X3D (8 cores / 16 logical CPUs, SMT pairs (2k, 2k+1)). Every local run is pinned to CPUs 12-15 at Idle, i.e. two physical cores on a shared PC, while CPUs 0-3 run other work. Times are Vienna (HTTPS Date header). Compiler: MSYS2 g++ 15.2.0 (Rev14); CI: g++-14 14.2.0 on ubuntu-24.04.

## 1. Identity of the builds (EXECUTED)
| build | source | kit v2.3 `-Expose` LTO+PGO exe sha256 (pc1 = pc2) | node identity in the kit |
|---|---|---|---|
| parent P | `7ce10a05` | `4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = trial_w6 (md5 331EA9BF…) | OFF pins, perft, bench_fens: ALL OK |
| **OFF** (compile-time 0), final | **`0599271`** as is (tags s0c, s0d) | **`4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = P byte for byte** | ALL OK |
| **GATE** (compile-time 1, `TtLockless` default false), final | **`0599271`** + the one define line flipped (s1c, s1d) | **`541e8b3d4333b99044ccafa7bcda82a1b5bf42a561eaf3b043b9871ed9faea1b`** | OFF: ALL OK; `TtLockless=true`: ALL OK (bench d11-22 = pins, perft = pins, plain = LTO+PGO), "IDENTICAL to OFF" |
| OFF, pre-review | `893b78d` (s0a, s0b) | `4181a589…` = P | ALL OK |
| GATE, pre-review (superseded by the R1 fixes) | `893b78d` (s1a, s1b) | `6c07563b8dfdeca2109c62e0d15df2877f62ca4cf084bc39c4f810c6bdecfe91` | OFF and `TtLockless=true`: ALL OK |

- Macro-0 preprocessing: `g++ -E -P` with the kit flags, blank lines stripped, is identical to P for all 8 units (`tools/pp_identity.ps1`; runs `out\pp\wip1_macro0` and `out\pp\fix1_macro0`).
- **Reproduction from the published artifacts.** This was the bug-hunt check, 20:4x Vienna. Steps: a fresh `git archive 7ce10a05 include src`, then `patch -p1 -F0 < smp_layout_after_w6.patch`, which gives the `0599271` tree byte for byte (`diff -r`), then the one-line flip to 1, then the kit. Result: **`541e8b3d…` again**: a third build (tag `rpg`) of the identical gate exe.
- The plain twins differ from P's plain twin only in PE bytes 137-138 and 217-218 (timestamp and checksum; 4 bytes, `cmp -l`).
- Kit: QA kit_v23 copy at Idle, without termination (IDEA_SOURCE.md). Wrapper `tools/kit_build.ps1`. Logs in `logs/kit/`.

## 2. Layout measured (EXECUTED)
`tools/layout_probe.cpp`, built against each tree with the kit flags at -O2. Logs: `logs/layout/P_layout.txt`, `logs/layout/G_layout.txt` (gate = final `0599271` source, macro 1).

| item | parent P (macro 0) | gate (macro 1, final) |
|---|---|---|
| sizeof / alignof Worker | 377664 / 64 | 377728 / 64 (+64 B per worker) |
| `nodes_` offset, line | 377496, line 5898 | 377536, line 5899 |
| members sharing `nodes_`'s line | root_effort_count_, pondering_, start_, **local_nodes_** (the owner writes it every node), all_workers_, node_limit_, node_limit_specified_ | **none** |
| `local_nodes_` | same line as `nodes_` | 377600, line 5900 (its own neighbours: the owner's fields) |
| 4 heap workers (`make_unique<Worker>`): nodes_ and local_nodes_ on the same line | YES for all 4 | **no** for all 4 |
| SharedSearchState: stop / ponder_hit_ns | line 1025, alone (the 65,600 B TT object ends at line 1024): **no change needed** | unchanged (TranspositionTable 65600 B in both) |
| distance between heap workers | megabytes apart (no adjacency between workers) | the same |
| TT cluster sizes | TTCluster 64 / 64 | TTCluster 64 / 64; TTLocklessCluster 64 / 64 |

Only the measured cross-thread line changed. Nothing else is padded.

## 3. Tests (EXECUTED)
| test | where | result |
|---|---|---|
| `forge_tt_lockless_tests` | native, CPUs 12-15, 1.5 s per config | round trip; differential: 300,000 probes and 224,119 hits with tables equal; contention, 4/8 threads × 1/4/16 clusters: **0 incoherent hits in 453,850,112 probes (75,459,423 hits)**; positive control (unvalidated two-word table): **1,673,288 incoherent hits**, so the fixture can detect tearing; lifecycle OK |
| `forge_smp_lifecycle_tests` | native | Threads 1/2/4/8 × both modes: every best move legal; stop, ponderhit and lifecycle cases bounded; T1 three-way identity (shared / exclusive / lockless) equal cold and warm on 6 FENs |
| `forge_tt_tests` (existing 12 groups) | native, macro 1 | PASS |
| **CI run 42677341394 (final `0599271`)** | ubuntu-24.04, g++-14 | **release**: macro-1 exe pins ALL OK; **`TtLockless=true` pins ALL OK** (uci_check `--opt`); **default macro-0 build** pins ALL OK, with no `TtLockless` option; macro-1 advertises `TtLockless type check default false`. **TSan**: contention 53,762,560 probes / 8,940,567 hits, **0 incoherent**; gating positive control 5,163,173 hits / **500,206 incoherent**; lifecycle (incl. the MINOR-1 regression) PASS; real TSan engine over UCI, TtLockless false/true × Threads 2/4: exit 0, 5 bestmoves each; **"TSan: 0 reports"**. ASan+UBSan green. Known-failure check PASS |
| CI run 42682884789 (`8beb10e`; engine = `0599271`, CI hardening only) | ubuntu-24.04, g++-14 | release: macro-1, `TtLockless=true` and macro-0 pins ALL OK; option-advertisement checks (output captured first) OK; TSan: "0 reports"; ASan+UBSan green |
| native `0599271` tests | CPUs 12-15 | tt_lockless: 0 incoherent in 437,689,856 probes (72,789,797 hits), control 2,462,613 incoherent (gating); smp_lifecycle incl. `direct_worker_after_toggle` PASS; tt_coherence 12 groups PASS |
| CI run 42673707949 (`893b78d`) | ubuntu-24.04, g++-14 | release: identity ALL OK (pins, perft, FMA 0), tests PASS; ASan+UBSan: PASS, no report; **TSan: both new tests PASS, "TSan: 0 reports"**; known-failure check PASS (only the 4 known forge_tests lines) |
| CI run 42674616047 (`4a8f12b`; engine sources = `893b78d`, 0-line diff) | ubuntu-24.04, g++-14, TSan build + `opus_round1/opus2_smp/tsan_extra.sh` | **under TSan**: contention 4/8 threads × 1/4/16 clusters gave 47,133,184 probes and 7,793,150 hits with **0 incoherent**; positive control 3,898,550 hits with **464,076 incoherent** (the fixture detects tearing under TSan too); lifecycle PASS; **real TSan engine over UCI** (go movetime / nodes / infinite+stop / ponder+ponderhit / Clear Hash / Hash / Threads / ucinewgame / quit) with TtLockless false and true at Threads 2 and 4: exit 0 and 5 bestmoves each; **"TSan: 0 reports"**; release and ASan+UBSan green |

## 4. L3 / L3b identity at Threads 1
### L3: full fens12k, cold (EXECUTED)
Setup: `tools/identity_check.ps1 -Mode cold`, `fens_12k_v2.txt` (md5 e7dbf2c8…), `go depth 13` with `ucinewgame` before each FEN, OwnBook false. Rows are (i, depth, score, nodes, bestmove). The body sha256 covers the 12,000 rows only; the run header with exe sha256 and options is in `logs/l3/L3_summary.txt`. P's reference rows are `logs/l3/P_4181a589_net*.cold.body.tsv`.

| exe | options | net on body sha256 | net off body sha256 | verdict |
|---|---|---|---|---|
| P `4181a589` (= trial_w6, = OFF build) | — | `0719943326d6b030…` | `e25cac43a12bf3bc…` | reference: 12,000 rows, 12,000 distinct |
| **gate `541e8b3d` (final)** | `TtLockless=false` | `0719943326d6b030…` | `e25cac43a12bf3bc…` | **IDENTICAL to P** (12,000 / 12,000 both) |
| **gate `541e8b3d` (final)** | **`TtLockless=true`** | `0719943326d6b030…` | `e25cac43a12bf3bc…` | **IDENTICAL to P** (12,000 / 12,000 both) |
| gate `6c07563b` (pre-review) | `TtLockless=false` | `0719943326d6b030…` | `e25cac43a12bf3bc…` | identical to P (superseded build) |

### L3b: warm table (EXECUTED)
One session per exe, no `ucinewgame`:
- `bench 1` and `go perft 1` first;
- then 1,000 FENs with `go nodes 20000`;
- every 25 FENs one change from the cycle Hash 1 / Hash 64 / Clear Hash / UseNNUE false / UseNNUE true / Hash 16 (40 changes);
- `bench 13` last, which must equal its pin.

The normalised transcript (nps/time removed) is compared byte for byte. Logs: `logs/l3b/L3b_summary.txt`; reference transcript `logs/l3b/P_4181a589_warm.body.txt`.

| exe | options | body sha256 | verdict |
|---|---|---|---|
| P `4181a589` | — | `618d5d3539e01c6b…` | reference: 10,680 lines |
| gate `541e8b3d` | `TtLockless=false` | `618d5d3539e01c6b…` | **IDENTICAL** |
| gate `541e8b3d` | **`TtLockless=true`** | `618d5d3539e01c6b…` | **IDENTICAL** |

### Liveness of `TtLockless` (EXECUTED; `tools/liveness_check.ps1`, `logs/live/liveness.txt`)
A node-identical option shows up as "IDENTICAL to OFF" in the kit. Its documented side effect proves it is live.

Threads 1, depth 12:
- legacy: cold a1 = 53,479 nodes; warm a2 = 4,139; after Clear Hash a3 = 35,964;
- lockless: b1 = 53,479 and b2 = 4,139 (= legacy);
- after `setoption TtLockless false`: b3 = 35,964 = a3. The toggle emptied the table exactly as Clear Hash does.

**LIVENESS: PASS.**
## 5. Race / stress (EXECUTED)
### Sanitizers (CI, Linux)
- TSan: "TSan: 0 reports" in all three CI runs (§3). The final run 42677341394 (`0599271`) covered:
  - the unit fixtures (0 incoherent, with a gating positive control);
  - the lifecycle tests at Threads 1/2/4/8;
  - the real engine over UCI with `TtLockless` false and true at Threads 2 and 4.
- ASan+UBSan: green, no report.
- Scope: TSan proves absence of reports **on the executed paths only**. It is not a "race proof".

### UCI lifecycle stress on the final gate `541e8b3d` (native, CPUs 12-15; Threads 8 = oversubscribed smoke)
Tool: `tools/uci_lifecycle_stress.ps1`. Every bestmove is checked by the engine's own `go perft 1` on the same position. isready latency is measured while a search runs, and quit must give exit code 0.

| run | cycles, seed | action mix (counts) | legal bestmoves | max isready latency (searching) | peak working set | exit | verdict |
|---|---|---|---|---|---|---|---|
| `TtLockless=false` | 300, 20261109 | Threads 1/4/8, Hash 1/16/64, Clear Hash, ucinewgame, go movetime / nodes / depth / infinite+stop / ponder+ponderhit / ponder+stop | 219 / 219 | 28.3 ms | 161.0 MiB | 0 | **PASS** |
| `TtLockless=true` | 300, 20261109 | same | 219 / 219 | 39.3 ms | 161.0 MiB | 0 | **PASS** |
| `TtLockless=false` | 2000, 7 | same seed, same action mix as the ON row | 1,567 / 1,567 | 36.9 ms | 161.1 MiB | 0 | **PASS** (118.8 s) |
| `TtLockless=true` | 2000, 7 | movetime 396, nodes 290, depth 163, infinite+stop 275, ponder+ponderhit 257, ponder+stop 186, isready-while-searching 149, Threads changes 152, Hash 128, Clear Hash 79, ucinewgame 74 | 1,567 / 1,567 | 31.8 ms | 161.1 MiB | 0 | **PASS** (118.9 s) |

### Native unit tests, repeated (final code)
- tt_lockless ×4: each with 0 incoherent hits; the gating control saw 2,462,613 / 1,399,776 / 842,443 / 2,448,957 incoherent.
- smp_lifecycle ×3: PASS.
- tt_coherence: PASS.

Logs: `logs/tests/`, `logs/stress/`.

### Commands for Threads 1/4/8 (executed above vs prepared)
- EXECUTED on CPUs 12-15: Threads 1, 4 and 8 inside the stress runs (`-ThreadSet '1,4,8'`), and Threads 1/2/4/8 inside `smp_lifecycle_tests`.
- PREPARED-ONLY: the native-core runs in SCALING_PLAN.md and COMMANDS.md.
## 6. Final bug hunt (20:33:00-21:00:30 Vienna, 27.5 min, ended when the checklist was exhausted, not padded; EXECUTED; logs in `logs/bughunt/` and `logs/tests/bh_*`)
| check | result |
|---|---|
| re-hash the lock exe (C:) and every job exe | unchanged: trial_w6 / P / A/A copy / OFF build s0c = 4181a589; gate exe / s1d = 541e8b3d |
| pins on the final gate exe, `TtLockless` false and true (net on d11-22, net off d11-22, perft startpos/kiwipete) | **ALL OK** in both modes (`bh_gate_off.pins.txt`, `bh_gate_on.pins.txt`). This adds net-off pins on the exe level |
| engine sources frozen since `0599271` | `git diff 0599271 HEAD -- include src`: empty. The tip's include/src equals the OFF kit input |
| gate rebuilt from the published patch (fresh P export + `smp_layout_after_w6.patch` + flip, kit tag `rpg`) | **541e8b3d**: third identical build |
| GitHub tips equal the local tips; MD5SUMS of both packs verify | OK |
| invalid `TtLockless` value | "info string invalid value for option TtLockless"; mode unchanged |
| Threads 2 and 3 in lockless mode | legal best moves |
| Hash 2048 with 4 mode toggles | node counts identical in both modes (23,823 at depth 9). Working set 2,058 MiB per mode (one table resident). **Peak 4,106 MiB during a toggle**: allocate-before-free (R1 MINOR-3) briefly needs 2 × Hash, exactly like P's own Hash `resize` |
| contention fixture, 6 s per configuration | **1,888,357,888 probes, 313,545,226 hits, 0 incoherent**; control 8,749,241 incoherent |
| lifecycle with T1 identity at depth 11 (6 FENs, cold and warm, three paths) and lifecycle cases at depth 8 | PASS |
| own leftover processes | none. A background wait loop for the never-written recheck file was ended cooperatively by writing a labelled placeholder (`out\review\R1_recheck_smp.md`); nothing was terminated |
| stale documentation | fixed: SCALING_PLAN (old gate hash), SPEC §5 control wording, skill dispatch line, BENCH title, SPEC §3.1/§4/§5 names and wording |
| replacement under pressure: **Hash 1 MB** (16,384 clusters), 1,000 FENs, cold, `go depth 12` | P, gate `TtLockless=false` and gate `TtLockless=true`: identical rows (body sha256 `aa5b30715761c8bd…`, 1,000 distinct). Slot choice and tie-breaks match P under constant replacement |
| deeper warm table: FENs 2001-2300, `go nodes 200000`, same option cycle (12 changes), no ucinewgame | P, gate OFF and gate ON: identical transcripts (body sha256 `dd2126651f1777b9…`, 4,574 lines) |
| the other trial_w6 TT configuration: `FORGE_SPD_TT_NOTLS=0` + `FORGE_SMP_LAYOUT=1` (plain -O2 build, `-Wall -Wextra`) | 0 warnings. Pins (net on/off d11-22, perft) **ALL OK** with `TtLockless` false and true (lockless works through the public, non-owned TT path too) |
| Threads 8 lockless stress, 1,500 cycles, seed 99 (oversubscribed smoke) | 1,144 / 1,144 legal bestmoves, isready ≤ 26.7 ms, exit 0: **PASS** |
| **setoption while a search runs** (`go infinite`, then after 150 ms `TtLockless` true/false, Hash 64/16, Clear Hash, ucinewgame; Threads 1/4/8) | UCI stops and joins the search before touching the table: every interrupted bestmove is legal, the following `go depth 8` is legal, exit 0. **PASS** (`setoption_during_search.txt`) |
| stress driver control: P itself, 2,000 cycles, seed 7 | PASS with 1,567 / 1,567 legal bestmoves, the same count as the gate runs with the same seed (the driver gives no false failures and the action sequence is reproducible) |
| special search modes at Threads 1: `go searchmoves …` (2 positions, depth 10-11) and `go mate 2/3` | P = gate OFF = gate ON in depth, score, nodes and best move (`special_modes.txt`) |
| provenance of the copied tools (`logs/provenance/`) | `kit_v23_vs_idle_copy.diff`: exactly the 2 documented edits (Idle + readback; no termination on timeout), 5 changed lines. `uci_lib_vs_o2_uci_lib.diff`: only the header/constants/placement check and `Assert-OspdDisk` hunks; every UCI driver function is byte-identical to the speed job's `uci_lib.ps1` |
| the two new tests rebuilt at the kit's `-O3 -DNDEBUG` (they were -O2 before; checks for optimisation-sensitive UB) | tt_lockless: 496,848,896 probes, **0 incoherent**, control 2,190,922 incoherent; smp_lifecycle: PASS (a 9th fixture run, beyond the 8 counted above) |
| every existing test, natively on Windows, gate configuration (macro 1; one g++ line each, CPUs 12-15) | `forge_tests`: exactly the 4 known AL1 FAIL lines (the CI checker's list); correction_history, runtime_psqt, pawn_span, nearest_pawn, pv_metadata, rule50 and legal_witness (with its fixtures and openings): **PASS** |

Fixture totals over all 8 runs (5 native at 1.5 s per configuration, 1 native at 6 s, 2 under TSan in CI): **4,053,817,344 probes, 673,781,118 hits, 0 incoherent.**

## 7. Advisory NPS (EXECUTED; never a verdict, not scaling evidence, not Elo)
Tool: `tools/nps_smoke.ps1`. Each round starts every config fresh, in alternating order. 8 FENs, OwnBook false, Hash 64. The CPUs are 12-15: two physical cores with their SMT siblings, on a shared PC. **P_AA** is a byte copy of P that measures the noise floor (A/A). Logs: `logs/nps/F_*`.

| run | P (median nps) | P_AA / P | gate OFF / P | gate ON / P | spreads (min-max over rounds) |
|---|---|---|---|---|---|
| Threads 1, `go nodes 1000000`, 8 rounds | 1,940,663 | 1.0067 | 1.0155 | 0.9732 | 3.6-15.3 % |
| Threads 4, `go nodes 2000000`, 8 rounds | 6,295,595 | 1.0451 | 1.0383 | 1.0613 | 11.0-20.1 % |
| Threads 4, `go movetime 1500`, 6 rounds | 6,090,389 | 1.0495 | 1.0235 | 1.0763 | 3.5-15.4 % |

**Reading.**
- The A/A copy alone differs by up to +5 %, so no difference in this table is resolvable here.
- The weak hint worth timing: gate ON at Threads 1 may cost about 2-3 % (decoding K/D with two multiplies per slot instead of the legacy exclusive path's plain struct reads). The gains at Threads ≥ 2 are unproven.
- QA's quiet native-core run (SCALING_PLAN.md) decides.

A first NPS run used the pre-review gate exe `6c07563b` by mistake (its config was written before the R1 fixes) and had no A/A copy. It is kept in `logs/nps/superseded_6c07563b/` and **not cited**.
- Correction (2026-11-09, enc work): the decode of `0599271` used **three** multiplies per slot (`mix32`: one for the move, two mixing rounds), on all four slots of every probe. §8 measures that cost directly, and §10 removes most of it.

## 8. TT micro-benchmark (EXECUTED; advisory; the TT access path alone, not engine NPS)
**Tool.** `tools/tt_microbench.cpp`:
- built with the kit flags plus `-O3 -DNDEBUG`; it refuses to build without NDEBUG;
- through the existing `SearcherTestProbe` friendship it times the engine's real per-access dispatch (`Worker::probe_tt` + `Worker::store_tt`);
- one Worker per thread, one shared table, a probe + store pair per operation.

**Configs.**
- **L** = legacy. At Threads 1 this is the owned path (`tt_owned_`: no stripe lock, as `go`/`bench` at Threads 1); at Threads ≥ 2 it is P's striped locks.
- **X** = lockless.
- **A** = legacy again, the A/A noise floor.

**Method.** Workloads: random keys (mostly misses and replacements) and a hot pool of 4,096 keys (mostly hits). Rounds alternate L X A / A X L. Numbers are X/L ratios of the median Mops per config. `tools/micro_table.py` pools the runs, and the A/L column is the noise reference. CPUs 12-15 (2 physical cores with SMT, on a shared PC). Logs: `logs/enc4/micro/`.

**Engine trees.** Each was built with the same tool source:
- `0599271` ("old"; `mix32`, all four slots decoded);
- `527a696` ("enc2"; one-multiply tag32, the probe decides on raw words);
- enc3 (registers + `bit_cast` decode + raw-word store; working tree);
- `a675c04` ("enc4" = enc3 + the eight loads written out; the candidate).

| hash MB | keys | T | old | enc2 | enc3 | **enc4** | A/L range |
|---|---|---|---|---|---|---|---|
| 16 | hot4096 | 1 | 0.516 | 0.664 | 0.670-0.682 | **0.740** | 0.947-1.050 |
| 16 | random | 1 | 0.721 | 0.741 | 0.804-0.810 | **0.853** | 0.916-1.023 |
| 256 | hot4096 | 1 | 0.503 | 0.653 | 0.618-0.671 | **0.706** | 0.971-1.062 |
| 256 | random | 1 | 0.840 | 0.918 | 0.910-0.919 | **0.933** | 0.977-1.026 |

How the Threads 1 rows were run:
- old / enc2 / enc3 come from one palindromic series of 2 runs each;
- enc3 / enc4 come from a second palindromic series of 3 runs each;
- for enc3 the table gives both series' medians;
- all runs are `1.0 s × 6 rounds`.

| hash MB | keys | T | old (2 runs) | enc2 (2 runs) | enc3 (1 run) | **enc4 (1 run)** |
|---|---|---|---|---|---|---|
| 16 | hot4096 | 2 | 1.552 | 1.964 | 2.051 | **2.240** |
| 16 | hot4096 | 4 | 1.598 | 2.113 | 2.146 | **2.296** |
| 16 | random | 2 | 1.364 | 1.477 | 1.599 | **1.694** |
| 16 | random | 4 | 1.307 | 1.522 | 1.609 | **1.669** |
| 256 | hot4096 | 2 | 1.478 | 1.824 | 1.901 | **2.110** |
| 256 | hot4096 | 4 | 1.549 | 2.056 | 2.180 | **2.110** |
| 256 | random | 2 | 1.106 | 1.205 | 1.243 | **1.246** |
| 256 | random | 4 | 1.202 | 1.315 | 1.325 | **1.264** |

How the Threads ≥ 2 rows were run:
- old / enc2 are an ABBA of full runs, 2 each, `1.0 s × 4 rounds`;
- enc3 / enc4 are single full runs, `1.0 s × 4 rounds`;
- the A/L columns of these runs: 0.867-1.139.
- A first full run of the old code (`out/micro/run1.txt`, `1.5 s × 6 rounds`) gave the same picture: Threads 1 X/L 0.51-0.85, Threads ≥ 2 1.14-1.58.

**Reading.**
- At **Threads ≥ 2** the lockless table moves 1.25-2.3 times as many probe + store pairs as P's striped locks. This is the pack's purpose, and enc2-enc4 raised it further (hot pool 1.5-1.6 → 2.1-2.3).
- At **Threads 1** the owned legacy path takes no lock, so the lockless encoding can only cost. That cost fell from 0.50× to 0.71-0.74× of the legacy throughput on the hot pool, and to 0.85-0.93× with random keys.
- In engine terms this is an **estimate, not a measurement**. Assume about one probe + store pair per node at about 1.5 M nodes/s per thread. The remaining Threads 1 extra (about 7 ns per pair on the hot pool) is then about 1 % of search time, down from about 3 % for `0599271` (§7's weak 2-3 % hint).
- Engine NPS stays QA's quiet timing (SCALING_PLAN.md).

## 9. Tag strength census (EXECUTED; exact; `tools/tag_scan.cpp`, log `logs/enc4/tag_scan.txt`)
Criterion (SPEC 3.3): a difference `delta` of two data words (generation bits cleared) can keep the tag only if `delta * TagMul` lies within 2^32 of 0 (mod 2^64). That holds for 2^33 − 2 of the 2^64 − 1 non-zero deltas, density 2^-31.

| part | deltas | can collide |
|---|---|---|
| 1. score/eval only (bits 0-31), exhaustive | all 2^32 − 1 positive deltas (and their negatives) | **1** (and its negative): `0xB11924E1` = F47, the 47th Fibonacci number, since `TagMul / 2^64 = 1/φ`. In int16 fields that is score +9,441 with eval −20,199. The fable bug hunt predicted exactly this delta independently |
| 2. depth / bound / pv / rule50 only (bits 32-55), exhaustive incl. borrows | 33,554,430 | **0** (proven: odd multiplier, no carry) |
| 3. single bits outside the generation bits, both signs | 59 × 2 | **0** |
| 4. combined: \|Δscore\|, \|Δeval\| ≤ 4,096 (int16, with the uint16 wrap) × every realistic depth/bound-pv/rule50 difference (\|Δdepth\| ≤ 255, \|Δboundpv\| ≤ 7, \|Δrule50\| ≤ 100) | 268,468,224 (score, eval) difference **labels** × 823,095 distinct high-half deltas, exact with at most two high-half residues per low-half delta. Through the uint16 wrap a stored low-half delta can carry two labels (fable bug hunt NIT-7), so both counts are label counts, about twice the distinct deltas | **102,888** (label, high-half) combinations: density 4.65e-10 ≈ 2^-31 of the box, as the criterion predicts (the bug hunt's uniform-density estimate: about 102,900). The smallest: Δscore −33, Δeval +36, Δdepth +14, Δboundpv −6, Δrule50 −71, all at once |
| unit test group 1: \|Δscore\|, \|Δeval\| ≤ 32 (with wrap), \|Δdepth\| ≤ 8, any bound/pv, \|Δrule50\| ≤ 4 | 38,191,094 | **0** |

The old `mix32` tag had no such structure: a perfect-looking 2^-32 for every pair, with no class guaranteed. Mixed pairs from a same-position re-store (small field differences) are now never accepted.

## 10. Qualification of the candidate `a675c04` (enc4; EXECUTED 21:58-22:5x Vienna; logs `logs/enc4/`)
The whole set of §1-§6 was repeated on the new exes. The parent's references are unchanged (same P exe, same FEN files, same options).

### Builds
| build | source | kit v2.3 `-Expose` exe sha256 (pc1 = pc2) | kit identity |
|---|---|---|---|
| OFF (0) | `a675c04` as is (tags f0c, f0d) | **`4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = P = trial_w6** | ALL OK |
| **GATE (1)** | `a675c04` + the one define flipped (f1c, f1d) | **`a4b57032294d9d9efe2742408bb0a56da970cd1146f15c360a1fe99aada2c54b`** | OFF: ALL OK; `TtLockless=true`: ALL OK, "IDENTICAL to OFF" |

- Kit checks: 0 real missing-profile warnings, vfmadd 0, LTO on the link line (`logs/enc4/kit/`).
- Macro 0: `g++ -E -P` identical to P for all 8 units (`logs/enc4/pp/pp_identity.txt`).
- The published patch `7ce10a05..a675c04` (+357/−0, md5 `83928636b7cfcce60544d24bbd36fe6b`), applied with `patch -p1 -F0` to a fresh P export and flipped, gives the gate tree byte for byte (`diff -r`).

### Threads 1 identity of the gate `a4b57032` vs P's references
Same tools and parameters as §4 and §6 (`tools/identity_check.ps1`, `tools/liveness_check.ps1`). Every row printed `engine exit ok=True`.

| check | options | body sha256 = P's | verdict |
|---|---|---|---|
| L3 cold fens12k, depth 13, net on | `TtLockless=false` / `=true` | `0719943326d6b030…` | **IDENTICAL** (12,000 / 12,000, both modes) |
| L3 cold fens12k, depth 13, net off | `UseNNUE=false;TtLockless=true` | `e25cac43a12bf3bc…` | **IDENTICAL** (12,000 / 12,000) |
| L3 cold fens12k, depth 13, net off | `UseNNUE=false` (re-run `e4_OFF_netoff_r2`) | `e25cac43a12bf3bc…` | **IDENTICAL** (12,000 / 12,000) |
| L3b warm, 1,000 FENs, 40 option changes | `TtLockless=false` / `=true` | `618d5d3539e01c6b…` | **IDENTICAL** (10,680 lines, both modes) |
| Hash 1 MB replacement pressure, 1,000 FENs, depth 12 | `Hash=1` / `Hash=1;TtLockless=true` | `aa5b30715761c8bd…` | **IDENTICAL** (both modes) |
| deeper warm, FENs 2001-2300, `go nodes 200000`, 12 changes | `TtLockless=true` | `dd2126651f1777b9…` | **IDENTICAL** (4,574 lines) |
| pins: bench d11-22 net on and off, perft startpos/kiwipete | `TtLockless=false` / `=true` | `53d7bdfd0b0cdacd…` | **ALL OK** (both modes) |
| liveness, depth 12 | toggle vs Clear Hash | a1 = b1 = 53,479; a2 = b2 = 4,139; a3 = b3 = 35,964 | **PASS** on this PC, and in CI (`liveness_check.py`, the same numbers on Linux) |

- The aborted run: `e4_OFF_netoff` stopped at FEN 2,893. Its .NET append to its UCI log failed ("being used by another process") because my progress check (`grep -c`) held the file at that moment. Its partial hash is **invalid and not cited** (`logs/enc4/DEVIATIONS.md`). The re-run `e4_OFF_netoff_r2` (12,000 / 12,000 identical) is the row of record.

### Race / stress
- **CI run 42697936926** (`a675c04`, ubuntu-24.04, g++-14):
  - release: pins ALL OK for macro 1, for `TtLockless=true` and for macro 0; engine exit code 0 everywhere; **liveness PASS**; macro-0 exe has no TtLockless option.
  - All three modes: `require_pack_tests` shows both pack tests `Passed`.
  - **TSan**:
    - contention 4/8 threads × 1/4/16 clusters: 136,144,640 probes, 21,853,352 hits, **0 incoherent**;
    - gating control: 501,641 incoherent;
    - lifecycle PASS;
    - real TSan engine over UCI at Threads 2/4 × both modes: exit 0, 5 bestmoves each;
    - **"TSan: 0 reports"**.
  - **ASan+UBSan**: PASS, no report. Known-failure check PASS.
- **Native unit tests** (`logs/enc4/tests/`):
  - `a675c04` tt_lockless: decode = field decoder on 200k pairs; differential with BoundNone, tables equal; contention 0 incoherent; control 3.67 M incoherent.
  - `a675c04` smp_lifecycle: PASS.
  - enc3 tt_coherence (12 groups): PASS.
  - CI runs all CTests on `a675c04`.
- **UCI lifecycle stress** on `a4b57032`, Threads 1/4/8, 300 cycles, seed 20261109:
  - `TtLockless=true`: 219 / 219 legal bestmoves, max isready latency while searching 61.2 ms, peak 161.1 MiB, exit 0: **PASS**;
  - `TtLockless=false`: 219 / 219, 54.1 ms, 161.1 MiB, exit 0: **PASS**.

### Advisory NPS (never a verdict; `tools/nps_smoke.ps1`, 8 FENs, Hash 64, OwnBook false; logs `logs/enc4/nps/`)
| run | P_AA | old gate OFF (`541e8b3d`) | old gate OFF, byte copy | new gate OFF (`a4b57032`) | new gate OFF, byte copy | old gate ON | new gate ON |
|---|---|---|---|---|---|---|---|
| E4, Threads 1, `go nodes 1000000`, 8 rounds | 1.014 | — | — | 0.953 | — | 0.967 | 0.938 |
| E4b, Threads 1, 10 rounds | 1.000 | 1.006 | — | 0.963 | — | 0.929 | 0.927 |
| **E4c**, Threads 1, 10 rounds | 1.026 | 1.043 | 1.057 | **0.991** | **1.052** | — | — |
| E4, Threads 4, `go nodes 2000000`, 8 rounds | 1.006 | — | — | 0.984 | — | 1.034 | 1.025 |

All values are ratios to P's median in the same run.

**Reading.**
- In E4 and E4b, the new gate's OFF mode looked 4-5 % slower than P. Yet its hot machine code is the old gate's, instruction for instruction:
  - `objdump` of `Worker::search` (3,988 lines) and `Worker::qsearch` (3,608 lines) differs in 0 lines after address normalisation;
  - every hot function has the same size;
  - everything after the root driver sits 128 bytes lower, because the root driver inlines `hashfull_lockless`, which shrank by 112 bytes.
- **E4c settles it.** The byte copy of the new gate runs at 1.052, as fast as the old gate (1.043) and its copy (1.057), while the original file runs at 0.991. The same bytes in another file differ by 6 %.
- So that was a **per-file effect** (physical placement of the file's pages; the speed job's R12 finding), not a property of the binary.
- Within one exe and one run, the ON/OFF ratio at Threads 1 is: new gate 0.984 (E4) and 0.963 (E4b); old gate 0.958 (§7) and 0.923 (E4b).
- **Nothing here is resolvable on this PC.** QA's ABBA times fresh byte copies per round (speed-lock path), which removes per-file effects.

### Review
R2 = the fable bug hunt over `0599271`, `527a696`, `a675c04`, `89cddf7` and `b1a7fc6`: **no engine defect at any severity**. Tooling/doc findings: MINOR-1 (log sharing) and NIT-1..9, all fixed (REVIEW_LOG.md).

## 11. Qualification of the candidate `89cddf7` (enc5; EXECUTED 23:03-23:29 Vienna; logs `logs/enc5/`)
enc5 = enc4 + `FORGE_LOCKLESS_UNTRAINED_OPT` on the definitions of `probe_lockless` and `store_lockless` (SPEC 3.7). The whole set of §10 was repeated on the new exes.

### Builds and codegen
| build | source | kit v2.3 `-Expose` exe sha256 | kit identity |
|---|---|---|---|
| OFF (0) | `89cddf7` as is (tags h0c, h0d) | **`4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = P = trial_w6** (pc1 = pc2) | ALL OK |
| **GATE (1)** | `89cddf7` + the one define flipped (h1c, h1d) and the identical scratch tree g1 (g1c) | **`2940fb0514dd2ef058d6512bf66659074f162293f7d31ccac23779c2e65762e5`** (three identical builds) | OFF: ALL OK; `TtLockless=true`: ALL OK, "IDENTICAL to OFF"; 0 missing-profile warnings |

- The published patch `7ce10a05..89cddf7` (+366/−0, md5 `f07082fdc8a06cb5baaae9cb76f3b538`), applied to a fresh P export and flipped, gives the gate tree byte for byte.
- **Codegen** (`logs/enc5/codegen/lockless_placement.txt`, objdump):

| gate | `probe_lockless` | `store_lockless` |
|---|---|---|
| enc4 `a4b57032` | `0x1401034f2`: the cold tail of `.text` after all hot code, unaligned; 274 instructions; rolled slot loop with stack-indexed loads | `0x140103ade`, 155 instructions |
| enc5 `2940fb05` | `0x14000bc20`: normal `.text`, aligned; 364 instructions; the unrolled register code of the `-O3` micro-benchmark build | `0x14000c190`, 170 instructions |

- No other function changed its code.
- The hot search code moved by +1,984 bytes, because the two functions now sit before it. Placement only, as §10 showed for a 128-byte shift.

### Threads 1 identity of the gate `2940fb05` vs P's references (`logs/enc5/id/`)
| check | options | verdict |
|---|---|---|
| L3 cold fens12k, depth 13, net on | `TtLockless=false` / `=true` | **IDENTICAL** (12,000 / 12,000, `0719943326d6b030…`, both modes) |
| L3 cold fens12k, depth 13, net off | `UseNNUE=false` / `UseNNUE=false;TtLockless=true` | **IDENTICAL** (12,000 / 12,000, `e25cac43a12bf3bc…`, both modes) |
| L3b warm, 1,000 FENs, 40 option changes | both modes | **IDENTICAL** (`618d5d3539e01c6b…`) |
| Hash 1 MB replacement pressure, 1,000 FENs, depth 12 | both modes | **IDENTICAL** (`aa5b30715761c8bd…`) |
| deeper warm, `go nodes 200000`, 300 FENs | `TtLockless=true` | **IDENTICAL** (`dd2126651f1777b9…`) |
| pins (bench d11-22 net on and off, perft) | both modes | **ALL OK** (`53d7bdfd0b0cdacd…`) |
| liveness, depth 12 | toggle vs Clear Hash | **PASS** (53,479 / 4,139 / 35,964 in both sessions) |

Every row printed `engine exit ok=True`.

### Race / stress
- **CI run 42708220996** (`89cddf7`):
  - release: pins ALL OK (macro 1, `TtLockless=true`, macro 0), engine exit 0, FMA 0, **liveness PASS**.
  - All modes: both pack tests `Passed`.
  - **TSan**: contention 182,691,328 probes, 29,632,522 hits, **0 incoherent**; control 678,627 incoherent; lifecycle PASS; real engine over UCI at Threads 2/4 × both modes: exit 0, 5 bestmoves each; **"TSan: 0 reports"**.
  - **ASan+UBSan** PASS.
  - Compiler warnings: the same 6 pre-existing `-Wconversion` lines as the macro-0 build; no attribute warning.
- **UCI lifecycle stress** on `2940fb05`, Threads 1/4/8, 300 cycles, seed 20261109:
  - `TtLockless=true`: 219 / 219 legal bestmoves, max isready latency while searching 26.6 ms, peak 161.1 MiB, exit 0: **PASS**;
  - `TtLockless=false`: 219 / 219, 21.1 ms, 161.0 MiB, exit 0: **PASS**.

### Tools (MINOR-1, NIT-9)
`tools/test_log_sharing.ps1` runs a 300-FEN identity check while a hostile reader keeps opening its UCI log without sharing writing. A survival counts only with at least 10 reader attempts.

| tools | runs | result |
|---|---|---|
| current (`89cddf7`+) | 2 | the reader was refused 135 and 124 times: **RUN SURVIVED**, 300 rows |
| `a675c04` | 2 | **RUN BROKEN** at the reader's first grab: `AppendAllText ... being used by another process`, the same error that aborted `e4_OFF_netoff` |

Logs: `logs/enc5/minor1/`.
