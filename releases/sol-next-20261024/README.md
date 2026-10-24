# Forge native research delivery — 2026-10-24

These are isolated research and validation artifacts, not an accepted strength release. The accepted integration branch was not changed. No matches or Elo gain are claimed.

| Delivery | Source / integrity | Handoff |
|---|---|---|
| [Defensive buffer source ZIP](forge-buffer-source.zip) | source `30e703e`; [SHA256 manifest](buffer-source-manifest.json) | [CR draft](../../validation/sol-next-20261024/buffer/CR_DRAFT.md) |
| [H256 int16 full source ZIP](forge-int16-research-source.zip) | source `074102419c90c6b3725cd83c172e1ec22a2d8203`; [SHA256 manifest](int16-source-manifest.json) | [CR draft](../../validation/sol-next-20261024/int16/CR_DRAFT.md) |
| [Windows qualification tools](sol-zen5-qualification.zip) | SHA256 `7a7375e62bb22b834da4fa4d34e98b945d9d9f38d8f731e0a3c71e79141d907c` | [Instructions](../../tools/windows/EXPECTED_OUTPUT.md) |

Both [buffer_fix.patch](buffer_fix.patch) and [int16_fix.patch](int16_fix.patch) are cumulative `-p1` patches against exact `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`. [buffer_only.patch](buffer_only.patch) is the minimal buffer repair. Cumulative patches preserve inherited optional SIMD/alignment/completed-iteration work; none silently resets accepted work or changes the supplied network. Independent real reapplication audits passed. ZIPs contain all buildable source/tests/tools; historical validation/release payloads, Git objects and generated Python caches are excluded.

`NnueInt16` is OFF by default. Its accuracy gate passed; Linux speed verdict is NOISE, not a gain. The native ON d13/d16 counts 850773/3130100 are from the exact documented Linux AVX2-float/int16 profile. They are not a measured Windows or combined-stage3 result. Obtain and preserve actual Windows build identities and node gates before using a frozen option profile; do not silently substitute a different source revision or adjust node counts to conceal a mismatch.

The qualification ZIP contains cross-built Windows oracle/phase helper EXEs and their manifests. They have **not** run on Windows. To qualify GCC15.2 engine builds, rebuild the helpers with the same compiler, matching source cores and flags using EXPECTED_OUTPUT.md; the bundled LLVM-MinGW examples do not by themselves qualify differently compiled GCC engine kernels. No tested Windows int16 playing executable is delivered here.

The PowerShell script passed syntax/verdict tests and six synthetic failure gates on Linux PowerShell7.5.2. Native CPU affinity/priority, complete million-position Windows execution, Zen5 NPS and whole-engine phase percentages remain unverified. Its optional phase probes measure API ns/call only. Stage2 remains a possible regression until measured FASTER. Old script documentation saying no int16 map was supplied describes its earlier tool checkpoint; the later Linux numerical/node evidence is in the current CR draft.

[One-page report](../../SOL_REPORT_20261024.md) · [Continuation](../../validation/sol-next-20261024/CONTINUE.md) · [Tool status](../../validation/sol-next-20261024/TOOL_STATUS.md) · [Evidence limits](../../validation/sol-next-20261024/PRESERVATION_LIMITS.md).
