# Forge text evidence archive

This archive preserves exact UTF-8 bytes of local text evidence. It is not an engine release: no executable or NNUE network is included. A manifest describes content-addressed text chunks and original files. Publication may be incomplete until the uploader verifies every listed chunk. A manifest alone is not proof that every chunk is available remotely.

## Format and provenance

`manifest.json` uses `utf8-concatenated-text-stream-v1`. Concatenate `chunks` in numeric `index` order, validating each chunk's byte length, SHA-256 and contiguous `offset`. The result has exactly `stream_bytes` bytes. For each `archived_files` entry, read `bytes` bytes at `stream_offset`, verify `sha256`, and restore under its original `path`. Offsets count bytes, not Unicode characters. Identical whole-file contents may share offsets; chunk boundaries are not file boundaries. UTF-8 decoding is validated but content is never re-encoded or newline-normalized during reconstruction.

`already_remote` entries were byte-identical to an immutable Git commit named in `remote_baseline_commit`. Retrieve them from that commit, not the moving branch tip. Where a local file differed from an existing remote version, its snapshot is in `archived_files`; the prior remote file is not overwritten. Restore to a new directory to avoid conflating versions.

## Verify and reconstruct

Download `manifest.json`, `reconstruct.py.txt`, and all hash-named chunk files into a flat `chunks/` directory. Review the script, then run with Python3 (standard library only):

```
python reconstruct.py.txt manifest.json --chunks chunks
python reconstruct.py.txt manifest.json --chunks chunks --output restored
```

The first command verifies all archived contents without writing restored files. The second verifies everything first, then writes exact bytes. It never overwrites a different existing file. To also verify and restore `already_remote`, supply a Git checkout containing the pinned commit:

```
python reconstruct.py.txt manifest.json --chunks chunks --output restored --baseline-repo /path/to/repository
```

Without `--baseline-repo`, the script explicitly reports that baseline files were not independently fetched/verified. Missing, truncated or altered chunks fail verification. Keep enough free disk space for a temporary concatenated stream plus restored files. The script uses no network and installs nothing.

## Interpretation

Archived raw output can include intentionally wrong diagnostic controls, incomplete experiments, stale intermediate notes and failed attempts. Use the final reports and manifests to distinguish these; preservation does not imply validation. Native test coverage remains finite and dependent on the recorded build, options, network and positions. It does not establish universal correctness or an Elo/performance improvement.
