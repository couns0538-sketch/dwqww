# R14-B check chain (the "works in Forge" run before the code freeze)

`verify_chain.sh TAG` runs, strictly one step after the other on CPUs 2-3: the relabel test suite, the bridge to the
1M proof, `fresh_checkout_checks.sh` (fresh clones with this PC's default git settings: suite, probe LTO / PGO builds
and their reference answers, loader DLL rebuild = b5, Windows self-test, acceptance, adoption rehearsal on a fresh
copy of the live trainer tree), the loader ABBA in the live setting (old `--num-workers 4` vs fast with 2 builders),
prepare of R8 v5 shards 271 + 272, and an end-to-end R8 v5 job (3,000 rows, PGO probe) through assemble and fen2bin.

These are the exact scripts that ran; they read Opus's scratch inputs (`D:\o14b\ref` old loader DLL,
`D:\o14b\fl\b5_install`, `D:\o14b\npt` trainer copy, `D:\o14b\r2\proof` proof jobs) and write under `C:\o14b\vc_TAG`.
To reuse them elsewhere, change those paths at the top of each script. Results: the RESULTS.md of each item.

`refreeze.sh TAG` is the shorter re-check after a relabel2.py-only change once the code is frozen: the suite from the
worktree and from a fresh clone, the bridge to the 1M proof, the function-level diff against the proof's code
(5c88438f) with a note for every changed labelling function, and the new sha256 to write into the documents. The
probe builds, the loader DLL and the adoption rehearsal do not depend on relabel2.py and are not repeated.
