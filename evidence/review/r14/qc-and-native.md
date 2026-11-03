# QC and native review milestones

QC initial review confirmed aggregate status incorrectly followed only the six-
field key, unassigned rejected rows escaped coverage, and routing failures were
miscounted as FEN parse failures. All findings accepted, reproduced, fixed and
independently rechecked. Final reviewed QC suite:43 tests plus36 subtests passed.
Log: D:/a14/evidence/test_logs/r14/qc/review-green01/output.log
MD5:4c672693fdc8e55b82eb5d8248638211.

Native r02 static review found no concrete unsound move-generation/pruning defect.
Two zip-based tests could hide truncated responses: exact count/ID checks added,
14 quick tests passed. This is permission to qualify, not production acceptance.
Subsequent independent parser review found consecutive empty-square digits were
accepted; the native author is fixing/rebuilding before million-pair qualification.
Do not attribute r02 tests to that forthcoming candidate.

Qualification harness review found nonfinite deadline admission, smoke status
surviving transport cleanup failure, aggregate counts compensating an incomplete
one-ply foundation, and final report allocation after a resource stop. All findings
accepted; fixes and tests in progress. No million-pair PASS exists yet.

Parent scan review confirmed adjacent-digit FEN grammar and unordered guard-band
inputs. Both now have red/green regression coverage. Added interrupted iterator,
long final row, exact-resolution mutation, partial-report and denied-allocation
tests. Latest27 tests passed, substantive recheck pending before production scan.
