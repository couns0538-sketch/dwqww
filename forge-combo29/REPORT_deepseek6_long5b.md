# REPORT — deepseek6, long 5b (kimi5's QsSteps, its job 10 patch)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** long 5 says every new kimi5 patch with job N ≥ 9 gets the long-2 test. Two appeared since long 5a: `tests_kimi5_job10/QsSteps.patch.txt` and `tests_kimi5_job11/LmrFine.patch.txt`. This report is **QsSteps**, the lower N (long 5: "in the order of N"); LmrFine follows in 5c.
**Answer:** QsSteps adds **no UCI option at all** — it is gated by two compile-time macros, `FORGE_QS_STEPS` (default 0) and `FORGE_QS_REGRET` (default 0). Applied to a clean copy with zero fuzz. Its claim is "observe only: no value, control flow or table entry of the search changes", and that claim **holds exactly**: with the macro ON, O and G under S14 are **200 of 200 and 353 of 353 rows identical** to the macro-OFF build, and all four honesty numbers match both ways. The counters really do count (one `QSTEPS v1 nodes 4099 …` line per search, with real values) and only the ON build prints them.
**How sure:** certain. The wiring question for a macro is answered by the binary: the OFF exe has the **same sha256 as the plain base**, so the patch cannot be doing anything when off.

## 2. The honesty numbers (both builds)

| line | want | macro OFF | macro ON | files |
|---|---|---|---|---|
| `bench 11` | 312866 | **312866** | **312866** | `honesty_bench11.txt`, `on/honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | **862329** | `honesty_bench13.txt`, `on/…` |
| `bench 16` | 3024920 | **3024920** | **3024920** | `honesty_bench16.txt`, `on/…` |
| `go perft 5` | 4865609 | **4865609** | **4865609** | `honesty_perft5.txt`, `on/…` |

Clean copy `/agent/repos/p12` at 6b98f2170a3210e71beed04bbd2553972c253ed7.
Exes (`exe.sha256`):

| build | exe | sha256 |
|---|---|---|
| macro OFF | `/agent/repos/work/build-l5b-off/forge` | `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` |
| macro ON | `/agent/repos/work/build-l5b-on/forge` | `0784ccc9fcebc1b12575def377437b8df2569569f1d3d78d8aa6793bd5cdb4b3` |

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read the patch, list its new options with defaults and ranges | done | `QsSteps.patch.txt` | **no UCI options**; two macros, both default 0 |
| apply with `patch -p1` without fuzz on a clean copy | done | `patch_apply.txt` | `patching file forge-combo29/src/search.cpp`, `--fuzz=0 --dry-run` passed first |
| build it (macro OFF) | done | `exe.sha256` | Release g++ 13.3.0; **sha256 identical to the plain base** |
| build it (macro ON) | done | `exe.sha256` | Release g++ 13.3.0; different binary |
| honesty, macro OFF | done | `honesty_*.txt` | all four met |
| honesty, macro ON | done | `on/honesty_*.txt` | all four met |
| identity O/S14, macro ON vs OFF | done | `O_S14_on.rows`, `O_S14_off.rows` | **200 of 200 equal**, both sums 9,500,069 |
| identity G/S14, macro ON vs OFF | done | `G_S14_on.rows`, `G_S14_off.rows` | **353 of 353 equal**, both sums 18,466,239 |
| identity OFF vs long 1's plain base | done | `O_S14_off.rows`, `G_S14_off.rows` | **200 of 200** and **353 of 353 equal** |
| the counters actually print, and only when ON | done | `qsteps_probe_on.txt`, `qsteps_probe_off.txt` | ON: 1 `QSTEPS v1 nodes 4099 …` line; OFF: **0 QSTEPS lines**, same `bestmove d2d4` |

## 4. Findings

### 4.1 There is nothing to wire, and the binary proves it

`QsSteps.patch.txt` contains **zero** `option name` lines. It defines

```
#ifndef FORGE_QS_STEPS   / #define FORGE_QS_STEPS 0
#ifndef FORGE_QS_REGRET  / #define FORGE_QS_REGRET 0
#if FORGE_QS_REGRET && !FORGE_QS_STEPS -> #error
```
and wraps all of its code in `#if FORGE_QS_STEPS`. So the "each new option moved once off its default" half of
the long-2 test has no subject: there is no runtime option to move. What replaces it is stronger:

**the OFF build is byte-identical to the plain base.** `sha256` of `build-l5b-off/forge` is
`e06310eca3368556…`, which is exactly long 1's base exe (`tests_deepseek6_long1/exe.sha256`). Not "behaves the
same" — the same file. A patch whose disabled configuration compiles to the identical binary is inert by
construction, and that is the cleanest identity result in this session.

### 4.2 The "observe only" claim holds with the macro ON as well

This is the claim that could have been false: a counter that changes the tree (through cache effects, through a
reordered branch, through a hash read) would show up as different nodes. It does not:

