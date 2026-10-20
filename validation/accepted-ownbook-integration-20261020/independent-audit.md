Independent accepted-lineage OwnBook audit passed 807 checks.

Exact source356e863 and source5101c25 exports match Git. The sole production
change requires OwnBook=true for timed external-book selection; the original
156-line candidate script is unchanged and runs against all three exact builds.
Baseline Release reproduces the disabled-book leak before and after toggling;
candidate Release and ASan/UBSan suppress it. Every profile uses e2e4 when
external book is enabled and bypasses book for depth2 analysis. All 12 original
CTest suites and 15 original OwnBook assertions passed. GCC14.2, common strict
float flags, FORGE_NATIVE=OFF, fatal sanitizer/leak options, recorded return
codes, process-group cleanup and before/after source/executable/core identities
agree with original evidence. No current live owned process group remains.

The directional UCI text strips CRLF and combines stderr/stdout; it is not a
raw process-byte capture. Returned moves were syntax-checked, not independently
legality-oracle checked. This is the bounded external-book toggle/depth contract;
it does not establish universal correctness, speed, strength, remote-CI artifact
accessibility or an integration decision. The audit ran no engines or tests.
