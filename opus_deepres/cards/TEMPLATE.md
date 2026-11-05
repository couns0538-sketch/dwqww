# T<nn>-<id>: <short title>
Status: COMPLETE | PARTIAL (every unfinished field says PENDING)

## Source
Repo(s), file paths or PR / test pages, commit links (https://github.com/OWNER/REPO/commit/SHA), test-log links.

## Licence
As read at the exact commit (tools/licence_at.py), and the use it allows: "copy with notice" (MIT/BSD/Apache) or
"ideas only" (GPL / AGPL / no licence). For ideas-only sources: README / docs / commit titles / PR text / test logs
were read, never source.

## Mechanism
Own words. No pasted, translated or paraphrased code from ideas-only sources; no tuned constants carried over.

## Forge fit
Has it? `file:line` in the lock source (tools/forge_has.sh), what is there, what would change.

## Expected gain
Source's number with its conditions (Elo +- error, TC, book, games, LLR bounds, engine, link).
Forge estimate: <number or range> **UNPROVEN**.

## Effort
Crew hours (code + proofs), CPU hours (SPRT games at the gate rate), GPU hours if any.

## Test plan
Pre-gate checks (bench / perft pins OFF, identity, box tests), then the gate route: UHO SPRT [0,5] at STC, then LTC;
node-identical speed changes = nps ABBA only.

## OFF-by-default design
UCI option or build switch name, default, range, and why OFF is node-identical to the lock (the bench pins).
