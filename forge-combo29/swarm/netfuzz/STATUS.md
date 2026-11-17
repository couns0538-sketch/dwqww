# STATUS — swarm/netfuzz

## State: complete and pushed

| part | state |
|---|---|
| Honesty gate, release `-DFORGE_NNUE_V3=1` | **4/4 PASS** (312866 / 862329 / 3024920 / 4865609), `bench` on stdin |
| Honesty gate, default build | **4/4 PASS** (proves the flag does not move the search) |
| 60 hand-built mutants, release arm | **done** — 53 refused, 7 loaded, all 7 by design |
| 60 hand-built mutants, ASan+UBSan arm | **done** — 0 sanitizer lines, 0 verdict disagreements |
| Sanitizer planted-fault proof | **done** — ASan heap-use-after-free and UBSan signed overflow both fire |
| Engine-level loudness (both streams, `isready`, search blocked) | **done** — every refusal loud on stdout/stderr, `isready` still answers `readyok`, no `bestmove` follows |
| Allocation accounting (`operator new` counter) | **done** — bombs allocate 0 for the claim |
| Amplification (2.00×–3.66×, linear in file length) | **done** |
| Slurp-before-check / unbounded read | **done** — 8 GB file = 8.4 GB RSS; `/dev/zero` aborts on `bad_alloc` |
| 1,819-case header sweep, both arms | **done** — 0 sanitizer lines, every accept legal by design |
| 12th net reachability + counterfactual | **done** — eval 68 vs 94, restored returns 68 |

## The one line

**The v3 loader is memory-safe against malformed input: 53 of 60 mutants refused, 7
loaded and all 7 must load, 0 sanitizer lines in 1,879 cases.** Its one real defect is
that it **slurps the whole file before checking anything**, so it spends L bytes to
refuse an L-byte file and never terminates on `/dev/zero`.

## Binary identity (do not merge with the default-build claim)

- Fuzzed binary is **`-DFORGE_NNUE_V3=1`**, sha256 `a1d0c0254e73776721b96bf1b5c24cf13f375c5675b57bc008f2d26599d3fcb1`.
- `NNUEArch` **does not exist in a default build**; verified `NNUEArch_occurrences 0`,
  `UseNNUE_occurrences 1`. So this is **not** the audited default binary and says
  nothing about the v2 (`FORGENET`) loader.

## Corrections made during the work (recorded, not hidden)

1. **My expectation for `hdr_flags_residual` was wrong.** I predicted the loader would
   refuse a residual net; it accepts it and **UCI** refuses it
   (`residual v3 networks are not supported`). The engine-level verdict is still
   `refused` and still loud — the expectation table was wrong, not the loader.
2. **My first sanitizer plant proved the wrong thing.** A 1-byte heap overrun is caught
   by UBSan's object-size pass first, so ASan never reported. Replaced with a
   use-after-free, which only ASan can see.
3. **My first reachability sweep produced a masked null.** 326 positions, 0 differing
   evaluations — because the corrupted lane was negative and SCReLU clamps to 0. The
   corruption *is* observable (68 vs 94) once a position whose lane lands positive is
   constructed. The null was the corpus, not the engine.
4. **My first UCI driver reported a 30 s stall that was my own bug.** `select()` on a
   `TextIOWrapper` reports nothing while Python holds decoded lines in its own buffer.
   Replaced with reader threads; sessions now take 0.10 s.

## Not tested

Threading; the residual evaluation path (unloaded before any eval); real training-corrupt
nets; the v2 loader; partial-publication semantics after `bad_alloc`.

## Reproduce

```sh
scripts/build.sh <forge-combo29> /tmp/probe          # both arms
scripts/pins.py /tmp/build/rel/forge --v3            # gate
python3 scripts/make_mutants.py <net> /tmp/mut > /tmp/mut.json
python3 scripts/run_mutants.py /tmp/mut.json /tmp/probe <forge> /tmp/r.json --asan
python3 scripts/loudness.py <forge> /tmp/mut.json /tmp/loud.json
python3 scripts/sweep_asan.py /tmp/probe/loadprobe_rel /tmp/probe/loadprobe_asan <net> /tmp/w /tmp/s.json --bytes
python3 scripts/slurp_test.py /tmp/probe/loadprobe_rel /tmp/slurp.json 4
```

The test net is **not committed** (6.3 MB binary). `scripts/make_valid_net.py` and
`make_v3_testnet.py` on branch `for-fable-and-opus/swarm-71` regenerate byte-identical
nets from a fixed seed; `test_v3.fnn3` sha256 `1db8525e…`.
