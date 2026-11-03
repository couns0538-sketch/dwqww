"""Retain one exact public npm archive and extract a separate review tool."""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import urllib.request

sys.dont_write_bytecode = True
HERE = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
sys.path.insert(0, str(HERE))
from filter_positions import low_priority
from resource_policy import storage_guard

ROOT = Path('C:/astra8_data/extension3h_20261103/pyright_tool')
URL = 'https://registry.npmjs.org/pyright/-/pyright-1.1.414.tgz'
INTEGRITY = 'FPZZb51jepDX4eP7TEYDeNFtmE3WgwkkEcJpvH3/QmUSsj0EAy3LXu+xB4T/FWDejtsXlCfFr/rbWFjwuwuXww=='


def main():
    low_priority()
    storage_guard(ROOT, allowance=40_000_000)
    ROOT.mkdir()
    archive = ROOT / 'pyright-1.1.414.tgz'
    with urllib.request.urlopen(URL, timeout=30) as response:
        data = response.read(15_000_001)
    if len(data) > 15_000_000 or base64.b64encode(hashlib.sha512(data).digest()).decode() != INTEGRITY:
        raise ValueError('archive size or registry integrity mismatch')
    with archive.open('xb') as stream:
        stream.write(data)
    with tarfile.open(archive, 'r:gz') as package:
        members = package.getmembers()
        total = sum(m.size for m in members)
        if total != 19_457_120 or len(members) != 5423:
            raise ValueError('package differs from inspected registry metadata')
        seen = set()
        for member in members:
            relative = PurePosixPath(member.name)
            key = member.name.casefold()
            if (not member.isfile() or relative.is_absolute() or relative.parts[0] != 'package'
                    or '..' in relative.parts or ':' in member.name or '\\' in member.name or key in seen):
                raise ValueError('unsafe archive member')
            seen.add(key)
            destination = ROOT.joinpath(*relative.parts)
            if not destination.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError('archive path escape')
        storage_guard(ROOT, allowance=total+1_000_000)
        for member in members:
            destination = ROOT.joinpath(*PurePosixPath(member.name).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with package.extractfile(member) as source, destination.open('xb') as output:
                shutil.copyfileobj(source, output, 1024*1024)
    metadata = json.loads((ROOT/'package/package.json').read_text())
    if (metadata['name'], metadata['version'], metadata['license']) != ('pyright','1.1.414','MIT'):
        raise ValueError('unexpected package identity')
    receipt = {'url': URL, 'sha256': hashlib.sha256(data).hexdigest(),
               'sha512_integrity': 'sha512-'+INTEGRITY, 'compressed_bytes': len(data),
               'expanded_bytes': total, 'files': len(members), 'licence': metadata['license'],
               'method': 'isolated extraction; no npm lifecycle scripts or global installation',
               'resource': storage_guard(ROOT, allowance=1_000_000)}
    with (ROOT/'INSTALL.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
