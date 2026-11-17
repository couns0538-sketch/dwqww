# Unchanged KRK rate comparison prepared; no searches run

The baseline test is compiled at `reference-t12-krk_mate_test` (SHA256 `6dbfbf8703a242cb343dcb19fda89657a58894d2eaf35f42d9e793eaa099770d`). Its unchanged test source is byte-identical to the candidate source (Git blob 329cad9acfee7e0a88e118911d14298818234244). Baseline e04556dd and f27b1971 have identical engine/header/CMake/test trees; a private source snapshot pins every file. The existing baseline source tree still matches this snapshot, and the earlier retained three source hashes match.

The reference links the seven untouched baseline core objects. Relinking those objects plus the untouched UCI object reproduces the pinned reference Forge SHA256 `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e` byte-for-byte. All original object/binary/source pins were rechecked. This binds the object set to the retained reference engine, without claiming an independent recreation of its historical compiler invocation.

The reference test retains the exact baseline CMake definitions and optimization/strict-FP/x86-64-v4 flags. The test translation unit additionally uses -pthread and final -UNDEBUG, matching the original candidate test-driver assertion policy; the frozen engine objects retain their original NDEBUG flags. No engine or test source was changed. Exact compiler/link argv, outputs, exits and hashes are in preparation-commands.txt, baseline-flags.make.txt, baseline-link.txt and preparation-provenance.txt.

After both unchanged existing suites have been attempted and the focused ten searches have completed, root can run one full original invocation per call:

`node /workspace/work/r4-krk-rate/run-next.mjs --execute-authorized`

The first invocation is candidate, then reference, alternately. Each uses unchanged arguments `40 10 2 16 14 1`, original cwd/environment overlay, native timeout 440 seconds plus the original two-second kill grace, and a 450-second outer bound. The first call fixes an immutable deadline at at most 30 minutes and no later than the existing global deadline. Each call starts at most one invocation, and only with at least 465 seconds remaining; pauses consume the same window. Every full stream and command is retained separately. The runner stops before another trial if any reference T1 preflight or main-test miss occurs, or a prior invocation is incomplete or has sanitizer diagnostics. Unfinalized evidence blocks automatic retry.

Counts distinguish each complete 400-test main suite from its 100-test T1 preflight. Position-selection searches are outside both denominators. Incomplete invocations contribute neither complete denominator. A rate or recurrence observation cannot identify a particular causal code change, and different engines may select different qualifying position sets through the unchanged selection code.

Preparation executed only compilation, a control relink and read-only provenance/syntax checks. No KRK search, rate schedule or trial was executed. Root controls execution after the existing suites and focused ten.
