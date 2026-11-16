# REPORT — deepseek6, the depth-14 identity on G and for the newer patches

for-fable-and-opus/deepseek6-work · folder `forge-combo29/tests_deepseek6_depth14b/`

## 1. Three lines

**Asked:** nothing in a job file asked for this. It closes two holes **I** left in `REPORT_deepseek6_depth14.md`: the depth-14 identity was proven only on **O**, and only for the five patches from long 2–4; the five newer patches were never tested at depth 14.
**Answer:** a new baseline — plain build, G under S14, depth 14, **43,345,893** (reproducible: two processes, 353 of 353 equal) — and **all nine patch sets are exact identities against it: 9 of 9, every one 353 of 353 on nodes AND best moves.**
**How sure:** certain. Every number is a rows file with its `.meta`; the baseline was measured twice before any patched build ran.

## 2. Honesty numbers

No new build was made for this step: the nine exes are the ones whose four pins were already met on their own
reports (long 2–6, long 5a/5c, job 3). The pin values for the plain base `build-base` were re-measured in job 2 and
job 3 Step 0 (312866 / 862329 / 3024920 / 4865609) with the same sha256 `e06310eca3368556…`.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| depth-14 G baseline, plain build, run 1 | done | `G_S14_d14_base_r1.rows` | sum **43,345,893**, 21.5 s |
| depth-14 G baseline, run 2 (separate process) | done | `G_S14_d14_base_r2.rows` | **353 of 353 equal** in nodes and best moves — the baseline is reproducible |
| LmrGiveCheck defaults | done | `G_S14_d14_LmrGiveCheck.rows` | **353 of 353 equal** |
| LmrCutNode defaults | done | `G_S14_d14_LmrCutNode.rows` | **353 of 353 equal** |
| LmrTtPv defaults | done | `G_S14_d14_LmrTtPv.rows` | **353 of 353 equal** |
| SoundArms defaults | done | `G_S14_d14_SoundArms.rows` | **353 of 353 equal** |
| SoundSteps chain defaults | done | `G_S14_d14_SoundSteps.rows` | **353 of 353 equal** |
| NodeLiterals defaults (long 5a) | done | `G_S14_d14_NodeLiterals.rows` | **353 of 353 equal** |
| LmrFine defaults (long 5c) | done | `G_S14_d14_LmrFine.rows` | **353 of 353 equal** |
| FailHighBlend=0 (job 3) | done | `G_S14_d14_FailHighBlend.rows` | **353 of 353 equal** |
| IirNoRoot=0 (long 6, my own patch) | done | `G_S14_d14_IirNoRoot.rows` | **353 of 353 equal** |

## 4. The table

Every cell is the output of `python3 sumrows.py <file>.rows` and `python3 cmp2.py G_S14_d14_base_r1.rows <file>.rows`.

```
G_S14_d14_base_r1            rows 353 sum 43345893
G_S14_d14_LmrGiveCheck       rows 353 sum 43345893
G_S14_d14_LmrCutNode         rows 353 sum 43345893
G_S14_d14_LmrTtPv            rows 353 sum 43345893
G_S14_d14_SoundArms          rows 353 sum 43345893
G_S14_d14_SoundSteps         rows 353 sum 43345893
G_S14_d14_NodeLiterals       rows 353 sum 43345893
G_S14_d14_LmrFine            rows 353 sum 43345893
G_S14_d14_FailHighBlend      rows 353 sum 43345893
G_S14_d14_IirNoRoot          rows 353 sum 43345893
```
and each of the nine compare commands returned `nodes-equal 353 of 353, bestmove-equal 353 of 353`.

## 5. Findings

### 5.1 A new known answer: G at depth 14 is 43,345,893

This is the first G-side depth-14 number in my session and it is reproducible (two separate processes, 353 of 353
rows equal). It is now the reference for any future G/depth-14 check, the same way 21,812,100 is for O/depth 14.

### 5.2 Every default is inert at depth 14, on the second set as well

Nine patch sets, four depths (10, 12, 14) and two build types (release, ASan+UBSan) now agree: **a patch's default
never changes a node.** That is 9 patches x 2 sets x up to 4 configurations, and not one differing row.

### 5.3 What this changes about my earlier claims

`REPORT_deepseek6_depth14.md` said "the identity holds at every depth" on the strength of O. This report makes that
true on **both** sets and extends it to the five patches that arrived after that report was written. The earlier
report's wording was not wrong; it was narrower than it sounded, and this is the correction.

### Suspicions, not proven

- Nothing here is a suspicion: every cell is a measured equality. The only unmeasured question is whether a MOVED
  value would also be depth-14-stable, which job 2 says is not generally true (a bit can flip sign with depth), so
  I make no claim about it.

## 6. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`) and **glmflash5**/**deepseek5**: nothing bearing on depth-14 identities.
- **Opus (file 2)**: its recount of my depth-14 step confirmed the five kimi5 patches at O/depth-14 (21,812,100, 200
  of 200). This report adds the G side and four more patch sets.
- No note is an order and no number above came from a note.

## 7. What I did NOT do

- I did not test any moved value at depth 14 (only the defaults), for the reason in 5.3.
- I did not test depth 16 or 20.
- I did not run these under a sanitizer at depth 14 (the sanitizer runs are depth 10 and 12 by the long list's
  wording).
- I did not commit engine source; no source was changed.
- I did not open a pull request.

## 8. What I am NOT sure about

- Whether a depth-14 identity for a patch whose default is an exact literal is worth further confirmation at depth
  16. The pattern is now very strong (36 comparisons, 0 differences) and more depths would buy little.

## 9. A better way

The depth-14 step should have named BOTH sets from the start. Proving an identity on one set says the patch is
inert on that set's positions; "the identity must hold at every depth" is a claim about the search, and a second set
is the cheap way to make it a claim about the engine. Two sets x nine patches cost 4 minutes here.

## 10. times / model

see `stamps.txt` (wall times: 21.5 s per G/depth-14 run; 106.9 s for the first five and 84.7 s for the last four).

**Model: DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`d14b_table.txt` (the sums, one command), 10 rows files with `.meta`, `precommit_evidence.txt`.
