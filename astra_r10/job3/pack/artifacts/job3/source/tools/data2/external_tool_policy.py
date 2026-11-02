"""Original boundary checks for optional external GPL-3.0 data tools.

IDEA_SOURCE: crew external-tool policy; Git directory/worktree metadata contracts.
Empty managed-filesystem .git placeholders are not repositories.
"""
import os
from pathlib import Path


def is_git_directory(path):
    return (path / 'HEAD').is_file() and ((path / 'objects').is_dir() or (path / 'commondir').is_file())


def repository_at(path):
    marker = path / '.git'
    if is_git_directory(path) or is_git_directory(marker):
        return True
    if marker.is_file():
        with marker.open('rb') as stream:
            return stream.read(7) == b'gitdir:'
    return False


def require_external_path(path):
    reference = Path(os.path.abspath(path))
    # Resolve the original spelling before lexical dot-dot normalization:
    # link/../tool may target a different file than abspath(link/../tool).
    resolved = Path(path).resolve()
    # Both spelling and target matter: repo-local aliases are not external
    # installs, and an external alias cannot conceal a repository target.
    for candidate in (reference, resolved):
        if any(repository_at(parent) for parent in (candidate, *candidate.parents)):
            raise ValueError('external GPL-3.0 tooling must stay outside every repository')
    return resolved
