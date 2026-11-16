# REPORT job 3 — AREA 2 (every option the engine lists, at min / max / min-1 / max+1 / a word / nothing)

what was asked / the answer / how sure
- Asked: every option the engine lists in its `uci` answer set to its min, max, min-1, max+1, a word, and
  nothing, between searches and during a search; per option: the answer line, any crash, and whether the next
  search is legal.
- Answer: 82 options (58 spin, 21 check, 2 string, 1 button), 550 cases. 0 crashes, 0 sanitizer lines,
  0 follow-up searches that failed to answer, 0 illegal bestmoves, 0 missed `readyok`. Out-of-range spins are
  all refused with the documented line, spins refuse a word, checks refuse a word, and the no-value case is
  refused for every spin and check. The one thing worth reporting: the button `Clear Hash` answers
  `info string invalid value for option Clear Hash` if it is sent WITH a value — including `value 0` and
  `value true`. It still clears the hash correctly when sent the correct way (no value).
- How sure: high. Every option name and range comes from the engine's own `uci` output (saved as
  `out/uci_answer.txt` and parsed into `out/options.json`), not from a list I typed, and every count below is
  a re-count of the 550 committed records by `summarise.py`, which exits if the record set is empty.

## honesty numbers

```
release build (honesty) sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
  bench 11 312866 / bench 13 862329 / bench 16 3024920 / perft 5 4865609  -> PASS (HONESTY.txt)
build under test sha256 b109a0a5acce5b0ddad5707c04f8263fe51f48a890df4a7a2ea6ffcef8a43f99
  nm __asan_ 35 / __ubsan_ 15 / __tsan_ 0; planted fault counted 3 lines, control 0 (sanitizer/NOTES.md)
```

## the table

`python3 summarise.py out` — reads `out/results.jsonl` and `out/options.json` only. Pasted:

```
cases 550 over 82 options (spin 58, check 21, string 2, button 1)
crashes                0
sanitizer lines         0
follow-up search no answer 0
illegal bestmove        0
isready after setoption missed readyok 0

PREDICTION 5: spin min-1/max+1 cases 116, WITHOUT an invalid-value line: 0
PREDICTION 6: spin 'word' cases 116, silently accepted: 0
PREDICTION 7: check 'word' cases 42, accepted without invalid line: 21
PREDICTION 8: no-value cases 82, WITHOUT invalid line: 3 (4%)
   of those, how many printed NOTHING at all: 3
    string Book File []
    string NnueFile []
    button Clear Hash []
```

Prediction 7 needs a correction, and it is mine, not the engine's: my "word" column contains both `banana`
and `true`, and `true` is a LEGAL value for a check option. Broken down by value:

```
check-option cases by value (idle):
  value 'banana' cases 21  accepted-without-invalid-line 0
  value 'true'   cases 21  accepted-without-invalid-line 21
  value ''       cases 21  accepted-without-invalid-line 0
spin options accepting 'true'?  cases 58, accepted 0
```

So every check option DOES reject `banana` and DOES reject no-value; my table counted the legal `true` as a
failure. Prediction 7 held after all. I state it this way because "21 accepted" looks like a fault and is not.

### step | done-partly-not done | evidence | result

| step | state | evidence | result |
|---|---|---|---|
| option list taken from the engine's own uci answer | done | `out/uci_answer.txt`, `out/options.json` | 82 options, 58 spin / 21 check / 2 string / 1 button |
| prediction committed alone first | done | `prediction.txt` | 10 predictions with ranges |
| every option x min/max/min-1/max+1/word/nothing, between searches | done | `out/results.jsonl` | 492 cases, 0 crash / 0 san / 0 illegal |
| during a search (seeded sample of 20 options, 4 values each) | done | `out/results.jsonl` (`during: true`) | 58 cases, 0 crash / 0 san |
| next search legal after every case | done | field `legal` in every record | 0 false |
| table built from raw by a script | done | `summarise.py` | pasted above |
| button behaviour reproduced alone | done | `../finding_button/repro.txt` | `value 0` / `value true` / `value 1` all answer invalid |
| bogus NnueFile does not silently change eval | done | `../finding_button/nnuefile_probe.txt` | eval identical (hce 59 nnue -26 total 33) before, during and after |

## findings

S-F5 — the button option `Clear Hash` answers `info string invalid value for option Clear Hash` when a value
token follows it, including `value 0`, `value 1`, `value true`. It clears the hash correctly when sent the
correct way (`setoption name Clear Hash` with no value), so the cost is a spurious error line that a GUI may
surface to the user, not a failed clear.
Show it again:

```
printf 'uci\nisready\nsetoption name Clear Hash value 0\nisready\n' | /agent/repos/base/forge-combo29/build/forge
```

Raw: `../finding_button/repro.txt`. Source, verified by opening the file: src/uci.cpp:299-301 —
`else if (name == "Clear Hash") { if (value_text.empty()) searcher.clear_hash(); else note_invalid(); }`.
So the behaviour is deliberate in the code; whether it is desirable is a judgement I leave to Opus, but a
button that answers "invalid value" for `value 0` is at least surprising, because every other engine I know
ignores the value of a button.

Not a finding, recorded so nobody re-derives it: a bogus `NnueFile` prints `info string nnue: cannot open
file` and leaves the BUILT-IN net active — the eval output is byte-identical before, during and after
(`../finding_button/nnuefile_probe.txt`). So there is no silent "NNUE off" trap here.

## suspicions, not proven

- The `during` regime sends `setoption` 5-15 ms into a `go infinite` and then `stop` 30 ms later. In every
  run the `stop` arrived and the follow-up search worked, but my driver is single-threaded, so what I measured
  is "the option is accepted while a search is running", not "the option's effect is taken up by the running
  search". A `Threads` change during a search, for instance, cannot take effect until the next search in this
  engine, and I did not measure whether it silently does nothing.
- `NNUEArch` and `NNUEArchFile` did NOT appear in the `uci` answer of this build (only `UseNNUE` and
  `NnueFile` did), so they were not tested. `UseNNUE` was tested and behaves like any other check.

## what I did NOT do

- Did not test an option sent twice in a row, or two options at once.
- Did not test values with embedded spaces for spin/check (the grammar cannot express them) or a string value
  containing `value` as its first word, which is the one parsing ambiguity in the `setoption` reader.
- Did not verify that `Threads` actually creates that many threads (that is area 4).

## what I am NOT sure about

- Whether any spin option's CLAMPED value is what actually reaches the search. I verified the ANSWER LINE and
  that the next search is legal; I did not verify, per option, that e.g. `Hash value 99999` really produced a
  2048 MB table.
- Whether the 2 string options listed are the complete set on a build with an external net present. This
  build reports `UseNNUE` and `NnueFile` only, i.e. `nnue::available()` is true but `FORGE_NNUE_V3`'s
  `NNUEArch` is absent, so the set is build-dependent and my table describes THIS build.

## times

see `out/meta.txt` (`started_utc`) and the `date -u` lines in the commits; the full 550 cases took one run
recorded in `run.log`.

## last command's output

```
$ ls job3
options_job.py  out  prediction.txt  run.log  smoke  summarise.py
$ ls out
meta.txt  options.json  results.jsonl  summary.txt  summary2.txt  uci_answer.txt
```
