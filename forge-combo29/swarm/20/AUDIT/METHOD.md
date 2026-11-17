# METHOD — the rules I hold myself to, and the tools that enforce the mechanical ones

> **RULE 0 (put first because I got it wrong twice): before calling a candidate worse, check that the REFERENCE is
> working.** Two findings died of this. S-C20 confirmed a "defect" against a UCI definition I never looked up. My job-67
> verdict rejected a working patch because I compared it to a build that had **collapsed to depth 1 with no usable
> lines** — so the candidate "differed" by hundreds of centipawns from garbage. In both cases the comparison was fine
> and the yardstick was broken. **A difference is evidence only if both sides are trustworthy**; check the reference
> behaves sensibly (produces output, does not collapse, reproduces a known value) *before* you read the delta.

> **RULE 0b: a declared gap must be MEASURED before a candidate is called ready.** I could have declared the 8 MB
> alternate table a success after S-C43/S-C44 — median 0 cp, tolerance passed, MultiPV 8 best-case, no saturation at
> 4x clock. Every number was true and the conclusion would have been wrong: the one regime I kept naming as "the
> honest boundary" (deep endgames, depth 23) is where it fails (p90 112 cp against a 100 cp limit, S-C45). **The gap
> you keep declaring is usually the answer.** This is RULE 0's sibling: check the reference is working, *and* check
> the regime you did not test.

## ASK FOR PROVENANCE BEFORE REFUTING (learned from a near-miss)

When another seat's number did not reproduce for me, the instinct that mattered was: **ask for the executable's
identity and the exact ordered option list before saying "refuted"**. I recorded "NOT REPRODUCED, not refuted" and
requested both. That was the right call, and here is the honest accounting of what it bought.

**What it did not do:** provenance was *not* the cause. Their binary turned out to be identical to mine (same sha256).

**What it did:** it removed a whole hypothesis class for one line of work — with the hash in hand "different build" was
off the table — and the request for the **ordered option list** is what surfaced that their S14 list carried no `Hash`
or `Threads`. That pointed at option *construction*, which was the actual bug: they passed the six PC20 extras **alone**
over default options, never S14+six. Six-over-defaults reproduces their `f3g3 / cp 1627` exactly; true PC20 gives
`f3g2 / cp 1790`, exactly mine.

So: **the asking is what narrowed the search to the bug, even though the thing I asked about was innocent.** A refusal
to refute without provenance costs one round trip and buys the elimination of the wrong explanation.

## A LARGE CENTIPAWNS SCORE IS NOT A DEFECT; A SHORT MATE PV IS

Seat 05's violator showed `cp 4056` at `go nodes 20000` where a deeper search finds `mate 7`, and I first wrote that up
as a defect. It was not: at 20,000 nodes **no mate had been claimed at all** — the engine was reporting an honestly
unfinished search, and a huge winning score with no mate claim misleads nobody. The real truncation on that board is at
**50,000** nodes, where it claims `mate 11` with an 18-ply PV needing 22.

**The discriminator, reusable:**
- **DEFECT — truncation:** a `mate N` claim whose PV is **shorter than 2|N| at the depth the claim first appears.**
- **NOT a defect — unfound mate:** **no** `mate` claim at the shallow limit; a `cp` score that is merely less
  informed. Reporting +4000 cp for a won position whose mate you have not proven is correct behaviour.

To apply it you must find **the depth at which the mate claim first appears** and test the PV *there* — not compare a
budget-limited score against a deeper one and call the difference a fault. That was my S-C48b error. The sentence that generalises it, past mates to ANY
budget-versus-depth comparison:

> **Ask whether the shallow arm had any right to know the answer before you call its answer wrong.**

A search given 20,000 nodes and one given 250,000 are not two measurements of the same thing; the cheap one is
*allowed* to be less informed. Comparing them and labelling the difference a defect mistakes **a budget for a bug**.
This is RULE 0 in its general form: check that the reference is working — here, check that the reference was even
*entitled* to the result you are comparing against.

## NAME THE CONSTRUCTION, WITH ITS OPTION COUNT

**A config that is wrong by construction looks exactly like a config that is right.** Seat 30's retracted 30-F59 came
from a "PC20 arm" that passed the six extra switches **alone** over default options instead of on top of S14 — and it
still produced a plausible score and a legal move, so nothing downstream could tell. It was catchable only by asking
for the ordered option list.

Two practices, both cheap:

1. **Name the construction in the finding line, with the count.** Mine reads `S14 (17 options) + 6 extras`, not
   "PC20". A count is checkable at a glance: 17 = the 14 S14 settings + Threads + Hash + OwnBook false. If someone
   claims "PC20", 17+5 is the number that must appear.
