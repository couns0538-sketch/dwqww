# Windows 24 archive restore helper adaptation (preparation only)

Source template: `validation/tt-refresh-20261021/archive-complete/restore_new_scratch.py`.
Frozen candidate source: `7db08eac6ead99d641834c56ccec06a06600586a`; parent23: `1d3ed25bea2c8b781f7ee5a178af0f66061b3984` (root supplied; no source/producer directories inspected).

- Original script SHA256: `1efc0d1998d33973eed109e28e042ed047237ffc3ddcc94d4651ef3eb91050fc`
- New script SHA256: `65805f76ae02a12a193df33f5079c0061eaaf547821c4571dc7754f6497171f3`
- Script mode preserved from immutable template: `0600`
- Exact source diff: one manifest-default line (+1/-1), with all remaining bytes unchanged.

```diff
-NAME = 'forge-pawn-span-fc23918-20261020-complete.manifest.json'
+NAME = 'forge-see-proof-reuse-7db08ea-20261021-complete.manifest.json'
```

The immutable23 helper itself retained an older pawn-span manifest default. The new default matches the anticipated24 base; explicit `--manifest-name` remains supported. The CLI already accepts absolute `--parts`/`--destination` paths and embeds no scratch/stage names. Root can later freeze explicit new `/workspace/.cloud-setup/see-proof-reuse24-complete-*` stage/scratch arguments; no location is created by this preparation other than these two owned files' directory.

Unchanged restore behavior: externally pinned manifest SHA256; raw-split-ZIP schema and 67,108,864-byte (64 MiB) split size; each part's byte count/SHA256 and reassembled ZIP count/SHA256; unique safe ZIP/payload paths and no symlinks; exact embedded/external file manifest equality; every payload byte count/SHA256 verified before scratch creation; new nonexistent absolute scratch only; per-original restored-byte verification, file modes/mtimes and directory modes restored through the original mode map. Original error handling and fail-closed checks are preserved, with no new audit layer, cleanup, original-path write, engine/compiler/Git/network call, or optional comparison.

Validation performed: source-only AST parse, exact single-line replacement/reversal assertion, immutable-template byte check, and prepared-file mode/hash inspection. No helper import/execution, snapshot, production archive, part reassembly, genuine scratch recovery, mutable Windows/root producer-directory read, engine, Git or network action occurred. Parent Windows proof/canonical capture49139 closure and root's separate authorization for one actual archive plus scratch recovery remain pending. This helper grants no execution authority.
