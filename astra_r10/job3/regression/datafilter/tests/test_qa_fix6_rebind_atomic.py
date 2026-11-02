"""QA fix 6 (CR LOW-B): a failed rebind must not leave a new manifest (or a .partial) on disk."""
import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def old_manifest(tmp_path):
    p = tmp_path / 'old.json'
    p.write_text(json.dumps(dict(strength='UNPROVEN', hyperparameters={})), encoding='utf-8')
    return p

def test_failed_verify_leaves_nothing(tmp_path, monkeypatch):
    import rebind_manifest as R
    def boom(path):
        assert Path(path).name == 'new.json.partial'
        raise KeyError('train')
    monkeypatch.setattr(R, 'verify', boom)
    new = tmp_path / 'new.json'
    with pytest.raises(KeyError):
        R.rebind(old_manifest(tmp_path), new)
    assert not new.exists() and not (tmp_path / 'new.json.partial').exists()

def test_pass_publishes_verified_bytes(tmp_path, monkeypatch):
    import rebind_manifest as R
    seen = {}
    def ok(path):
        seen['bytes'] = Path(path).read_bytes()
        return dict(status='PASS', manifest_sha256='of-partial')
    monkeypatch.setattr(R, 'verify', ok)
    new = tmp_path / 'new.json'
    res = R.rebind(old_manifest(tmp_path), new)
    assert new.read_bytes() == seen['bytes'] and not (tmp_path / 'new.json.partial').exists()
    assert res['status'] == 'PASS' and res['manifest_sha256'] == R.sha256(new)
    assert json.loads(new.read_text())['derived_from']['path'].endswith('old.json')

def test_existing_new_or_partial_refused(tmp_path, monkeypatch):
    import rebind_manifest as R
    monkeypatch.setattr(R, 'verify', lambda p: dict(status='PASS'))
    old = old_manifest(tmp_path)
    (tmp_path / 'a.json').write_text('keep')
    with pytest.raises(FileExistsError):
        R.rebind(old, tmp_path / 'a.json')
    assert (tmp_path / 'a.json').read_text() == 'keep'
    (tmp_path / 'b.json.partial').write_text('stale')
    with pytest.raises(FileExistsError):
        R.rebind(old, tmp_path / 'b.json')
    assert not (tmp_path / 'b.json').exists() and (tmp_path / 'b.json.partial').read_text() == 'stale'