2. **Assert it where the config is built.** `AUDIT/hardened.py` now has
   `assert_regime(opts, "PC20")`, which raises if the S14 settings, the five extra switches or Threads/Hash are
   missing. Tested both ways: a true PC20 passes, an extras-only list is rejected with the missing names listed. This
   is the check that would have caught the bug at the moment it was written, rather than two hours later by inference.

## THE BINARY RULE (found while failing to re-check another seat)

**A behavioural claim needs the EXECUTABLE'S IDENTITY in the file — sha256 and `id name` — not just its settings.
Regime plus binary is a complete citation; either alone is half.**

Why: I could not reproduce seat 30's 30-F59 (PC20 playing a 200 cp worse move). I ruled out the option list and the
Hash, but their `check17/` files record **no exe hash and no `id name`**, so I cannot show their binary is mine. That
turns a possible refutation into a bare "unreproduced", which is much weaker than either verdict.

**And the check caught me too:** auditing my own folder, **none of job55, job61, job64, job66, job69, job70 or job71
recorded the exe sha256** — the same gap I was about to criticise. Settings without a binary are half a citation.

The fix is mechanical: `AUDIT/hardened.py` now exposes `exe_identity(exe)` returning `{exe, sha256, id_name}`, to be
dumped into every job's meta/JSON. Regime (S-F44) plus binary is a complete citation.

## THE DRIVER RULE (hard rule; seat 19's sweep found 222 of my files that violated it)

**Every engine interaction must read stdout until `bestmove` before sending anything else — and every row whose
search produced ZERO `info depth` lines must ABORT the job, not be recorded.**

Why it is stated this brutally: my `job3/fallback.sh` piped `position`/`go`/`quit` together. `quit` wins, and the
engine answers with its **first generated move** — a `bestmove` with no search behind it. That produced **222 committed
files containing zero `info depth` lines**, every one of them a fabricated answer sitting in an evidence directory.
I discarded the harness and the conclusions were unaffected (verified: no finding cited those files), but the output
stayed there, unlabelled, looking like evidence to anyone scanning the branch.

The rule in practice:
- `AUDIT/hardened.py` is the only driver: it writes a command, reads to the answer, then writes the next.
- **A zero-`info depth` row is a HARNESS FAILURE, not a result**, unless the job is *about* the unsearched-move path
  (and then it must be labelled as such and paired with a control that does produce search lines).
- Committed transcripts must be **either** real engine output **or** clearly-labelled script summaries — a mechanical
  sweep cannot tell them apart, so the file must say which.

## WHEN A NUMBER CONTRADICTS A HARD BOUND, THE BOUND WINS

The fastest falsification available, and it needs no re-run. Three times tonight it settled something that more
measurement could not:

1. **A claimed "missed mate in 3" on a board with no forced mate** (my S-F21) — settled by exhaustive search proving
   no mate exists at any ply ≤ 15.
2. **A "defect" that was a budget-limited search compared against a deeper one** (my S-C48b) — settled by asking
   whether the shallow arm was *entitled* to the answer.
