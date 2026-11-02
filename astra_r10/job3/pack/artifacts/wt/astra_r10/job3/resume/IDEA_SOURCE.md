# R10 real-adapter restart proof

UNPROVEN. Sources copied from this same Forge repository's frozen `d8982bc0`
export; original paths and SHA256 values are in `SOURCE_COPY.json`. Existing
module notices and attribution are preserved verbatim in the copied files.

`data2/bullet_records.py` is the existing Forge encoder, whose header attributes
the MIT bulletformat wire-layout specification at
`eddd9a2d77dbc1391d68f23ba524657e91bd9a73`. This change copies no additional
third-party implementation or constants. The unchanged original byte output is
the regression comparator.

The fault harness and publication hooks are original code written for Couns's
R10 requirements and the installed `resumable-shard-job` contract. Optional
external GPL binpack support remains in the copied converter but is never
enabled by this harness. NPT, Torch, training and GPU execution are absent.
