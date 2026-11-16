# deepseek6 long 23 — RECOUNT of glmflash5's jobs 23 and 24

Branch: for-fable-and-opus/deepseek6-work
Model: DeepSeek V4.1 Flash 1017
Item: the list's long 23 — "RECOUNT glmflash5's jobs 23 and 24 from its `gamelist_M*.txt` files with your own
code: W-L-D, the five pair outcomes, pair Elo with its 95 % interval, how many openings any two matches share.
We recounted both; our numbers are held back until your report."

## 1. What was asked, the answer, how sure

**Asked:** an independent recount of ten committed match lists (M51–M54 job 23, M55–M60 job 24) plus the
opening-overlap matrix.

**Answer:** the numbers reproduce **exactly**. All ten W-L-D triples, all ten n5 vectors, all ten Elo points and
all ten 95 % intervals equal glmflash5's to the last printed digit (`recount_out.txt` vs
`evidence/glm_job23_stats_out_committed.txt` / `evidence/glm_job24_stats_out_committed.txt`); my own pair-level
bootstrap over 20,000 resamples lands within ±0.3 Elo of every closed-form interval. The opening answer is
**2 of 105 pairs share openings, not 0**: `M53 & M54` share all 1000 (both `start=2001` on job 23's file — the
deliberate job-23/24 repeat) and `M46 & M50` share all 1000 (the same 1000 openings replayed at 20000 nodes
instead of 2000 — a job-22 pair, not a job-23/24 pair). Every other pair shares nothing.

**How sure:** high on the recount — it is arithmetic over committed text, my tool shares no line with theirs, and
the only disagreement I ever had (my first intervals were exactly 2× too wide) was my own half-point unit bug,
found and fixed by the bootstrap. High on the overlap counts. **Medium-low on one of their labels**: their
job-23 committed `job23_stats_out.txt` contains a line their own committed `job23_stats.py` cannot produce (3).

## 2. Honesty numbers (raw output files in `raw/`)

Build: `/tmp/ds6/build-release/forge`, commit 6b98f217, GCC 13.3.0, `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`,
sha256 `7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`, `id name Chess Engine Forge 6.4.24
candidate`. Fresh process per line; the four commands were typed into a file and piped in.

| pin | required | measured | file |
|---|---|---|---|
| bench 11 | 312866 | **312866** | `raw/bench11.txt` |
| bench 13 | 862329 | **862329** | `raw/bench13.txt` |
| bench 16 | 3024920 | **3024920** | `raw/bench16.txt` |
| go perft 5 | 4865609 | **4865609** | `raw/perft5.txt` |

All four exact. This item runs no engine search at all (it recounts committed game lists), so the four pins
serve only to show that the build this report's numbers come from is the honest base build.

## 3. Step table

| step | state | evidence file | result |
|---|---|---|---|
| claim before the first command | done | `CLAIM.txt`, commit `919278bdd` | claimed 19:21:58Z, GLM's long 22 claim was live so I took 23 |
| prediction before the first count | done | `PREDICTION.md`, commit "deepseek6 long 23 prediction" | 8 predictions, each with its kill range |
| honesty check (4 pins) | done | `raw/bench11.txt` `raw/bench13.txt` `raw/bench16.txt` `raw/perft5.txt` | all four exact |
| my own recount tool (no line of theirs) | done | `recount_long23.py`, `recount_out.txt`, `recount_out_all.txt` | see section 4 |
| the ten lists, W-L-D / n5 / Elo / 95 % | done | `recount_out_all.txt` | all ten equal theirs to the printed digit |
| bootstrap interval check, 20,000 resamples | done | `recount_out_all.txt` (one line per match) | every closed-form interval confirmed |
| M49 recounted from its own rows | done | `recount_out_all.txt` | n5 `[79,207,386,208,120]` rebuilt, = theirs |
| opening overlap, all pairs | done | `overlap_long23.py`, `overlap_out.txt` | 2 of 105 non-zero, both "same openings" cases |
| opening slice audit vs the .epd | done | `evidence/openingcheck_all.txt` | all 10 windows exact, all 1000 openings in order |
| their own job-24 script re-run | done | `evidence/glm_job24_stats_rerun.txt` | **byte-identical** to their committed output |
| their own job-23 script re-run | done | `evidence/glm_job23_stats_rerun2.txt` | **fails**, and cannot print their three-look pool line |
| spread between looks vs one strength | done | `heterogeneity_long23.py`, `heterogeneity_out.txt`, `chi2_out.txt` | Q 8.351 / df 4, p = 0.080 — no evidence of real spread |
| the pools they published, recomputed | done | `pools_long23.py`, `pools_out.txt` | all four pool lines equal theirs |

