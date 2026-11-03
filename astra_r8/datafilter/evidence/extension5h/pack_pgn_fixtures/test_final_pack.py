"""Authored proof graphs for final packaging; no real evidence is mutated."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

DRIVER=Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter/evidence/extension5h/pack_final.py')
spec=importlib.util.spec_from_file_location('final_pack_fixture',DRIVER)
pack=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf-8')


@pytest.fixture
def case(tmp_path,monkeypatch):
    root=tmp_path/'owned';core=root/'core';suite=root/'suite';validation=root/'validation'
    handoff=root/'handoff';v7=root/'historical';output=root/'pack'
    core.mkdir(parents=True)
    driver=core/'evidence/extension5h/verify_input_repair.py'
    sources=[core/'records.py',core/'tests/test_one.py']
    for path in [*sources,driver,core/'evidence/conftest.py']:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# authored fixture\n',encoding='utf-8')
    pins={str(path):pack.sha256(path) for path in sources}
    installed=root/'installed.py';installed.write_text('# pinned runtime\n',encoding='utf-8')
    runtime={'python':'fixture','torch':'fixture','files':{str(installed):pack.sha256(installed)}}
    put(handoff/'manifest.json',{'runtime':runtime})
    put(v7/'manifest.json',{'historical':True})
    protected={'manifest.json':pack.sha256(v7/'manifest.json')}
    suite.mkdir()
    log=suite/'pytest.log';log.write_text('544 passed, 15 warnings, 11 subtests passed in 1.00s\n',encoding='utf-8')
    put(suite/'exit.json',{'exit_code':0,'source_stable':True,'log_sha256':pack.sha256(log)})
    for name in ['source_before.json','source_after.json']:put(suite/name,pins)
    put(suite/'command.json',{'arguments':['-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp=authored','astra_r8/datafilter']})
    put(suite/'cpu_runtime_fixture.json',{'before':runtime,'after':runtime})
    receipts={}
    for name in ['shared_selfplay_source.json','native_admission.json','bounded_filter.json','published_verify.json']:
        path=validation/name;put(path,{'status':'PASS','fixture':True})
        receipts[name]={'path':str(path),'sha256':pack.sha256(path)}
    stages={}
    for name in ['identity','orientation']:
        path=validation/(name+'_receipt.json');put(path,{'status':'PASS','fixture':True})
        stages[name]={'receipt':str(path),'sha256':pack.sha256(path),'seconds':0.1}
    complete={'status':'PASS','source_files':{**pins,str(driver):pack.sha256(driver)},
              'receipts':receipts,'stages':stages,'runtime':runtime,
              'manifest_sha256':pack.sha256(handoff/'manifest.json'),'protected_v7':protected}
    put(validation/'COMPLETE.json',complete)
    helper=root/'inventory_helper.py';helper.write_bytes(pack.HELPER.read_bytes())
    monkeypatch.setattr(pack,'HERE',core)
    monkeypatch.setattr(pack,'WORK',root)
    monkeypatch.setattr(pack,'V7',v7)
    monkeypatch.setattr(pack,'V7_SHA',protected['manifest.json'])
    monkeypatch.setattr(pack,'HELPER',helper)
    monkeypatch.setattr(pack,'BUDGET_ROOTS',(root,))
    monkeypatch.setattr(pack,'low_priority',lambda:None)
    monkeypatch.setattr(pack,'storage_guard',lambda path,**kw:{'destination':str(path),'fixture':True})
    monkeypatch.setattr(pack,'verify',lambda path:{'status':'PASS','manifest_sha256':pack.sha256(path)})
    monkeypatch.setattr(pack.subprocess,'check_output',lambda *a,**kw:'1'*40)
    monkeypatch.setattr(sys,'argv',['pack_final.py','--output',str(output),'--suite',str(suite),
                                  '--validation',str(validation),'--handoff',str(handoff)])
    return SimpleNamespace(root=root,core=core,suite=suite,validation=validation,
                           handoff=handoff,v7=v7,output=output,complete=complete,installed=installed,helper=helper)


def test_healthy_complete_fixture_packages(case):
    pack.main()
    assert json.loads((case.output/'COMPLETE.json').read_text())['status']=='PASS'


@pytest.mark.parametrize('field',['source_files','receipts','stages'])
def test_incomplete_validation_is_rejected(case,field):
    put(case.validation/'COMPLETE.json',{**case.complete,field:{}})
    with pytest.raises(ValueError):pack.main()
    assert not (case.output/'COMPLETE.json').exists()


def test_empty_suite_sources_are_rejected(case):
    for name in ['source_before.json','source_after.json']:put(case.suite/name,{})
    with pytest.raises(ValueError):pack.main()
    assert not (case.output/'COMPLETE.json').exists()


def test_empty_tested_runtime_is_rejected(case):
    put(case.suite/'cpu_runtime_fixture.json',{'before':{'files':{}},'after':{'files':{}}})
    with pytest.raises(ValueError):pack.main()
    assert not (case.output/'COMPLETE.json').exists()


@pytest.mark.parametrize('kind',['receipt','stage'])
def test_required_evidence_cannot_alias_another_proof(case,kind):
    complete=case.complete
    if kind=='receipt':
        complete['receipts']['native_admission.json']=complete['receipts']['shared_selfplay_source.json']
        (case.validation/'native_admission.json').unlink()
    else:
        complete['stages']['orientation']=complete['stages']['identity']
        (case.validation/'orientation_receipt.json').unlink()
    put(case.validation/'COMPLETE.json',complete)
    with pytest.raises(ValueError):pack.main()
    assert not (case.output/'COMPLETE.json').exists()


@pytest.mark.parametrize('which',['log','receipt','stage','runtime','manifest','v7','v7_extra','helper'])
def test_linked_evidence_change_before_inventory_is_rejected(case,monkeypatch,which):
    targets={'log':case.suite/'pytest.log','receipt':case.validation/'native_admission.json',
             'stage':case.validation/'identity_receipt.json','runtime':case.installed,
             'manifest':case.handoff/'manifest.json','v7':case.v7/'manifest.json',
             'v7_extra':case.v7/'unapproved.json','helper':case.helper}
    original=pack.input_identity
    state={'changed':False}
    def changed(path):
        if not state['changed']:
            state['changed']=True
            target=targets[which]
            target.write_bytes(target.read_bytes()+b' ' if target.exists() else b'{}')
        return original(path)
    monkeypatch.setattr(pack,'input_identity',changed)
    with pytest.raises(ValueError):pack.main()
    assert not (case.output/'COMPLETE.json').exists()
