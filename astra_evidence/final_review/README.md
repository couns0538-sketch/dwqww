# Final review validation results

The first review was interrupted by an unavailable execution environment; a fresh20-minute pass began after recovery. Only the completed clock receipt establishes duration. Engine source is unchanged by the review fixes.

## Native bench after the OFF-validator correction

Threads1, Hash16, OwnBook=false; explicit candidate SmpProtectProvenScore=false. These are node-identity checks, not a controlled speed comparison. Every real-engine bench in this final rerun follows; earlier runs remain in A2/A3 tables.

| Mode | Depth | Nodes | Time ms | NPS |
|---|---:|---:|---:|---:|
| base | 11 | 312866 | 301 | 1039421 |
| candidate | 11 | 312866 | 323 | 968625 |
| base | 13 | 862329 | 869 | 992323 |
| candidate | 13 | 862329 | 901 | 957079 |
| base | 16 | 3024920 | 3039 | 995366 |
| candidate | 16 | 3024920 | 2878 | 1051049 |
| base | 20 | 12389307 | 14603 | 848408 |
| candidate | 20 | 12389307 | 11479 | 1079301 |
| base | 22 | 34048354 | 29212 | 1165560 |
| candidate | 22 | 34048354 | 32662 | 1042445 |

## Review findings and corrections

- Confirmed invalid OFF values could silently be ignored/clamped, yet the old checker returned PASS. Type/range and controlled-setting validation now reuse the companion option parser.14 test methods PASS after10 failing RED subcases;17 option-checker methods and11 independent post-fix probes PASS. The companion tools/check_bundle_opts.py must remain in the normal repository-relative layout.
- Native full serial CTest result recovered after the outage:55/56 PASS, exit8. Its only failing executable prints the exact same four forge_tests diagnostics as native base. Initial52/54 outcome and later controlled SMP retests remain preserved; no inferred scheduling cause is promoted to fact.
-21,600 native comparator grid cases: base/OFF byte-identical; ON protects the positive winning score band. Original native code, commands, core-library hashes and streams are in smp_independent/. Mate protection already existed in the base. No end-to-end TB-file or proof-provenance claim.
- Live UCI2/3thread lifecycle test passed. A separate raw-transcript audit confirms exactly3 bestmove lines per process,6 total. No full-engine TSan claim.
- A5 reuses original published fixtures and verifies both requested cases explicitly; no weakened test or modified expected node count. Original build logs and negative-control fixture failure are in ../A5/.

IDEA_SOURCE: Owner review request, original Forge source and independently written negative controls; no other engine code.

## Python3.10 compatibility correction
Independent review found hashlib.file_digest requires Python3.11, whereas CMake accepts Python3.10. The regression first reproduced AttributeError with that API removed; the checker now hashes in bounded chunks.16 OFF-checker methods pass, including multi-chunk executables with independent whole-file SHA256 comparisons. This simulates the missing API on Python3.12; an actual Python3.10 interpreter was not available. Native final d11 rerun after the hash-only change follows; both recorded binary hashes independently match.

| Mode | Depth | Nodes | Time ms | NPS |
|---|---:|---:|---:|---:|
| base | 11 | 312866 | 324 | 965635 |
| candidate | 11 | 312866 | 535 | 584796 |

## Independent final-script replay
A new run against the final streaming-hash script passed11/11probes. The reusable harness, exact argv/cwd/timestamps, source copies/hashes and original output bytes are preserved under postfix_reproducible_v2/. Its77manifest entries verify. This is new evidence, not a reconstruction of earlier ad-hoc runs.

## Broader sanitizer check
All targets built successfully with ASan/UBSan. The first serial CTest session was terminated by a tool-server disconnect after test18completed; its17passing cases and known forge_tests failure are preserved, with no final suite exitcode. A separate run resumes at test19on the same configuration; its final status will be recorded separately.

Final update: review duration 1239.08 seconds (20m39s). Both checker fixes passed. The separate resumed sanitizer segment passed 38/38. The subsequent uninterrupted 56-test qualification passed the unchanged repository exception policy: raw CTest 55/56, exactly four known tactical diagnostics, zero sanitizer reports. Final classification verified all 64 actual command inputs unchanged and preserved four generated outputs separately. See ../sanitizer_complete_20261029/.
