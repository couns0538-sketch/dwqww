# T04G-01: Null-search cutoffs fill only the second killer slot
Status: COMPLETE

## Source
Altair PR 105 "Null search no killers" (https://github.com/Alex2262/AltairChessEngine/pull/105, merge e42311036d,
2023-07-17, test https://chess.swehosting.se/test/2639/); the rule is still in Altair@b2447b825b `src/search.cpp:584`
(null-search flag) and `:1128-1136` (killer update). Call-site grep at b2447b825b: the flag is set in the null-move
child, the null-move verification re-search and the singular verification search (`:733`, `:743`, `:931`). Those
three call sites were confirmed at HEAD only; at the PR's commit only the patch (killer update) was read.

## Licence
MIT at b2447b825b and at every Altair commit (LICENSE touched once, 7f28fb4127; notes/T04G/licences.md): copy with
notice. Nothing copied; mechanism in own words.

## Mechanism
A quiet move that cuts off in a node reached by a null move refutes "passing": it is usually a threat. Such a move is
a weaker killer for the real sibling positions than the killer earned in a real node. Rule: in a null-search node, a
quiet cutoff goes into killer slot 2 and leaves slot 1 alone; only when slot 1 is empty does it take slot 1. Nothing
else changes (history updates as before). With two killers both tried before the other quiets, the effect is the
order of the threat move versus the old first killer, plus which of the two survives the next eviction.

## Forge fit
LACKS. `bash tools/forge_has.sh 'killers\['`: the lock shifts slot 1 into slot 2 on every quiet cutoff
(`src/search.cpp:733-736` in `update_quiet_stats`), with no null-search test. Lock frames: the null-move child writes
`(ss+1)->killers` (null move made at `:972-979`), the frame its real siblings read next (only grandchildren are
cleared at entry, `:907`); the singular search (`:1095`) and the null-move verification (`:990`) run on the SAME
frame `ss`, so their cutoffs overwrite the killers the next sibling of this node copies (`:335`). All three are
detectable inside `update_quiet_stats` without new state: parent move none and ply > 0 (null child, see `:966`),
`ss->excluded_move` set (singular), `!ss->null_move_allowed` (verification, `:989`). Counter moves are not touched
in a null child already (`:738` needs a real previous move).

## Expected gain
Altair PR 105: +4.07 +- 3.28 Elo (95 %), 8+0.08, Threads=1, Hash 32 MB, SPRT [0,5] (-2.94, 2.94), LLR 2.95,
n=22,696 (W 6,120 L 5,854 D 10,722); book not stated; no LTC. Mid-2023 Altair (weaker, hand-crafted era), so the
error bar spans roughly +0.8 to +7.4 and transfer is uncertain.
Forge estimate: 0 to +3 Elo **UNPROVEN**.

## Effort
Crew ~1.5 h (6 lines + option, OFF pins, ON-live bench, pin_check, smoke). CPU: one STC SPRT [0,5] ~6.6k games
~13-15 h at 430-502 games/h; LTC only if STC passes. No GPU.

## Test plan
Pre-gate: OFF bench / perft pins equal to the lock FD3A5190; ON bench nodes differ (live); planted-bug check (swap the
slot) changes ON nodes; T1 smoke. Gate: UHO SPRT [0,5] at STC (Threads=1), then LTC; bit 2 (singular + verification
contexts) as a second line only after bit 1 is decided.

## OFF-by-default design
UCI option `KillerNullSlot2` (bits, default 0, range 0-3): bit 1 = null-move child, bit 2 = singular and null-move
verification searches. Own start value 1. At 0 the branch is never taken, so the killer update, the tree and the bench
pins are the lock's.
