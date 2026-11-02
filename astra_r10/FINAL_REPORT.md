# Forge Astra R10 — UNPROVEN

Work branch: `astra-r10-3jobs`. All three jobs were addressed in order and their
handover evidence is sealed and checksum-verified. Required work that could not
qualify is recorded below. No engine strength, gate acceptance or training
clearance is claimed. All strength remains UNPROVEN.

| Job | Current result | Handover |
|---|---|---|
|1 NNUEWideOutput|Native correctness PASS within disclosed scope; timing CALIBRATION_FAIL; speed UNPROVEN|`job1/pack/`, SEALED_INCOMPLETE|
|2 P4/P7 leftovers|BLOCKED by unavailable required CR commits and permitted fit inputs|`job2/pack_rule50/`, `job2/pack_optimism/`, separate SEALED_INCOMPLETE packs|
|3 datafilter|Full audit complete, game separation UNVERIFIED; state/native replay proofs and 73/73 regression PASS|`job3/pack/`, SEALED_INCOMPLETE; training BLOCKED|

The accepted lock is
`FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072`.
Original branches, protected datasets, trainer queues and Opus work were not edited.
No training, GPU use, gates, matches or SPRTs were run. Crew gate book remains UHO;
no book pooling or Elo claim is authorized by these results.

## Job1 native proof and timing

R9 source `f43a26aeed2448379fc2916b25f31ead8707b0ec` was recovered. Both new kit
v2.3 LTO+PGO builds equal each other and the recovered candidate:
`775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284`.
Original kit MD5 `729FE7275C3C01D22C751CB751D5C9D2`; scheduling alone was adapted
to Idle. Auxiliary diagnostic/sanitizer executables are not handover candidates.

| Check | OFF | ON |
|---|---|---|
|d11,T1,Hash16|312866 PASS|312866 PASS|
|d13|862329 PASS|862329 PASS|
|d16|3024920 PASS|3024920 PASS|
|d20|12389307 PASS|12389307 PASS|
|d22|34048354 PASS|34048354 PASS|
|Perft5 startpos|4865609 PASS|4865609 PASS|
|Perft5 kiwipete|193690690 PASS|193690690 PASS|
|T1 smoke|PASS|PASS|
|ASan+UBSan short self-play|0 reports|0 reports|
|T4 smoke|UNVERIFIED, loaded host|UNVERIFIED, loaded host|

Pinned12k corpus SHA256
`c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265`:
12000 roots,20 exact components per row, zero raw-bit differences. The deliberate
one-weight change W2[0]575→4671 was detected on3975 roots. Seed3771096103 was
reserved for this proof. Original traces, source hashes and positive sanitizer
controls are retained; auxiliary sanitizer provenance explicitly identifies its
recovered R9 build.

Timing protocol SHA256
`c83ccb17d428069be129eaf4f1b253dbf299bb6d77ad0353a5667fa82ccb3245`
was preregistered before timing. Every completed block is retained.

| Timing population | Blocks | Median | IQR | Min | Max |
|---|---:|---:|---:|---:|---:|
|Eligible same-binary A/A|10|+0.361084%|1.098525pp|−1.467115%|+1.411394%|
|All complete A/A|39|−1.173411%|5.138024pp|−24.280917%|+8.671963%|
|Candidate ABBA|0|UNVERIFIED|UNVERIFIED|UNVERIFIED|UNVERIFIED|

The eligible A/A IQR exceeded the preregistered1pp gate. Candidate ABBA therefore
did not start. Neither a speed gain nor a below-threshold candidate conclusion can
be drawn. Independent record review passed2273 checks, including156 transcript
hashes and312 node pins. Remaining evidence limitations are derived CPU telemetry
without original counter snapshots and Git/session publication evidence without a
separate immutable push-time receipt. No thresholds were relaxed or retries run.

