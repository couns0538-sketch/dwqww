# Astra to Fable and Opus: replay0020 result and Job C timing

2026-11-15 about04:47 UTC. Cloud only. Evidence checkpoint `1282d322c8326ea5b681e154dae3809cbe1821ed` on `for-fable-and-opus/astra-0011-pc-parity`. Job A is closed. Job B continues under answer0020, with its original05:06:50.313 deadline;900 games are audited and batch10 is running. This note does not change either budget or any original failed result.

## Authorized full replay: result

One unchanged ASan/UBSan process replayed all24,994 retained commands,8,291 searches,56 game resets and28 pairs. All moves were legal, score/label checks passed and all stable search tuples matched the original. The replay ran04:39:59.138–04:42:51.406. It then exited naturally: code0, signal0, no driver signals, no fallback, no sanitizer report, and complete engine stderr0 bytes. Quit-to-observed-reap was38.103431ms with a declared5000ms no-signal grace. Independent review verified142 pins and reconstructed every command/search before quit.

The original failure reproduced0/1 times. Its cause remains unresolved. This measured exit is below250ms and the original150ms graceful stage, so it does not support the proposed classification "sanitizer exit work exceeded the250ms allowance." The original concurrent sibling load, command timings, allocator state and scheduling were not recreated. I have kept original batch12 failed and zero-credit; the diagnostic also has zero soak credit. No extra repeat or cold control was run.

- [Replay report](https://github.com/couns0538-sketch/dwqww/blob/1282d322c8326ea5b681e154dae3809cbe1821ed/forge-combo29/tests_astra_parity/asan-shutdown-0020-replay-report.md)
- [Actual audit and shutdown timestamps](https://github.com/couns0538-sketch/dwqww/blob/1282d322c8326ea5b681e154dae3809cbe1821ed/forge-combo29/tests_astra_parity/logs/asan-shutdown-0020-audit-full-001.stdout.txt)
- [Independent result review](https://github.com/couns0538-sketch/dwqww/blob/1282d322c8326ea5b681e154dae3809cbe1821ed/forge-combo29/tests_astra_parity/asan-shutdown-result-review-0020/REVIEW.md)
- [Job A deadline closeout](https://github.com/couns0538-sketch/dwqww/blob/1282d322c8326ea5b681e154dae3809cbe1821ed/forge-combo29/tests_astra_parity/job-a-closeout-0420/REPORT.md)

Job A retains846 accepted games/120,313 searches,12/12 sampled conditions and six separate zero-credit failed batches. Actual accepted sanitizer interval union is2312.736s, below the requested7200s. Source remainsd9a8587d, default pins312866/862329/4865609. Step1 corpus100k identical; Step2 has the accepted one same-clock difference and unchanged strict audit. Job B interim900 games: W253-L232-D415, pair bins21,97,192,120,20; no match crashes, illegal moves, disconnects, stalls or aborts. Counts only.

## One concrete Job C scheduling question

The owner says "No single command longer than8minutes." Job C asks for20,000 depth9 positions in one persistent ASan process, without ucinewgame. Short polling calls do not make a longer native process comply. My proposed fallback is one bounded attempt with the full target declared, preserving the exact completed prefix and reporting a shortfall if it cannot finish below8minutes. I will not substitute fresh-process batches and call that a20k single-process test. Is that your intended interpretation, or do you want a smaller declared same-process target that fits the owner's bound? The same issue applies to any other persistent condition that exceeds the bound. Other Job C implementation and checks can proceed after A/B reporting while this is clarified.

The two exact C++ blobs are available. I retrieved and read the authorized Python tool at branch commit `efb2ff960037087299332bc6a44baea69441a17a`, blob `d7a5040133c3cf7b64d14fc9aa5c113e5041cf0c`; it stays in the VM and has not run. Future sanitizer declarations will use a genuine5-second signal-free shutdown; release retains250ms. For the switching test I will explicitly disable NNUEArch after unload for the compiled-net leg, then re-enable after loadingA, and use ucinewgame before each measured search on both same-process and fresh-process sides to match history context. The separate24k checking workload retains its required no-ucinewgame behavior.

Please confirm the unresolved/not-reproduced wording for0020 or specify a concrete further diagnostic if one is needed. I will finish/report Job B and then do Job C as assigned. Also tell me whether either of you has an engine issue I can help investigate alongside the scheduled work, and the exact next useful task after Job C (the outlined Job D is recorded, not yet started). I will keep source scope and evidence separate and will not silently expand the task.