## 4. Findings, each with the command that shows it again

**F1. The ten matches reproduce to the digit.**
`python3 recount_long23.py in` (with `MATCHES="M49 M51 M52 … M60"` for the M49 line) prints, per match, the same
W-L-D, n5, Elo and 95 % interval that their `job23_stats_out.txt` / `job24_stats_out.txt` hold. One example
(`M55`): mine `W-L-D=744-649-607 n5=[84, 197, 373, 232, 114] Elo=+16.52 95%[+4.63,+28.40]`; theirs is the same
line. Ten of ten matches equal.

**F2. Their intervals are right, and my first ones were wrong — the bootstrap is what caught it.**
The first run printed `M51 … 95%[-27.27,+19.28]`, exactly twice their width: I had treated n5's index as points
when it is half-points. After the fix the closed form gives `[-15.63,+7.64]` and the 20,000-resample bootstrap
gives `[-15.47,+7.64]` — two different algebras, one answer. `grep bootstrap recount_out.txt`.
The bug itself is checkable from M51's published n5 alone: `evidence/interval_unit_bug.py` re-derives both
intervals and prints width 46.54 with the half-point confusion against 23.27 without, ratio exactly 2.0000
(`evidence/interval_unit_bug.txt` is its output).

**F3. The opening answer is 2 of 105, and both are "same openings, different node budget or deliberate replay".**
`python3 overlap_long23.py in` prints the full 15×15 matrix. Only `M46&M50` and `M53&M54` are non-zero, each
1000 of 1000. Their commands show why: `M46` and `M50` both use `-openings …job22.epd start=1` and differ only in
`nodes=2000` vs `nodes=20000`; `M53` and `M54` both use `start=2001` on job 23's file. So M54 is a **replay of
M53's openings at 10× the budget**, and their `POOL variant@20000 (M54+M59)` therefore contains 1000 openings
already counted at 2000 in `M53`'s group — a real, if small, dependence between their "variant@2000" and
"variant@20000" pools.

**F4. Their job-24 script reproduces their job-24 output byte for byte; their job-23 script does not.**
`cd evidence && python3 glm_job24_stats.py M55 M56 M57 M58 M59 M60` needs `/tmp/evid/openings_job24.epd`
present, then its output is identical to their committed file (`diff` empty; `glm_job24_stats_rerun.txt`).
`python3 glm_job23_stats.py M51 M52 M53 M54` dies with `KeyError: 'M50x'` at line 57 — it expects a match named
`M50x` that it never loads — and it prints **one** pool line where their committed output has **two**; the
"THREE looks" pool line in their committed file (`pairs=3000 n5=[283,624,1141,625,327] Elo=+5.15`) was **not**
produced by the script they committed. My own recount produces that exact line from the three n5 vectors
(`pools_out.txt`), so the number is right and only its provenance is wrong: the committed script was edited
after its output was saved.

**F5. The spread between looks is ordinary noise — the pooled interval is not conservative, it is the right size.**
Cochran's Q over the five 2000-node variant looks: `Q=8.351` on 4 df, `p=0.080` (`chi2_out.txt`). Under the
usual 5 % gate that is *not* heterogeneity, so their fixed-effect pool `+6.67 [+1.35,+12.00]` stands. But
p=0.08 is close, and for that pool the random-effects interval would be `+6.65 [-1.04,+14.34]` — 8 Elo wider on
each side. The other four groups are clean (`p` = 0.58, 0.40, 0.54, 0.28). Worth knowing before anyone quotes
`+6.67 [+1.35,+12.00]` as a hard positive: over five looks of one configuration, the between-look scatter alone
could produce this.

**F6. Their "identity endings" line is arithmetically true but it is a tautology in these configs, not a check.**
In all ten lists `white_mates + black_mates = W + L` exactly, and `decisive/drawn ending consistency: 0
violation(s)` in `recount_out_all.txt`: every decisive game in these lists ends in mate, and no drawn game is
labelled a mate. So the identity holds because the *ending vocabulary* is {White mates, Black mates, four draw
kinds}, not because it tests the result field against the mate field. It would catch a corrupted result string,
nothing more.

