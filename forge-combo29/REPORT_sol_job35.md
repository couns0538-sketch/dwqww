# Sol — Job 35 kF and r15d self-play with eight random opening plies

## Step 0. Unchanged builds and net768

I reused Job 34's two GCC 14.2.0 native binaries. r15d SHA-256 was `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671`. kF SHA-256 was `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb`. Both use the same flags and define `__AVX512F__`, `__AVX512BW__` and `__BMI2__`. [Job 34 build receipt](sol/job34/build-evidence/build-all.txt)

Both binaries passed all seven fresh-process runs. Defaults `bench 11`, `bench 13` and `go perft 5` returned 312866, 862329 and 4865609 nodes. PC20 bench 11 and 13 returned 278024 and 587276. With PC20 and active net768 they returned 882074 and 4275906. Net768 SHA-256 was `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. Every net-enabled pin and game log recorded `NNUE v3 active` and checksum `30ab43b4ba5db5f3`. [r15d raw pins](sol/job35/pin-evidence/r15d.raw.txt) · [kF raw pins](sol/job35/pin-evidence/kF.raw.txt) · [Net generation](sol/job34/net-evidence/net768-generation.txt)

## K25 and C25 controls

Both controls used r15d, net768, Threads 1, Hash 16 and `go softnodes 2000` on games 1–20. The three opening files matched before launch, SHA-256 `b5b2888142cd439d4d8a95774f8dd314d221e8fdce19300d7c8e742b3b9d1691`. [Opening verification](sol/job35/opening-evidence.txt)

- **K25 PASS.** The two PC20 runs had identical records across all 20 games. Each produced 2,182 records and 9,276,055 last-info nodes. [Exact comparison and hashes](sol/job35/K25.txt)
- **C25 PASS.** With only `LmrQuietBase` changed from 93 to 60, 19 of 20 games differed. The first differing line was game 1, ply 8. It was `1 8 g4g5 2389` with PC20 and `1 8 g4g5 2243` with base 60. The eight random plies were `h2h3 b7b5 b1c3 f7f6 c3a4 h7h5 g2g4 f6f5`. [First difference and records](sol/job35/C25.txt)

The prediction was the sole file in commit `0f71e6e`, after both controls and before U1. [Frozen prediction](sol/job35/prediction.txt)

## Prediction grades

| U1 forecast | Observed | Grade |
|---|---|---|
| 0–5 differing games out of 1,000 | 0 out of 1,000 | Met |
| Node columns equal | All 120,131 values equal | Met |

## U1. Games 1–1000

Both binaries used PC20, active synthetic net768, Threads 1, Hash 16 and `go softnodes 2000`. Each played both colors from its independently generated opening file. The recorded nodes are from the last literal `info string softnodes nodes` line on each search.

| Record file | Status | Completed games | Records | Opening SHA-256 | Record SHA-256 | Last-info node sum |
|---|---|---:|---:|---|---|---:|
| `raw/U1-r15d.records.txt` | complete | 1000 | 120131 | `c4d4285bf447d3dcea73040871a684933dbc431b273eb8072ea3bb81b94c763a` | `bb709f5aae25ef5b750c81ce94cefe8c0cff5edb9decb5c42fa10829724a7533` | 502179747 |
| `raw/U1-kF.records.txt` | complete | 1000 | 120131 | `c4d4285bf447d3dcea73040871a684933dbc431b273eb8072ea3bb81b94c763a` | `bb709f5aae25ef5b750c81ce94cefe8c0cff5edb9decb5c42fa10829724a7533` | 502179747 |

**IDENTICAL.** Openings passed byte comparison first. 0 of 1000 common completed games differ. Equal node columns yes.

[Opening `cmp`](sol/job35/U1.openings-cmp.txt) · [Record `cmp`](sol/job35/U1.cmp.txt) · [Raw U1 records](sol/job35/raw)

## U2. Games 1001–1500

U2 began after the U1 push and used the same builds, PC20, net768, Threads 1, Hash 16 and `go softnodes 2000` on the next 500 seeds.

| Record file | Status | Completed games | Records | Opening SHA-256 | Record SHA-256 | Last-info node sum |
|---|---|---:|---:|---|---|---:|
| `raw/U2-r15d.records.txt` | complete | 500 | 57656 | `60fae669a3f492ca27f0601e2041a7f55197c1f878ab3663c9f99caa30fbfde0` | `b3cabc86937e6e8632eeed54616993f4ea552c5e116ad75109ff425d6146be20` | 239105488 |
| `raw/U2-kF.records.txt` | complete | 500 | 57656 | `60fae669a3f492ca27f0601e2041a7f55197c1f878ab3663c9f99caa30fbfde0` | `b3cabc86937e6e8632eeed54616993f4ea552c5e116ad75109ff425d6146be20` | 239105488 |

**IDENTICAL.** Openings passed byte comparison first. 0 of 500 common completed games differ. Equal node columns yes.

[Opening `cmp`](sol/job35/U2.openings-cmp.txt) · [Record `cmp`](sol/job35/U2.cmp.txt) · [Raw U2 records](sol/job35/raw)

## Facts

- The separate opening files passed `cmp` before each measured phase. Independent generation reproduced all 3,060 rows across the arm files, including the controls. The U1 and U2 ranges use different game seeds. [Opening proof](sol/job35/opening-evidence.txt) · [U1 pre-run comparison](sol/job35/U1.openings-cmp.txt) · [U2 pre-run comparison](sol/job35/U2.openings-cmp.txt)
- Game 1160 ended after `f2f4 e7e6 g2g4 d8h4`. Both U2 sidecars count it as a completed checkmate after four random plies, with zero searched records. It is the only opening-only terminal in these fixtures. [Opening proof](sol/job35/opening-evidence.txt) · [r15d U2 sidecar](sol/job35/raw/U2-r15d.records.txt.meta) · [kF U2 sidecar](sol/job35/raw/U2-kF.records.txt.meta)
- U1 reached the remote at 23:05:14 UTC before U2 started. U2 reached it at 23:07:52. Both complete original archives passed byte readback, and the independent pass checked legal moves and first claimable endings across both ranges. [Independent audit](sol/job35/independent-job35.txt) · [UTC stamps](sol/job35/stamps.txt)

## Suspicions

The unchanged node traces support the interpretation that kF's single-worker stop optimization preserves the loop's soft limit on these games. The records do not trace which internal optimization paths ran. [Raw readback](sol/job35/readback.txt)

## What this check cannot see

The PC's engine build (clang 23 for Windows, its profile), its trained net (net768 is made up), the PC's own random
numbers (other games of the same kind), more than one thread, Hash sizes other than 16.

## What I did not do

I used the two unchanged cloud executables and synthetic weights. I made no tracked engine-source changes and ran no training or owner PC work.

## What I am not sure about

The record equivalence is specific to these seeds, one-thread PC20 and synthetic net768 at `go softnodes 2000`. It leaves open other seeds, builds and trained weights. The comparison gives no separate speed estimate.

## Reproduction

Python 3.12.14 and python-chess 1.11.2 generated each game opening with `random.Random(g)` and `rng.choice(list(board.legal_moves))` in the library's order. The driver sends the full move trail with `position startpos moves`, resets once per nonterminal opening, uses one engine process for both sides and checks for claimable draws or the 300-ply cap. The first searched record normally has absolute zero-based ply 8. Each numeric value comes from the last literal `info string softnodes nodes` line. [Fixtures and hashes](sol/job35/opening-evidence.txt) · [Exact driver](sol/job35/whole_games35.py) · [Raw records](sol/job35/raw)

[UTC stamps](sol/job35/stamps.txt) · [Archive readback](sol/job35/readback.txt) · [Precommit tree](sol/job35/precommit-readback.txt)
