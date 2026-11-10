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
## 6. Final bug hunt (20:33-21:03 Vienna; EXECUTED; logs in `logs/bughunt/` and `logs/tests/bh_*`)
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
| stale documentation | fixed: SCALING_PLAN (old gate hash), SPEC §5 control wording, skill dispatch line, BENCH title |

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