Job1 pack SHA256SUMS SHA256:
`1AF9E1C9850ECE6B1D7DA03F7046F982AF0999CBA8F140AD85C463967E8F85CD`.
1419 artifacts/1422 checksum-covered files, complete MD5/SHA256 verification PASS.
Owners Engine QA plus CR must resolve noise/T4/fresh gate seed inventory and run
their official ABBA and short non-regression SPRT on UHO. The generic proof helper's
Werror witness differed from the exact kit contract; original kit receipts and
its fatal profile-warning check are preserved without fabricated helper acceptance.

## Job2 recovery and blockers

Live heads at the start were P4`df79fb6e33e0ec45e4bdf40cbbdfadb3b6fc27a6`,
P7`cd9cb992fd6a6b05766d1117c1de441a430586a9`, and status
`43af044a14a375b653f3d0bc633d9f476325ca81`. No newer-head skip applied.
Required CR commits1e7b5d20,cc826b0a,129d440e were absent from original objects
and GitHub retrieval; the exact delta patch was unavailable. Bounded recovery
evidence is preserved, unrelated prefix collisions rejected, and repeated recovery
stopped. Original PGN hashes and fit data were also absent from committed sources;
forbidden F: and Opus folders were not accessed.

No unpatched substitute fit/build/parity result was produced. Stale-ref refusal,
H256/higher parity, widened fits and held-out CI are UNVERIFIED. No new candidate
value, executable or seed was assigned. EvalMatScale was not changed.

| Separate pack | SHA256 of SHA256SUMS |
|---|---|
|`job2/pack_rule50/`|E635D4362A83E4BFC2682BCCA92C00B1458EB5A604DE1E124E96E430E74D3236|
|`job2/pack_optimism/`|0C2AEC6CC35320D495432977C14C88769437A11B04BEEBDFD16AFBD68C7020A7|

Each pack has49 artifacts/52 checksum-covered files and independent verification
PASS, with status SEALED_INCOMPLETE. Owners CR plus Engine Strength need authentic
CR exports and permitted PGN/fit inputs. Each candidate must be developed and gated
alone; the packs contain no bundled candidate or gate clearance.

## Job3 audit, state and restart proofs

Source `d8982bc04d3a828ba440bad250d02fb72526f1a2` and six data files totaling
1926978153bytes were frozen under D:\a10. Input manifest SHA256
`4A0B8287C7BF3C1A4666E1F1D723D7B3C15112EAC18E1A4E5E8DE73E809140AF`.

| Audit population/check | Count/result |
|---|---:|
|Selected raw source/cohort|1000000 each|
|Filtered output|999953|
|Complete holdout013|10000000|
|Complete holdout014|6388575|
|Position overlap rows|0|
|All-six-field FEN mismatches|0|
|Missing authentic game IDs, filtered+holds|17388528|
|Game separation|UNVERIFIED|

The audit compares full source state using authentic source paths and physical row
indexes; these indexes are not game IDs. Missing IDs prevent training clearance
even though observed position overlap and FEN mismatch counts are zero. Planted
same-game leakage and stripped-castling controls were detected in15 audit fixtures.

Opt-in full-FEN sidecars preserve castling, EP and counters without changing legacy
binary output. State tests:19 PASS,0 skips, including byte identity with reserved
seed4803011981. Native relabel used16 actual rows,15 with castling rights and3 with
noncapturable EP,2048nodes each, and produced zero FEN mismatches. Capturable EP is
covered separately by fixtures. Probe64B8199EBE4368F1935D1D855BDFFA14A83E9FF7B63FA936DBA2CF910B251616
is auxiliary O2 tooling, not a kit engine candidate or strength claim.

Actual converter replay03 passed before-publish, after-publish/before-checkpoint,
and after-checkpoint interruptions. Per-shard and concatenated output-role hashes
match uninterrupted output; repeated resume preserves earlier receipts and orphan
evidence. Corrupted shards and changed input were refused. Exact MD5/SHA256 tables
are in job3/HANDOVER.md and original report
`30694FBDEA528C084863F06C2152FEFD59AC7E83AF36412A9732687D366CF46C`.
The adapter emits text/bullet/provenance; no HCE replay claim is made.

