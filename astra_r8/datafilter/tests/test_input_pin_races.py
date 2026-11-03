"""Only authored temporary inputs are mutated by these pinning regressions."""
import builtins
from copy import deepcopy
import inspect
import json
import os
from pathlib import Path
from types import SimpleNamespace

import chess
import pytest

import filter_positions as filters
import npt_adapter as adapter
from records import dumps, record


def payload(score=20):
    return dumps(record(chess.STARTING_FEN,score,'cp',1,'fixture',1,'selfplay'))+'\n'


def source(tmp_path):
    path=tmp_path/'records.jsonl'
    path.write_text(payload(),encoding='utf-8')
    return path,filters.sha256(path)


def test_change_after_successful_hash_cannot_become_index_baseline(tmp_path,monkeypatch):
    path,expected=source(tmp_path)
    original=filters.sha256
    changed=False
    def mutate_after_hash(supplied):
        nonlocal changed
        result=original(supplied)
        if Path(supplied)==path and not changed:
            changed=True
            path.write_text(payload(30),encoding='utf-8')
        return result
    monkeypatch.setattr(filters,'sha256',mutate_after_hash)
    monkeypatch.setattr(adapter,'sha256',mutate_after_hash)
    with pytest.raises(ValueError,match='chang|mismatch'):
        adapter.RowFile(path,expected)
    assert changed


def test_index_handle_must_be_the_hashed_file_even_if_path_is_stable(tmp_path,monkeypatch):
    path,expected=source(tmp_path)
    alternate=tmp_path/'alternate.jsonl'
    alternate.write_text(payload()+payload(30),encoding='utf-8')
    def redirected(supplied,*args,**kwargs):
        return builtins.open(alternate if Path(supplied)==path else supplied,*args,**kwargs)
    monkeypatch.setattr(adapter,'open',redirected,raising=False)
    with pytest.raises(ValueError,match='identity|chang|mismatch'):
        adapter.RowFile(path,expected)
    assert filters.sha256(path)==expected


def test_fetch_handle_redirection_cannot_return_rows_from_another_file(tmp_path,monkeypatch):
    path,expected=source(tmp_path)
    pinned=adapter.RowFile(path,expected)
    alternate=tmp_path/'alternate.jsonl'
    alternate.write_text(payload(30),encoding='utf-8')
    monkeypatch.setattr(adapter,'open',lambda supplied,*args,**kwargs:
                        builtins.open(alternate,*args,**kwargs),raising=False)
    with pytest.raises(ValueError,match='identity|chang|mismatch'):
        pinned.fetch([0])


def test_in_place_change_during_fetch_never_returns_a_batch(tmp_path,monkeypatch):
    path,expected=source(tmp_path)
    pinned=adapter.RowFile(path,expected)
    original=adapter.validate_record
    def mutate_after_parse(row):
        result=original(row)
        path.write_text(payload(30),encoding='utf-8')
        return result
    monkeypatch.setattr(adapter,'validate_record',mutate_after_parse)
    with pytest.raises(ValueError,match='chang|identity'):
        pinned.fetch([0])


@pytest.mark.skipif(os.name != 'nt', reason='Windows path/handle ctime semantics')
def test_windows_handle_change_time_is_not_compared_as_path_creation_time(tmp_path,monkeypatch):
    path,expected=source(tmp_path)
    original=adapter.os.fstat
    def handle_stat(descriptor):
        observed=original(descriptor)
        fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
        values={field:getattr(observed,field) for field in fields}
        values['st_ctime_ns']=path.stat().st_ctime_ns+1
        return SimpleNamespace(**values)
    monkeypatch.setattr(adapter.os,'fstat',handle_stat)
    pinned=adapter.RowFile(path,expected)
    assert pinned.fetch([0])[0]['score_stm']==20


def context_manifest(tmp_path):
    train=tmp_path/'train.jsonl';train.write_text(payload(),encoding='utf-8')
    validation=tmp_path/'validation.jsonl';validation.write_text(payload(),encoding='utf-8')
    manifest=tmp_path/'manifest.json'
    value={'train':{'path':str(train),'sha256':filters.sha256(train)},
           'validation':{'path':str(validation),'sha256':filters.sha256(validation)}}
    manifest.write_text(json.dumps(value),encoding='utf-8')
    return manifest,value,filters.input_identity(manifest)


def context_with_pin(train,manifest,pin):
    # Also exercise the original constructor during the RED run: a missing new
    # keyword must not hide the real unverified-path behavior behind TypeError.
    options={'expected_identity':pin} if 'expected_identity' in inspect.signature(train.Context).parameters else {}
    return train.Context(manifest,'filtered_wdl_v1',**options)


def test_manifest_bytes_must_match_verified_identity_before_row_files(tmp_path,monkeypatch):
    import train_adapter as train
    manifest,value,pin=context_manifest(tmp_path)
    changed=deepcopy(value);changed['train']['path']='unverified-record-path'
    manifest.write_text(json.dumps(changed),encoding='utf-8')
    calls=[]
    def refuse(*args):
        calls.append(args)
        raise AssertionError('unverified manifest reached RowFile')
    monkeypatch.setattr(train,'RowFile',refuse)
    with pytest.raises(ValueError,match='manifest'):
        context_with_pin(train,manifest,pin)
    assert not calls


def test_manifest_change_during_context_initialization_is_rejected(tmp_path,monkeypatch):
    import train_adapter as train
    manifest,value,pin=context_manifest(tmp_path)
    original=train.RowFile
    changed=False
    def mutate(*args,**kwargs):
        nonlocal changed
        result=original(*args,**kwargs)
        if not changed:
            changed=True
            manifest.write_text(json.dumps({**value,'changed':True}),encoding='utf-8')
        return result
    monkeypatch.setattr(train,'RowFile',mutate)
    with pytest.raises(ValueError,match='manifest'):
        context_with_pin(train,manifest,pin)


def test_valid_context_retains_exact_byte_digest_and_checks_later_mutation(tmp_path):
    import train_adapter as train
    manifest,value,pin=context_manifest(tmp_path)
    context=context_with_pin(train,manifest,pin)
    assert context.digest==pin['sha256']
    context.check_manifest_identity()
    manifest.write_text(json.dumps({**value,'changed':True}),encoding='utf-8')
    with pytest.raises(ValueError,match='manifest'):
        context.check_manifest_identity()
