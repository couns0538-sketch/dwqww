# Idea source - TtReplaceCache

- **Brief:** the owner's 5-hour brief, 2026-11-06, job 3 ("ST-TtReplaceCache").
  - The idea is a micro speed change from a public engine pull request: SF #7281.
  - It is used as an idea only. No source was ported, in particular not the 21-bit packed keys or the XOR-key writes.
- **The change.** Forge's TT is a key32 + 4-slot cluster. In the replace selection, the metric of the current pick
  (`depth - 4 * relative_age`) is kept in a local. It is no longer recomputed for every slot comparison.
- **Code:** own code (`tools/apply_trc.py` makes the change, anchored and fail closed).
- **Licence:** own code, same terms as the repository.
