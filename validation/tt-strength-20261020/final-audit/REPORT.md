# Failed TT strength run: original-evidence audit

**The whole strength attempt is invalid: Baseline forfeited on time in started game85. No TT strength or speed conclusion is accepted.** The frozen wrapper correctly stopped on the warning; no game was retried, discarded, resumed or pooled. The failure is not an archive-publication error and does not establish a candidate regression.

Run [39403471059](https://github.com/couns0538-sketch/dwqww/actions/runs/39403471059), attempt1, immutable launch `b48af4c3882d7c20ef3fe5bceea6fe2ae8a7d893`, compares baseline6.4.11 `c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e` with candidate6.4.12 `8865666cc0ab4961cd507bae40ff6ce44e9319df`. Equal native2+0.02, Threads1/Hash32/MoveOverhead10/OwnBookfalse, serial color-swapped openings and prospective0/+5 SPRT remain the original protocol. No threshold was relaxed.

The permanent original evidence is [results commit ffc598ad](https://github.com/couns0538-sketch/dwqww/tree/ffc598ad12760e5cdc8cb1ee15383f13787acad8/archived-results), branch `results/tt-strength-39403471059-1`. All98payload files /74,576,609raw bytes passed archive/part/internal-manifest/per-file hash verification. ZIP16,268,649bytes, SHA256 `386df22a0bd8580ff959678202d72b2931abcbda2401214a5151df37ddea301b`. Data-only extraction rejected unsafe paths and symlinks; no archived executable, archived helper or game was executed during audit.

All42final frozen inputs map to original preserved bytes and match both expected/actual final hashes. Both engine source TARs are byte-identical to fresh `git archive` exports, all72candidate/69baseline exported source hashes match build provenance, actual engine/core/Fastchess hashes agree, strict GCC14Release flags remain intact, and each original CTest log records9/9passed. The Fastchess source TAR matches pinned `60d7a7a26c6b0582a15c112fb29a1829bef2adb3`. All original package/workflow/validator files match the immutable launch. The offline integrity/forensic helper completed126checks. Operational bench A/A passed its predefined gross gates; this supplies no candidate NPS estimate.

Independent legal replay passed every retained PGN record. A/A has8normal games /4complete pairs /1,108legal plies, identical paired moves and results. SPRT has84normal completed PGN games /42complete pairs /11,129legal plies: W13/D59/L12, pentanomial `[1,6,26,9,0]`, matching native state. Exact selected-opening prefix/order, swapped colors and final-board result support pass. These completed records do not rescue the failed attempt. The raw session shows game85started and a baseline time warning; no completed game85PGN record was written. No alternate PGN was reconstructed.

Raw SPRT log line276647 is the only warning/error/fatal line:

```text
[WARN  ] [09:59:55.200065] <     139790924117696> fastchess --- Engine Baseline loses on time by 45ms
```

The wrapper ends with `RuntimeError('match_fail_fast: Fastchess warning/error in fastchess.log')`. Console records BaselineTimeouts1/Crashed0 and an interrupted tournament. Both engines then exit normally; all85sessions per engine have exitstatus0. There is no original crash/illegal-move warning. The natural1024-pair cap, native H0/H1 boundary and300-minute emergency deadline were not reached.

The exact final position is `1R6/5k2/1P2r3/3K1p1p/5R1P/8/8/8 b - - 4 50`, after99legal plies from the original opening. Baseline receives `go wtime 423 btime 63 winc 20 binc 20` at09:59:55.091251. Its last completed iteration is observed at09:59:55.199898: depth10,47145nodes, reported24ms. Legal `bestmove e6e1` is observed at09:59:55.199947: **108.696ms after outgoing go**, against63ms remaining. Readiness follows; warning records45ms late. These are original hosted UTC timestamps, not user-local schedule times.

Frozen baseline source already accounts for request receipt. Its timer uses steady_clock and polls every1024nodes; at63ms plus20increment and10overhead, ordinary allocation yields available53ms, soft17ms, hard31ms. The timing/polling bodies are unchanged between the two frozen engines. The observed24ms completed-iteration time does **not** identify when later work, formatting/flush, transport, manager reads or scheduling occurred. It cannot prove either a safe engine response or an84ms output delay. Whole-run cgroup counters show no quota throttling, but cannot exclude host preemption or per-move stalls. The current6.4.13 untimed-reporting reconciliation is not a demonstrated remedy for this forfeit.

`game85-original-protocol.log.gz` preserves the exact contiguous final-session log bytes, with original line offset/hash in `forfeit-exchange.json`. The two `game85-*-original-input.txt` files extract original outgoing commands, retaining both sides' full warm-game history; they are diagnostic stdin records, not newly played games. `forfeit-exchange.json` retains the final original position/go/info/bestmove/warning lines, timestamps, legal current FEN, clock budget and all original-log hashes.

Next causal experiment: use a new instrumented build from trusted frozen source and a separately preregistered diagnostic, preserving original failed evidence. Observe receipt/Worker entry/timer polls/result/pre-and-post stdout flush plus manager receipt with monotonic wall and thread CPU clocks. Replay the preserved warm command history only as a labelled diagnostic; compare cold-position behavior separately. This can distinguish a long search interval from output/manager delay or host descheduling. Do not infer that cause from the last `info`, rerun this failed strength protocol, alter its overhead/tolerance or reuse its reserved openings to seek acceptance.

Reproduce offline checks with the retained original extraction:

```sh
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/python validation/tt-strength-20261020/final-audit/audit_forfeit.py
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/python validation/tt-strength-20261020/final-audit/legal_replay.py
```

Original giant files remain in the durable results archive and outside the checkout; this directory holds small audit records and exact diagnostic excerpts. No native Windows/Ryzen, accepted Elo, speed or Stockfish claim follows.
