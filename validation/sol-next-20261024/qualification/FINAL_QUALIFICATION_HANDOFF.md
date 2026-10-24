# Final qualification preservation note

No qualification source correction is needed. The repository PowerShell script matches the tested v2 handoff SHA256 `e52e8ba069aab14bdc78897672c7744f0d6f959f72fc3b0b244348145f0cb8fd`. The actual UCI source emits both exact activation/fallback strings required by that gate.

The skill was prepared as a patch and later applied by the root owner: before SHA256 `ca5b98d93f0f190944d1718ea3963fde17c7d5fbfdee89318ce1f86d8e58f8f0`, proposed/current SHA256 `adefefb5b7b419e933f9cba76ff9c1087f40855ee2597c341f0f28a43118fe24`, patch SHA256 `e514ca1c92ea7a3a7d22eeca71f3d9c1c2b1cfe9f041c6d7facac9240dc9baf6`. It adds 16 physical lines/removes 0. The packet's `repo_source_unchanged` field records its preparation-time state; it is not a claim that the root's later application did not happen. Do not reapply the patch when the current skill already has the after hash.

Copy the files listed in FINAL_PRESERVATION_FILES.json plus the manifest itself. It keeps the eight-file skill packet/checksum list, the complete small v1 source packet, combined v1/v2 PASS summaries, curated development-error excerpts, and only the final failing child exchanges for each synthetic gate. Existing repository qualification root-console captures and current source/manifests need no duplicate copy. No SDK/runtime/cache or full synthetic directory is required.

Important labels for the final report:

- `verification/failures-before-fix.log` contains curated excerpts of actual startup/serialization errors plus diagnosis. Full raw transcripts of those development attempts are not retained in these files; do not call the extract a complete raw log.
- Existing qualification `root-*.stdout.txt`/`root-*.stderr.txt` files capture the PowerShell wrapper console. The specifically selected child-level stdin/stdout/stderr files provide separate raw synthetic exchanges. The tiny truncated oracle is a deliberate invalid fixture, not a real oracle corpus.
- PowerShell 7.5.2 parser/verdict checks and six synthetic failure gates passed. This does not validate a complete successful million-position/AA/ABBA session, native Windows priority/PE/ISA behavior, or performance. The Linux dry-run skips the Windows Normal-priority setter.
- The existing RESULT.json remains accurate: Windows protocol NOT_RUN, native Zen5 performance UNMEASURED, whole-engine phase split NOT_MEASURED; optional microprobes report API costs only. No Elo claim follows.

| Synthetic case | Expected rejection | Actual child invocations | Paired/summary CSV |
|---|---|---:|---|
| bad_d11 | BADNODES | 6 | Absent |
| bad_d13 | BADNODES | 7 | Absent |
| nonzero | BADEXIT | 6 | Absent |
| oracle | ORACLE_FAIL | 21 | Absent |
| bad_option | BADOPTION | 26 | Absent |
| inactive_backend | BACKEND_INACTIVE | 26 | Absent |

Final v2 combined PASS stdout SHA256: `cb095d233bd19d96f7f0ca9ecdf0f7873d3991ba648e58da6945b94c93132751`; stderr is empty. V1 script SHA256 remains `b5f12dd07868dc4000d2debbaa37ec3f84623d2edffd42cff23f3e164cc4396e`. The source/verification manifests and exact paths in the preservation list make these small records independently auditable.
