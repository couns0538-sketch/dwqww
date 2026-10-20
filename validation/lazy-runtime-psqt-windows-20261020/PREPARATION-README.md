# Forge 6.4.19 Windows preparation checkpoint

Source `61f598056572dfade6994af8ad2e38817cd28aa3`; immutable Windows 18 parent
`fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`. Source export has 71 files and matches
every frozen Git/root-source-gate hash. Exactly seven exports change; Board,
NNUE source/weights, evaluation parameters and earlier tests remain unchanged.

The derived strict LLVM-MinGW 23.1.3 Zen5 static Release pipeline uses j1,
no FMA, LTO or fast-math. Ten planned Wine checks include 347 runtime PSQT and
54 correction-history assertions. Exact Windows parent bench signature 352313
is preregistered; any mismatch must be preserved and investigated.

All ten Python scripts parse. The read-only artifact auditor is prepared,
including exact source, eight built PE files, seven shipped PE files, actual
runtime object provenance, safe ZIPs and raw manifests. All 219 protected
Windows 18 evidence/artifact files retain their original hashes. Derived script
diffs and hashes are in PIPELINE-ADAPTATION.json. One failed text-only preparation
probe is retained in STATIC-PROBE-FAILED-ATTEMPT1.json; it was a probe-expression
mismatch and did not execute an engine or expose an engine failure.

Source export was authorized separately. No C++ compiler, engine, Wine,
packaging or artifact audit was executed. WINDOWS-BUILD-CLEAR.json is absent;
the default gate rejects execution. Wait for explicit root clearance after
native qualification is stable, then create the concrete build-clear record
from the template with the exact frozen SHA and counts. Run build and validation
through run-phase.py; freeze-bench-signature.py must precede run-package.py.
The read-only audit also requires the windows6419-package-ready marker.

No speed, NPS, Elo, native Windows/Ryzen or Stockfish-superiority result is
claimed. Native 19 qualification and parity evidence remain separate.
