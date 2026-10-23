# Independent Windows raw-evidence recovery verification

PASS. No builds, tests, benchmarks, recovered executables, or engine searches were run.

Exact commit: `a6a3386debea08f0010cc8a1feed25d8c983f0af`. The committed recovery index, release ZIP, and all eight additional-original files were read directly from Git blobs and compared byte-for-byte with the checkout. Their blob OIDs and SHA-256 hashes are preserved in `COMMITTED-INPUTS.json`, alongside exact copies under `committed-inputs/`.

All **509** indexed closed outer files (**52,973,133 bytes**) were reconstructed under `restored-outer/` from those committed inputs. Every restored file equals the closed original in bytes, SHA-256, size, and restored Unix mode. All **198** original producer-manifest entries and the manifest-membership flags match. The original and reconstructed file sets are identical. Original source inventories before and after the verification are identical.

The ZIP supplies **501** file mappings from **275** distinct members. All remaining **8** file mappings use the committed additional originals. No unresolved recovery gap was found.

One source ZIP-member permission differs from its original outer permission; the index explicitly stores the original mode, and reconstruction restored it correctly:

- `forge-6.4.24-nnue-a52efa5f7864-trial-windows-zen5/weights/nnue_weights.inc`: ZIP 0o644, original/restored 0o600.

The verifier's actual exit code is **0**, with **0 stderr bytes**. Exact argv, script hash, timestamps, stdout/stderr, per-file source mapping, and before/after inventories are retained. `FILES-SHA256.json` seals all evidence except itself and the separately generated `SEAL-VERIFICATION.json`, which binds the manifest hash after rereading every sealed file.

This proves local exact-commit recoverability of the closed evidence. It does not independently verify remote GitHub access/publication, source authenticity beyond the pinned Git object, engine correctness, speed, Elo, or whether later runs remain valid. The parent retains sole ownership of Git and publication; no repository file was edited.

Next action: preserve this independent receipt with the pipeline checkpoint, then continue the already qualified NNUE trial workflow without changing the default network/search or rerunning the completed Windows build merely for this recovery check.
