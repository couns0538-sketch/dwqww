# NNUE strength package preparation

Source is frozen; review gate remains **PENDING_REVIEW**. Candidate6.4.11 is
`c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`; baseline6.4.9 is
`4edda780c68a742f20565d4e6a54a0c99a2c88a6`. Both protocol and workflow contain
the actual candidate SHA. Release9/9 and both actual-core differential streams
match frozen gold; ASan and Windows validation remain pending. No playing
strength or speed gain is accepted.

The candidate's only runtime change versus6.4.9 is quiet+capture NNUE update
fusion (44added lines); the remainder ofnnue.cpp, including original fallback,
refresh, evaluation and weights, is byte-identical after removing those lines.
CMake/UCIchanges are version labels only. All68source-export input hashes,
unchanged tests/bookmetadata, and2added diagnostic-only driver tools are recorded
in source-inputs-SHA256.json/source-scope-audit.json and originaldiff files.

Fresh SHA-visible validation passed40/40 mocked runner tests and8/8 archive
tests. StaticYAML, each shell step withbash-n, PythonAST, both pool sizes,
disjointness, strictEPnone, exact separately frozen runtime order/SHA,
68source-input files checked against both Git objects, and all22package/workflow
SHAentries passed. Evidence is retained asroot-ready-* files. No engine or
Fastchess was executed for these package checks.

Earlier logs remain unchanged. The initial39-test attempt exposed a fixture's
250msPython-startup assumption, not a runner cleanup defect; its failure is
retained. The deadline fixture now advances its mocked emergency clock only
after actual parent/child+stdout handshake. Root-ready tests beforeSHAinsertion
are preserved separately from the final SHA-visible reruns.

Before launch root must finish ASan/Windows validation and final independent
review, record actual evidence, update gate/narrative, refresh packageSHAregistry,
and passcheck_prelaunch.py --require-ready. ROOT_CHECK_COMMANDS.md gives exact
commands and inventory sources. The gate stays closed until then. Original
pre-source-freeze protocol/workflow/README/inventory/STATUSare preserved here.

No builds, engine execution, games, launch, branch mutation, commit or push were
performed by package preparation. Git commands used only read frozen objects.

Fresh complete opening verification also passed: original archive/license/PGN
hashes, all34700legal16plygames,34700unique positions,3097actualEPpositions
excluded without rewrite,31603eligibleEPnonepositions, all42original registry
hashes plus explicit164confirmation cohort and unused historical tails, zero
overlap, unchanged4/1024selector pools, and exact separately frozen runtime
order/SHA atseed20261021. The checker reads only the frozen registry list;
it does not scan new workspace selections or change any opening input.
Root-ready-opening-check.json/.stdout/.stderr retain this result.

## Final root readiness

The pending-review preparation above is historical. Sourcec5cbf97 passed Release9/9,
ASan/UBSan9/9 and instrumentedstreamidentity, sixcold/warmparentsearchparity,
Windows8Winechecks/crossplatformstreams and independentartifact/codegenaudit.
Rootindependent40runner+8archive mockedchecks pass. Protocol now records full
proof-fileSHA256s and is PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH.
A single new triggerbranch push is authorized; no games have run yet.
