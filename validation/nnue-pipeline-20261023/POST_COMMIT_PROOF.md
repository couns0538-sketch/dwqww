# Recovering the final post-commit native proof

Every source-branch commit is followed by the original14-test native suite and
`bench 11` with the unchanged shipped network. The expected old-net signature is
292545; it is not used for the separate trained-net qualification.

Earlier post-commit originals are in `native-after-*`. The final commit's tests
necessarily run after that commit exists. Their raw commands, stdout, stderr,
actual process exits and result are therefore preserved in an immutable Git note,
without creating an endless sequence of source commits solely to store the last
commit's logs. The note is published only after actual tests pass and the source
branch's remote SHA is verified. Existing remote note refs are never overwritten.

For the final source SHA, fetch the published note refs and show its seven-character
suffix reference (replace the angle-bracket placeholders with actual values):

```sh
git fetch origin 'refs/notes/forge-nnue-pipeline-20261023-*:refs/notes/forge-nnue-pipeline-20261023-*'
git notes --ref=refs/notes/forge-nnue-pipeline-20261023-<SHA7> show <SHA40>
```

The JSON includes the full source SHA, original per-file sizes/modes/SHA256 and a
base64 ZIP of all final native-proof originals. Check the ZIP SHA256, then its
member bytes against `original_files`; Unix modes are recorded in both metadata
and ZIP. Publication receipts record the remote note commit and an additional
public HTTP readback when GitHub serves it. Git remote verification and optional
HTTP availability are separate observations. The helper
`publish_final_native_git_note.py` preserves exact commands/streams/receipts in a
fresh local handoff directory and refuses to overwrite an existing remote ref.

This proof concerns default-engine regressions and unchanged292545 repeatability.
The candidate-net's own28 Linux tests,348974-node repeat, Windows14 checks and
378596-node repeat are separate evidence. None of these establish Elo or NPS gain.
