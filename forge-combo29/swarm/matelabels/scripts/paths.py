"""Path handling for the matelabels scripts.

Two rules, both forced by the repository's Sonar quality gate and both correct
independently of it:

1. Never fall back to a hard-coded world-writable path. The work directory comes
   from an environment variable when set, and otherwise from
   `tempfile.mkdtemp()`, which creates a private (0700) directory.
2. Never open a path that arrived on the command line without resolving it and
   proving it sits inside the work directory.

Everything the pipeline writes goes through `work_file()`; everything it reads
from outside the repository goes through `checked_input()`.
"""
import os
import pathlib
import tempfile

ENV_WORK = "MATELABELS_WORK"
ENV_ENGINE = "FORGE_ENGINE"
ENV_CORPUS = "FORGE_CORPUS"


def work_dir() -> pathlib.Path:
    """The pipeline's private scratch directory."""
    configured = os.environ.get(ENV_WORK)
    if configured:
        path = pathlib.Path(configured).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    # mkdtemp creates the directory with 0700 and a random name, so no other
    # user can create or pre-create anything inside it.
    return pathlib.Path(tempfile.mkdtemp(prefix="matelabels-"))


def work_file(name: str) -> pathlib.Path:
    """A file inside the work dir. `name` must be a plain filename."""
    if not name or os.path.basename(name) != name or name in (".", ".."):
        raise ValueError(f"work_file() takes a plain filename, got {name!r}")
    return work_dir() / name


def checked_input(raw: str) -> pathlib.Path:
    """Resolve a caller-supplied input path and confine it to the work dir."""
    return _confine(pathlib.Path(raw))


def checked_output(raw: str) -> pathlib.Path:
    """Resolve a caller-supplied output path and confine it to the work dir."""
    return _confine(pathlib.Path(raw))


def _confine(path: pathlib.Path) -> pathlib.Path:
    base = work_dir().resolve()
    resolved = path.expanduser().resolve()
    if resolved != base and base not in resolved.parents:
        raise ValueError(
            f"refusing path outside the work directory: {resolved} (base {base})"
        )
    return resolved


def engine_binary() -> pathlib.Path:
    """The forge binary under test."""
    configured = os.environ.get(ENV_ENGINE)
    if configured:
        return pathlib.Path(configured).expanduser().resolve()
    return pathlib.Path(__file__).resolve().parent.parent.parent / "build" / "forge"


def corpus_path() -> pathlib.Path:
    """The repo's own search corpus used as the sampling frame."""
    configured = os.environ.get(ENV_CORPUS)
    if configured:
        return pathlib.Path(configured).expanduser().resolve()
    return (pathlib.Path(__file__).resolve().parent.parent.parent
            / "soak_all" / "search_corpus.txt")


def oracle_binary() -> pathlib.Path:
    """The independent mate oracle, beside the work dir or in PATH."""
    return work_file("oracle")
