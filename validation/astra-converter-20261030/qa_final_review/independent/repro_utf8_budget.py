import json,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,'/tmp/forge-astra-fen-convert/tools/data2')
import convert_dataset as c
with tempfile.TemporaryDirectory(dir='/tmp/astra-qa-independent-20261030') as temp:
 root=Path(temp);src=root/'input.txt';ids=root/'game_ids.txt';src.write_text('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | 61 | 0.0\n');ids.write_text('\U0001f600'*256+'\n')
 a=c.parser().parse_args(['convert','--input',str(src),'--game-ids',str(ids),'--out',str(root/'out'),'--no-filters','--min-free-mb','0'])
 budget=c.disk_budget(a,[]);c.run(a);chunk=c.read_chunks(root/'out')[0];actual=sum((root/'out'/chunk[role]).stat().st_size for role in ['text','bullet','provenance'])
 print(json.dumps({'game_id_characters':256,'game_id_utf8_bytes':1024,'output_estimate_bytes':budget['output_bytes_estimate'],'actual_retained_output_bytes':actual}))
 assert actual>budget['output_bytes_estimate']
