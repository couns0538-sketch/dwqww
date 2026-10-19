# One bounded hosted Linux pilot

Frozen candidate6.4.7 source2c0c7efa49023d8e3f49de3f5596f333a3f01202 versus
6.4.4 source816423b1ddac23a00244449deef59dba736055a9, isolating three speed
candidates. Both have completed local correctness gates; no new gain is accepted.

Workflow branch forge/hosted-strength-20261019-2115. One push requests execution;
actual Actions availability, authorization, start and completion are unverified.
No retry/auth workaround if submission is blocked. The accepted branch stays9108.

Identical GCC14C++20 flags, native Linux1CPU, fresh same-binary benchmark AA gate,
then4fixed-node paired AA openings, then ONE logistic SPRT[0,+5],alpha/beta.05,
2+0.02,Threads1,Hash32,OwnBookfalse.16min/500pairs cap,24min entirejob cap.
First48pairs are its prefix, never a separate outcome gate/reset. Full protocol,
504disjoint frozen openings and original selection/failed-Git-smoke evidence are
under .github/hosted-strength. Raw files upload and a fresh results branch are
attempted even on ordinary failure. Platform loss/hard cancellation may prevent it.

Any fault, incomplete strict pair, input mutation, calibration failure or deadline
without a boundary means no accepted Elo gain. Linux-only scope; no native Ryzen,
Windows speed or Stockfish superiority claim. Preserve every raw PGN/log unchanged.
