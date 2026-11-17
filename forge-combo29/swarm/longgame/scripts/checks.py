"""A check that survives `python -O`.

Every guard in this seat exists to stop a measurement from being recorded when its own
precondition failed -- an empty fixture set, a control that cannot see the thing it controls
for, a sample that is not the size it claims. Written as `assert`, all of them vanish under
`python -O`, which turns a loud failure into a silent wrong number.

`require` raises instead, so the guard is part of the program rather than a debugging aid.
"""


def require(condition, message):
    """Raise AssertionError with `message` when `condition` is falsy.

    Deliberately not `assert`: this must still run under `python -O`.
    """
    if not condition:
        raise AssertionError(message)
