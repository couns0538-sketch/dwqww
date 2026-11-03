"""Runtime evidence must be complete and tied to the approved installed runtime."""
import json
import os
from pathlib import Path

import pytest

import verify_handoff as v
from test_handoff_adversarial import fixture


@pytest.mark.parametrize('damage', ['empty_files','missing_file','missing_python',
                                  'changed_python','changed_torch','extra_file',
                                  'substitute_path','rehash_changed_installed',
                                  'duplicate_resolved_path'])
def test_runtime_omission_or_replacement_cannot_pass(tmp_path,monkeypatch,damage):
    path,manifest,_=fixture(tmp_path,monkeypatch)
    runtime=manifest['runtime']
    native=tmp_path/'native.dll'
    if damage=='empty_files':runtime['files']={}
    elif damage=='missing_file':runtime['files'].pop(str(native))
    elif damage=='missing_python':runtime.pop('python')
    elif damage=='changed_python':runtime['python']='different-python'
    elif damage=='changed_torch':runtime['torch']='different-torch'
    elif damage in ('extra_file','substitute_path'):
        extra=tmp_path/'different.dll';extra.write_bytes(native.read_bytes())
        runtime['files'][str(extra)]=v.sha256(extra)
        if damage=='substitute_path':runtime['files'].pop(str(native))
    elif damage=='rehash_changed_installed':
        native.write_bytes(b'changed owned runtime fixture\n')
        runtime['files'][str(native)]=v.sha256(native)
    else:
        alias=str(native.parent)+os.sep+'.'+os.sep+native.name
        runtime['files'][alias]=runtime['files'][str(native)]
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='runtime'):
        v.verify(path)


def test_current_reviewed_local_file_still_needs_its_actual_hash(tmp_path,monkeypatch):
    _,manifest,_=fixture(tmp_path,monkeypatch)
    runtime=manifest['runtime']
    local=tmp_path/'wrapper.py'
    monkeypatch.setattr(v,'REVIEWABLE_RUNTIME',{str(local.resolve())})
    local.write_bytes(b'# reviewed local admission change\n')
    with pytest.raises(ValueError,match='runtime hash'):
        v.verify_runtime(runtime,set())
    runtime['files'][str(local)]=v.sha256(local)
    v.verify_runtime(runtime,set())


def test_original_contract_bytes_are_pinned_before_parsing(tmp_path,monkeypatch):
    path=tmp_path/'approved.json'
    path.write_text(json.dumps({'runtime':{'python':'fixture','torch':'fixture','files':{}}}))
    monkeypatch.setattr(v,'APPROVED_MANIFEST',path)
    monkeypatch.setattr(v,'APPROVED_PREVIOUS_SHA256',v.sha256(path))
    assert v.approved_runtime()['python']=='fixture'
    path.write_text('{"runtime":{"python":"changed"}}')
    with pytest.raises(ValueError,match='contract manifest changed'):
        v.approved_runtime()
