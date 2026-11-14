SCRATCH HUMAN REPORT RENDERER ENHANCEMENT

Production renderer baseline SHA256:
f49db3c24c2e192c4e6ac478b9488d05d8c9170f54718ef8aac03ae180f5fc44
Proposed renderer SHA256:
880ac38a8125dec01eb87030bc715ccb6f7f1729f7a447598f241cc919e588cc

Production renderer, controller, state and repository outputs were not edited.
Root owns adoption, report regeneration and commits. The proposal was created
from the current root renderer and preserves its prior content and edits.

New D/E/F rendering matches audit rows to finished state attempts using phase/id,
finishedUTC, recorded counts and available process exit/signal. Missing, stale,
duplicate, active and unmatched rows remain explicit. Missing audit/process
fields display unavailable, not an inferred clean result.

Per-batch evidence rows show Threads, depth/node settings and literal candidate
flags in order ContHist4PlyRead / NonPawnCorrection / LmrDeeperShallower. Values
come from each retained raw SUMMARY, with parsed-SUMMARY fallback; current phase
descriptions never supply conditions. A raw/parsed mismatch omits conditions
and is called out. Incomplete attempts without condition output stay unavailable.

Canonical primary-log TSan warnings are summed once for matched audited batches.
Resolved source-file/line pairs are grouped globally by warning kind and sorted
pair, with per-batch contributions retained. The same pair reported2 and3 times
in separate batches is one observed group with5 reported warning blocks, not
five bugs or two distinct bugs. Unresolved blocks remain separate. Runtime exit66
without warning text remains visible independently from chess faults0. Timeouts
are distinct from crash claims. Footer inconsistencies/group-count mismatches
and audit omissions are retained, not silently patched.

2G compact counters now include tests_completed,cases,mate_cases,nonmate_cases,
rule50_cases. Existing exact-counter appendix and all state counts are unchanged.
The generic audit column now correctly says artifacts with diagnostic markers;
its underlying array length was never a count of individual diagnostics.

Verification: final-check.txt and renderer-synthetic-test.mjs. Tests include
pure rendering of deeply frozen inputs; unchanged state/audit; repeated/reversed
source-pair grouping; missing/stale/duplicate records; unresolved warnings;
exit66 with0warning blocks; unavailable process fields; inconsistent group counts;
per-batch Threads4/depth9 and candidate-true node2000 conditions; raw/parsed
condition mismatch; root notes and requested2G short counts preserved.

Previews:
- synthetic-preview.md: synthetic warnings/failures only, not native findings.
- live-readonly-preview.md: actual read-only state snapshot with audit-after-D2;
  finished2D1/2D2 represented, active2E omitted. No native workload was executed.

Review files:
- render-report-baseline.mjs
- render-report-proposed.mjs
- render-report-proposal.diff.txt
- renderer-synthetic-test.mjs
- final-check.txt
