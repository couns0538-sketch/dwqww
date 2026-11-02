# Regression attempts — UNPROVEN

All original test assertions remain unchanged. Every attempt has a fresh output,
manifest, command binding, admission log and original launcher logs/receipt.

| Attempt | Runner SHA prefix | Runtime | Result |
| --- | --- | --- | --- |
| preflight01 | 743E673F | runtime312 / NumPy1.26.4 | Import-only PREFLIGHT_PASS; no tests. Native0, all before/after identities unchanged. Result C48A7CCE. |
| suite01 | 743E673F | runtime312 / NumPy1.26.4 | Infrastructure FAIL before collection: pytest exit3 opened Windows NUL as its default log file, refused by strict D write guard. Native1, zero tests. Result DEDFA93C. |
| suite02 | 238342D6 | runtime312 / NumPy1.26.4 | 73 collected,61 passed,1 failed,0 skipped; stopped after first failure. The historical negative changes NumPy version to1.26.4, identical to this runtime. Also rejected by workspace guard because pytest created optional current symlinks. Result97CE78B6. |
| suite03 | 2A1DE65B | runtime312np254 / NumPy2.5.4 | PASS:73 collected/73 passed/0 failed/0 skipped; pytest0/native0. Clean capture, disk/reparse checks and all before/after input bindings. Result DF6058CB. |

The corrected log path is an explicit file beneath the fresh output; the write
guard is unchanged. The frozen historical test documents NumPy2.5.4. The new
runtime uses its official CPU wheel and preserves the original runtime312 and
all previous outputs. Neither historical test constants nor their assertions
were changed. Its Python/Torch environment still differs from the historical
ROCm environment; this qualification is CPU only.

Exact old source/helper/runtime-manifest identities are archived in
`reviewed-runner743e/` and `reviewed-runner2383/`, with explicit source-to-archive
maps. No previous evidence is attributed to a later runner revision.

Bounded recovery removed only the29 owned pytest convenience aliases from
suite02 after exact inventory and complete target-file hashing. Every target
file set/hash remained unchanged, and the strict workspace guard passed again.
BEFORE SHA `9AA318228717F386BEC42BC92F07E4D4304B81F8022274E8585A535CDDE40342`;
AFTER SHA `9A99DB800D3DFC7C5D81C69132FF29D7098095F91982766B8E71A8B08B7CDF4F`.
The suite02 guard breach remains a rejected historical qualification.

The final owned harness suppresses only pytest's optional current-alias
creation, records each intended relationship and restores the private hook.
A real tmp_path fixture passed with exact sentinel bytes and no reparse output:
result SHA `3525259BD918B10E42646955558CB4F40B3D2AF0A84FE7D094B215B0DC0473C2`.
The global reparse policy, source/DLL guards and actual fixture directories are
unchanged. Original73 qualification requires a clean final native result and
launcher receipt; earlier partial passes do not satisfy it.

The final suite03 clean result is
`DF6058CB1CA6FE41580056384CE756CD021A744B0F50DE12BAA36E847900338B`.
Its manifest is `2FF8931F83BF6CDBCDC9045395503EE6EE9DB0F6634007029FE8E09610DB5CC1`,
and private-runtime manifest is
`29F8359847D9FC9E25B4B6166805F71940FD35548F9E222587CF16C422C7230E`.
Pytest ran for90.00seconds,132.6seconds including identity checks. One existing
checkpoint/scheduler test emitted the preserved scheduler-order warning. No
optimizer update, training loop or GPU use occurred. Source/NPT loader, private
runtime and installed toolchain snapshots were unchanged. The separately
inspected admission pair was CPUs3%/3%, host75%, then0%/5%, host72%; the launch
was within15seconds of the final sample. Exact command/admission timestamps are
in the original files, and both CPUs were released at09:15:06Z.

Independent final evidence review confirmed73 unique original nodeids and73
matching passed calls, all219 setup/call/teardown reports PASS, all14 original
test files byte-identical, and all101 copied-file pins exact. All44 observed
external NPT imports were prebound and unchanged. The exact last-sample to
command interval was6.16seconds. No regression-evidence finding remains open;
this does not establish data-holdout clearance or engine strength.
