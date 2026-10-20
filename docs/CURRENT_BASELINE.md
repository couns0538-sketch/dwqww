# Current baseline

Accepted integration `forge/6.4-hourly-20261019` is
`2fc649effb6d2f09f4fdf63b44d59283fe26b616`. Its last three commits add tools/evidence;
engine source is unchanged from `9108d012526be80c6d163f7cab684e6acd9abf8d`.
Merge `3cabc1b` preserves these newer records without changing the candidate.

Latest fully correctness-tested isolated source is **Forge6.4.11**,
`c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`, branch
`forge/nnue-capture-fusion-20261019`. It preserves6.4.10 and all earlier repairs,
accepted residualNNUE weights and training infrastructure. Its guarded capture
path fuses copy+threepasses into one while keeping both subtractions then addition.

Release9/9, ASan/UBSan9/9 and instrumentedupdateidentity pass. All1644actualAPI
cases and original21.2MBstream match6.4.10 and Windows byte-for-byte;79capture
cases cover distinct/in-place use. EightWinechecks plus independentWindows
artifact/codegenaudit pass. Sixcold/warm1Tparentcomparisons remain exact;
benchmark signatures419798Linux/351063Windows. InitialASanconfigure omittedbench
inexport; failedattempt retained, newcompleteexportattempt2 passed.

WindowsZIP: `releases/forge-6.4.11-candidate-windows-zen5.zip`,
SHA256 `59978ffd9c38688663179642541859d7540d620b9669bfe9e1186f0a0184aa46`.
This is Wine correctness, not nativeRyzen performance.

NPS/Elo remain unproven. Hostedperformance39334266771 failed its strict3%AA
noisegate and ran noAB/kernel; keep originalthreshold and no retry.
Fresh647-versus644confirmation39332822379 is active and separate; no public
gamecounts/result yet. It does not test6.4.8–6.4.11. Earlier147gamepilot is
inconclusive; never pool its descriptive144game estimate with freshgames.

New649-versus651long0/+5SPRT package is reviewed/preregistered, launch pending:
1024freshpairs, equal2+0.02, naturalboundary/cap,300minuteemergencyfailureguard,
originalsource/binaries/UCI/PGN/logs and finalhashes archived. No24hcontinuous
agent or6hchat scheduler is available. Next sourceinvestigation counts actual
duplicateNNUEoutputcalls before considering a safelyinvalidatedcache.

Read [ledger](EXPERIMENT_LEDGER.md), [next work](NEXT_EXPERIMENTS.md), and
[6.4.11 evidence](../validation/nnue-capture-fusion-20261019/HYPOTHESIS.md).
