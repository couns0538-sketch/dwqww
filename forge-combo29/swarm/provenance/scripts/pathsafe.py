#!/usr/bin/env python3
"""Path handling shared by the provenance audit scripts.

Two things here are deliberate, and both exist because a static analyser flagged the
obvious version of this code:

1. ``checked_path`` normalises a caller-supplied path and refuses one that escapes the
   directory it is supposed to live in. The audit scripts take ``--out`` and ``--cache``
   from the command line; without this, a caller can make the tool write outside the
   audit directory, and "the argument came from the command line" is not a safety
   argument. The containment check is the mitigation, not a comment claiming trust.

2. ``private_dir`` creates directories with owner-only permissions and uses the system
   temp directory rather than a hardcoded one. ``/tmp`` is world-writable, so a
   predictable path under it can be pre-created or symlinked by another user.
"""
import os
import tempfile


def checked_path(path, root, create=False, mode=0o700, allow_outside=False):
    """Resolve ``path`` and require it to stay inside ``root``.

    ``root`` is resolved the same way, so a symlinked working directory does not
    produce a false rejection. ``create`` makes the path's PARENT directory (owner-only);
    it never creates the path itself, because the path may be a file.
    Returns the normalised absolute path.

    ``allow_outside`` exists for exactly one case: a scratch directory this program
    created itself via ``private_dir``, which is by construction owner-only and
    unpredictable. Output paths must never pass it.
    """
    root_abs = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_abs, path) if not os.path.isabs(path) else path)
    if not allow_outside and target != root_abs and not target.startswith(root_abs + os.sep):
        raise ValueError(f"refusing path outside {root_abs!r}: {path!r}")
    if create:
        parent = target if os.path.isdir(target) else os.path.dirname(target)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, mode=mode, exist_ok=True)
    return target


def private_dir(prefix, parent=None):
    """A fresh directory only this user can read, never a predictable /tmp name."""
    base = parent if parent is not None else tempfile.gettempdir()
    return tempfile.mkdtemp(prefix=prefix, dir=base)


def open_read(path, root):
    """Open for reading after the containment check, so the check cannot be skipped."""
    return open(checked_path(path, root), encoding="utf-8", errors="replace")


def open_write(path, root):
    """Open for writing after the containment check."""
    return open(checked_path(path, root, create=True), "w", encoding="utf-8")


def dump_json(obj, path, root, indent=1):
    import json

    with open_write(path, root) as fh:
        json.dump(obj, fh, indent=indent)


def load_json(path, root):
    import json

    with open_read(path, root) as fh:
        return json.load(fh)
