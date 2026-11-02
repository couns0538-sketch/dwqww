# Job3 handover — UNPROVEN

Owners: Engine NNUE plus CR. This is an incomplete data-tool evidence handoff.
Training clearance is BLOCKED because authentic game IDs are absent. No training,
GPU work, engine match or gate was run. Frozen source is
`d8982bc04d3a828ba440bad250d02fb72526f1a2`; all work uses owned D:\a10 copies.

The converter's opt-in `--keep-fen` sidecar preserves all six FEN fields and binds
each row to its source. Legacy binary output remains unchanged. Relabeling can
consume the pinned sidecar manifest; it validates all rows, including unselected
rows, against the binary state and metadata. Existing explicit Lichess game IDs
are preserved; none are invented for source files that lack them.

| Check | Result | Evidence/scope |
|---|---|---|
| Complete holdout position audit | PASS within scope |999953 filtered rows vs10000000 hold013 and6388575 hold014;0 overlaps|
| Six-field FEN audit against raw source | PASS |0 cohort or filtered state mismatches;1000000 selected source rows|
| Authentic game separation | UNVERIFIED |17388528 missing IDs across filtered and both holdouts; observed zero game overlap is not clearance|
| State fixtures | PASS |19 tests,0 skips; castling, capturable/noncapturable EP, counters, stale metadata and legacy byte identity|
| Native relabel | PASS within scope |16 actual source rows,15 castling/3 noncapturable EP;0 six-field mismatches;32768 nodes|
| Actual converter replay03 | PASS |all3 fault points, first/repeated resume, per-shard and concatenated role MD5/SHA256 equality|
| Deliberate failures | Detected |planted same-game leak, stripped castling, corrupt shard, changed input and metadata races|
| Original73 regression tests | PASS |73/73,0 skips,native0; all14 original test files byte-identical; independent evidence review closed|
| Training readiness | BLOCKED |missing authentic IDs; no qualified training manifest or fresh training seed inventory|

The raw audit status is UNVERIFIED and its launcher exited2 as designed. Input
hashes and row counts are in `audit/native-actual01/audit.json` and INPUT_MAP.
The retained348110848-byte SQLite index has SHA256
`ffb7bba18efe8d69bfac8e8b4e1e29b4d84c464df647d375848a6b7f07aac3a7`.
Bulk frozen inputs, that index and the private CPU runtime are retained on the PC;
their hashes are included rather than duplicating them in this pack.

Actual replay03 compares output roles in checkpoint order. Original no-fault,
candidate no-fault and all three resumed runs have identical values below; each
individual shard is also compared. The adapter emits text, bullet and provenance,
so this replay does not claim HCE regeneration identity.

| Role | MD5 | SHA256 |
|---|---|---|
|bullet,512bytes|313a03447aada08fdc6bea76379daf84|4d5cf407cbb194f1be27b2b59385de8f0e5e928e5ce2d768cff5fe4c05cf4170|
|provenance,54bytes|3fbec076b4fc164e07d33cf96c3edf60|88ba1b7c90eada923ad95e0ca64683b05a814055b0fcbadfd2ab300ca0df28cd|
|text,1263bytes|33058b047e7031c2420133bb430d3332|afe0d5fc51a6f226439144718ead2287801ea729bfd9953f0561b56a589d72fe|

Primary replay report SHA256:
`30694FBDEA528C084863F06C2152FEFD59AC7E83AF36412A9732687D366CF46C`.
Faults are before publish, after publish/before checkpoint, and after checkpoint.
Retained staging/orphan files and earlier receipts are rehashed after both resumes.
Only owned test children are interrupted. Proof01 used mock upstream teacher data.
Proof02 had correct bytes but FAILED admission because load sampling and launch
were batched without inspection; its evidence is preserved. Proof03 has separately
inspected quiet samples and a fresh immediate observation, bound to its archived
safety launcher. It supplies the primary admitted proof.

