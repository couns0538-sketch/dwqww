# S02 check of seat 11's S-F8 — REFUTES the "silently" half, CONFIRMS the mechanism

Their finding: "`setoption` with the value word omitted is accepted SILENTLY and changes NOTHING:
`setoption name UseNNUE false` prints no line and `eval` still shows the net running (`nnue 20`), while
`setoption name UseNNUE value false` gives `nnue 0`. Cause: the name loop `while (input >> token && token !=
"value")` (src/uci.cpp:265) eats every token up to `value`, so `false` becomes part of the option NAME
(`UseNNUE false`), which matches no option and is dropped with no message."

## what I measured (my own harness, `check_s11f8.py`, written from their sentence)

```
eval (hce, nnue, total):
  default                          (18, 20, 38)
  `... UseNNUE value false`        (18, 0, 18)   <- control: differs in nnue
  `... UseNNUE false` (no `value`) (18, 20, 38)  <- equals the default

bench 13 nodes:
  default 862329 ; `UseNNUE value false` 907205 ; `UseNNUE false` 862329
```

So the EFFECT they describe is real and I confirm it: omitting `value` changes nothing, and the correct form
changes both the eval and the tree size.

## where it breaks: the engine is NOT silent

```
$ printf 'uci\nisready\nsetoption name UseNNUE false\nisready\nquit\n' | forge
uciok
readyok
info string unknown option UseNNUE false
readyok
```

and on the ASan build identically. Contrast runs:

```
$ setoption name UseNNUE value false     -> no info string (accepted)
$ setoption name Bogus value 1           -> info string unknown option Bogus
```

Raw: `repro_direct.txt`.

## verdict: REFUTES the wording, CONFIRMS the mechanism
- CONFIRMED: the word is swallowed into the name (src/uci.cpp:265, read and quoted below), so the option is
  not applied. `eval` and `bench 13` both prove nothing happened.
- REFUTED: "accepted SILENTLY ... prints no line ... dropped with no message". The dropped name is reported by
  the unknown-name path at src/uci.cpp:476 — `info string unknown option UseNNUE false`. So a harness or a GUI
  that reads the engine's answers DOES see the mistake; the failure mode is "reported as an unknown option",
  not "silent".
- Their practical warning stands and is worth keeping: it broke their own harness by sending
  `setoption name Threads 1`, which the engine reports as `unknown option Threads 1`. Anyone building a harness
  should read the unknown-option line.

## why this matters enough to file
The difference changes what a fix would have to do. If it were silent, the fix is "make the parser report a
missing value". As measured, the parser already reports it, under a misleading name: the message says the
option is unknown when the real problem is a missing `value` keyword. That is a MESSAGE-QUALITY issue, not the
silent-ignore trap the finding claims.

## source, opened and read (not taken from their report)
```
258:        } else if (command == "setoption") {
263:            if (token == "name") {
264:                while (input >> token && token != "value") {
265:                    if (!name.empty()) name += ' ';
266:                    name += token;
267:                }
268:                if (token == "value") input >> value_text;
```
and
```
476:                std::cout << "info string unknown option " << name << std::endl;
```
Their line citation (uci.cpp:265) points at the `name += token` line inside that loop; the loop itself starts
at 264. Their citation is off by one but clearly means the same loop.

## the guard that caught this
The first run of my check ABORTED rather than printing CONFIRMS, because its last condition was "omitting
`value` prints no info string at all" and that condition was FALSE. This is seat 19's warning working as
intended: the check fails loudly instead of confirming a half-true claim. `out/verdict.json` holds the five
conditions and which one failed.

## times
see the `date -u` lines in the commits.
