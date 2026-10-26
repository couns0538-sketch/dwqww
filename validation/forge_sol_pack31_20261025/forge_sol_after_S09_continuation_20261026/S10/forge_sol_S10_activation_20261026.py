"""Reject an ineffective or unknown S10 option using original d11 transcripts.

This is an activation gate, not a strength or complete Std qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
def validate_activity(uci,off,on,option):
 def nodes(text):
  matches=re.findall(r'^info string bench depth 11 nodes ([0-9]+) time [0-9]+ nps [0-9]+$',text,re.M)
  if len(matches)!=1:raise ValueError('one depth11 benchmark record required')
  return int(matches[0])
 advertised=[s for s in uci.splitlines() if s.startswith('option name '+option+' ')]
 if advertised!=['option name '+option+' type check default false']:
  raise ValueError('exactly one default-OFF typed option must be advertised')
 active='info string '+option+' active'
 if active in off.splitlines():raise ValueError('OFF transcript reports active')
 if on.splitlines().count(active)!=1:raise ValueError('ON transcript must report active once')
 before,after=nodes(off),nodes(on)
 if before!=308972:raise ValueError('OFF d11 differs from fixed lock reference308972')
 if after==before:raise ValueError('ON equals OFF: reject unknown or ineffective option')
 return {'off_nodes':before,'on_nodes':after,'status':'PASS_ACTIVATION_ONLY','option':option}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('uci-output','off-output','on-output'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--option',required=True);parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args()
 try:args.out.mkdir(parents=True,exist_ok=False)
 except FileExistsError:parser.exit(1,'output directory already exists\n')
 paths={k:getattr(args,k+'_output') for k in ('uci','off','on')}
 result={'input':{k:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in paths.items()}}
 try:
  result.update(validate_activity(*(paths[k].read_text() for k in ('uci','off','on')),args.option))
 except (ValueError,UnicodeError) as error:result.update(status='FAIL',reason=str(error))
 (args.out/'forge_sol_S10_activation_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n')
 print(result['status']);return int(result['status']=='FAIL')

if __name__=='__main__':raise SystemExit(main())
