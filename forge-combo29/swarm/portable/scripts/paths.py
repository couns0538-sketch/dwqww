"""Shared paths and input validation for the portable-build scripts.

Two things live here that the individual scripts should not each reinvent:

1. **Paths.** Every script previously hard-coded `/tmp/build`, which made them
   unusable anywhere else and made a stale `/tmp` silently feed an analysis.
   `work_dir()` reads `PORTABLE_WORK` and refuses a relative path, so the
   directory is always explicit and absolute.

2. **Validation of anything that came from argv or the environment.** These
   scripts take an engine binary, a FEN file and an output path from the command
   line. A harness is a tool for measuring a local build, not a service, but a
   path that was never checked is still a path that can point anywhere -- so the
   binary must exist and be executable, the FEN file must be a regular file of
   plausible size, and every write location is resolved inside the work dir
   rather than trusted verbatim.
"""

import os
import stat


class InputError(ValueError):
    """A path or argument the scripts will not use. Never silently ignored."""


def work_dir(create=False):
    """The measurement work directory, absolute.

    Set PORTABLE_WORK to relocate it. A relative value is refused rather than
    resolved against the cwd, because the scripts change directory nowhere and a
    relative root would depend on where they happened to be invoked from.
    """
    path = os.environ.get("PORTABLE_WORK", "/tmp/build")
    if not os.path.isabs(path):
        raise InputError(f"PORTABLE_WORK must be an absolute path, got {path!r}")
    if create:
        os.makedirs(path, exist_ok=True)
    elif not os.path.isdir(path):
        raise InputError(f"PORTABLE_WORK does not exist: {path!r}")
    return path


def engine_path(name):
    """The built engine binary for a variant, validated.

    Rejects a directory, a missing file, and anything not executable, with a
    message that says which build is missing -- so a typo in a variant name
    fails here instead of surfacing as an empty benchmark result.
    """
    path = os.path.join(work_dir(), name, "forge")
    if not os.path.exists(path):
        raise InputError(f"no engine binary at {path!r} -- run scripts/build_all.sh first")
    if not os.path.isfile(path):
        raise InputError(f"{path!r} is not a regular file")
    if not os.access(path, os.X_OK):
        raise InputError(f"{path!r} is not executable")
    return path


def engine_arg(value):
    """Like engine_path() but for an explicit path supplied on the command line."""
    if not value:
        raise InputError("empty engine path")
    path = os.path.realpath(value)
    if not os.path.isfile(path):
        raise InputError(f"engine {value!r} is not a regular file")
    if not os.access(path, os.X_OK):
        raise InputError(f"engine {value!r} is not executable")
    if not os.stat(path).st_mode & stat.S_IXUSR:
        raise InputError(f"engine {value!r} has no execute bit")
    return path


def fen_file(path):
    """A FEN corpus, validated: regular file, non-empty, all lines plausible.

    A FEN file that is empty or one line long would make an ABBA run return a
    confident median over nothing, which is the failure mode these scripts exist
    to avoid. So the shape is checked, not just the existence.
    """
    path = os.path.realpath(path)
    if not os.path.isfile(path):
        raise InputError(f"FEN file {path!r} is not a regular file")
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    if not lines:
        raise InputError(f"FEN file {path!r} contains no positions")
    for i, line in enumerate(lines, 1):
        # Six space-separated FEN fields; the engine's own validator is stricter,
        # but a line that is not even shaped like a FEN must not reach the engine.
        if len(line.split()) < 4:
            raise InputError(f"FEN file {path!r} line {i} is not a FEN: {line!r}")
    return path, lines


def in_path(value):
    """A path to READ, confined to the work dir.

    Bare filenames resolve inside the work dir; an absolute path must already be
    inside it. A path outside is refused rather than opened, so a typo in a
    variant name cannot silently read some other file on the machine.
    """
    root = os.path.realpath(work_dir())
    if os.path.isabs(value):
        path = os.path.realpath(value)
    else:
        path = os.path.realpath(os.path.join(root, value))
    if os.path.commonpath([root, path]) != root:
        raise InputError(f"input path {value!r} is outside the work dir {root!r}")
    return path


def out_path(value):
    """An output location, resolved and confined to the work dir.

    A bare filename resolves inside the work dir; an absolute path must already be
    inside it. Either way the parent directory must exist, because a write that
    silently creates a missing tree is how outputs end up somewhere unintended.
    """
    path = in_path(value)
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        raise InputError(f"output directory does not exist: {parent!r}")
    return path


def script_dir():
    """The directory holding these scripts, so sibling imports work."""
    return os.path.dirname(os.path.realpath(__file__))
