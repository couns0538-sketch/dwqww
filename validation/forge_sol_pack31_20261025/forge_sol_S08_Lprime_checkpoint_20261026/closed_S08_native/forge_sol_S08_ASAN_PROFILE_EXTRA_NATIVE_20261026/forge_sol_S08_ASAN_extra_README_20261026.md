# S08 actual profile-ON sanitizer supplement, 2026-10-26

**PASS.** Actual frozen ASan/UBSan engine4f6b1b5e… ran with leak detection enabled on CPU4 at nice19. The complete original fifteen-case CTest PASS is a prerequisite, separately retained by root; these additional samples do not replace it.

- `bench_prof 11`:308972nodes,55counters, no overflow.
- First25canonical WAC positions:Threads1,20000fixednodes each; all legal bestmoves and valid55-counter packets.
- WAC001/009/018:Threads2,20000requestednodes each; all legal bestmoves and valid55-counter packets. Actual counters:[21024, 20442, 21788]. No single-thread ceiling is asserted for these parallel searches.
- Startpos perft4:197281; kiwipete perft4:4085603. Root divide sums match both totals.
- Runtime:44.436seconds; minimum free disk:63324160bytes. Source2923freeze and engine SHA256 unchanged.
- Child rc0, zero stderr bytes, complete raw streams, graceful quit/EOF drain, reader queues cleared.

The read-only replay independently rehashed original captures, reparsed all29counter packets, compared all28actual input FEN/thread requests, checked bestmove legality with python-chess, and checked both perft totals. It launched no engine. Four small bestmove validation tests also pass. The primary raw engine streams are profile_on.stdin/stdout/stderr, with profile_on.receipt.json; controller outer completion was observed through tool transport and is not mislabelled as a separately captured raw file.

Source and commands are preserved. Actual launch:

```bash
env PYTHONPATH=/workspace/.cloud-setup/venv/lib/python3.12/site-packages \
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 \
  UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 \
  taskset -c 4 nice -n 19 python -B \
  /workspace/forge-pack24-20261026/S08/forge_sol_S08_ASAN_profile_extra_20261026.py \
  --execute --output /workspace/forge-pack24-20261026/S08/forge_sol_S08_ASAN_PROFILE_EXTRA_NATIVE_20261026
```

The folder already exists and is sealed evidence; do not rerun that command into it. Runtime escalation was approved only to allow LeakSanitizer to inspect its own process after the sandbox's verified EPERM restriction. Sanitizers were not disabled. No NPS, Elo, native Windows or Zen5 claim follows from these correctness samples.
