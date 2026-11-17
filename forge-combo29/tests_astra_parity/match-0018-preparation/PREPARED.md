# Job B admission under decision0018

Fresh metadata-only adapter prepared 2026-11-15 around03:04UTC. The earlier unused match helpers remain untouched. No engine, Git, root-state or runtime-declaration write occurred.

Fable0018 explicitly permits JobB while JobA sanitizers remain pending. The new declaration truthfully records `jobAComplete:false`, `step2Accepted:true`, `sanitizerPending:true`. It pins decision `fe59dc3ab072480f7360f0b356ff01a900d2ab35`, decision text SHA256 `a85053e51b66fb82cbc2033acf27d5e4cb83f22d64938c430870a15eeaf7fe3b`, and the immutable accepted Step2 evidence SHA256 `11284dcae54beb48546c53f0ca9f4d3c4f92d8cdc97fbd0872452cfbb30f3c5e`.

Source remains `d9a8587df8ad4d0ff1231632cb1ac72b590c04bf`, release binary SHA256 `df76cddaea8a37dae7f8d1a5178700e0168aad8c463764ed6870d9c4fce2dc56`. Sanitizer completion is not claimed. Earlier TSan failures, counts and classifications are untouched.

Root fills only the actual plain UCI proof file/hash in a new copy of `DECLARATION-INPUT.template.txt`. Root must separately clear the global stop under0018; neither helper clears it. Declaration and launch require root's effective Step2 gate and `blockFurtherEngineWork:false`.

```text
node /workspace/work/parity-match-0018-preparation/controller.mjs declare INPUT_FILE
node /workspace/work/parity-match-0018-preparation/controller.mjs prepare
node /workspace/work/parity-match-0018-preparation/controller.mjs run B-0001 --execute-authorized
node /workspace/work/parity-match-0018-preparation/controller.mjs audit B-0001
node /workspace/work/parity-match-0018-recording-preparation/record.mjs B-0001 --check
node /workspace/work/parity-match-0018-recording-preparation/record.mjs B-0001
```

Runtime directory remains the unused `/workspace/work/parity-run/matches-hindsight`. Protocol is unchanged: same final binary, HindsightDepth true versus false, MateAlphaGuard false, Threads1, Hash16, OwnBook false,50000 nodes/move; official fastchess and UHO book, fixed seed202611150011,100-game batches, color-reversed pairs, no adjudication. Maximum6000 games or two hours from declaration. The optional250000-node leg is not included. Native work remains exclusive; existing input/config/trace/PGN/pair/hash guards and timeouts remain intact.

Verification completed without new games: nine admission/negative checks, two retained native-result reaudits (400 completed games credited;314 raw finished games in an incomplete batch credited zero), twelve recorder accounting checks and ten final syntax checks. Existing tests were retained. Both actual declaration and first live record remain root work.

Frozen protocol SHA256: `6421456840bc13431da54085bb99c40533d60ed34027dd759482ec84928e7892`.
Frozen controller SHA256: `a17da2efce953f84c1eab052d892210e45ed8adc3e153a48d3ec88ff00a4dbea`.
Frozen recorder SHA256: `2160080f7d70c37cd309fe494b2d2cc0da4affbcbf63bffd2bd09dff738d62a6`.

Counts only. Raw runner output remains preserved; no Elo or speed claim is made.
