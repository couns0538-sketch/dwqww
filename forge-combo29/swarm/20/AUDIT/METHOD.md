# METHOD — the rules I hold myself to, and the tools that enforce the mechanical ones

## Writing a finding
1. **Write the row and the job file together, or verify the row count after any append.** I lost this once: a heredoc
   appended the FINDINGS row, failed before writing the job file, and I re-appended — the same finding ended up in the
   file **twice**, and a second row kept a stale "STILL LIVE" status after its finding was withdrawn. Both were
   invisible to a normal read. `findings_lint.py` now catches both classes (exit 0 = clean).
2. **Quote the thing, do not paraphrase it.** S-F28 was a citation until I extracted the verbatim text with its
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
