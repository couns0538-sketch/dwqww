# Gates for this seat — what travels and what does not

Three structural checks guard this seat's documents: `audit_findings.py` (finding-table shape and evidence paths),
`doc_check.py` (the reference pages), `rule_check.py` (the rule catalogue's own numbering and counts).

## The hook is now tracked, and activation is one command

`githooks/pre-commit` is **version-controlled** (unlike `.git/hooks/`, which git never tracks). To activate it in any
clone:

```
git config core.hooksPath forge-combo29/swarm/23/githooks
```

## What travels with the branch, stated exactly

| link in the chain | travels with the branch? |
|---|---|
| `githooks/pre-commit` (the hook itself) | **YES — tracked** |
| `audit_findings.py`, `doc_check.py`, `rule_check.py` | **YES — tracked** |
| `install_gate.sh` (the older copy-to-.git variant) | YES — tracked, but superseded |
| `core.hooksPath` in `.git/config` | **NO — local configuration** |

So the mechanism travels and the *activation* does not. Anyone reading this clone-fresh must run the one command above;
until they do, the hook is present but not consulted, and the seat has no automatic gate. Saying "the gate runs on every
commit" without that qualifier would be the same fault as a number without the position it came from.

## Why this exists

Three times in one session an unescaped pipe inside a table cell split a row (23-F83, F122, F147). The audit caught all
three — a reader never could — but only because it was run afterwards. A check a reader cannot perform and an author can
forget is only a gate when it runs automatically, so it does now, in this checkout, having been proved to block:
a planted malformed row was reported as a 7-cell row and the commit did not land (23-F148/F149/F150).