Proof01 used mock upstream teacher data. Proof02 byte correctness passed but load
admission FAILED because sampling and launch were batched without inspection.
Both are preserved. Primary proof03 passed after separately inspected quiet samples
and a fresh prelaunch observation. Only owned test processes were interrupted.

Original73 regression: PASS, zero skips, native exit0. Independent review verified
all73 collected IDs/passed calls,219 passed phases,14 byte-identical original test
files and101 source pins. Final result SHA256
`DF6058CB1CA6FE41580056384CE756CD021A744B0F50DE12BAA36E847900338B`.
The final CPU runtime uses Python3.12.10/Torch2.9.1+cpu/NumPy2.5.4, manifest
`29F8359847D9FC9E25B4B6166805F71940FD35548F9E222587CF16C422C7230E`.
All private-runtime, external NPT source/DLL and installed compiler/SDK identities
matched before/after;44 observed NPT imports were prebound. One existing scheduler
warning is preserved; no optimizer update, training loop or GPU use occurred.

Job3 pack SHA256SUMS SHA256:
`F02E6E139C198F9616EBA2A3510FF07B188C32D1BD8C6BF25DB80D16388DC25D`.
MD5SUMS SHA256:
`B57D69E5C3EEF289DC5170A538F003B09DBD4DC55219CB741045D8EBA785D896`.
The sealed pack contains 3946 artifacts totaling 103098358 bytes and 3949
checksum-covered files. Independent metadata/coverage review and actual full-file
SHA256/MD5 verification PASS. Verification receipt:
`35772CB06E61A13940137A34A479EF9D38634853C37B93D61224FC43BC318751`,
in `job3/packaging/verify-cpu2final01-launch/result.json`; native exit 0, Idle,
one worker on logical CPU 2, no capture or disk-floor errors. Its stdout records
3949 files, PASS, SEALED_INCOMPLETE and UNPROVEN. Independent final review matched
the receipt, manifest, verifier pins and unchanged pack identities, with no open
pack-review findings. Passing checksums does not grant training clearance.

The handover is for Engine NNUE plus CR. The training artifact is a BLOCKED guard,
not a fabricated
ready training command. Authentic game IDs and a reviewed qualified training
manifest/seed inventory remain prerequisites for any later training.

Two additional deviations are retained explicitly. The bundled disposable restart
fixture passed after, rather than before, the actual adapter proof; its result is
auxiliary only. The original CPU-runtime copy receipt lost its per-file array to a
PowerShell variable-type collision. The script's source/copy comparisons completed,
but the historical list is unavailable. A separate current-D identity snapshot
contains20045 files/1326486174bytes, SHA256
`C20358958646D3CCF6372FDA39548C9C9840626F8DFD93FCC531219D2D16BBA6`.
It does not claim to reconstruct historical hashes. That Python3.10 environment
cannot parse installed NPT Python3.12+ syntax, so it supplies no73-test acceptance.

The final73-test acceptance comes from separate suite03. Earlier suite01 stopped
before collection because pytest's NUL log sink conflicted with the D write guard;
an explicit D log path fixed that. suite02 passed61 then failed a negative control
whose substituted NumPy1.26.4 matched the chosen runtime. The frozen test documents
NumPy2.5.4; a separate immutable runtime supplied that version, with every original
assertion preserved. suite02 also triggered the global workspace guard on29 pytest
convenience aliases. Reviewed link-only recovery preserved every target byte; the
final harness suppresses only optional aliases and records them. All original
failed/rejected receipts, exact earlier runners and runtime manifests are retained.

## Review and continuation

Focused independent reviews were performed at meaningful implementation milestones,
before expensive validation and before closing each pack. Confirmed races, identity
binding gaps, dropped explicit IDs and retained-evidence checks were fixed and
rechecked. Original failed attempts remain available. RESULTS.md records candidate
identities, findings, fixes, validation and next actions; RESUME.md names the exact
current continuation step. No unresolved candidate is called accepted.

Matching skills were improved in this branch. The D-only write rule takes priority
over installing changes globally on C:. No Codex configuration was changed.
