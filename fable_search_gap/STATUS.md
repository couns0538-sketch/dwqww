# STATUS: fable52 search-gap job

Updated 2026-11-09 20:40 PT. Branch `fable52-search-gap-20261109`. Read this file first when resuming.

## Done

- Job folder, blob-less clone and branch created. Disk on D: went from 34.33 to 34.08 GiB free (my footprint is about 0.1 GiB).
- Lock exe and reference exe hashed; both match their pins. The lock exe reproduces all twelve pins on CPU 3-6 at Idle.
- Source of record fixed: the Engine QA lock pack on the PC. No repo commit holds the combo29 search source.
- Lock `search.cpp` read in full, plus the TT, history, board and eval interfaces.
- All 387 fetched branches indexed; 3,754 text files pulled into a local corpus for dedupe searches.
- The crew's master lists read: 81 ranked idea families, the 101-row lock feature diff, the R15 candidate index, 110 gate rows, today's live candidates.
- `COVERAGE.md` written.

## In progress

- Failure analysis of the gate table and the surviving logs.
- Dedupe ledger and source audit.

## Working conclusion so far (not final)

Every mainstream search mechanism I checked is either in the lock, already built or gated by the crew, or already listed and dropped in the crew's research notes. One classic mechanism, enhanced transposition cutoffs, appears in none of those places. Its primary source is a 1996 paper; later practitioner reports are weak. No verdict has been written yet.

## Exact next action

1. Run the log-based failure analysis and write `EVIDENCE.md`.
2. Write `DEDUPE.md` and `IDEA_SOURCE.md`, commit and push.
3. Decide: one qualified mechanism, or NO QUALIFIED GAP. Write the spec or the dossier, then `FALSIFICATION.md`.
4. One reviewer pass, fixes, `REVIEW_LOG.md`.
5. `FILES.md`, final `STATUS.md`, final push.

## Resume commands

```powershell
# every shell call of this job starts with this line (TEMP/TMP on D:, no git prompts)
. D:\forge_jobs_20261109\fable52\out\env.ps1
Set-Location D:\forge_jobs_20261109\fable52\repo
git status --short; git log --oneline -5

# pinned run of any tool (CPU 3-6, Idle); example: the lock pin check
$T = "$REPO\fable_search_gap\tools"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T\pin.ps1" -Exe C:\Python315\python.exe `
  -ArgLine "-I -B $T\uci_probe.py pins --exe $OUT\exe\combo29_E1284F7F.exe --workdir $OUT\run --out $OUT\logs\pins_combo29.json"

# rebuild the branch index and the dedupe corpus if out\ was lost
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T\pin.ps1" -Exe C:\Python315\python.exe `
  -ArgLine "-I -B $T\tree_index.py $REPO $OUT\index\tree_index.tsv"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$T\pin.ps1" -Exe C:\Python315\python.exe `
  -ArgLine "-I -B $T\fetch_corpus.py $REPO $OUT\index\tree_index.tsv $OUT\corpus --include `"\.(md|cpp|hpp|h|patch|diff)$`""

# push (this branch only)
git push origin fable52-search-gap-20261109
```

If `out\env.ps1` is missing, recreate it: it sets `$J`, `$REPO`, `$OUT`, points `TEMP` and `TMP` at `D:\forge_jobs_20261109\fable52\out\tmp`, and sets `GIT_TERMINAL_PROMPT=0` and `GCM_INTERACTIVE=never`.

## Rulings (decisions I took where instructions met)

- **Review.** One fresh-context reviewer at the end, as AGENTS.md asks, on a different model. No other agents.
- **CPU.** The Forge connector tools that run engines use CPU 0-1, so I do not call them. All engine runs go through `tools/pin.ps1` (mask 0x78, Idle).
- **Commit identity.** Repo-local `couns0538-sketch <couns0538-sketch@users.noreply.github.com>`. Existing agent commits use the same name but not a no-reply address; I chose the no-reply form so no private email is written.
- **Line endings.** `core.autocrlf=false` in this clone only, so file hashes in `FILES.md` equal the committed bytes.
- **Sparse checkout.** Only `fable_search_gap/` and `skills/forge-search-gap-dossier/` are materialised; the ten files of `main` stay untouched in the tree.
- **Test-first skill not loaded.** No product code is written. Each tool is checked against a known answer instead: the launcher against a negative control, the probe against the twelve pins.
- **Memory and scratch.** Nothing written under `C:\Users\...\.claude` apart from the plan file that plan mode required.

## Unproven claims

- Nothing in this folder is an Elo claim.
- "No repo commit matches" covers the 387 fetched branches only.
- The parent chain of the lock source is quoted from crew records; I did not rebuild the lock.
