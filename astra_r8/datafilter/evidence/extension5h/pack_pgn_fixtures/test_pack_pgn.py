"""Collection proof regressions; mutate authored copies only."""
import copy
import json
from pathlib import Path
import pytest
from test_final_pack import pack

ORIGINAL = Path('C:/astra8_data/extension5h_20261103/collection_v3')

@pytest.fixture
def proof(tmp_path):
    for p in ORIGINAL.iterdir():
        if p.is_file():
            (tmp_path/p.name).write_bytes(p.read_bytes())
    value=json.loads((tmp_path/'COMPLETE.json').read_bytes())
    args=['-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp=authored',*value['targets']]
    return tmp_path, value, args

def test_complete_ordered_collection_is_bound(proof):
    root,value,args=proof
    bound=pack.BoundInputs()
    assert pack.check_collection(bound,root/'COMPLETE.json',value['source_files'],args)==564
    assert len(bound.files)==5
    bound.verify()

@pytest.mark.parametrize('damage',['sources','targets','missing_collection','duplicate_node','wrong_count','command','log'])
def test_narrowed_or_unbound_collection_is_rejected(proof,damage):
    root,value,args=proof
    sources=copy.deepcopy(value['source_files'])
    if damage=='sources':value['source_files']={}
    elif damage=='targets':value['targets']=value['targets'][:-1]
    elif damage=='missing_collection':value['collections']=value['collections'][:1]
    elif damage=='duplicate_node':value['collections'][0]['nodes'].append(value['collections'][0]['nodes'][0])
    elif damage=='wrong_count':value['nodes']-=1
    elif damage=='command':value['collections'][0]['command'].append('-k=one')
    elif damage=='log':(root/'broad.stdout.log').write_text('narrowed\n',encoding='utf-8')
    (root/'COMPLETE.json').write_text(json.dumps(value),encoding='utf-8')
    with pytest.raises(ValueError):
        pack.check_collection(pack.BoundInputs(),root/'COMPLETE.json',sources,args)