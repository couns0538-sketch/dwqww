"""The one place this seat touches python-chess's private repetition key.

`python-chess` exposes no public way to get the key its repetition logic compares, so counting
occurrences of a position means calling `Board._transposition_key()`. That is a private API and a
real fragility: if the library changes, every site that calls it breaks silently or loudly in
several places at once.

Two things make it acceptable and are stated rather than hidden:
  1. It is confined to this function, so there is exactly one call site to fix.
  2. `_transposition_key` is what the library's OWN `is_repetition()`/`can_claim_threefold()`
     use, so using anything else would be measuring a different relation than the one a
     reference library would report. A public alternative that returned something different
     would be worse, not better.

The value is used ONLY as a dictionary key for counting occurrences. No bit-level meaning is
attached to it, so a change to the hash itself changes nothing here as long as it stays a
function of the position.
"""


def repetition_key(board):
    """An opaque, hashable key that is equal for positions the library calls identical.

    Counting equal keys over a move list gives the occurrence count of each position, which is
    the quantity the drawn-root bail keys on. See the module docstring for why this reaches into
    a private attribute.
    """
    return board._transposition_key()  # noqa: SLF001  (documented above; single call site)