**F7. Every opening slice is exactly the declared EPD window, in order.**
`evidence/openingcheck_all.txt`: for all ten matches, line `start-1+k` of the .epd equals the FEN of opening k,
for all 1000 k. So no list silently starts somewhere else.

**F8. Colour balance is exact, so no list carries a White/Black bias in the pairing.**
`recount_out_all.txt`, top block: every one of the ten has `cand_white=1000 cand_black=1000`, `bad_pairs=0`
(each pair is the same FEN with the colours swapped).

## 5. Suspicions, not proven

- **S1.** The `M50x`/`M54x` names in their job-23 script suggest an earlier draft where the job-22 R1 matches were
  loaded under those names; the committed run probably had them, then they were removed before the commit and the
  output was not regenerated. Not proven — I only know the committed pair does not run.
- **S2.** Their pool label "the previous POOL line above is M49+M51 only — its label was wrong" is a hand-written
  correction in an output file. It is right about the label, but it also means at least one pool line was typed,
  not printed. The numbers in both lines do check out against mine.
- **S3.** Whether any *single* look was cherry-picked for their report headline: `M55` at `+16.52` and `M49` at
  `+14.43` are the two extreme looks, and a `2.59`-to-`26.27` interval on a look that ought to sit near `+6` is
  the kind of thing a reader quotes by accident. I see no evidence of selection in the files; I simply note that
  the two biggest numbers are single looks.

## 6. What I read from my colleagues

- **glmflash5** (`NOTES_glmflash5.md` tail): not re-read this item beyond its job-23/24 files themselves. Its
  `job24_summary.txt` self-corrects a mislabelled pool line, which is the same habit I flag in S2.
- **kimi5**: not read this item (the item is a recount of another helper's data; nothing in kimi5's notes bears
  on it). My standing rule is to read both notes before a job file and every four hours; this item took less
  than that, so the next item refreshes them.
- I used **no** advice from either note as an instruction; the recount formulas are mine.

## 7. What I did NOT do

- **Did not run any engine match or any search.** This item is a recount; the engine build exists only to satisfy
  the honesty check, and no node count in this report comes from a search.
- **Did not recount M55–M60's opponent options beyond parsing them.** I extracted every `option.*` string from
  the ten `cmd_M*.txt` files (`evidence/config_table_raw.txt`) to confirm the *pools* group identical
  configurations, and they do: every `variant` match carries `CheckExtensionDepth=8 LmrGiveCheck=0
  LmrInCheck=0` and every `CED8alone` match carries `CheckExtensionDepth=8` and nothing else.
- **Did not re-play a single game.** No PGN exists in my inputs and I did not fetch one: the recount is of the
  result rows, which is what the item asks.
- **Did not open a pull request**, did not touch any branch but my own, did not commit any engine source.

## 8. What I am NOT sure about

- Whether `M46`/`M50` being the same openings is deliberate. Their files make it look deliberate (different node
  budgets on one opening file), but their own pool line calls the pair "M54x job21 + M50x job22", which mixes
  job numbers in a way I cannot resolve from the files I have.
- Whether the three-look pool line in their committed output came from an uncommitted newer script. I can only
  say the committed one cannot print it.
- My heterogeneity read is a Q test on five looks with p=0.080: an honest "no evidence of real spread", not a
  proof that all five measure one strength.

## 9. A better way

For the next bundle of matches, commit the **script and its output in the same commit and re-run the script
once from a clean directory before committing**, with the .epd files it needs copied into the item's folder
rather than read from `/tmp/evid`. Both failures in F4 are that one habit: a script that reads an absolute
`/tmp` path and a script that no longer matches its own saved output. A two-line `make check` (run the script,
`diff` against the saved output) would have caught it at the time.

Second: when two matches replay the same openings at different node budgets, say so in the pool label. Their
`variant@20000` pool contains `M54`, which reuses `M53`'s 1000 openings from the `@2000` group — a reader who
treats the two pools as independent is over-counting.

## 10. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

`git status --short` and `ls` of the folder, run as the last command before this report's commit:
see `final_ls.txt` in this folder (pasted verbatim there so the report itself stays text).
