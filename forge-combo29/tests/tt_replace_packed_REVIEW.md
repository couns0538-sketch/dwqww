# Temporary packed TT priority prototype

Production unchanged. Source-only snapshot of 2da9593, with the adjacent
prototype patch applied only under the existing candidate macro. Reproduce
with `python3 forge-combo29/tests/tt_replace_packed_validate.py`; this recreates
only the temporary snapshot. Engine flags derive from the straight-cache
receipt; sources are restricted to src/include. No bundled binary fetched.

Priority is `4*score+slot`, score=-124..255, slot=0..3, so priority=-496..1023
fits signed int. Signed minimum preserves score order, then earliest index on
ties. Converting the selected priority to unsigned and masking by3 recovers
slot even for negative values. Static assertion requires cluster size4. Full
hit scan, generation refresh, first-empty return and BoundNone holes remain.

Exhaustive UBSan oracle passes all866,400 ordered slot pairs across every score
pair in the complete domain. Pairwise order plus associativity of min covers
four occupied entries. Actual public TT tests pass in NOTLS0 and1 under TSan:
4096 replacement-oracle cases each, existing lifecycle/bounds/hole contracts,
and4threads*5000 concurrent probe/store operations. No sanitizer report.

Owned-probe GCC14 O3 assembly saves rbp/r12/rbx (straight-cache also saves r13).
Symbol size639 bytes, versus643 straight-cache and664 immutable lock. Packed
priority introduces scaling/index-decode arithmetic. Public locked probe size
688 versus677 straight-cache and723 lock. These are code-generation facts,
not evidence of faster execution. Full disassembly retained.

Temporary engine SHA256:
a106b182f785c0fa2fb6dffaf57390a9134659664f078c287309a3a9cb93509e
Temporary search.cpp SHA256:
bba5b7aa696a3f6b7dabb7b10a7ab9bbd4679b09b79d347d37a1d3cc260c1fa4

Full engine pins/equivalence, default-off identity and timing have NOT been
rerun for this prototype. The earlier mixed straight-cache ABBA results do not
transfer. Keep temporary pending broader validation; no promotion or speed/Elo
claim. Existing included-but-uncalled renamed contract main emits the already
documented return warning; actual tests invoke contract functions directly.
