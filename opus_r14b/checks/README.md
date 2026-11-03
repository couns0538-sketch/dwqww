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

`hash_sweep_r14b.sh OUT_FILE` re-runs the post-freeze hash sweep over the R14-B documents: every cited hash must match
a file, a commit or a reasoned allow-list entry. 20:48: 0 unmatched (88 file, 18 commit, 39 allow list). 21:30: 13
tokens cited since then pointed at files outside its list (the lock exe, the four kept exes, the P6 crfix patch, two
scratch builds); after adding them, 0 unmatched (107 file, 24 commit, 39 allow list). Refreeze run 21:04-21:10:
0 failures. refreeze.sh validated on the frozen code.

`make_index_r14b.sh` writes `FILES.txt` + `SHA256SUMS` of both item folders (forge-job-workflow "Finish", with the
shared helpers in `F:\opus_scratch\tools`, read-only use) and runs `sha256sum -c` on them; re-run it after any edit in
an item folder and commit both files with the edit. `fresh_checkout_checks.sh [OUT_DIR]` takes its output folder as an
argument since 22:35 (default `C:\o14b\fresh`, which must not exist).

`e2e_r8v5.sh OUT_DIR [ROWS]` runs the frozen relabel2.py end to end on R8 v5 data (the 50M runbook's input format):
prepare -> run (LTO+PGO probe, 20k nodes, 2 workers) -> status -> assemble -> fen2bin + hce_dump on both outputs, with
11 checks (records = rows, 0 bad / clamped, rows and game overlap, shard settings, a second run / assemble). 22:53:
11 / 11 PASS, output byte-identical to the 20:30 chain run on the first freeze.

`final_checks.sh OUT_DIR` is the end-of-job check in one command (about one minute): doc_lint over all R14-B
documents, the file indexes (must already be committed), `sha256sum -c` in fresh clones of both item branches, the
hash sweep, test_tools.sh, the installer and scope tests from the item 1 clone, relabel2.py = the frozen sha256 of
RELABEL_HANDOFF.md plus e2e_r8v5.sh, and every worktree clean and in sync. Dry run 22:56: 8 / 8 steps PASS.
