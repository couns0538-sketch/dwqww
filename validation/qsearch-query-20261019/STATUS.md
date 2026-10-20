# Qsearch query deferral: correctness passed; speed/Elo unmeasured

Source/tests `4e15dea025c4b1ced9cbb5c9000a0cb627edcf15`, branch `forge/qsearch-query-20261019`.
Parent is tested6.4.5 source82cd2c2 (publication63ee572); accepted integration
remains9108d012. Reuses upstream3dddd864 one-line pure-query relocation.

Compute Board::gives_check only inside its sole qsearch use guard. Checking
evasions and mating-loss contexts avoid the unused calculation; every move,
pruning condition, board update, history, search constant and NNUE stays intact.

Release8/8 and ASan/UBSan8/8 passed. Existing actual-Worker checked-evasion
regressions exercise the omitted query path. Legal-witness18,947 checks pass.
Six cold/warm1T cases and419798bench nodes exactly match6.4.5. Original logs,
commands, source/library/binary hashes are in the Linux archive and manifest.

Seven Windows Wine checks passed, including perft,TT8,rule50,18,947witness checks,
UCI,ponder and351063bench nodes. [Windows ZIP](../../releases/forge-6.4.6-candidate-windows-zen5.zip)
SHA256 `4c7d9a0ae9c14922406d0846665e61dedafce1f6b73472cad11ecd7745bb9513`. Independent static package audit passed.

Retain as correctness-tested isolated performance candidate. No NPS/Elo gain is
established; zero new games. Prior shared-host and pinned calibration failures
block reliable timing, so no repeated timing/match attempts were run here.
Next: lazy MovePicker check-mask initialization, separately frozen/tested.
