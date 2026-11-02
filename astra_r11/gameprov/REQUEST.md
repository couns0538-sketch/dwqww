# Pack request schema 1

`schema`: 1. `scope`: `production` or explicit `fixture`.

`inputs` is an ordered array of:

```
{"id":"holdout013","role":"holdout013","format":"forge",
 "path":"D:/permitted/immutable/input.txt","sha256":"64 lowercase hex",
 "rows":10000000,"bytes":650287208}
```

Roles are `source`, `cohort`, `train`, `holdout013`, `holdout014`. Production
requires precisely the six pinned R10 files: source001/source002,
cohort/filtered, holdout013/holdout014. `forge` means exact six-field FEN,
integer score and result separated by ` | `. `jsonl` means the original R10
normalized object, with exact `source`, positive physical `source_row`, `fen`,
`ply`, `raw_score` and `result_white`. Every normalized object is preserved;
train must be an exact subset of the frozen cohort. Frozen filtered identity
prevents restoring the 47 previously excluded records.

`source_labels` maps each exact normalized `source` string to its raw source
input ID. File relocation does not alter the original source string or digest.

`origins`: array of `{path, sha256, rows, bytes, format:"archived-game-rows-v1"}`.
The archive's SHA256 must already be in the independently reviewed production
registry. Each archive line is exactly `{game_index, ply, fen}`, using a real
zero-based game index and original ply, not a new ordinal inferred from FENs.
Each archive game/ply occurs once. This exchange format requires proof of the
archival exporter and its historical source; it is not that proof by itself.

`bindings`: array of `{path, sha256, rows, bytes}`. Each file contains JSONL objects:

```
{"input_id":"filtered","physical_row":1,"origin_sha256":"64 lowercase hex",
 "game_index":0,"ply":8}
```

The binding-file digest must independently appear in the reviewed binding
registry, with the exact `{population_input_id: input_sha256}` context. Archive
trust does not authorize caller-supplied mappings: identical FEN/ply positions
can occur in several authentic games. A request cannot register its own mapping.

The binding identifies the physical line in a population input and the exact
position in an authenticated archive. A mapping is unique, must match all six
FEN fields and ply, and cannot refer outside the pinned population. Bindings
are optional/sparse; absent ones create explicit UNTRACEABLE outcomes. An empty
origin/binding collection is the current honest production request.

`game_id` is SHA256 of ASCII `astra-gameprov-v1`, NUL, lowercase canonical source
SHA256, NUL, decimal authentic game index. Held-out game membership takes
precedence over training: matching training rows become `moved_holdout`. Missing
original holdout game evidence blocks qualification regardless of retained-set
overlap. No random seed or random split is involved.

The builder's request paths are replaced with relative bundled artifact paths
in PACK.json. The verifier never opens original source paths. It reads only the
pack, the reviewed code trust registry and its fresh D:/a11 audit output.

Synthetic test APIs require an explicit separate trust object with `origins`
and `bindings` collections; the latter maps each fixture binding digest to the
fixture population-input digest map. Fixture trust is refused for production.
The public production CLI does not expose a trust-registry override.
