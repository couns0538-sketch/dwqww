# NumPy revision assembly — UNPROVEN

The original assertion remains unchanged. The frozen test records NumPy2.5.4
and assigns1.26.4 as a deliberate mismatch. The initial new CPU runtime's actual
1.26.4 made that negative ineffective. Suite02 therefore remains a failed attempt
(73 collected,61 passed,1 failed,0 skipped, stopped at the first failure); its
workspace guard flag is preserved separately and is not erased by this revision.

Independent `proof_contract` review cleared assembler `AA3D1704` and wrapper
`BE47DB29`: fixed original manifest/lock, explicit old NumPy omissions, source
consumed-byte and destination hashes, official new wheel identity, offline
hash-required installation into a fresh stage, and bounded exclusive copies.
No former runtime file, archive or evidence file was edited or deleted.

After the separately reviewed alias recovery restored the strict workspace
guard, the first load observation was WAIT. The next inspected pair qualified:
CPU3 7.8 then12.5%, host80.28125 then80.1875%. The full-root launcher ran Idle on
CPU3 with one worker and a1.4 GB reservation. Actual measured new-byte budget was
702,044,298 bytes, including copied inputs, two NumPy expansions, archives and
bounded logs. C30/D50 and15 GB workspace limits passed.

Assembly returned native0 at2026-11-02T09:07:52.5505928Z, with no capture errors
or disk-floor breach. It produced18,824 immutable input files totaling
597,686,913 bytes. Authoritative and branch manifests are identical, SHA256
`29f8359847d9fc9e25b4b6166805f71940fd35548f9e222587cf16c422c7230e`.
The revised wheel lock is
`560cdd1b73fdf0e28ab9ac6c0ac8d2dfaf8c20824eeb409748944ac4ae16517f`.

The new NumPy2.5.4 wheel and official metadata are retained under the new
runtime's downloads directory, and their exact URL/hash/licence receipts are in
the wheel lock. All other runtime inputs retain the original manifest identities.
The stage is preserved. Existing console launchers other than f2py keep original
bytes and old interpreter paths; the qualification entrypoint is explicitly the
new runtime's python.exe and does not invoke those console launchers.

CPU3 was released and the new path/hash delivered to the regression runner.
Assembly alone is not native import/compiler compatibility or73-test PASS.
The original runtime and every earlier attempt remain available unchanged.
