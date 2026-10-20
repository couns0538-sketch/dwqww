# Forge 6.4.9 external-book control

The actual 6.4.8 parent bypasses OwnBook=false after an external book loads.
The isolated candidate requires own_book at game-search book dispatch, preserving
file loading, analysis/ponder/restricted-search behavior and all 6.4.8 work.
It ports only upstream3c197fa's one-line guard; that remote candidate had not
been compiled against Forge. Accepted integration remains9108d012.

The stronger real-process regression failed against the frozen parent and now
passes: external-file positive control, disable, reenable, load-while-disabled
(without a second false toggle), reenable; successful one-entry loads and spaced
paths are asserted. Choosing the same searched move is allowed. Original
transcripts and the unmodified upstream harness are retained. Full Release9/9
passed after all build targets completed. ASan/UBSan and Windows are pending.

An initial CTest was mistakenly launched before build completion; four test
executables were absent. Raw incomplete logs and the masked wrapper exit are
preserved separately. That attempt is invalid validation, not an engine failure;
the fresh command record preserves CTest's exit code.

The earlier647vs644hostedmatch used no external Book File. Verified frozen
options leave its filename empty, so this specific bypass did not trigger.
That match remains inconclusive for its independently recorded deadline/orphan.
This UCI fix has no claimed NPS or Elo gain.
