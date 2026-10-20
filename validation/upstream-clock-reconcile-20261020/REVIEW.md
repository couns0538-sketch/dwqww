# Independent clock reconciliation review

Reviewed frozen source `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d` against frozen 6.4.12 `8865666cc0ab4961cd507bae40ff6ce44e9319df`, the accepted clock contract in `AUDIT.md`, and the separate `automatic-origin-api.cpp` diagnostic. **No blocking production defect found.** This is a static independent review; no compiler, engine, test suite, external review service or match was run by this reviewer. Root's build and runtime gates remain separate evidence.

## Contract and preservation checks

- `SearchLimits.start_time` is appended after the existing aggregate prefix. Both facade and Worker resolve nonzero `start_time` before legacy `request_start`; the legacy value remains usable when the accepted spelling is zero. Explicit values remain honored in analysis and ponder modes, as the documented compatibility contract requires.
- Automatic facade timing uses exactly `!infinite && !ponder && (time_ms >= 0 || movetime_ms >= 0)`. A depth, node or mate cap combined with a finite clock remains clocked. The shared fallback origin is captured before the worker vector, TT generation, exclusive gate admission and helper creation; the same immutable `worker_limits` is passed to every worker.
- UCI captures `command_start` immediately after the complete input line, before stopping/joining prior search or parsing the go payload, and only assigns the accepted field under that same finite-clock predicate. Untimed analysis, infinite-with-clock and ponder automatically leave both timestamp fields zero. Book/perft behavior is unchanged.
- Worker-local fallback applies only when both origins are unset. Ponder budget measurement still uses `ponder_hit_ns`, returns zero before the hit, and gives a hit timestamp priority over either request timestamp. Reported elapsed time/NPS continue to use the raw search origin; the change does not add a separate reporting clock.
- Exact byte comparison against frozen 886 confirms the complete Worker body after timestamp selection is unchanged. In particular, local and published node counters reset before expiration can return; the root restriction/legal fallback, expired helper preflight before helper deadline surrender, and ponder deadline precedence remain intact.
- TT locking/gating, lifecycle and rule50 behavior are unchanged by the production diff. `src/nnue.cpp`, `src/board.cpp` and `include/forge/board.hpp` are byte-identical to frozen 886. The only production delta consists of timestamp selection, UCI assignment and version labels. Accepted `356e863dbd86d2ce24b8ee9486d7406f1d525480` is an ancestor of the reviewed frozen commit.

## Focused test assessment

The new unit assertions cover accepted-field expiration, both conflicting-field precedence directions, exact authoritative origin retention, legacy fallback, and a direct expired helper call with a fresh legacy timestamp. The previous clock/moves-to-go, root restriction, warmed helper zeroing, multiworker expiration, pre-hit/immediate-hit/expired-hit ponder, infinite and fixed-node cases are retained. I found no assertion that weakens an existing gate.

The automatic-origin diagnostic has sound main-worker observations: its wrapper records real helper-creation boundaries without inserting sleeps, delegates the actual pthread call, requires three successful helpers and a legal returned move, then distinguishes before-admission versus after-admission origins. It uses matching headers/cores as described in `BUILD_COMMANDS.md`; reusing a new header against the old core would invalidate the test and is correctly avoided by those commands.

Two coverage limits should remain explicit when reporting results; neither identifies a current implementation bug or requires broader feature work:

1. `automatic-origin-api.cpp:41,57-64` reads only the main Worker's origin. A passing run establishes the main origin relative to helper admission, not equality of all helpers' finite-clock origins or their individual worker-local untimed origins. The source currently supplies the same resolved finite origin to every worker, and the existing helper-expiration tests protect the important zero-work safety case. Do not describe this diagnostic alone as observing every worker's origin.
2. This diagnostic calls Searcher directly. It does not exercise `parse_limits` or the separate finite-timed assignment in UCI. The preserved native UCI probe covers movetime and untimed depth; it does not itself cover all UCI node/mate-with-clock, infinite-with-clock or ponder combinations. The current UCI predicate matches the facade predicate on inspection. State that scope accurately, or use the already planned UCI mode checks if root is executing them; no new test framework is needed.

## Reviewed input identity

All production files remained equal to the frozen reviewed commit at the end of review. SHA-256:

| Input | SHA-256 |
|---|---|
| `src/search.cpp` | `e643a7e2754b4cde2d45cec9e2dcc2e3785879e58f1c23307f97d2268ed6eb7a` |
| `src/uci.cpp` | `e357dcfae771de0e8580f9c6a3e61f3c4af9b0d9d68a8cb3167b2c50bb3cb0dd` |
| `include/forge/search.hpp` | `a8f905e88a71def150249749282a0e36d5e75557555718570dc7c6db31f68763` |
| `tests/tests.cpp` | `6f2c61c7f58d29930fa0bf142dbc6ea35637e20e943247a30ba0b60441e268a3` |
| `automatic-origin-api.cpp` | `b017b51d5c57357c35d03da3102fcb4579539a505f4470a194e97db1b36ccd40` |

Only this review file was written in the checkout; a temporary diff was saved under `/tmp` for inspection. Existing frozen match inputs, engines, builds and Git state were not changed by this reviewer. This reconciliation supplies no speed, playing-strength or platform-transfer claim.
