"""PGN proof must close all inherited dependencies; authored small graphs only."""
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_final_pack import case,pack,put

@pytest.fixture
def pgn(case,monkeypatch):
    base=copy.deepcopy(case.complete)
    base_path=case.root/'input_repair_validation/COMPLETE.json';put(base_path,base)
    base_sha=pack.sha256(base_path)
    monkeypatch.setattr(pack,'PGN_BASE_SHA',base_sha)
    driver=case.core/'evidence/extension5h/verify_pgn_repair.py';driver.write_text('# authored fixture\n')
    snapshot=case.root/'pgn_raw_fen_review/records_before.py.txt';snapshot.parent.mkdir();snapshot.write_bytes((case.core/'records.py').read_bytes())
    old_manifest=case.root/'handoff_v8/manifest.json';old_manifest.parent.mkdir();old_manifest.write_bytes((case.handoff/'manifest.json').read_bytes())
    inherited={name:dict(path=item.get('path',item.get('receipt')),sha256=item['sha256']) for name,item in {**base['receipts'],**base['stages']}.items()}
    lineage=case.validation/'source_lineage.json'
    put(lineage,dict(status='PASS',base_proof_sha256=base_sha,before_records_sha256=pack.sha256(snapshot),current_records_sha256=pack.sha256(case.core/'records.py'),inherited_receipts=inherited))
    complete=copy.deepcopy(base);complete.pop('stages')
    complete['receipts']={name:dict(path=str(case.validation/name),sha256=pack.sha256(case.validation/name)) for name in ('source_lineage.json','native_admission.json','published_verify.json')}
    complete['base_proof_sha256']=base_sha;complete['driver_sha256']=pack.sha256(driver)
    mandatory={**complete['source_files'],str(driver):pack.sha256(driver),str(snapshot):pack.sha256(snapshot),str(base_path):base_sha,str(old_manifest):pack.sha256(old_manifest),str(case.handoff/'manifest.json'):pack.sha256(case.handoff/'manifest.json')}
    mandatory.update({item['path']:item['sha256'] for item in inherited.values()})
    complete['bound_inputs']=mandatory
    put(case.validation/'COMPLETE.json',complete)
    log=case.suite/'pytest.log';log.write_text('564 passed, 15 warnings, 11 subtests passed in 1.00s\n')
    put(case.suite/'exit.json',dict(exit_code=0,source_stable=True,log_sha256=pack.sha256(log)))
    monkeypatch.setattr(pack,'check_collection',lambda *args:564)
    monkeypatch.setattr(sys,'argv',['pack_final.py','--output',str(case.output),'--suite',str(case.suite),'--validation',str(case.validation),'--handoff',str(case.handoff),'--validation-mode','pgn','--collection',str(case.root/'collection.json')])
    return SimpleNamespace(case=case,complete=complete,snapshot=snapshot,inherited=inherited)

def test_complete_pgn_graph_passes(pgn):
    pack.main()
    assert json.loads((pgn.case.output/'COMPLETE.json').read_text())['status']=='PASS'

@pytest.mark.parametrize('damage',['empty','missing_snapshot','missing_identity','conflicting_identity'])
def test_pgn_inherited_dependencies_cannot_be_omitted(pgn,damage):
    complete=pgn.complete
    identity=pgn.inherited['identity']['path']
    if damage=='empty':complete['bound_inputs']={}
    elif damage=='missing_snapshot':complete['bound_inputs'].pop(str(pgn.snapshot))
    elif damage=='missing_identity':complete['bound_inputs'].pop(identity)
    elif damage=='conflicting_identity':complete['bound_inputs'][identity]='0'*64
    put(pgn.case.validation/'COMPLETE.json',complete)
    with pytest.raises(ValueError):pack.main()
    assert not (pgn.case.output/'COMPLETE.json').exists()