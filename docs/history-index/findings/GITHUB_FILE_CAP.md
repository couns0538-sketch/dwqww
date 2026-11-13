# What a 300-file listing does not show

GitHub's pull-request file list and some directory pages stop at 300 entries. The inventory below was made with local `git ls-tree` and `git diff-tree` on 2026-11-13, after the frozen tip list. It does not depend on the website.

## Directories with more than 300 immediate files

330 unique tip trees were listed (the 327 frozen trees, plus the three sibling branches that existed by the afternoon). 16 trees contain a directory with more than 300 immediate blobs. Four directory paths:

| Directory | Trees | Most children |
|---|---:|---:|
| `validation/astra-a1-data/github_delivery/full_transfer_receipts_20261030/chunks` | 11 | 882 |
| `validation/sol-next-20261024/int16/NPS-Linux-dry-run/raw` | 5 | 348 |
| `validation/forge_sol_pack31_20261025/forge_sol_S11_closed_native_parity_20261027/B_native` | 1 | 335 |
| `validation/forge_sol_pack31_20261025/forge_sol_S11_closed_native_parity_20261027/LP_native` | 1 | 335 |

Alphabetical order is not GitHub's only sort, so a particular name might land on either side of the cut. The counts do not. Anything past the 300th name in that order is one of 458 unique blobs. 208 of those are JSON receipts about 823 bytes each. Two are the 67 KB S11 parity results named in `findings/BUGS.md`. The rest are stdout, gzip, and a few logs. None of those 458 blobs is a `search.cpp`.

## Tip commits that change more than 300 files

Eight of the 327 unique tip commits have a `diff-tree` larger than 300 paths. A pull request of that commit cannot show every path.

| Files | Tip commit | Example branch | Subject |
|---:|---|---|---|
| 4035 | `e6868fd56ebb` | `astra-r10-3jobs` | Seal verified R10 data pack |
| 901 | `17aa0cae1d36` | `forge/sol-pack31-20261025` | Preserve S11 parity streams |
| 432 | `1c0f5c956382` | `forge/clock-contract-reconcile-20261020` | 6.4.13 validation checkpoint |
| 418 | `63ec719e2706` | `forge/double-extension-path-20261020` | 6.4.14 validation checkpoint |
| 333 | `563bd406e911` | `forge/hosted-nnue-strength-20261019-20261020-0040` | Forge6411 Windows evidence |
| 322 | `352b6ff2c0e4` | `forge/hosted-promotion-see-strength-20261020-202830` | 6.4.17 candidate |
| 318 | `27070febf353` | `forge/nnue-pipeline-20261023` | Native NNUE qualification |
| 312 | `5b9b132bf179` | `forge/see-proof-reuse-20261021` | Interrupted Forge24 qualification |

The commits are the full ids in `branches/HEADS.tsv` for those branches. The 12-hex prefixes above are unique in that file.

Files that sit past the 300th alphabetical path of the 4,035-file commit include the astra datafilter `RESULTS.md` (blob `c25059861c4d4e66f373d4d9c0a5c19511023cc7`). It was read. It is a data-filter handoff, not an Elo result. It records a holdout overlap that a later split removed, and a case-fold pair `source/a` and `source/A/child.txt` that a Windows checkout cannot materialize together.

Also read from past the cut, and not engine defects: the clock-reconcile independent audit (872 checks, no engine run, blob `cc47caca2970df9b49158c32d101a1751b54dd5e`), the time-forfeit runner review (a process-group cleanup bug the same file says was then fixed in that runner, blob `ab2b5937aad8dad1de2f218fe632b662ef631b02`), and the NNUE pipeline recovery report (509 files reconstructed, no engine run, blob `2d469bfe55036da13d4f02e065d3d8593b9011fa`). The S12 operator README in the same overflow (blob `252101f6a372562d63dfe430a2987765e23004f4`) is source-only and says no native run was authorized.

The 22.2 MB `opus_round1_20261027.tar.xz` is one file. A 300-file cap does not hide it. It is still unopened.
