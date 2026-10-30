"""Small real-filesystem publication collision checks, no native children."""
from pathlib import Path
import datetime,hashlib,json,sys
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools/data'))
from forge_pos import PosWriter,Record,text_record
from filter_positions import _publish_final
here=Path(__file__).resolve().parent/'no_overwrite_boundaries';here.mkdir()
fen='4k3/8/8/8/8/8/8/R3K3 w - - 0 1';row,_=text_record(fen+' | 10 | 0.5')
records=[]
for suffix in ('.hce','.fen','.pos'):
    folder=here/suffix[1:];folder.mkdir();writer=PosWriter(folder,'case',True,with_fen=True)
    writer.append(Record(row.board,row.score,row.meta,12),fen=fen)
    target=folder/('case'+suffix);sentinel=('preexisting owner '+suffix+'\n').encode();target.write_bytes(sentinel)
    try:writer.seal()
    except FileExistsError:
        assert target.read_bytes()==sentinel
        assert (folder/'case.pos.part').exists()
        try:writer.seal()
        except ValueError as error:assert 'aborted' in str(error)
        else:raise AssertionError('failed writer was allowed to seal later')
        records.append({'boundary':suffix,'existing_bytes_unchanged':True,'publication':'REJECTED','parts_retained':True})
    else:raise AssertionError('existing output was replaced: '+suffix)
folder=here/'summary';folder.mkdir();sentinel=b'preexisting summary owner\n';(folder/'summary.json').write_bytes(sentinel)
try:_publish_final(folder,{'status':'SEALED','synthetic_fixture':True})
except FileExistsError:
    assert (folder/'summary.json').read_bytes()==sentinel
    assert (folder/'summary.json.pending').exists() and (folder/'manifest.json.pending').exists()
    records.append({'boundary':'summary.json commit receipt','existing_bytes_unchanged':True,'publication':'REJECTED','parts_retained':True})
else:raise AssertionError('existing commit receipt was replaced')
receipt={'status':'PASS_NO_REPLACEMENT_BOUNDARIES','finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':records,'scope':'Actual Linux filesystem EEXIST at POS/HCE/FEN or summary publication; does not establish Windows runtime qualification'}
(here/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
