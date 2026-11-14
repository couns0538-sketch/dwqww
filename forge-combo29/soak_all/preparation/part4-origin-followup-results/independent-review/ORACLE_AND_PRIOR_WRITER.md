# Oracle cross-check and earlier writer review

This addendum reviews already-recorded evidence in `part4-origin-thirdpass`, `part4-origin-fourthpass`, and `part4-origin-oracle`. I ran only static text parsers; no native engine or oracle was executed by this reviewer.

The oracle input consists of **exactly all 11 mate-valued WORKER_PROBE observations in the 20-frame second-pass subtree**, as independently matched by frame, FEN, raw score and bound. Its retained run exits 0, signal null, with empty stderr. Every output is a legal KRK state and all 11 bound inequalities recompute true. Maximum recorded current halfmove clock plus DTM is 21. The direct table query uses the unchanged `KrkTablebase` header (SHA256 `4bd157bdef50e809fd9e48630aa961b63cdca07cd2082dbe14d8464bbcdaa0b7`) with the matching production board/layout compile defines. It ignores repetition and rule 50, as its source explicitly says. The oracle executable's exit status alone is not a bound check: the harness prints `bound_relation` but does not return failure on zero. Here I checked the actual 11 printed relations, not merely exit 0.

For limiting frame 23233, DTM is **5**, giving exact position-relative score **31995**. Consumed BoundLower **31987** is weaker and agrees with `31995 >= 31987`; it denotes a conservative 13-ply deadline, not the fastest five-ply mate. Qsearch frame 23231 has DTM 6, exact normalized score −31994, agreeing with its consumed Upper −31994. The other nine recorded probe inequalities also agree. This validates these numeric comparisons against the retained no-history oracle output; it does not certify a universal bound property or all writes in the trace.

## Prior producer

The third pass has 864 contiguous events; the fourth has 896. I independently reproduced normalized full stdout equality and address-normalized repeated trace equality for both. Incremental source changes only add the second watched key/cluster and subtree frame 22377 to the existing observational hooks. No extra TT probe or generation mutation appears.

For key `1726806482296082090`, the first mate-valued accepted payload and last accepted payload before consumer 23233 are from **frame 22377**, root iteration 13, ply 8, entry depth 6, clock 8. In the third pass its accepted store is sequence **394**, raw **31987**, **BoundLower**, cluster 24539/slot 0/epoch 5/generation 1. The previous accepted value is ordinary score 494 at frame 19497. Later stores exist after consumer 23233 and must not be mistaken for its producer.

The fourth pass expands this producer to four frames:

1. White frame 22377 plays `d3d2`, calling black frame 22378.
2. Frame 22378 plays `a1b1`, calling white frame 22379.
3. Frame 22379 plays `d1e2`, calling black frame **22380**.
4. Frame 22380 returns **MAIN_TT −31979**, consuming key `16140578755083273993`, raw **−31990**, **BoundUpper**, stored depth 7/clock 7, at current ply 11/clock 11. Return negation propagates through the three callers. Writer 22377 returns 31979 and stores `31979 + 8 = 31987`.

The earlier origin of that −31990 payload is outside this four-frame pass and is being traced separately. This record establishes a further dependency, not a terminal checkmate proof.

## Important boundary of the oracle statement

The third-pass ledger also contains **later** accepted writes for the same key at frames **24345 and 24349** tagged **BoundUpper 31987**, and frame **24358** tagged **BoundExact 31987**. The retained oracle's exact no-history DTM score for that board is **31995**. Consequently those engine classifications cannot be described as globally exact-DTM upper/equality bounds: `31995 <= 31987` and `31995 == 31987` are false. They are outside the 11 consumed-probe inequalities verified above. This is a concrete reason to distinguish selective finite-depth search classifications from global DTM claims, rather than saying all observed TT bounds are oracle-certified.

Those later tags do not, by themselves, demonstrate that the original winning deadline is too short or that the original root is not a forced mate. The Lower deadline actually consumed by frame 23233 is conservative, and the original root's printed unqualified `mate 17` remains a slower deadline than the retained oracle's chosen-move DTM 17 plies. No production fix follows solely from a short PV or from treating a selective score as the global fastest mate. Any broader bound-soundness claim must specify its semantics and account for the later classifications explicitly.

Evidence is retained in `third-fourth-oracle-command.txt`, `third-fourth-oracle-source-command.txt`, `oracle-source-output.txt`, and the independently extracted third/fourth ledgers. Third-pass raw trace SHA256: `3edabcd5503600e18c6eaccddca6b6362fca0919a323d1388d207dfc14e0c455`; fourth-pass: `3de23b21aab4df8f33ac1d8d7050e7cdabd328f08cef10a5f657a1f9fe1759df`.
