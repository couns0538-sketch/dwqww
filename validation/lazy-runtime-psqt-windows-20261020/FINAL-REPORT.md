# Forge 6.4.19 Windows validation

Frozen source `61f598056572dfade6994af8ad2e38817cd28aa3`, parent `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`.
The private runtime PSQT/unclamped phase cache intends exact evaluation and search
parity. This stage does not modify source or accept search strength changes.

The fresh LLVM-MinGW 23.1.3 strict Zen5 C++20 Release build passed on its first
attempt with j1, static linking and no FMA, fast-math or LTO. Eight actual PEs,
the static core, runtime test object, frozen source, compile records, flags and
original command/stdout/stderr records are retained.

All ten Wine checks passed on their first attempt: core/perft, 347 runtime PSQT
checks, 54 correction-history checks, eight TT groups, rule50, 18,947 legal
comparisons, UCI, ponder, five OwnBook transitions and exact preregistered parent
bench signature 352313. Inputs remained unchanged. AVX2 instructions were
observed and fused operations were absent.

The closed-writer package has 20 members and 19 verified checksums. The raw ZIP
retains all 205 original files. An independent read-only audit passed all 1,184
checks on its first execution, including 71 frozen source files, actual tested
PE/core/runtime object identities and all 219 unchanged Windows 18 originals.
Original preparation-stage records remain historical, including one failed
text-only static probe; no engine or artifact audit retry was needed.

Artifact: `releases/forge-6.4.19-candidate-windows-zen5.zip` (13,577,092 bytes).
ZIP SHA256: `f0ec03308098bf8e675647f091b3b1afeb74d2632d9c972883e5907cfcb23d85`.
Engine SHA256: `265b676d6542622c5b876799236c2319fb91c8afa606a925087d36baf0b44caf`.
Core SHA256: `086dce85e7ae9f64b872d94301c3497654d723fbdf89a8c4c588f798c2ac1933`.
Raw SHA256: `5ab2eb4a9c59e197037d4145576b85f8092295898e4af1c025a642367da674c8`.

All build/runtime/package/audit CPU work finished at 22:21:56 UTC. No remaining
compiler, engine, compression or hash job belongs to this Windows stage.

This is a validated Windows candidate, not an Elo-accepted release. Native 19
qualification remains separate. Original 6.4.16 TSan FAILED 8/9 remains qualified.
No speed, NPS, Elo, native Windows/physical Ryzen result or Stockfish superiority
is established here. Next: root preserves/pushes these immutable artifacts and
continues isolated native equal-time performance and strength validation.