Native relabel report SHA256:
`A459B3CA75087969E76018E72D0ABE9E662DD177A29A9FA03DC82F4FF3200B78`.
Auxiliary probe SHA256:
`64B8199EBE4368F1935D1D855BDFFA14A83E9FF7B63FA936DBA2CF910B251616`.
The probe is an O2 diagnostic build, not a kit v2.3 engine candidate. No engine
performance or strength inference is authorized. Native16 rows contain no authentic
game IDs and are a diagnostic sample only. A separate bounded filtered sample will
be collected with a complete source hash before/after extraction.

Review caught and fixed consumed-manifest/metadata races, final binary mutation
checks, Windows ADS paths, dropped explicit Lichess IDs and missing retained-file
checks. All substantive fixes received focused independent rechecks. Original RED,
failed and auxiliary evidence is retained. Full20 incomplete-pack sealer fixtures
passed without skips; strict qualified-pack validation was unchanged.

Seed4803011981 is reserved for the one baseline/default/opt-in byte comparison.
No new training seed is assigned. The training command artifact deliberately exits2
with BLOCKED/UNPROVEN; it does not pretend a ready training command exists. Crew
must supply authentic game IDs, rerun full game-level separation, resolve any final
regression blocker and review a separately prepared training command before use.

Additional evidence limitations: the disposable bundled restart fixture passed
after the native proofs, rather than before them as the skill prescribes. Its
ORDERING.json records that deviation; it does not replace the actual replay proof.
Fixture MD5efd4d2e8d2829b84108d7da32bae00dd and SHA256
703ae72d2663d0f196854151eebfc9a1f85a22f3cb8606898a5fdebfe121916f match.
The original CPU-runtime copy script compared source/copy hashes successfully,
but a typed PowerShell variable collision serialized its per-file list as text.
That malformed receipt remains untouched. RUNTIME_CURRENT_HASHES.json separately
records the20045 current D-copy files/1326486174bytes at SHA256
C20358958646D3CCF6372FDA39548C9C9840626F8DFD93FCC531219D2D16BBA6;
it does not reconstruct the lost historical per-file list. The Python3.10 runtime
qualified state tests but could not parse the installed NPT Python3.12+ syntax.
Full regression qualification used a separate CPU environment as recorded below.

Final native regression report:
`DF6058CB1CA6FE41580056384CE756CD021A744B0F50DE12BAA36E847900338B`.
Runtime manifest:
`29F8359847D9FC9E25B4B6166805F71940FD35548F9E222587CF16C422C7230E`;
Python3.12.10, Torch2.9.1+cpu, NumPy2.5.4,18824files/597686913bytes.
Runner:
`2A1DE65B4581AE4CB1E74B9D0559DCD420702B060737AD9E00AD9F2F2DD7CAF0`.
All73 collected IDs have passed calls; all219 setup/call/teardown reports passed.
All101 copied-source pins and44 observed NPT import bindings were independently
checked. Private runtime, external NPT source/DLL and installed MSVC/SDK snapshots
match before/after. The suite used Idle CPUs2/3, Torch/BLAS/compile1, no GPU,
optimizer updates or training loops. One existing scheduler-order warning remains.
This CPU environment differs from the historical ROCm environment.

All attempts are preserved. preflight01 passed imports only. suite01 collected
zero tests because the strict D write guard refused pytest's default NUL log sink;
the owned harness now supplies an explicit D log file. suite02 collected73,
passed61 and failed1 before stopping: its NumPy1.26.4 equaled the historical
negative test's deliberately substituted version. The frozen test documents2.5.4;
a separate immutable runtime restores that version without changing the assertion.
suite02 also tripped the workspace guard on29 owned pytest convenience aliases.
Bounded reviewed recovery removed only those links, proving every target file set
and hash unchanged. The final harness suppresses only optional alias creation and
records the intended relationships. Its actual tmp_path fixture passed. Earlier
guard failures remain rejected historical evidence, never clean qualification.

The final collector binds each primary report to its exact launcher, preserves
earlier failed attempts and inventories retained generated caches without copying
external generated code into Forge. Its11 focused fixtures passed and independent
review closed. The pack remains SEALED_INCOMPLETE/UNPROVEN because authentic
game-ID clearance and a qualified training manifest are missing. Its final sealed
checksum identity is recorded in the root FINAL_REPORT after verification.
