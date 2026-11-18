# kimi5 job 24 report — item 10 (NullCutOnly + TtNodeTypeDepth: node-type-aware null move and TT cutoff) on the PC build

Three plain lines: I was asked to write my own port of the item-10 change (null-move pruning only at
expected cut nodes; the main search's TT cutoff at depth ≤ D needs cut_node == (tt_score >= beta)) onto
the PC build (6b98f217 + pc_r15, `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`), prove it against their
known answers, measure depth scaling, and count how much of today's pruning sits at the "wrong" node type
and what the search behind a refused TT cutoff returns. The port is done and **every known answer of
file 24 holds**: all eight Step 0 numbers, all eight depth-12 sums with first-threes, all sixteen row
hashes, the counting build equal to the plain build on all five runs, and every Step 3 structural rule
with zero forbidden counts. How sure: node-for-node AND best-move-for-best-move equality with their rows
on 553 positions × 4 settings; the depth-14 rows and the 1,306 counter lines are this run's own raw files.

(1) **Step 0: MET** (first build, no rerun needed; one failed cmake attempt with the wrong compiler is
not a run, its log is not committed). (2) Prediction: **5 rows, 4 KILLED** (only P2 survives; details
below). (3) Step 1: base, nc, t5, both equal their known rows on 200 of 200 O and 353 of 353 G each;
changed-node positions per ON setting below. (4) Step 2 table below. (5) Step 3 tables below;
200 + 353 + 200 + 200 + 353 = 1,306 searches summed.

## Step 0 (raw files in `tests_kimi5_job24/step0/`; a fresh process per line)

Build = 6b98f217 + `pc_r15.patch` (swarm file 5 lines 56–2374, sha256
`d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`, re-verified) + my
`NodeType10.pc.patch.txt` (sha256 `e1c87d64c0d40eb031a658694a2148924ddad9ecd9bb50b01986a3f368c11790`;
applies with `patch -p1 -F0`, zero fuzz — round-trip verified against my build tree, `roundtrip.txt`).
g++ 13.3.0, Release, `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` (the job-23 lesson: the guard is a
compiler flag, not a CMake variable), AVX-512+BMI2 present (no FORGE_PORTABLE). Exe sha256
`80c2d50aa9288ff7df9336a87819d2a7fe88f0ff5c042c6cba627b10e342b234` (`step0/exe.sha256`).

| settings | bench 11 | bench 13 | bench 16 | go perft 5 |
|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ |
| S14 | 242796 ✓ | 656517 ✓ | – | – |
| PC20 | 278024 ✓ | 587276 ✓ | – | – |

Both new options in the `uci` list with the file-24 ranges and defaults (NullCutOnly spin 0..1 def 0;
TtNodeTypeDepth spin 0..20 def 0) — `step0/uci_list.txt`. No `unknown option`/`invalid value` in any
Step 0 file. Every setoption line in `step0/*_input.log`.

**The two places in the PC build** (6b98f217 + pc_r15; `sed -n '1847p;1943p' src/search.cpp` shows them):
the main search's **TT cutoff test is src/search.cpp line 1847** (`if (!pv_node && excluded.is_none() &&
tt_hit && tt_score != ValueNone && tt_depth >= depth && ...`); the **null-move test is src/search.cpp
line 1943** (`if (!bare_king_mode && depth >= tune::NullMoveMinDepth && eval >= beta && ...`). My patch
adds one conjunct to each, two tune ints with their `parameters()` entries, and the two externs.

## Prediction, graded row by row (`tests_kimi5_job24/prediction.txt`, own commit before Step 1, never edited)

| # | guess | kill range | measured | verdict |
|---|---|---|---|---|
| P1 nc/base, d14, G | 1.030 | KILLED outside [0.990, 1.080] | 1.0865 | **KILLED** (above) |
| P2 t5/base, d14, G | 1.005 | KILLED outside [0.960, 1.050] | 1.0399 | survives |
| P3 null tries at cut_node false, base G d12 | 0.30 | KILLED outside [0.15, 0.50] | 0.04447 | **KILLED** (below) |
| P4 TT cutoffs d1..5 disagreeing, base G d12 | 0.30 | KILLED outside [0.15, 0.45] | 0.06769 | **KILLED** (below) |
| P5 refused cutoffs confirmed, t5 O+G d12 | 0.55 | KILLED outside [0.35, 0.75] | 0.94267 | **KILLED** (above) |

Wrong in one direction three times: I put far more pruning at the wrong node type than there is (4.4 %
of null tries, 6.8 % of shallow TT cutoffs, not ~30 %), and the stored bound behind a refused cutoff is
far more honest than I thought (94 % confirmed, not 55 %).

## Step 1: identities against their port (raw rows in `tests_kimi5_job24/rows/`, checker `check_s1_j24.py`, output `check_s1.txt`)

PC20, `go depth 12`, O = first 200 lines of `UHO_Lichess_4852_v1.epd`, G = set G (353). Row hashes =
first 16 hex of sha256 of the values in position order, each followed by one LF. **All 8 sums, all 8
first-threes and all 16 row hashes equal file 24's known answers** (`check_s1.txt`: every line OK,
OVERALL: ALL EQUAL). Changed node counts against base per ON setting (best-move changes in brackets):
nc O 188/200 [10], nc G 335/353 [70]; t5 O 200/200 [50], t5 G 348/353 [96]; both O 200/200 [54],
both G 349/353 [98].

## Step 2: depth scaling (`step2_j24.py`, `step2_table.txt`; bootstrap 95 % over positions, 2000 resamples, seed 12)

| set | depth | setting | nodes | ratio | boot95 | bm≠base |
|---|---|---|---|---|---|---|
| O | 12 | base | 8,315,168 | 1.0000 | – | 0 |
| O | 12 | nc | 8,274,914 | 0.9952 | [0.9689, 1.0173] | 10 |
| O | 12 | t5 | 8,658,881 | 1.0413 | [0.9858, 1.0903] | 50 |
| O | 12 | both | 8,590,222 | 1.0331 | [0.9790, 1.0773] | 54 |
| O | 14 | base | 19,377,109 | 1.0000 | – | 0 |
| O | 14 | nc | 19,249,693 | 0.9934 | [0.9485, 1.0330] | 16 |
| O | 14 | t5 | 20,595,884 | 1.0629 | [1.0063, 1.1126] | 46 |
| O | 14 | both | 20,351,414 | 1.0503 | [0.9848, 1.1048] | 47 |
| G | 12 | base | 17,611,204 | 1.0000 | – | 0 |
| G | 12 | nc | 18,015,717 | 1.0230 | [0.9777, 1.0664] | 70 |
| G | 12 | t5 | 17,596,929 | 0.9992 | [0.9476, 1.0424] | 96 |
| G | 12 | both | 17,955,756 | 1.0196 | [0.9687, 1.0626] | 98 |
| G | 14 | base | 41,052,503 | 1.0000 | – | 0 |
| G | 14 | nc | 44,603,463 | 1.0865 | [0.9900, 1.1990] | 70 |
| G | 14 | t5 | 42,690,187 | 1.0399 | [0.9751, 1.0947] | 95 |
| G | 14 | both | 44,186,167 | 1.0763 | [1.0073, 1.1331] | 94 |

Cross-check: G base d14 = 41,052,503 and O base d14 = 19,377,109 equal job 22's recounted base sums to
the node. No depth-14 sum equals its depth-12 sum. Every interval except both/G-d14 and t5/O-d14 spans 1.

## Step 3: what the two options would remove (`rows_count/`, summer `sum_nt10.py`, output `step3_sums.txt`, derived `step3_derived.txt`)

Counting build = the port + observe-only counters (`NodeType10Count.pc.patch.txt`, exe sha256
`8ae04492ad3f14b684571b8a46a0a6c4a99c2d49f1cb4ff865cb709c64628e1d`), one `NT10C` line per search.
**First known answer holds: the counting build's rows equal Step 1's rows position by position on all
five runs** (cntbase_O/G, cntnc_O, cntt5_O/G). 1,306 searches summed (the summer prints the count per run).

**Null move (armed on ELIGIBILITY = every node today's code enters the null search), base, d12:**

| set | tries cut=T | tries cut=F | ≥β cut=T | ≥β cut=F | returned cut=T | returned cut=F |
|---|---|---|---|---|---|---|
| O | 121,761 | 1,817 | 86,698 | 297 | 86,698 | 297 |
| G | 341,726 | 15,902 | 241,266 | 3,311 | 241,266 | 3,311 |

Wrong-type share: O 1.47 %, **G 4.45 %** of tries (P3). A cut=F try scores ≥β only 16 % (O) / 21 % (G) of
the time vs 71 % at cut=T. returned ≡ ≥β everywhere: at depth 12 no node reaches the depth-14
verification and NullThreatVerify is off, so every null score ≥ β returns. **Known answer: under nc
(cntnc_O) the tries with cut_node false are 0 in every one of the 200 searches** (and ≥β/returned too).

**TT cutoffs taken today (main search), base, d12:**

| set | depth | ≥β agree | ≥β disagree | ≤α agree | ≤α disagree | between |
|---|---|---|---|---|---|---|
| O | 1–5 | 332,885 | 13,397 | 24,418 | 10,181 | 0 |
| O | 6+ | 6,950 | 399 | 1,426 | 216 | 0 |
| G | 1–5 | 1,114,278 | 53,664 | 92,997 | 33,986 | 0 |
| G | 6+ | 55,617 | 1,925 | 7,433 | 757 | 0 |

Disagreeing share at depth 1–5: O 6.19 %, **G 6.77 %** (P4); at depth 6+: O 6.84 %, G 4.08 %. t5 would
refuse exactly the disagreeing d1–5 cells. "Between" (α < stored < β) is 0 everywhere, as it must be at
null-window non-PV nodes.

**Under t5, what the search behind a refused cutoff returns (cntt5, d12):**

| set | refused (≥β / ≤α) | confirmed | overturned | confirmed share |
|---|---|---|---|---|
| O | 35,499 (17,993 / 17,506) | 33,199 | 2,300 | 93.5 % |
| G | 118,160 (64,074 / 54,086) | 111,650 | 6,510 | 94.5 % |
| O+G | 153,659 | 144,849 | 8,810 | **94.3 %** (P5) |

Per depth (O+G): d1 94.3 %, d2 94.6 %, d3 94.0 %, d4 92.6 %, d5 91.7 %. **Known answers: no refused
cutoff lies at depth 6 or more (0), none has a stored score between α and β (0), and none agrees** (a
refusal is possible only when cut_node ≠ (score ≥ β), by construction). Note: t5's refused count on G
(118,160) is larger than base's taken-disagreeing count (87,650): refusing cutoffs grows the tree, and a
bigger tree holds more shallow TT cutoffs of every class.

**The question's answer:** almost none of today's pruning sits at the wrong node type — 1.5–4.4 % of
null tries and 6.2–6.8 % of shallow TT cutoffs — and the search behind a refused TT cutoff **confirms**
the stored bound 94 % of the time (only ~6 % overturned). So t5 on these suites is almost pure node
cost (G d14 1.0399), and nc removes a small, mostly-failing-low slice yet still grows the G tree
(d14 1.0865): the 17–21 % of all-node null tries that would have cut were worth more than the rest saved.

## Step table

| step | state | evidence | result |
|---|---|---|---|
| 0 | done | `step0/` | all 8 numbers exact; both options listed |
| prediction | done | `prediction.txt` (own commit) | 5 rows, 4 KILLED |
| 1 | done | `rows/`, `check_s1.txt` | ALL EQUAL: 8 sums, 8 first-threes, 16 hashes |
| 2 | done | `rows/` d14, `step2_table.txt` | table above |
| 3 | done | `rows_count/`, `step3_sums.txt` | 1,306 searches; every structural known answer holds |
| patch | done | `NodeType10.pc.patch.txt`, `roundtrip.txt` | `patch -p1 -F0`, zero fuzz, round-trip exact |

## Findings (each with file and line; commands reproduce)

1. The two patched places: TT cutoff test `src/search.cpp:1847`, null-move test `src/search.cpp:1943`
   (PC build). See them: `sed -n '1847,1863p;1943,1950p' src/search.cpp` on a 6b98f217+pc_r15 tree.
2. The port is their code: every file-24 known answer holds (`cd tests_kimi5_job24 && python3 check_s1_j24.py rows 12`).
3. Wrong-type pruning is rare and the refused cutoffs are mostly honest (tables above;
   `python3 sum_nt10.py rows_count rows`).
4. The sign flips job 21 warned about appear here too: nc shrinks the O tree (0.9934 at d14) but grows
   the G tree (1.0865 at d14); t5 costs 4–6 % on O but only 0–4 % on G. Every interval but two spans 1.

Suspicions, not proven: none new.

## From my colleagues

- deepseek5 (`for-fable-and-opus/deepseek5-work`, NOTES read, reports listed through job 30): its job-30
  lesson — "when a counter reads a state variable, read it at the moment the event happens" — is exactly
  the design of my refusal classification (record at the refusal, classify at that node's own return by a
  per-ply slot, never a global). Its self-play protocol (S5) was not needed here (no games). Nothing of
  its Killer/CounterMove rates touches this job.
- glmflash5: file 25 (Opus) says it has stopped, nothing new to read. Its branch
  `cursor/glmflash5-work-cb5c` was fetched and its report list checked (newest: job 27, cross3); nothing
  applied. Read nothing further.

## What I did NOT do

- No games played (the job asks for counters, not strength). No depth-16 scaling. The `both` setting got
  no counting runs (not asked).
- The first background build attempt (cmake picked clang 18, which cannot link libstdc++ here) never
  produced a binary or a measurement; nothing of it is committed. The g++ rebuild is the only build used.

## What I am NOT sure about

- Under CuckooRep (on in PC20) the cuckoo wrapper can call the node search twice; my refusal
  classification pairs a refusal with the return of the inner call that refused it. I argued the pairing
  is exact (per-ply slot cleared on every entry), but I did not prove it with a dedicated run. The
  refusal/confirmed totals are consistent (confirmed ≤ refused per class everywhere).
- The TT gate reads `depth` at the cutoff test (after the hindsight depth adjustment), which is the depth
  the cutoff test itself uses. That my rows equal theirs on 553 positions says their port reads the same.

## A better way

The job's design is already the right one; one cheap addition for the next counter job: the `both`
counting run would cost two minutes and would show whether nc and t5 interact (nc removes all-node null
tries, which changes which nodes are cut nodes downstream, which moves the t5 refusal counts). If the
interaction is zero, the two options can be tuned independently; if not, they cannot.

## Times

See `tests_kimi5_job24/stamps.txt` (pasted `date -u` lines only; claim 09:01:24Z, Step 1 rows 09:04:34Z,
Step 2 rows 09:05:32Z, Step 3 runs 09:07:19Z, all 2026-11-18).

## Model

Kimi K3 (the model name my runtime gives: kimi-k3).

`git status --short` and `ls -R` of the job folder as the last command before this commit:
`tests_kimi5_job24/final_ls.txt`.
