# REPORT — deepseek6, long 64 (the eleven counters on all of G at depth 14)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long64/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** long 17's eleven counters on all of G at depth 14 under S14; the counter build's node sum must be
**43,345,893** and its rows must equal the plain rows. Table: counter | G depth 12 | G depth 14 | ratio.

**Answer:** the pin is **exact** — the counter build gives **43,345,893** and its 353 rows are **identical to the
plain build's** (353 of 353). The counters separate into two clean groups at the depth step (tree ratio **2.3473**):

- **The gate and the rfp/razor path grow WITH the tree** — gate 2.4071, rfp_ret 2.4167, razor_try 2.4011,
  razor_ret 2.3951, iir 2.3767 — all within 3 % of the tree ratio.
- **The null-move and ProbCut chain grows FASTER**: null_try **3.0019**, probcut_cut **3.0434**, probcut_enter
  **2.9376**, null_ge_beta/null_cut **2.9277** — 25–30 % above the tree ratio.

And in **absolute** terms the gate carries **54.4 %** of the whole counter growth (+11,397,421 nodes) and
`rfp_ret` **29.1 %** (+6,084,040); everything else together is under 17 %.

**How sure:** certain of every total (353 counter lines per depth, both logs committed, one command re-derives the
table). The grouping above is the measured ratio table; the mechanism sentence in F3 is inference.

## 2. Honesty numbers

Counter build: base 6b98f217 + my long-17 `ns17_counters.patch.txt`, `--fuzz=0` on a clean copy, sha256
`4bb9ccad15f65e3a3ff1230dd04fd5c40451b8a80c5f6ff8b36c55ee4541530b`; **bench 11 = 312,866** verified before the
runs.

**The item's own pin, met on the first run:**

| what | required | measured |
|---|---|---|
| counter build's G depth-14 sum | 43,345,893 | **43,345,893** |
| its rows against the plain build's | equal | **353 of 353** |

Both builds over all 353 positions, S14, Threads 1, Hash 16, OwnBook false.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed, verified on origin | done | `CLAIM.txt` | 23:41:04Z |
| prediction as its own commit | done | `PREDICTION.md` | 7 predictions |
| counter build (ns17 on clean 6b98f217) | done | `stamps.txt` | fuzz 0, bench 11 exact |
| counter G depth 14 | done | `runs/CTR_d14.rows` + `.log` | **43,345,893**, pin met |
| plain G depth 14 (the row control) | done | `runs/PLAIN_d14.rows` | 353/353 equal |
| counter G depth 12 (for the ratios) | done | `runs/CTR_d12.rows` + `.log` | 18,466,239 (the known d12 sum) |
| aggregation and ratios | done | `agg_ns17.py`, `agg_out.txt`, `ratio64.py`, `ratio_out.txt` | section 4 |
| scorecard | done | `scorecard.txt` | 5 held, 2 killed |

**Why the depth-12 G run exists:** long 17's counters were measured on **O**, and this item asks for G. A
depth-14-vs-depth-12 ratio built from O's depth-12 counters would compare two different position sets, so I ran
G's depth 12 with the counter build too (a third run). Its sum is **18,466,239**, the published G depth-12 known
sum, which is an independent confirmation that the counter build searches the plain tree at depth 12 as well.

## 4. The table (`python3 ratio64.py runs/CTR_d12.run.log runs/CTR_d14.run.log`)

Tree ratio d14/d12 = **2.3473**. "ratio / tree" is the counter's own ratio divided by that.

| counter | G depth 12 | G depth 14 | ratio | ratio / tree | share of growth |
|---|---|---|---|---|---|
| gate | 8,100,027 | 19,497,448 | 2.4071 | 1.0255 | **54.42 %** |
| razor_try | 155,244 | 372,764 | 2.4011 | 1.0229 | 1.04 % |
| razor_ret | 145,048 | 347,407 | 2.3951 | 1.0204 | 0.97 % |
| rfp_ret | 4,294,595 | 10,378,635 | 2.4167 | 1.0296 | **29.05 %** |
| null_try | 350,717 | 1,052,802 | **3.0019** | 1.2789 | 3.35 % |
| null_ge_beta | 245,298 | 718,154 | **2.9277** | 1.2473 | 2.26 % |
| null_cut | 245,298 | 718,151 | **2.9277** | 1.2472 | 2.26 % |
| null_verify | 12 | 178 | 14.8333 | 6.3193 | 0.00 % |
| probcut_enter | 223,494 | 656,529 | **2.9376** | 1.2515 | 2.07 % |
| probcut_cut | 58,446 | 177,874 | **3.0434** | 1.2965 | 0.57 % |
| iir | 610,786 | 1,451,630 | 2.3767 | 1.0125 | 4.01 % |

