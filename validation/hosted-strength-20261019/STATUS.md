# Hosted6.4.7 timed test: promising snapshot, SPRT inconclusive

Run39325939081 compared source2c0c7efa49023d8e3f49de3f5596f333a3f01202
with6.4.4 source816423b1ddac23a00244449deef59dba736055a9 on hostedLinux
AMD EPYC7763,GCC14.2,oneCPU,Threads1,Hash32,OwnBookfalse,2+0.02.
Both preregistered benchmark AA gates and4paired readiness openings passed.
Native logisticSPRT[0,+5],alpha/beta.05 reached its960s wall cap without H0/H1.

Last native144game snapshot:60wins/42draws/42losses,+43.66±28.69Elo,
LLR0.79 matching independent0.789741647. This uncertainty is native/descriptive
for that earlier snapshot; it is not an accepted gain or the final147recordresult.

Original147normal completed records contain62wins/43draws/42losses:73complete
pairs plus orphanround74. Game148started but has no PGNrecord. Complete73pairs
descriptively give61wins/43draws/42losses and independentGLR0.815076605, inside
±2.944438979. Strict whole-PGN validation fails; no records were trimmed,
reconstructed, pooled or resumed. Two stop/quit warnings occurred at shutdown.
No pre-deadline fault is attributed. Independent python-chess replay verified all
20018recordedmatchplies plus1048readinessplies,zeroillegalmoves.

All59 snapshot files match immutable results commit1e9361d0e35a17c0d63a90d9431a6bb875d0817d
on results/hosted-strength-39325939081-1. OriginalPGNs/logs/state/buildproofs and
all public observations are archived unchanged. Actual hosted executable bytes
were not retained; linked build/source/binary hashes are retained. The deadline
path lacks successful final input rehash. Future runs should preserve binaries
and rehash in finally, with sufficient predeclared headroom for complete pairs.

Decision: retain promising6.4.7; no acceptedElogain.6.4.8root-effort change is
separate and untested for strength. No nativeWindows/Ryzen/Stockfish inference.
