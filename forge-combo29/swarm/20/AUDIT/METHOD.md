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

## Writing a finding
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
3. **State build + settings in every line.** Base `6b98f217` vs PC r15; `none` / `S14` / `PC20`; Threads 1 unless the
   job is about threading.
4. **A zero needs a planted one** (FABLE file 2, rule 1). Every "0 findings" of mine has a planted control through the
   same harness, or it is labelled "not shown".
5. **Pre-state the rule before measuring.** The worse-than-noise-band rule for the MultiPV class test, and the
   "UNSAFE if median depth < half healthy" rule for the Hash boundary, were both written before the numbers.

## Measuring
6. **Cold or warm — always say which.** A fresh process per search and one long-lived process differ by ~2 plies at a
   fixed clock (S-F51). Any clock table without that word is not a number.
7. **Check the machine before and after a timing or depth run**: `machine_clean.sh` (exit 0 = fit to measure). A leaked
   engine process of mine held a core for 3,400 s and produced one bogus probe, which I withdrew.
8. **Both clocks in every `go` line.** A one-sided clock hangs when the OMITTED clock is the side to move's (S-C39).
9. **Never add a timing number I measured badly.** I declined to re-quote seat 30's speed table because this shared-but-
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
