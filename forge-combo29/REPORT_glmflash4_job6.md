# glmflash4, job 6 report (2026-11-15)

**The fixes off ARE the port** (step 1: tree G with everything at its default
prints all four known numbers without tables, and with tables its three bench
numbers and a 500-position identity run are byte-identical to tree P's). Of
the seven faults I could **show two at the root and see them fixed** (G5, G6),
**one partially** (G8: the toggle changes the search on all 5 of my rows, but
the score class stayed correct — the branch's class-level fault needs its
6-men fixture), and **four not at the root** (G1, G2, G3, G7: the branch's own
evidence for these is instrumented or 5/6-men; the branch ITSELF reports 0
false root claims on 200,000 roots for G2's class of fault, and my runs agree
with that). **Nothing crashed and no sanitizer tripped** (planted fault first,
then bench and 50 endgame positions under ASan+UBSan with tables and all bits
on: zero findings; the ASan bench equals the release node count exactly).
**Nothing was cut**; all three steps ran complete.

**The one big deviation, said first:** the prescribed table source
`https://tablebase.lichess.ovh/tables/standard/` is NOT REACHABLE from this
machine — the run's network policy allows 159 named hosts and that is not one
of them (`curl` fails with an SSL connection reset). I searched for mirrors
inside the allowed set (GitHub search, Hugging Face search, the branch's own
`ci_fetch_tables.sh` — its default mirror `tablebase.sesse.net` is also not on
the allowlist) and found none. What I used instead: **the official
python-chess test table set** (niklasf/python-chess, `data/syzygy/regular/` —
70 files, 35 WDL + 35 DTZ, all 3-4-men materials; that repo's own SOURCE.txt
says they came from `tablebase.sesse.net/syzygy/`, the same mirror the
project's CI script uses). Consequences, checked and stated:
- **64 of the 70 files have sha256 IDENTICAL to the branch's own
  `fixtures/TABLES.sha256`** (all 32 four-man materials, both files each). The
  6 that differ are the three 3-man tables (KPvK, KQvK, KRvK) — a different
  generation of the same materials (their game-theoretic values are what they
  are; my oracle cross-checks used the same files the engine read). Files:
  `step0/table_verification.txt`, `tables/sub_hashes.txt`.
- The subset answers probes up to 4 men. The branch's known pins WITH tables
  (313631 / 866959 / 2460490, full 145+145 set) are therefore NOT reproducible
  here: tree P with my subset prints 312697 / 852834 / 2682662 (its searches
  reach 5-men probe positions the subset cannot answer). The step-1 check was
  run the honest way instead: **tree P and tree G on the SAME subset** —
  identical numbers and a byte-identical 500-position identity run.
- The load line differs accordingly: `info string Syzygy: 35 WDL and 35 DTZ
  tables, up to 4 pieces` (vs the branch's 145/145, up to 5).

## Step 0 — trees and tables

- Base `d4f43124` (source at the root), Release, g++, `-DFORGE_NNUE_HIDDEN=256`
  as a compiler flag; both patches applied `patch -p1 -F0`, clean, no rejects
  (P: `fit` notes below; the same commands as my earlier jobs).
- Tree P = base + `opus_r13/p6/syzygy_port.patch`; tree G = P +
  `opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch`. Both built
  (`build/`); tree G built a SECOND time with the three gap macros
  (`-DFORGE_SYZYGY_TB_BOUNDS=1 -DFORGE_SYZYGY_ROOT_EXACT=1
  -DFORGE_SYZYGY_RULE50=1 -DFORGE_EXPOSE_TUNABLES=1`, build dir `build_gaps/`)
  — see step 1a.
- Tables: the subset above, `/tmp/syzygy_sub` (70 files); WDL-only copy for
  G6 at `/tmp/syzygy_wdl_only` (hard links to the same files).
- Known answers without tables, tree G as built (macros off): bench 11
  312866, bench 13 862329, bench 16 3024920, perft 4865609 — all four match
  (`step1/G_notables_*.txt`).

## Step 1 — the fixes switched off are the port

a. **Macro defaults:** the patch gates every change in `#if
   FORGE_SYZYGY_TB_BOUNDS` / `_ROOT_EXACT` / `_RULE50` blocks; an undefined
   macro is false, so tree G as built (no extra flags) has all fix code
   ABSENT — that is the "fixes off" state, and it is what my first tree-G
   build is. The three UCI switches, quoted from the patch (and, with the
   macros on, from the live `uci` reply of `build_gaps/forge`):
   `option name SyzygyTbBounds type spin default 0 min 0 max 7`,
   `option name SyzygyRootExact type spin default 0 min 0 max 3`,
   `option name SyzygyRule50 type spin default 0 min 0 max 3`
   (`step1/macro_default_quote.txt`; the tunables are advertised only with
   `-DFORGE_EXPOSE_TUNABLES=1`, which the branch's own recipe also sets).
   Without that flag the switches are still ACCEPTED by `setoption` (the
   tunables loop), just not listed.
b. Without tables: the four known numbers (above). With tables (subset):
   tree P = tree G = 312697 / 852834 / 2682662 for bench 11/13/16 —
   byte-identical behaviour (`step1/P_tables_*.txt`, `step1/G_tables_*.txt`).
   500 positions (first 500 UHO lines, `go depth 9`, tables loaded) on tree P
   and tree G: **one sha256 per side — both
   1dea89ccf3c24a241869...; identical bytes; smallest node count 4735**
   (`step1/` identity outputs were produced by `scripts/identity_run.py`;
   hashes in the run log below).

## Step 2 — each fault, shown by hand (bit off vs on, tree G macros-on build)

General method: my own UCI driver (`scripts/s2_harness.py`), fresh process per
scenario, `ucinewgame` where the scenario needs a clean TT, python-chess over
the SAME subset as the oracle. The branch's own fixtures are 5-6 men
(clock.fens: all 19,905 rows are 5-men; f1.toggle.fens: all 400 rows 6-men;
read.k0.tsv pairs 6-men) — with a 4-men subset their engineered rows cannot
probe, so where I could not use the branch's case I built the same mechanism
in covered materials and say so per row. G1's zugzwang fixture HAS 4-men rows
(146 of 1250) and those I took from the branch.

| fault | case used | bit off | bit on | agrees with the branch? |
|---|---|---|---|---|
| G5 | constructed: `8/8/8/3k4/8/8/5Q2/6K1 w - - 83 1` (KQvK, dtz 17, dtz+clock=100; oracle: boundary-win) | `score cp 2` — the exact win DEMOTED to cursed, the branch's own fault wording | RootExact=3: `score cp 1135`, a clearly winning search score; the demotion is gone | YES on the fault form ("an exact win is shown as cursed (+2)", ledger G5); the fixed form shows the search score, per the README's report rules |
| G6 | constructed WDL-only rows (DTZ files hidden), e.g. `8/8/8/3k4/8/8/5Q2/6K1 w - - 84 1` | RootExact=0: **4 TB-band root claims, 2 wrong vs oracle** (claims at clocks where the truth is cursed/draw) | RootExact=1: **0 TB-band claims, 0 wrong** | YES (ledger G6: 2186+2169 false on the clock fixture → 0) |
| G8 | constructed toggle rows at clock 90-94 (cursed/blessed under rule-true, full TB classes under rule-false) | Rule50=0: toggle changes the search on **5 of 5 rows** (after-toggle vs manual-Clear-Hash node counts differ; e.g. 5,383,534 vs 1,035,810); the root CLASS stayed correct on all 5 | Rule50=2: still node-count differences on 5 of 5 (915,895 vs 1,237,810) — my comparison cannot separate the fix's clear from history warmth; **the class-level fault (branch: 101+57 of 400 six-men rows) did not appear on my shallow rows** | PARTIALLY: the mechanism (stale entries alter the search) shows; the class-level fault and the node-identity fix are not demonstrated at my depths |
| G7 | constructed warm→raised-clock rows (KQvK dtz 17 → clock 95; KRvK dtz 29 → clock 83) | warm search at clock 0: `cp 31870` (probe fired); the same TT at the raised clock: row 2 took **33,062,467 nodes vs 2,842,704 fresh (11.6x)** — the stale win entries waste the search; the final class recovered (cp 2, correct) | Rule50=1: **identical output to bit-off** on both rows — the stored scores my rows produce were completable at those clocks (small k), so the read rule rightly left them | NOT SHOWN at claim level: the branch's engineered read rows (read.k0.tsv/read.mate.tsv, 6-men) need the full set; my rows show the cost effect only |
| G2 | scan: 250 constructed 4-men roots (14 materials), depth 10, root score class vs oracle | **0 disagreements** | **0 disagreements** | YES — the branch itself reports "false root claims 0 on both" over 200,000 roots and says the root does NOT separate the engines; its 2991-at-the-node count needs its claim harness (`BENCH.md`), which I did not run |
| G1 | the branch's own `zz2roots.fens`, the 146 four-men rows, first 60, depth 14 (bits 1+2 on in both runs; bit 4 off = SyzygyTbBounds 3, on = 7) | root outputs **identical to bit-on on all 60 rows** (0 diff lines) | — | CONSISTENT: the branch's 12 wrong null cuts are at-the-node findings from its instrumented run; root-invisible here as its own root-level zeros suggest |
| G3 | activity probe: 4-men and 5-men roots (probes demonstrably fire — TB-band scores in the output), bit 2 off vs on, depth 12-14 | vs | no output difference on **10 of 10 rows** | NOT SHOWN: the contamination is statistical inside one search (branch: 96,932 of ~4.4M updates, instrumented); nothing root-visible at my depths |

Every raw output is committed: `step2/P_step2_<fault>_<state>.txt` (14 files);
the driver and its exact commands are `scripts/s2_harness.py`.

## Step 3 — all fixes on

a. Tree G macros-on, tables loaded, `SyzygyTbBounds=7 SyzygyRootExact=3
   SyzygyRule50=3`: bench 11 **312697**, bench 13 **852857**, bench 16
   **2670573** (`step3/S3a_*.txt`). Against the fixes-off numbers on the same
   subset (312697 / 852834 / 2682662): d11 unchanged, d13 +23 nodes, d16
   −12,089 — the fixes demonstrably act while tables are loaded.
b. 100 endgame openings (6-8 men) generated exactly as the job says: the
   first 2,000 UHO openings played out with `go nodes 5000` per move until
   ≤8 men, first 100 kept (`step3/endgame100.txt`, produced by
   `scripts/gen_endgames.py`). 200 games, tree G against itself, all bits on
   (cand) vs off (base), tables on both, nodes 20000, Threads 1, Hash 16:
   **W-L-D 70-69-61, pair counts [0, 1, 97, 2, 0], 0 crashes, 0 illegal
   moves, 0 abandoned** (`matches/match_games_and_tail.txt`). Not an Elo
   measurement; the fixed engine played whole endgames without a fault.
c. ASan+UBSan build of tree G with the three macros
   (`build_asan/`): the planted-fault program reports its heap overflow
   (exit 1) — the tool proven first; then bench 13 with tables and all bits
   on: **852857 nodes, exactly the release number, zero sanitizer/error
   lines**; then 50 of the endgame positions with `go nodes 20000`: 50/50
   answers, **empty stderr** (`step3/S3c_*`).

## Files of the repository I opened

- `handoff/...`: `FABLE_TO_glmflash4_6.md`.
- Branch `opus-syzygy-gaps-20261107` (commit 04e6aa4b9c16611bae55b5d115ae9072aececfd1): `opus_syzygy_gaps/patches/syzygy_gaps_after_p6.patch` (all 18 hunks), `fixtures/TABLES.sha256`, `fixtures/f1.toggle.fens`/`clock.fens`/`zz2roots.fens`/`read.k0.tsv` (formats + materials only), plus, in job 5 (same session): README/GAP_LEDGER/REPORT/STATUS/BENCH/HANDOFF.
- Branch `opus-r13-p6-syzygy` (5f9a9606525d704c40d1479d2cc3ded363d66e99): `opus_r13/p6/syzygy_port.patch`.
- Branch `qa-syzygy-gaps-fixes-20261109`: `opus_r13/p6/ci_fetch_tables.sh` (read to learn the mirror the project uses).
- Commit `d4f43124`: `src/uci.cpp` (the Syzygy option branches, read around the patched hook) and the tree's structure; the port patch's changes I verified by `patch` output, not by reading its diff.
- github.com/niklasf/python-chess: `data/syzygy/regular/` (the table files + SOURCE.txt).

## Commands (all of them)

`date -u`; `curl -sSL https://tablebase.lichess.ovh/tables/standard/` (BLOCKED — SSL reset; recorded);
`cursor-cloud network-info` (the allowlist — lichess absent);
GitHub searches (`search_repositories` ×2, `gh api search/repositories` ×2, code search — rate-limited 429);
`git fetch --depth 1 origin qa-syzygy-gaps-fixes-20261109` + `git show` of its `ci_fetch_tables.sh`;
`git clone --depth 1 https://github.com/niklasf/python-chess.git`; file copies from its `data/syzygy/regular/`;
`sha256sum` over the 70 files + the python comparison against `TABLES.sha256`;
`git archive d4f43124... | tar -x -C /tmp/syzP` and `/tmp/syzG`; `patch -p1 -F0` (port; port+gaps);
`cmake`/`cmake --build` for tree P, tree G (plain + macros-on + ASan);
`uci_feed.sh` bench runs (G no-tables ×4; P tables ×3; G tables ×3; G macros-on all-bits ×3; ASan ×1);
`identity_run.py` 500-position ×2 (P, G) and 50-position ×1 (ASan);
`s2_harness.py` runs: g8off, g8on, g7off, g7on, g6off, g6on, g5off, g5on,
g2off, g2on, g1off, g1on, g3 (each its own process; two earlier g8/g7
iterations were DISCARDED as mis-designed — first with the toggle fixture's
6-men rows filtered to zero, then with a ucinewgame in every search that
destroyed the TT continuity the tests need; the harness fixes are in the
committed script's history note);
`gen_endgames.py` (first version had a driver bug — the engine was never told
the new position between moves; fixed, rerun);
`run_match.sh j6_match` (the 200-game match);
`make_match_file_j6.sh` (evidence assembly). NOTHING of the branch's scripts was run.

## Stamps (date -u / mtimes / match stamps)

- 21:06:10 first tablebase.lichess.ovh attempt (BLOCKED recorded)
- 21:06-21:08 mirror search (GitHub/HF/QA branch); 21:07:5x python-chess clone; tables staged
- 21:08:32 trees P and G built (both patches applied clean)
- ~21:09-21:10 step 1 benches + 500-position identity (P=G identical)
- 21:12:28 tree G macros-on build finished (build_gaps)
- 21:13-21:21 step 2 first iterations (discarded: fixture rows 6-men → 0 rows; then the ucinewgame bug) — the discarded outputs are overwritten by the final ones
- 21:22-21:24 G8 fixed reference (manual Clear Hash), rerun both states
- 21:25:09-21:26:00 final step-2 outputs (G7, G6, G5, G2, G1, G3) — file mtimes
- 21:27:2x step 3a benches; ASan build finished (background, started ~21:24)
- 21:27:59-21:28:31 the 200-game match (stamps.txt, exit 0)
- 21:28:3x-21:28:4x ASan bench + 50 positions + table verification file
- 21:29-21:35 this report, commit, push

## What I did not do

- I did not run ANY script of the syzygy branches (the job forbids it twice);
  every driver is mine.
- I did not obtain the full 145+145 table set (unreachable; see the
  deviation) and therefore did not reproduce the branch's known pins with
  tables; the pins were replaced by the same-subset P-vs-G identity.
- I did not run the branch's claim harness, boundary-walk fixtures, or
  read-side fixtures; G2/G3/G7's at-the-node evidence is quoted, not
  re-measured.
- I did not test the w6p6/combined patches here (they do not fit this tree;
  job 5's finding).
- No PR was opened; nothing outside my own branch was pushed or changed.

## What I am not sure about

- Whether the G8 clear-hook "should" have produced node-identical searches in
  my hand test: my comparison carries a history-warmth asymmetry I could not
  remove without also clearing the histories (which is `ucinewgame`, not what
  the fix does). The branch's own fixture for G8 is 6-men; my 4-men rows may
  simply be too shallow for the class-level fault.
- The G7 read rule changed nothing on my two rows; I believe (from reading
  `tb_score_fits_clock`) that my rows' stored scores were all completable at
  their clocks, so the rule rightly left them — but I did not verify the
  stored k values independently.
- The subset's 6 regenerated 3-man tables: values are mathematically
  determined, but I did not cross-check them against a second independent
  source; the branch's oracle numbers were produced with ITS tables.
- My constructed G5/G6/G7 cases show the MECHANISMS; how often such positions
  arise in real games is the branch's own open question, unanswered by me.

## A better way

- The egress policy should allowlist `tablebase.lichess.ovh` (and/or
  `tablebase.sesse.net`) for tablebase jobs on this machine; the job text
  should carry the reachable-mirror fallback rule that the branch's own
  `ci_fetch_tables.sh` already implements (mirror override + per-file md5),
  with the pack's `TABLES.sha256` as the verification target.
- python-chess's 3-4-man test tables are a FREE, officially-hosted subset
  that covers every 3-4-men mechanism in this pack (64/70 files
  byte-identical to the project's list). For root-visible faults (G5, G6) a
  4-men subset is enough to demonstrate fix-on/fix-off differences; a job
  that wants the full fixture scale should say which host to use when the
  primary is unreachable.
- My first two G8/G7 harness designs were wrong in ways only the OUTPUT could
  reveal (0 rows; then warm-history confounds). The cheap guard: before a
  hand-test battery, print the material distribution of the fixture and run
  ONE smoke row per state; both bugs surfaced there in seconds.
- The 200-game robustness match finished in 31 s at 20,000 nodes because the
  openings are 6-8-men; if a future job wants more coverage per minute,
  deeper node counts on few-men openings are nearly free compared to
  middlegame matches.

## Model

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run.