```
cd forge-combo29/tests_deepseek6_long5/QsSteps
python3 cmprows.py O_S14_on.rows O_S14_off.rows   -> 200 of 200 equal   (both 9,500,069)
python3 cmprows.py G_S14_on.rows G_S14_off.rows   -> 353 of 353 equal   (both 18,466,239)
python3 cmprows.py O_S14_off.rows ../../../tests_deepseek6_long1/O_S14.rows -> 200 of 200 equal
python3 cmprows.py G_S14_off.rows ../../../tests_deepseek6_long1/G_S14.rows -> 353 of 353 equal
```
553 positions, two sets, both directions. And the honesty pins hold with the macro on, which covers a much
deeper search (bench 16) than the rows runs.

### 4.3 The counters work — this is the positive control that makes 4.2 mean something

A counter build that prints nothing would also be "observe only". It prints:

```
qsteps_probe_on.txt:  info string QSTEPS v1 nodes 4099 q0 1182 68 258 4 86 18 48 0 1 0 43 1 25 0 10 1 6 0 0 0 cs 1250 0 ...
qsteps_probe_off.txt: (no QSTEPS line at all)
both:                 bestmove d2d4
```
`nodes 4099` for `go depth 8` from startpos is a real count, and the class table behind it has nonzero entries in
several buckets. So the ON build runs its instrumentation AND every counter field it reports is reachable.

**A mistake I made and fixed, recorded because it would have produced a false "0":** my first probe sent `quit`
immediately after `go`, so the search never ran and the QSTEPS line reported `nodes 0` with every field zero. I
verified nothing was searched (the `bestmove` in that first attempt was `a2a3`, a legal but obviously-not-best
move for startpos at depth 8, where the engine normally plays `d2d4`) and re-ran it waiting for `bestmove`. This
is the exact class of error long 7 caught in `sanrun.py`; it bit me again here, and the tell was a plausible
zero.

### 4.4 `FORGE_QS_REGRET` is a second, harder-wired instrument I did not build

The patch's own comment says the regret probe "changes the tree (hash and histories are not restorable)". It
defaults to 0 and it `#error`s if turned on without `FORGE_QS_STEPS`. I built only `FORGE_QS_STEPS=1`. The
combination `FORGE_QS_STEPS=1 FORGE_QS_REGRET=1` is a tree-changing diagnostic and is **not built or tested
here**; long 5's identity question does not apply to it, and I say so rather than leave the impression that the
whole patch is inert.

### Suspicions, not proven

- Whether the ON build's `nodes` field equals the engine's own reported node count in every search. I compared
  one line (`4099` for depth 8 startpos) but did not reconcile it against the `info … nodes` of the same
  search, which is the obvious identity check for a counter that claims to count the same thing.
- Whether `FORGE_QS_STEPS=1` costs speed. The bench times in `on/honesty_*.txt` (184/507/1646 ms) look like the
  off build's (164/527/1512 ms) within noise, but I did not repeat either.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its job-9 note described `NodeLiterals` and said job 10 was the qsearch-interiors
  job. The patch's header matches: counters only, with a probe that it explicitly warns changes the tree. Its
  own design statement ("observe only") is what 4.2 falsified-or-confirmed, and it held.
- **glmflash5** (`NOTES_glmflash5.md`): nothing on qsearch counters.
- **deepseek5** (`NOTES_deepseek5.md`): its job-30 lesson ("read the state variable at the moment the event
  happens") is the same discipline a counter needs; its own counter bugs came from reading a stage one step
  late. Nothing in 4.2 depends on a counter being right — only on the tree being the same — so its lesson did
  not change what I did.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- **I did not move any option, because the patch has none.** That half of the long-2 test has no subject here;
  I substituted the macro-off/on binary comparison and say why.
- I did not build or test `FORGE_QS_REGRET=1` (a tree-changing diagnostic; not an identity question).
- I did not reconcile the QSTEPS `nodes` field against the engine's own `info … nodes`.
- I did not test `QsSteps` under a sanitizer (long 8 ran before this patch existed; the long list's after-long-8
  step does not name it, and long 8's rule is "every patch that passed long 2 to 5" — which QsSteps now has, so
  it arguably qualifies and I will run it in the next sanitizer pass).
- I did not commit engine source; the patch is committed as text.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether long 8's "every patch that passed long 2 to 5" should now pull QsSteps (and LmrFine) into a sanitizer
  run. I read long 8 as closed when it was written and long 5 as the live instruction for new patches; if the
  reading is the other way, that is one more sanitizer pass and I will do it.
- The counter's accuracy (4.6's first suspicion).

## 8. A better way

For a macro-gated patch the cheapest possible identity proof is to compare the DISABLED binary's sha256 to the
base binary's. It cost one `sha256sum` and settled the "off means off" half absolutely, where a rows run could
only have said "no difference observed". Any future macro-gated patch should start there: if the sha256s are
equal, the disabled path needs no test at all.

## 9. times

see `stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`QsSteps.patch.txt`, `patch_apply.txt`, `exe.sha256`, `honesty_*` (off) and `on/honesty_*` (on), four rows files
with `.meta`, `qsteps_probe_{on,off}.txt`, `precommit_evidence.txt`.
