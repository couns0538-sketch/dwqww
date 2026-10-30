"""Read-only reconciliation of saved transport receipts, no network or credentials."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,re
root=Path(__file__).resolve().parents[3]
here=Path(__file__).resolve().parent
delivery=root/'validation/astra-a1-data/github_delivery'
transfer=delivery/'full_transfer_receipts_20261030'
release=root/'validation/astra-a1-data/release_preparation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
source=delivery/'publish_blob_assets.py'
spec=importlib.util.spec_from_file_location('publisher_read_only_review',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
manifest=read(delivery/'blob_assets.json');module.validate(manifest)
assert (delivery/'blob_assets.json').read_bytes()==(transfer/'blob_assets.json').read_bytes()
plan=read(transfer/'source_plan.json');jobs=read(transfer/'jobs.json');result=read(transfer/'transfer_result.json')
assert result['failures']==[] and result['completed']==result['total']==len(jobs)==294
assert len(plan['assets'])==len(manifest['assets'])==6
jobs_by_id={(j['asset_index'],j['chunk_index']):j for j in jobs};assert len(jobs_by_id)==len(jobs)
records=[];seen=set();summaries=[]
for asset_index,(asset,original) in enumerate(zip(manifest['assets'],plan['assets'])):
    assert {k:asset[k] for k in ('name','bytes','sha256')}=={k:original[k] for k in ('name','bytes','sha256')}
    offset=0
    for chunk_index,chunk in enumerate(asset['chunks']):
        key=(asset_index,chunk_index);job=jobs_by_id[key];seen.add(key)
        stem=f'{asset_index:02d}-{chunk_index:06d}';record=read(transfer/'chunks'/f'{stem}.json');ack=read(transfer/'chunks'/f'{stem}.stdout')
        assert all(record[k]==v for k,v in job.items())
        assert record['returncode']==0
        assert record['argv']==['gh','api','--method','POST','repos/couns0538-sketch/dwqww/git/blobs','--input','-']
        assert {k:record[k] for k in ('sha','offset','bytes','sha256')}==chunk
        assert chunk['offset']==offset and 0<chunk['bytes']<=8*1024*1024
        assert job['local_path']==original['local_path'] and job['name']==asset['name']
        assert job['source_stat'][2]==asset['bytes']
        assert re.fullmatch('[0-9a-f]{64}',record['request_sha256'])
        assert ack['sha']==chunk['sha']
        assert ack['url']=='https://api.github.com/repos/couns0538-sketch/dwqww/git/blobs/'+chunk['sha']
        assert (transfer/'chunks'/f'{stem}.stderr').is_file()
        offset+=chunk['bytes'];records.append(record)
    assert offset==asset['bytes']
    summaries.append({'name':asset['name'],'bytes':asset['bytes'],'sha256':asset['sha256'],'verified_saved_acknowledgments':len(asset['chunks'])})
assert seen==set(jobs_by_id)
assert len(list((transfer/'chunks').glob('*.json')))==len(records)
assets={a['name']:a for a in manifest['assets']}
transport=read(release/'transport_manifest.json');package=read(release/'forge_astra_a1_data_results_20261030.tar.gz.receipt.json')
assert transport['whole']==plan['reassembled_archive']
assert package['status']=='PASS'
assert package['archive_bytes']==transport['whole']['size'] and package['archive_sha256']==transport['whole']['sha256']
for part in transport['parts']:
    asset=assets[part['name']];assert (asset['bytes'],asset['sha256'])==(part['size'],part['sha256'])
assert assets['transport_manifest.json']['bytes']==(release/'transport_manifest.json').stat().st_size
assert assets['transport_manifest.json']['sha256']==sha(release/'transport_manifest.json')
failed=read(release/'forge_astra_a1_data_unsealed_attempt1_20261030.tar.gz.receipt.json')
failed_asset=assets['forge_astra_a1_data_unsealed_attempt1_20261030.tar.gz']
assert failed['status']=='PASS' and failed_asset['bytes']==failed['archive_bytes'] and failed_asset['sha256']==failed['archive_sha256']
for name in ('forge_astra_a1_data_results_20261030.tar.gz.receipt.json','forge_astra_a1_data_unsealed_attempt1_20261030.tar.gz.receipt.json'):
    assert assets[name]['bytes']==(release/name).stat().st_size and assets[name]['sha256']==sha(release/name)
smoke=delivery/'smoke_run_41010526993/artifacts/forge-astra-a1-delivery-41010526993-1'
smoke_receipt=read(smoke/'receipt.json');server=read(smoke/'server_assets_final.json')
assert smoke_receipt['status']=='PASS' and len(smoke_receipt['assets'])==1
assert smoke_receipt['manifest_sha256']==sha(smoke/'manifest.json')
assert module.exact_remote(server['transport_manifest.json'],assets['transport_manifest.json'])
report={'status':'PASS_SAVED_DELIVERY_PROVENANCE','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':sha(delivery/'blob_assets.json'),'assets':summaries,'asset_bytes_total':sum(a['bytes'] for a in manifest['assets']),'saved_git_acknowledgments':len(records),'largest_git_chunk_bytes':max(r['bytes'] for r in records),'whole_results_archive':transport['whole'],'smoke_release_asset':'PASS_SAVED_SERVER_SIZE_SHA256_METADATA','full_delivery_release_assets':'PENDING_ROOT_CURRENT_SERVER_VERIFICATION','limitations':['Saved acknowledgments and original package/transport receipts reconciled; no new remote reads or release mutations','Full large original archive bytes were not rehashed in this review','No credential values read or copied','Git blob acknowledgments alone do not certify release publication']}
(here/'provenance_result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
