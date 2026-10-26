"""Seal already completed S33/S48 evidence; no MC, engine or source mutation."""
from pathlib import Path
import base64
import datetime
import gzip
import hashlib
import json
import os
import shutil


ROOT=Path('/workspace/forge-pack24-20261026/S33')
REPO=Path('/workspace/dwqww')
DEST=REPO/'releases/forge_sol_pack31_20261025'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
    assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True)
    # Completed immutable owned artifacts share storage; no raw evidence dropped.
    os.link(src,dst)
    assert sha(src)==sha(dst)
def write(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
def seal(folder):
    rows=[]
    for p in sorted(folder.rglob('*')):
        if p.is_file():rows.append((p.relative_to(folder).as_posix(),sha(p),p.stat().st_size))
    manifest=folder/f'forge_sol_{folder.name}_SHA256SUMS_20261026.txt'
    with manifest.open('x') as f:
        for name,digest,size in rows:f.write(digest+'  '+name+'\n')
    return {'files':len(rows)+1,'manifest_sha256':sha(manifest),'bytes':sum(x[2] for x in rows)}


def main():
    s33=DEST/'S33';s48=DEST/'S48'
    assert not s33.exists() and not s48.exists()
    assert sha(ROOT/'forge_sol_S33_sprt_planner_20261026.py')=='008819d5387cdd5ac5d512bb2ebafd09f141aafc9b6904cba2f73a8373634d03'
    assert sha(ROOT/'forge_sol_S48_gate_guard_20261026.py')=='21713b327007b0cda450200e172f6affb27cd65ac10e26ed8680d9447669d855'
    audit=json.loads((ROOT/'forge_sol_S33_full_grid_independent_audit_20261026.json').read_text())
    # The original audit schema is preserved verbatim; its status is inspected,
    # not guessed from filenames or substituted by a success sentinel.
    assert str(audit.get('status','')).startswith('PASS')
    for shard in (0,1):
        r=json.loads((ROOT/f'forge_sol_S33_full_grid_20261026/shard{shard}/forge_sol_S33_shard_{shard}_completion_20261026.json').read_text())
        assert r['status']=='PASS' and r['cells']==315 and r['sources_unchanged']
    s33.mkdir();s48.mkdir()
    common=['forge_sol_S33_sprt_planner_20261026.py','forge_sol_S48_gate_guard_20261026.py']
    s06=REPO/'releases/forge_sol_pack31_20261025/S06/forge_sol_S06_statistics_20261026.py'
    assert sha(s06)=='4598c5839519af2ed4680b074669d097b9616dfe7c03c1afb7622b276efecb8a'
    for folder in (s33,s48):
        for name in common:copy(ROOT/name,folder/name)
        copy(s06,folder/s06.name)
    for name in ['forge_sol_S33_README_20261026.md','forge_sol_S33_report_20261026.md',
                 'forge_sol_S33_advice_net_20261026.md','forge_sol_S33_advice_search_20261026.md',
                 'forge_sol_S33_advice_speed_20261026.md','forge_sol_S33_model_and_API_20261026.md',
                 'forge_sol_S33_grid_driver_20261026.py','forge_sol_S33_merge_grid_20261026.py',
                 'forge_sol_S33_S48_delivery_builder_20261026.py',
                 'forge_sol_S33_six_cell_validation_20261026.json','forge_sol_S33_math_review_20261026.json',
                 'forge_sol_S33_numerical_ast_equivalence_20261026.json',
                 'forge_sol_S33_prove_numerical_ast_equivalence_20261026.py',
                 'forge_sol_S33_frozen_protocol_20261026.json',
                 'forge_sol_S33_full_grid_independent_audit_20261026.json']:
        copy(ROOT/name,s33/name)
    copy(ROOT/'tests/test_forge_sol_S33_sprt_planner_20261026.py',s33/'tests/test_forge_sol_S33_sprt_planner_20261026.py')
    for p in sorted((ROOT/'forge_sol_S33_full_grid_20261026').rglob('*')):
        if p.is_file():copy(p,s33/'grid'/p.relative_to(ROOT/'forge_sol_S33_full_grid_20261026'))
    for p in sorted((ROOT/'forge_sol_S33_merged_grid_20261026').iterdir()):
        if p.is_file():copy(p,s33/p.name)
    # Small reversible support bundle keeps every original negative attempt,
    # source control and six-cell raw array file without a generic ZIP delivery.
    support=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.py','.json','.log','.txt','.md','.npz')]
    support += [p for p in (ROOT/'tests').iterdir() if p.is_file()]
    archive=s33/'forge_sol_S33_support_evidence_20261026.jsonl.gz';index=[]
    with archive.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as z:
            for p in sorted(support):
                data=p.read_bytes();record={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':len(data)}
                index.append(record)
                z.write((json.dumps({**record,'data_b64':base64.b64encode(data).decode()},separators=(',',':'))+'\n').encode())
    with gzip.open(archive,'rt') as z:
        decoded=[json.loads(line) for line in z]
    assert len(decoded)==len(index)
    for row in decoded:
        data=base64.b64decode(row['data_b64'],validate=True)
        assert hashlib.sha256(data).hexdigest()==row['sha256'] and len(data)==row['bytes']
        assert data==(ROOT/row['path']).read_bytes()
    write(s33/'forge_sol_S33_support_index_20261026.json',{'status':'PASS','archive_sha256':sha(archive),'files':index,
         'scope':'Original local support bytes; no new matches. Full-grid raw terminal files separately retained under grid/.'})
    for name in ['forge_sol_S48_README_20261026.md','forge_sol_S48_report_20261026.md',
                 'test_forge_sol_S48_gate_guard_20261026.py','forge_sol_S48_final_review_20261026.json']:
        copy(ROOT/name,s48/name)
    copy(ROOT/'forge_sol_S33_merged_grid_20261026/forge_sol_S48_bias_and_comparability_20261026.json',
         s48/'forge_sol_S48_bias_and_comparability_20261026.json')
    # Shared-evidence binding is explicit; do not duplicate seventy MB of data.
    write(s48/'forge_sol_S48_shared_evidence_20261026.json',{
         'schema':'forge_sol_S48_shared_evidence_v1','source_grid_job':'../S33/grid',
         'original_full_grid_audit_sha256':sha(s33/'forge_sol_S33_full_grid_independent_audit_20261026.json'),
         'bias_summary_sha256':sha(s48/'forge_sol_S48_bias_and_comparability_20261026.json'),
         'source_S33_sha256':sha(s33/'forge_sol_S33_sprt_planner_20261026.py'),
         'source_S48_sha256':sha(s48/'forge_sol_S48_gate_guard_20261026.py'),
         'limits':'G104/G120 actual profiles and conc8 absent. MC-only uncertainty not corrected observation CI. No engine gain.'})
    result={'status':'SEALED_FOR_REVIEW_NOT_PUBLICATION_CLAIM','S33':seal(s33),'S48':seal(s48),
            'model_source_unchanged':True,'original_terminal_files':90,'new_engine_games':0}
    write(ROOT/'forge_sol_S33_S48_delivery_seal_20261026.json',result)
    print(json.dumps(result))


if __name__=='__main__':main()
