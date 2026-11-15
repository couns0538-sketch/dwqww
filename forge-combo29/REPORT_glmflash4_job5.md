# glmflash4, job 5 report (2026-11-15)

**The seven faults in one line each** (full detail at point 2; all seven are
CLOSED in the branch's ledger, each behind a default-off switch):

1. **G2** — shallow pruning keeps running while the node's best score is a TB
   loss, so a fail-soft TB loss is stored as an upper bound and reaches
   parents and the TT as a false TB win (`SyzygyTbBounds` bit 1).
2. **G3** — correction history learns from TB-band best scores, though mate
   scores are excluded from it (`SyzygyTbBounds` bit 2).
3. **G1** — a null move returns a TB-band score as a proven bound, though in
   zugzwang passing wins and moving does not (`SyzygyTbBounds` bit 4).
4. **G5** — at exactly dtz + counter = 100 an exact win shows as a cursed
   draw and a rounded move that really draws is mixed with moves that win or
   lose: a winnable result is thrown away (`SyzygyRootExact` bits 1+2).
5. **G6** — with the DTZ table missing, WDL-only ranks report a TB win/loss
   that the 50-move clock has already ruled out (`SyzygyRootExact` bit 1).
6. **G7** — a stored TB or mate TT score is used at a clock where it can no
   longer be completed before move 100 (a drawn root is lost on the branch's
   proof position), and a TB loss distance understates a line that ends in
   mate (`SyzygyRule50` bit 1).
7. **G8** — changing `Syzygy50MoveRule` keeps TB scores stored under the
   other rule (`SyzygyRule50` bit 2; the fix clears the hash on a rule
   change).

**Do the fixes fit on top of the port?** YES for the patch the branch names
as "the change to review": on a fresh export of `d4f43124` +
`opus_r13/p6/syzygy_port.patch` (md5 verified 4342d24f, applied clean),
`patch --dry-run` of `patches/syzygy_gaps_after_p6.patch` checks all five
files with no offsets and no fuzz (exit 0). The w6p6 variant also exits 0 but
with one hunk at "fuzz 2 (offset -242 lines)" — it is meant for the
trial_w6+port line, not this tree. The combined
`syzygy_port_and_gaps_after_w6.patch` does NOT fit this tree (exit 1 with
`--forward`: 3 reversed-detection skips, 3 "which already exists" skips,
16+1+1+3+3 hunks ignored): it is a whole-tree diff (`w6_only_989399b2/` →
`w6p6g_989399b2/`) whose intended base is the trial_w6 source, which the job
did not name for fetching, so I could not test it on its real base; the
branch says its own tool applied it there ("same tree", STATUS.md trial_w6
line).

**Does any fix change the engine outside the tablebase files?** YES — the
gaps patch touches `include/forge/search.hpp`, `src/search.cpp` (11 hunks)
and `src/uci.cpp` (1 hunk) outside `syzygy.inc`/`tablebase.inc` — but EVERY
such change sits inside a `#if FORGE_SYZYGY_TB_BOUNDS / _ROOT_EXACT /
_RULE50` block whose `#else` (or gate) restores the parent's expression, so
with the macros at 0 the preprocessed source is the parent's. I read every
one of the 18 hunks; the branch's byte-identical Build A claim is consistent
with what the patch contains.

**Scripts — do not run these without knowing them:** `bootstrap_clone.ps1`
clones the repository from GitHub (line 14); `env.ps1` contacts
google.com/cloudflare.com over HTTPS to read the Date header because, by its
own STATUS.md, the PC clock is wrong (line 30); `env.ps1` also sets the
running process's CPU affinity to 0xF000 (CPUs 12-15, line 18, inherited by
children) and `warm_identity.py` sets its own process priority (line 49);
`kit_build.ps1:66` deletes its own `.o` files and `run_san.ps1:27` deletes
its own `TB_HEAP` env var. Everything else I flagged is machine-specific
paths (`J=/d/forge_jobs_20261107/opus1` in the .sh files; `C:\`/`D:\` in the
.ps1 files) and writes to the job root outside the pack folder (`out/`,
`logs/` — by design). No downloads besides the two lines above, no privilege
escalation, no system-setting changes found (the grep patterns are at
point 5). NOTHING was run: this job executed `git`, `grep`, `wc`,
`sha256sum`, `md5sum`, `patch`, `find`, `ls`, `python3` for one local
text-parsing step, and `diff`-family reads only.

**What was cut:** nothing of points 1-6; I did not read any of the 44 log
files or the 14 fixture files beyond their names and sizes, and I read
`REVIEW_LOG.md` and the four `review/` files only by their summaries in other
docs, not line by line (see "What I did not do").

## Point 1 — the inventory

Full table committed as `tests_glmflash4_job5/gaps_inventory.txt` (155 rows:
path | lines | sha256 first 16 | kind; built with `wc -l` + `sha256sum` over
the exported folder). Totals by kind:

| kind | files |
|---|---|
| report/doc (top-level .md + tools/THIRD_PARTY_NOTICES.md) | 9 |
| engine patch (patches/) | 3 |
| script (.py/.sh/.ps1 in tools/) | 75 |
| test tool source (.cpp/.c in tools/) | 4 |
| log (logs/) | 44 |
| data (fixtures/) | 14 |
| review doc (review/) | 4 |
| data (manifests) | 2 |
| **total** | **155** |

Integrity: `sha256sum -c MANIFEST.sha256` verifies **153 of 153 listed files
OK** (the two manifest files themselves are the 2 unlisted files). The branch's
own patch hashes check out: `syzygy_gaps_after_p6.patch` md5 de4da16a...,
sha256 7ebe0714... (BENCH.md lines 11-12) — I verified the md5 claim for the
PORT patch (4342d24f) directly; the gaps patches' hashes I take from
MANIFEST.sha256 (verified via the manifest check above).

## Point 2 — the seven faults

Parent for all rows: lock source `d4f43124` + `opus_r13/p6/syzygy_port.patch`
(md5 4342d24f) = kit exe 150374ff (`GAP_LEDGER.md:7`). All numbers below are
the branch's own, read in `GAP_LEDGER.md` (row lines 14-20) and `BENCH.md`;
switch defaults: every macro compiles to 0 and every `tune::` int defaults to
0 = off (`README.md:16-17`, patch hunks `search.cpp @@63` and
`search.hpp @@250`).

| fault | what goes wrong (branch's proof case) | switch (default 0) | held by | test and numbers (parent → fixed) |
|---|---|---|---|---|
| G2 | shallow pruning continues past a TB loss; fail-soft stores an upper bound that reads as a false TB win upstream | `SyzygyTbBounds` bit 1 | `search.cpp` hunks `@@112,6+130` (g_loss_floor + FORGE_LOSS_FLOOR macro), `@@1072,7+1124` (pruning gate), `@@1523,6+1590` (floor set at search start) | claim harness, 3000 roots depth 10: 2991 of 10114 pruned fail-lows wrong; 3532 false TB wins at node ends; 2700+1476 wrong TT cuts → **0 at every site** (ledger line 14; BENCH "Interior claims") |
| G3 | correction history updates from TB-band scores (mates are excluded) | `SyzygyTbBounds` bit 2 | `search.cpp` hunk `@@1224,12+1279` (the added `!((tune::SyzygyTbBounds & 2)...)` exclusion on the `update_correction` call's gate) | 96,932 of ~4.4M updates from TB-band scores → **0** (ledger line 15; "harm not measured apart") |
| G1 | null move returns a TB-band score as proof; in mutual zugzwang passing wins | `SyzygyTbBounds` bit 4 | `search.cpp` hunk `@@995,6+1040` (TB-band null score replaced by beta) | 12 wrong returned null cuts in 8 of 1250 roots two plies before mutual zugzwang (R2 finding 1) → **0** at depth 16, +0.03 % nodes (ledger line 16) |
| G5 | at dtz+counter = 100: exact win shown cursed; a rounded drawing move mixed with winners/losers; a result lost | `SyzygyRootExact` bits 1+2 | `src/syzygy.inc` hunk `@@1172,6+1172` (+100 lines: root ranks + budgeted boundary walk) and `src/tablebase.inc` hunk `@@97,6+97` (+30) | exact solver on all 4569 boundary rows (2821 fully judged): parent 197 worse kept moves on decided roots + 259 at ranks 900/-900, 430 wrong reports, 27 wrong moves, 389 wrong scores, 5 of 800 replays lose a draw → **0/0/0 on decided roots**, 107 undecided, 34+4 worse on undecided only (ledger line 17; BENCH "Boundary roots") |
| G6 | WDL-only ranks report a TB win/loss the clock already ruled out | `SyzygyRootExact` bit 1 | `src/syzygy.inc` hunks (root report logic, same +100/+9 hunks) | clock fixture: 2186 + 2169 false TB scores; clock-0 fixture: 8; partial folders: 41 + 10 → **0** everywhere (ledger line 18; BENCH "Table-rule fixtures", "Partial table folders") |
| G7 | stored TB/mate TT score used at a clock that cannot reach move 100; TB-loss distance understates a mate-ending line; proof position `8/q7/8/8/8/3Q1RK1/k7/8 b - - 87 44` loses its draw by playing a7c7 | `SyzygyRule50` bit 1 | `search.cpp` hunks `@@127,6+154` (`tb_score_fits_clock` + `FORGE_TT_SCORE_USABLE` macro with parent `#else`), `@@795,7+840` and `@@919,7+964` (qsearch and search TT read conditions), `@@1054,6+1103` + `@@1180,6+1232` + `@@1224,12+1279` (store-side longest-mate-loss raise) | warm 3000 rows: 1842 wrong TT cuts, 5 false root claims; the FEN loses its draw → **0 returned at every site**, the FEN keeps the draw; cost 288 of 308 true warm claims kept (ledger line 19; BENCH "Warm table and rule change", Stress read-side rows: mutants m7/m8 give 239,790 and 18 wrong, head 0) |
| G8 | toggling `Syzygy50MoveRule` leaves TB scores stored under the other rule | `SyzygyRule50` bit 2 | `src/uci.cpp` hunk `@@292,12+292` (clear hash on a rule change while tables are loaded) | 400 roots: 101 + 57 rows change TB class vs a manual Clear Hash → **0**, node-identical to the manual clear (ledger line 20) |

The switches are three bit masks (`SyzygyTbBounds` bits 1/2/4 = G2/G3/G1,
`SyzygyRootExact` bits 1/2 = G6/G5, `SyzygyRule50` bits 1/2 = G7/G8); the
suite's full set is `7 / 3 / 3` (`README.md:31`). Bits work alone but close
the gaps only together where the ledger says so (e.g. `SyzygyRootExact=1`
alone keeps G5's false TB losses; per-bit tables in BENCH.md lines ~150-165).

## Point 3 — what the engine patches touch, together

`patches/syzygy_gaps_after_p6.patch` (the branch's "change to review"): by my
grep count **+226 / −3 lines** over 5 files (the branch's STATUS.md says
"234 changed lines" for it and its w6p6 twin — my method counts diff payload
lines only; the 5-line difference is unexplained and I did not chase it).
Per file:

| file | hunks | what changes there |
|---|---|---|
| include/forge/search.hpp | `@@250,6+250,15` | +9: the three gated `extern int Syzygy*` declarations |
| src/search.cpp | 11 hunks (`@@63`, `@@98`, `@@112`, `@@127`, `@@795`, `@@919`, `@@995`, `@@1054`, `@@1072`, `@@1180`, `@@1224`, `@@1523`) | gated tune ints + parameters entries; `g_loss_floor`/`FORGE_LOSS_FLOOR`; `tb_score_fits_clock`/`FORGE_TT_SCORE_USABLE`; two TT-read condition swaps (qsearch + search); null-move TB guard; longest-mate-loss tracking + store-side raise; correction-exclusion; floor set at search start |
| src/syzygy.inc | `@@1172,6+1172,106`, `@@1368,10+1468,19` | +109: root ranking, budgeted boundary walk, root report — INSIDE a tablebase file |
| src/tablebase.inc | `@@97,6+97,36` | +30: INSIDE a tablebase file |
| src/uci.cpp | `@@292,12+292,22` | +10: gated `Syzygy50MoveRule` clear-hash hook |

Changes OUTSIDE the tablebase files, one by one: every search.cpp /
search.hpp / uci.cpp hunk listed above is wrapped in `#if FORGE_SYZYGY_*`
with the parent's expression in `#else` (verified hunk by hunk: the two
condition swaps, the pruning gate, the null guard, the correction exclusion,
the uci clear-hash hook); the two one-line "swaps" replace
`tte.score_usable(...)` with the macro that expands to exactly that call
when the rule-50 macro is off, and `-MateInMaxPly` with
`FORGE_LOSS_FLOOR` = `MateInMaxPly`. The tunables entries and externs are
themselves inside the gates, so no new option exists in a macros-off build.
Conclusion: with the three macros at 0 nothing outside the tablebase files
can alter the engine — which the branch backs with a byte-identical Build A
(REPORT.md "Off means off").

The other two patches: `syzygy_gaps_after_w6p6.patch` = same +226/−3 over the
same five files (one hunk re-contexted for the trial_w6+port line);
`syzygy_port_and_gaps_after_w6.patch` = +1907/−9 over the same five files
(paths prefixed `w6_only_989399b2/` → `w6p6g_989399b2/`) — the P6 port's own
non-gated changes (probing hooks in search.cpp/search.hpp/uci.cpp, the reader
in syzygy.hpp/syzygy.inc, tablebase.inc) plus the gated gaps change, as one
diff for a gate build on trial_w6.

## Point 4 — do the patches fit? (the exact outputs)

Fresh export of `d4f43124` (source at the root), then
`patch -p1 < opus_r13/p6/syzygy_port.patch` from branch `opus-r13-p6-syzygy`:
applied clean (`fit/port_apply_output.txt`: patches
`include/forge/search.hpp`, `include/forge/syzygy.hpp`, `src/search.cpp`,
`src/syzygy.inc`, `src/tablebase.inc`, `src/uci.cpp`; md5 of the patch file
4342d24f77cfcfaeb63eb379e1635904 = the branch's claim, `GAP_LEDGER.md:7`).
Then, in the branch's own order (README "Parent and patches"):

```
$ patch -p1 --dry-run < patches/syzygy_gaps_after_p6.patch
checking file include/forge/search.hpp
checking file src/search.cpp
checking file src/syzygy.inc
checking file src/tablebase.inc
checking file src/uci.cpp
exit 0 — no offsets, no fuzz, no rejects
```

```
$ patch -p1 --dry-run < patches/syzygy_gaps_after_w6p6.patch
... 10 succeeded/offset lines, 0 fails; among them:
Hunk #11 succeeded at 1279 with fuzz 2 (offset -242 lines).
exit 0 — applies, but with fuzz and large offsets: not its intended base
```

```
$ patch -p1 --dry-run --forward < patches/syzygy_port_and_gaps_after_w6.patch
Reversed (or previously applied) patch detected!  Skipping patch.   (x3)
... which already exists!  Skipping patch.                          (x3)
16 out of 16 hunks ignored / 1 out of 1 hunk ignored (x3) / 3 out of 3 hunks ignored (x2)
exit 1 — does not fit this tree; base is trial_w6 (not fetched, not named by the job)
```

If the branch had delivered its fixes in another form: it does not — the
README's "Parent and patches" names exactly these patch files, and
`STATUS.md`/`HANDOFF.md` repeat them. The application order the branch gives:
port on d4f43124, then `syzygy_gaps_after_p6.patch` on that (the P6 line); or
the combined patch on a fresh trial_w6 tree (the w6 line), which its own
`tools/after_w6.sh` chain applies (`STATUS.md` Resume section).

## Point 5 — the scripts, read only

All 75 scripts are listed with one-line purposes in
`tests_glmflash4_job5/scripts_notes.txt` (54 descriptions quoted from the
README's own "Test tools" table, 21 are name-obvious fixture generators and
runners not listed there). Flags — anything that downloads, deletes, writes
outside its own folder, changes a system setting, or starts a program with
raised rights:

- **Downloads / network (2):** `bootstrap_clone.ps1:14`
  `cmd /c "git clone --filter=blob:none --no-checkout https://github.com/couns0538-sketch/dwqww ..."`
  (clones the repository); `env.ps1:30`
  `foreach ($u in 'https://www.google.com', 'https://www.cloudflare.com')`
  (HTTPS Date header for a clock check — STATUS.md says the PC clock is
  wrong). Nothing else: `curl|wget|Invoke-WebRequest|Invoke-RestMethod|DownloadFile|urllib|requests\.get|Start-BitsTransfer|System\.Net|WebClient|socket|http` over all 75 scripts found only these.
- **Deletes (2, both self-scoped):** `kit_build.ps1:66`
  `Remove-Item -LiteralPath "$objDir/$u.o"` (its own build objects);
  `run_san.ps1:27` `Remove-Item Env:TB_HEAP` (its own env var).
  Patterns used: `rm -rf|Remove-Item|rmdir|shutil\.rmtree|os\.remove|os\.unlink|del /` — no other hit.
- **System/process settings (2, self-scoped):** `env.ps1:18`
  `$me.ProcessorAffinity = [IntPtr]0xF000` (its own process, inherited by its
  children — the "Idle + mask 0xF000" the docs describe; not machine-wide);
  `warm_identity.py:49` `k32.SetPriorityClass...` (its own priority).
  `uci_tb.py:28-38` only READS affinity/priority. No
  `sudo|RunAs|reg add|schtasks|netsh|setx|Set-ExecutionPolicy` hit anywhere.
- **Writes outside the pack folder (by design):** the .sh scripts hardcode
  `J=/d/forge_jobs_20261107/opus1` (e.g. `after_w6.sh:11`,
  `claims_build_run.sh:6`) and write `out/`, `logs/` there; the .ps1 files
  use `C:\`/`D:\` job-root paths. They cannot run on another machine's
  layout unchanged — which matches the job's warning that they were written
  for another machine.
- **Programs started:** compilers and the built exes, as their purpose; no
  raised-rights start (`Start-Process -Verb RunAs` etc.: no hit).

## Point 6 — what the branch itself calls unproven or open

- "All strength claims are UNPROVEN: no games were played by this job, and
  nothing here says anything about Elo. Every ON path is a SEARCH CHANGE ...
  and needs QA's own SPRT after Code Review." (`README.md:3-4`; also
  REPORT.md:6, STATUS.md:23, BENCH.md:3.)
- P6 itself is unproven: "P6's own gates ... have no results, so P6 itself is
  unproven as well." (`HANDOFF.md:29-30`; ledger lines 8-10: 0 rows in
  FORGE_RESULTS.csv, the only related result a bundle H0 −26.61 nElo, "not
  attributable to Syzygy".)
- Limits (ledger lines 22-28, REPORT.md "What it costs"): the boundary walk
  decides at most 1000 moves/root and leaves **919 of 4569** purpose-built
  boundary rows undecided (mostly clocks 60-89; the independent solver also
  gave up on 812 of them); partial table sets leave 14,887 of 15,495
  boundary roots undecided; the store-side rule of `SyzygyRule50` bit 1 is
  NOT applied at a root or in qsearch — "No failing scenario was found ...
  Left as it is: no code without a failing test", "Code Review should judge
  it" (REPORT.md ~line 29-30); the WDL-only move filter can keep a 50-move
  draw; damaged-but-parsing table bodies can give wrong values (checksums
  not verified; 44 ASan runs: no crash, no out-of-range read).
- Cost stated: `SyzygyRule50` bit 1 withholds 20 of 308 true warm claims on
  the control rows (BENCH "Warm table and rule change"; HANDOFF judgement
  call 5).
- Judgement calls for Code Review, 7 of them (`HANDOFF.md:19-27`), including
  two I would second: the H1 "unconfirmed, by reading only" mate-band drift
  (a mate score read from the hash at a much deeper ply can drift into the TB
  band; "needs mates at a root ply above about 120 ... was not tested") and
  the claim harness judging mate-band claims by table result rather than mate
  distance, making those counts lower bounds (H1 finding 2).
- Own-reviews are explicitly NOT Code Review (`HANDOFF.md:15-17`); the
  pack's own bug history (B1-B6, H1) is in `REVIEW_LOG.md`.
- UNVERIFIED, not gaps (ledger lines 41-45): the two QA/CR documents
  `QA_P6_SYZYGY_QUEUE_20261101.md` and `CR_OPUS_R13_P6_SYZYGY_DELTA_20261101.md`
  "found in no git ref and in no searched folder"; six-piece behaviour
  (no 6-piece tables on that PC); strength.

## The commands I ran

`git fetch --depth 1 origin opus-syzygy-gaps-20261107` (twice — the first
FETCH_HEAD was overwritten by the second fetch below; the branch's commit is
pinned as 04e6aa4b9c16611bae55b5d115ae9072aececfd1);
`git fetch --depth 1 origin opus-r13-p6-syzygy`;
`git ls-tree -r --name-only <gaps-sha> | grep -c opus_syzygy_gaps`;
`git archive <gaps-sha> opus_syzygy_gaps | tar -x -C /tmp/gaps`;
`git archive d4f43124... | tar -x -C /tmp/syz_fit`;
`git show FETCH_HEAD:opus_r13/p6/syzygy_port.patch`;
`md5sum` (the port patch); `patch -p1` (the port, real apply, recorded
output); `patch -p1 --dry-run` ×3 (+ `--forward` variant of the third);
`sha256sum -c MANIFEST.sha256` (153 OK, 0 failed);
`wc -l` + `sha256sum` over all 155 files (the inventory);
`find`/`ls`/`sort`/`uniq -c` (structure counts);
`grep` over the patches (hunk map, macro-gate check, ± counts) and over the
75 scripts (the audit patterns at point 5);
one `python3` heredoc that parsed the README's tools table into
`scripts_notes.txt` (local text only). No script of the branch was executed.

## Stamps (date -u)

- 20:59:18 fetches started (budget start ≈ 20:59:30 when file 5 was read)
- 21:00:0x gaps commit pinned (04e6aa4b...), 155 files counted
- 21:00:3x folder exported to /tmp/gaps; README read
- 21:02:xx GAP_LEDGER read; 21:04:xx STATUS + REPORT read; 21:08:xx BENCH read
- 21:10:xx inventory built (155 rows); manifest verified (153 OK)
- 21:11:xx port patch fetched, md5 verified, applied to the fresh export
- 21:12:xx three dry-runs (first pass), re-run with true exit codes + `--forward`
- 21:14:xx hunk map + macro-gate read of all 18 hunks; ± counts
- 21:17:xx script greps (two rounds); 21:19:xx HANDOFF read; scripts_notes built
- 21:35-21:5x report written, committed, pushed

## What I did not do

- I did not run any script, build, or fixture of the branch; the only `patch`
  that modified files was the PORT patch on a throwaway export in /tmp, which
  the job's point 4 prescribes.
- I did not read the 44 `logs/` files or 14 fixture files (beyond name/size),
  `REVIEW_LOG.md`, the four `review/` reports, `IDEA_SOURCE.md`,
  `tools/THIRD_PARTY_NOTICES.md`, or the 4 tool sources line by line; their
  content reached this report only through the top-level docs.
- I did not fetch or test the trial_w6 line (the branch is not named in the
  job file), so the combined patch's fit on ITS base rests on the branch's
  own claim, not on my run.
- No PR was opened; nothing outside my own branch was pushed or changed.

## What I am not sure about

- The "+226/−3 by my grep" vs the branch's "234 changed lines" discrepancy
  (both patch variants count 229 payload lines by my method): I did not
  investigate which counting rule produces 234; the patch files themselves
  are committed on the branch and hash-verified.
- My one-line purposes for the 21 scripts not in the README's table are
  INFERRED FROM NAMES (the file marks them); I read none of them line by
  line. The flag-grep patterns cover the named classes; a pattern I did not
  think of could hide another network or delete call.
- The macro-gate conclusion ("nothing outside the tablebase files can alter
  the engine with macros at 0") is my reading of all 18 hunks plus the
  branch's byte-identical-build claim — I did not preprocess or compile
  anything to prove it myself.
- Whether the seven fixes are CORRECT is out of scope for a reading job; I
  report the branch's own evidence, not an endorsement.

## A better way

- The job asked for sha256 of every file; the branch ALREADY ships
  `MANIFEST.sha256` — my inventory's hash column therefore double-serves as a
  manifest re-verification (`sha256sum -c` first, then per-file first-16
  for the table). For future pack-mapping jobs: verify the manifest once and
  cite it, instead of hashing 155 files blind.
- The patch-fit question can be answered without a real apply: `patch
  --dry-run` after the port is enough (I applied the port for real only
  because the job said so; the dry-run of the port itself would have been
  sufficient evidence and touches nothing).
- `patch`'s interactive prompts (reversed-detection) swallow redirected
  output and can hang on a tty-less runner; `--forward` (skip reversed,
  never ask) makes such dry-runs scriptable. Worth a line in any job text
  that asks for patch fits.

## Model

I am glmflash4. The model behind this agent is GLM, trained by Z.ai; the
runtime presents it as GLM 5.3 Flash. I cannot verify a precise version
string from inside the run.