3. **`mate -25` on K vs K+R** (seat 27's withdrawal, which I verified) — 49 plies required, material maximum is 31.
   **Arithmetically impossible**, so no harness or build question needs asking.

**The rule: when a number contradicts a hard bound, the bound wins and the measurement is over.** State the bound, cite
how it was computed, and stop — do not spend an hour re-running a harness to explain a number that cannot be true.

**THE PRE-CHECK — one line anyone can run before reporting a mate, with python-chess and arithmetic:**

1. **Material maximum:** `K+R` or `K+Q` versus a lone king is **at most 16 moves (31 plies)**. **`K+B` or `K+N` alone
   versus a lone king is NOT a forced win at all.** Two bishops or B+N can force mate but need far more than a shallow
   search.
2. **The arithmetic:** a `mate N` score claims **2|N| plies** (N<0) or **2N−1** (N>0). If that number **exceeds the
   material's maximum**, the score is impossible — full stop.
3. **So the check is:** read the material, write down the maximum, compare plies. Ten seconds, no harness.

**Why this is the preferred route: a withdrawal by bound is STRONGER than any re-run would have been.** A re-run shows
*that* a number did not come out again and invites "different build, different harness, different machine". A bound
shows that the number **could not have come out of any engine on that material** — it is a statement about the position,
not about the measurement, and it cannot be argued with.

Also worth checking: node count against the budget given; depth against the depth limit; a score against the score
range the position's material allows.

## REPORT COUNTS, NOT RATES, AND NEVER AVERAGE ACROSS KINDS

When an event is **categorical** — a mate appears, a move changes, a crash occurs — the honest unit is a **count over
a stated denominator**, not a rate and never a magnitude.

Three cases where I held to this tonight:
- **"1 of 4 sparse boards had a mate appear; 0 of 4 full-material"** (S-C53) — a count. n=4 is not a rate.
- **Refusing to convert `mate 9` to centipawns to average it against `cp 4302`** — that mapping is arbitrary and yields
  seat 08's "meaningless 106×". An average across a categorical change and a continuous one is not a number about
  anything.
- **`go nodes 20000` truncation: "short by 4 plies", not "30 % wrong"** — plies are the unit the claim is made in.

**The test: if you had to explain the unit to the owner, would he agree two different values are the same kind of
thing?** A mate and a centipawn score are not; two depths are; two plies short are. When they are not, report the
counts separately and let him compare what he cares about.

## WRITING A FINDING
1. **Write the row and the job file together, or verify the row count after any append.** I lost this once: a heredoc
   appended the FINDINGS row, failed before writing the job file, and I re-appended — the same finding ended up in the
   file **twice**, and a second row kept a stale "STILL LIVE" status after its finding was withdrawn. Both were
   invisible to a normal read. `findings_lint.py` now catches both classes (exit 0 = clean).
2. **`mkdir -p` the job directory BEFORE writing its files.** I lost this three times: a heredoc that writes
   `jobN/<file>` fails if `jobN/` does not exist, and worse, it fails *after* the FINDINGS row was appended — so the
   row lands without its evidence file and a retry duplicates it. Either `mkdir -p` first, or use a file-writing tool
   that creates the path.
3. **Quote the thing, do not paraphrase it.** S-F28 was a citation until I extracted the verbatim text with its
   commit, blob and sha256.
4. **State build + settings in every line.** Base `6b98f217` vs PC r15; `none` / `S14` / `PC20`; Threads 1 unless the
   job is about threading.
5. **A zero needs a planted one** (FABLE file 2, rule 1). Every "0 findings" of mine has a planted control through the
   same harness, or it is labelled "not shown".
6. **Pre-state the rule before measuring.** The worse-than-noise-band rule for the MultiPV class test, and the
   "UNSAFE if median depth < half healthy" rule for the Hash boundary, were both written before the numbers.

## MEASURING
7. **Cold or warm — always say which.** A fresh process per search and one long-lived process differ by ~2 plies at a
   fixed clock (S-F51). Any clock table without that word is not a number.
8. **Check the machine before and after a timing or depth run**: `machine_clean.sh` (exit 0 = fit to measure). A leaked
   engine process of mine held a core for 3,400 s and produced one bogus probe, which I withdrew.
9. **Both clocks in every `go` line.** A one-sided clock hangs when the OMITTED clock is the side to move's (S-C39).
10. **Never add a timing number I measured badly.** I declined to re-quote seat 30's speed table because this shared-but-
   single-tenant box needs their interleaved method; a weak number in an owner-facing page is worse than none.

## Correcting myself
10. **Withdraw in place, and make the retraction visible in column one.** The retracted row keeps its original text with
    the wrong reasoning struck through; the withdrawal row's id cell reads `S-X WITHDRAWN`. Both lead with the
    retraction so neither can be quoted out of context.
11. **A confirmation of "X is wrong" is only as good as the definition of "right" behind it.** S-C20 was withdrawn for
    confirming a UCI-semantics claim I never looked up: `mate y` is for the side to move, so y = 0 means already mated.
    For protocol semantics the definition is checkable text, not intuition.
12. **Do not let a self-correction disappear into a later paragraph.** S-F49's cold depth figure got its own qualifier
    line (S-F49a) rather than an edit, because FINDINGS is add-only and a reader may quote the original.

## The tools
- `AUDIT/hardened.py` — the only engine driver: reads to `bestmove` before `quit`, refuses without `readyok`, flags
  unsearched answers.
- `AUDIT/machine_clean.sh` — exit 0 = fit to measure (busy forge procs, >50 % CPU processes, loadavg vs cores; zombies
  excluded because a defunct process holds no CPU).
- `AUDIT/findings_lint.py` — exit 0 = FINDINGS holds together (duplicate ids only as retraction pairs, no retracted id
  with a bare LIVE status, no malformed rows).
- `AUDIT/parse_audit.py`, `AUDIT/bundle_audit.py` — do my checkers pass a verdict when nothing was parsed; does any file
  let a bundle claim be read as a single-switch cause.
