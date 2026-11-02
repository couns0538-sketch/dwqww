"""Original harness adapter: record optional pytest aliases without reparse links."""
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def record_current_aliases(base):
    import _pytest.pathlib as pytest_paths
    base=Path(base).resolve()
    if not base.is_relative_to(Path('D:/a11/regression-runs')):
        raise ValueError('pytest alias guard requires owned output outside Git')
    original=pytest_paths._force_symlink
    aliases=[]
    def record(root,target,link_to):
        root=Path(root).resolve()
        destination=Path(link_to).resolve(strict=True)
        target=str(target)
        if not (root==base or root.is_relative_to(base)) or not destination.is_relative_to(base):
            raise ValueError('pytest alias intent escaped the exact owned basetemp')
        if Path(target).name != target or not target.endswith('current') or any(c in target for c in '\\/:*?'):
            raise ValueError('only optional pytest current aliases may be suppressed')
        aliases.append({'alias':str(root/target),'target':str(destination),
                        'action':'recorded_only; no symlink created'})
    pytest_paths._force_symlink=record
    try:
        yield aliases
    finally:
        pytest_paths._force_symlink=original
