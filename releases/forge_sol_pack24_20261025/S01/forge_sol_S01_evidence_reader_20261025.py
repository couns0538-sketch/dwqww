#!/usr/bin/env python3
"""Verify sealed S01 evidence bytes; optionally recover them into a new folder."""
import argparse,base64,hashlib,json
from pathlib import Path,PurePosixPath
p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('--extract',type=Path);a=p.parse_args();r=json.loads(a.bundle.read_text());names=set();decoded=[]
for row in r['files']:
 name=PurePosixPath(row['relative_path']);assert not name.is_absolute() and '..' not in name.parts and str(name) not in names;names.add(str(name));b=base64.b64decode(row['data_base64'],validate=True);assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'];decoded.append((name,b))
if a.extract:
 a.extract.mkdir(parents=False,exist_ok=False)
 for name,b in decoded:
  f=a.extract/str(name);f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb') as out:out.write(b)
print('S01_RAW_EVIDENCE_SHA256_PASS',len(decoded))