Per-depth buckets for every counter are in `agg_out.txt`.

## 5. Findings, each with the command that shows it again

**F1. The counters observe and change nothing at depth 14.** Counter sum = 43,345,893 = the plain build's, and
353 of 353 rows identical. Long 17's property holds at one more depth and on the other position set.

**F2. Absolute growth is the gate's and rfp's, together 83.5 % of everything.** +11,397,421 and +6,084,040 out of
+20,942,607. `iir` is a distant third (+840,844, 4.0 %). Reproduce: `ratio64.py`, the "largest absolute growths"
lines.

**F3. The null/ProbCut chain is the over-proportional group — not the depth-conditional statements I predicted.**
null_try 3.0019, probcut_cut 3.0434, probcut_enter 2.9376 and the null cutoff pair 2.9277 all run 25–30 % above the
tree's 2.3473, while `iir` (2.3767) sits essentially ON the tree ratio. In long 26 on O I found the opposite
ordering — there, probcut and iir were both over-proportional (1.122 / 1.084 against a 1.0705 tree) and the null
chain was near the tree ratio. So **which steps over-grow depends on the position set and the depth step**, and my
P4 (naming probcut_enter, iir, probcut_cut) is only two-thirds right.

**F4. `null_ge_beta` and `null_cut` differ by 3 events at depth 14** (718,154 vs 718,151) after being **exactly
equal** at depth 12 (245,298 each) and in every run of mine up to now. This is 0.0004 % of the null chain, but it
kills the "they are the same event counted twice" statement I have repeated since long 17: there is a path where a
null-move value reaches beta and does **not** return through the counted cut. Worth knowing before anyone treats
one as a proxy for the other.

**F5. `null_verify` fires 178 times at depth 14 against 12 at depth 12** — a 14.8x ratio, the largest of any
counter, and still 0.0 % of the total. On G under S14 the verification search becomes reachable at depth 14; the
count is small enough that it does not affect any ratio materially.

**F6. The gate is 1.026x the tree ratio, not exactly the tree ratio.** On O under T1 (long 26) the gate was
0.997x the tree ratio — a pure follower. On G at depth 14 it is 2.6 % above, which is the same direction as the
null/ProbCut group but a quarter of the size. The gate is not a perfect proxy for "the tree" at every depth/set.

## 6. What I read from my colleagues

- **long 17 and long 26's reports** (this session's own): the counter placements and the O depth-12/depth-14-free
  baseline they establish. The `agg_ns17.py` aggregator is long 26's, reused unchanged.
- **long 51's report** for the G depth-14 plain sum (43,345,893) — and this item's plain control reproduces it
  exactly, which is the third independent confirmation of that number.
- No colleague note was treated as an instruction.

## 7. What I did NOT do

- **Did not run O at depth 14** — the item says all of G.
- **Did not run the counters under V or CED 8 on G** — my long 18 did that on O at depth 12; nothing here repeats it.
- **Did not re-derive the counter placements** — the patch is long 17's, unchanged, and its observation-only
  property is re-verified here at a new depth.
- No pull request, no branch but mine, no engine source.

## 8. What I am NOT sure about

- The mechanism behind F3 (why the null/ProbCut chain over-grows on G at depth 14 while iir follows the tree). A
  plausible reading is that longer searches reach the null-move gate at depths where the reduced search is still
  expensive; I have no instrumentation for it.
- Whether F4's 3-event gap is deterministic or would move between runs at depth 14. Both runs are committed; a
  repeat would settle it and I did not spend the time.
- Whether the depth-12 G counters I produced here would match a future peer run; the sum does (18,466,239), the
  per-counter totals have no second source.

## 9. A better way

When an item asks for a **ratio across two depths on a set**, run the shallow side yourself even if a shallow run
exists **on a different set**. The three-run design cost about 10 minutes and is the only reason the ratio column
is a measurement rather than a cross-set guess — the same lesson as long 51, where the product had to be rebuilt
from same-depth singles.

## 10. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
