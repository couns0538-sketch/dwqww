# S11 integrity-review addendum, 2026-10-26

This addendum supersedes preparation hashes in prior v1/v2 source checkpoints.
No S11 compiler, engine, oracle or performance run has been launched. Existing
S11 engine patch/oracle and original37-file source preparation remain untouched.

The independent read-only review found four pre-native workflow gaps, all now
covered by tests and targeted repairs: retain and compare initial build/FIRST
and artifact identities; bind comparison manifests and global raw digests to
original captures; enforce deadline callbacks during chunk-index hashing and
final postflight; force failure for cleanup exceptions after tentative success.
The cleanup false-PASS was reproduced using a synthetic Python child and a
controlled scope-restoration failure. Before-fix sources and genuine RED outputs
are preserved. Final controls pass:15 parser/transport,7 orchestration and3 build
methods. Python fixture records never count as native chess evidence.

The final CLI still captures one original1M C++ stream per arm into100 fixed
10,000-record gzip1 chunks. It retains a sole original36-byte header and compares
every decoded byte, contiguous record/byte offsets and exact EOF. Each comparison
also checks the original captured indexSHA, bytes and global raw digest; internally
consistent replacement indexes cannot be substituted. Initial source/build/FIRST/
map/artifact snapshots are written into the result and frozen throughout the run.

For recovery only, `--allow-rewrapped-corpus` explicitly permits a NEW gzip wrapper
of the exact original S09 raw bytes. The raw SHA256 and52,261,200-byte size,1M
position count and1M unique count remain mandatory. The unchanged sealer verifies
both actual outer gzip metadata and raw bytes, then seals the input. The result
records the new wire hash/size and `EXPLICIT_REWRAP_SAME_ORIGINAL_RAW`; no positions
are regenerated or selected. Default operation still requires the original gzip
wire. Actual full-size rewrapped recovery has not been run here; interface controls
pass. The root's source preregistration and future native evidence decide execution.

An attempted independent follow-up was blocked by the agent thread limit; no
second independent review PASS is claimed. The coordinating root can read the
small changed functions before freezing source. Native work remains held until
S10 publication is independently verified and a finite resource grant is active.
