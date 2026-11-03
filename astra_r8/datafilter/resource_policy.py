"""R13 allocation policy: owned D:/a13 output, 50 GiB minimum free.

Historical roots are not enumerated. This check is not a filesystem quota;
the parent launcher monitors free space and owns the bounded process tree.
"""
import os
from pathlib import Path
import shutil
import stat

ARTIFACT_ROOT = Path('D:/a13')
BUDGET_ROOTS = (ARTIFACT_ROOT,)
MINIMUM_FREE_BYTES = 50 * 1024**3
MAX_ARTIFACT_BYTES = 15 * 10**9
DEFAULT_ALLOWANCE = 64 * 1024 * 1024


def check_output_path(destination):
    """Resolve a new write destination without permitting root/junction escape."""
    authorized = ARTIFACT_ROOT.absolute()
    resolved_root = ARTIFACT_ROOT.resolve()
    if resolved_root != authorized:
        raise ValueError('authorized artifact root must not be redirected')
    destination = Path(destination).resolve()
    if not destination.is_relative_to(resolved_root):
        raise ValueError(f'output must stay under {ARTIFACT_ROOT}')
    return destination


def _is_redirect(st):
    return stat.S_ISLNK(st.st_mode) or bool(
        getattr(st, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def tree_bytes(root):
    """Count payload lengths without following aliases or escaping a budget root."""
    root = Path(root)
    if not os.path.lexists(root):
        return 0
    info = root.lstat()
    if _is_redirect(info) or root.resolve() != root.absolute():
        raise ValueError(f'artifact budget root is redirected: {root}')
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError(f'artifact budget root is not a directory: {root}')
    total = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                info = entry.stat(follow_symlinks=False)
                if _is_redirect(info):
                    # Pytest creates `current` aliases. Their genuine targets are
                    # counted by ordinary traversal; following links would count
                    # twice or loop. External and dangling links fail closed.
                    target = Path(entry.path).resolve(strict=True)
                    if not target.is_relative_to(root.resolve()):
                        raise ValueError(f'artifact budget contains an external redirected entry: {entry.path}')
                    total += getattr(info, 'st_size', 0)
                    continue
                if stat.S_ISDIR(info.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    total += info.st_size
                else:
                    raise ValueError(f'artifact budget contains a nonregular entry: {entry.path}')
    return total


def storage_guard(root=None, allowance=DEFAULT_ALLOWANCE):
    """Check the actual destination, fresh reserves and aggregate retained bytes.

    ``allowance`` is a conservative bound on the next allocation, not the entire
    run. Call before every bounded write batch and before final publication.
    Other drives and historical evidence are read-only and never inventoried.
    """
    if type(allowance) is not int or allowance < 0:
        raise ValueError('allocation allowance must be a nonnegative integer')
    destination = check_output_path(ARTIFACT_ROOT if root is None else root)
    free = {}
    for drive, reserve in (('D:/', MINIMUM_FREE_BYTES),):
        free[drive] = shutil.disk_usage(drive).free
        needed = reserve + allowance
        if free[drive] < needed:
            raise OSError(f'{drive} below 50 GiB reserve plus planned allocation')
    retained = sum(tree_bytes(path) for path in BUDGET_ROOTS)
    if retained + allowance > MAX_ARTIFACT_BYTES:
        raise OSError('15 GB aggregate artifact cap exceeded')
    return {'destination': str(destination), 'free_bytes': free,
            'retained_bytes': retained, 'next_allocation_bytes': allowance}
