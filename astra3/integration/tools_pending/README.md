# A1 pending validation drivers

Status: PREPARED, native execution UNVERIFIED until the lead schedules it. These files execute no engine merely by being imported or with `--help`. Run only one native workload at a time.

## Existing support and reuse

`tools/smp_uci_regression.py --threads 2 --rounds 250` already provides the repeated stop/lifecycle workload, but it cannot select SmpV2/TmSoftHardClamp/SingularV2 through its CLI. Its transcript merges stderr and reconstructs text rather than retaining original separate bytes. Consequently `smp_option_stress.py` reuses its Run synchronization, legal-move/ponder checks, accounting and grace period, plus `tools/uci_regression.py` response deadlines. Raw capture is imported from the A1 `tests_pending/option_contract_tests.py`; no second byte-capture implementation was added. The five Run initialization fields are adapted to inject that engine.

## Threads=2 stop and option workload

```sh
TSAN_OPTIONS=halt_on_error=1 python3 astra3/integration/tools_pending/smp_option_stress.py \
  /absolute/path/to/tsan/forge --sanitizer tsan --iterations 250 \
  --out-dir /absolute/path/to/new/tsan-option-stress
```

For a Release smoke use `--sanitizer none` and the Release executable. The driver runs exactly 250 explicit go/stop cycles by default, then six additional go/setoption-stop/join cycles. Threads=2, Hash=16, OwnBook=false remain fixed. Four profiles cover OFF, all three independent new switches, N1 with SmpV2/TmSoftHardClamp, and N1 alone. No incompatible CorrExt combination is requested. Alternating infinite and ponder-clock searches wait for a completed iteration before stopping; all four initial profiles and every tenth cycle reach depth 7. Other cycles reach depth 3. A seeded short-delay schedule exercises lifecycle variation without asserting deterministic SMP nodes. This seed is a local workload seed, not a match/gate seed.

Each answer is checked against Forge's own perft1 legal-move list, including any ponder move. This tests UCI/search-state consistency; it is not an independent move-generator oracle. Every go must have exactly one bestmove. Python `-O`/`-OO` is rejected before starting any process because the reused SMP checks use assertions. The active echo must identify the selected profile. Live changes exercise both values of all three options while workers run. Original stdin/stdout/stderr bytes, per-cycle settings/answers, binary and source hashes, actual exit status and sanitizer diagnostics are retained under a new directory. A TSan-labelled run requires an actual `__tsan_init` ELF symbol and `TSAN_OPTIONS` containing `halt_on_error=1`; startup failure or any sanitizer diagnostic fails the run. A successful Release run does not qualify TSan.

No benchmark identity, mate-proof, speed or strength claim follows from this workload. Full CTest, the existing timing tests and all required OFF/ON identities remain separate.

## Fastchess strict two-game smoke

Generate the exact command records without running a match:

```sh
python3 astra3/integration/tools_pending/strict_smoke_commands.py \
  /absolute/path/to/integration/forge \
  --fastchess /tmp/astra3-tools/fastchess-src/fastchess \
  --out-dir /absolute/path/to/new/strict-smoke
```

The positive argv is:

```sh
/tmp/astra3-tools/fastchess-src/fastchess \
  -engine cmd=/absolute/path/to/integration/forge name=integration-A option.BundlePreset=N1 option.CaptureFutilityBase=0 \
  -engine cmd=/absolute/path/to/integration/forge name=integration-B option.BundlePreset=N1 option.CaptureFutilityBase=0 \
  -each proto=uci tc=5+0.05 option.Threads=1 option.Hash=16 option.OwnBook=false \
  -rounds 1 -games 2 -repeat -concurrency 1 -maxmoves 80 -strict \
  -pgnout file=/absolute/path/to/new/strict-smoke/positive/games.pgn append=false \
  -log file=/absolute/path/to/new/strict-smoke/positive/engine.log level=trace engine=true append=false realtime=true
```

The negative argv is identical except it adds `option.Astra3UnknownOptionProbe=1` to integration-A and writes to the separate `unknown_option` directory. Exact shell-quoted commands and shell-free argv arrays are generated for both. The lead must capture stdout/stderr as bytes, preserve the actual exit status, use each case's own cwd and a 180-second deadline, and hash originals afterward. Positive acceptance requires exit 0 and exactly two completed PGNs with no illegal move/crash/time forfeit; negative acceptance requires exit 1 **and** the named unknown-option diagnostic before any game starts. An arbitrary exit 1 is not evidence of correct strict rejection. Neither command is a strength gate; no SPRT/random seed/opening suite is used.

IDEA_SOURCE: user A1 integration/TSan/strict-UCI contract; existing Forge UCI/SMP validation code; official Fastchess command manual at commit ebfd64cb7fac80d4822c50b07dca4fe934779d21. No external engine algorithm or tuned constants.
