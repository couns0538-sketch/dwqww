"""Finalize retained downloads after the root-METADATA inspector correction."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import collect_wheels as c


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--threads', type=int, choices=[1], required=True)
    parser.parse_args()
    p = c.base.psutil.Process()
    c.need(p.nice() == c.base.psutil.IDLE_PRIORITY_CLASS and p.cpu_affinity() == [3], 'Idle CPU3 required')
    c.need(not (c.JOB / 'WHEEL_LOCK.json').exists(), 'preserve any existing lock')
    boot_raw = (c.JOB / 'BOOTSTRAP.json').read_bytes(); boot = json.loads(boot_raw)
    c.need(boot['status'] == 'BOOTSTRAP_PASS', 'bootstrap required')
    c.need(c.safety.digests(c.RUNTIME / 'python/python.exe')[0] == boot['interpreter_sha256'], 'interpreter drift')
    c.safety.disk_budget(50_000_000)
    workspace = c.safety.workspace_bytes()
    c.need(workspace + 50_000_000 <= c.safety.CAP, 'metadata-only reservation exceeds cap')
    metadata = c.RUNTIME / 'downloads/wheel_metadata02'
    c.need(not metadata.exists(), 'preserve failed metadata attempt')
    metadata.mkdir()
    index = c.base.download(c.TORCH_INDEX, metadata / 'torch-cpu-index.html', 4_000_000)
    links = c.Links(); links.feed(Path(index['path']).read_text(encoding='utf-8'))
    matches = [urllib.parse.urljoin(c.TORCH_INDEX, link) for link in links.links
               if Path(urllib.parse.unquote(urllib.parse.urlsplit(link).path)).name == c.TORCH_NAME]
    c.need(len(matches) == 1, 'exact official CPU Torch anchor required')
    parts = urllib.parse.urlsplit(matches[0])
    c.base.url_allowed(matches[0])
    expected = urllib.parse.parse_qs(parts.fragment).get('sha256', [])
    c.need(len(expected) == 1 and len(expected[0]) == 64, 'official CPU hash anchor required')
    wheels = c.RUNTIME / 'downloads/wheels'
    sha, _, size = c.safety.digests(wheels / c.TORCH_NAME)
    c.need(sha == expected[0], 'retained CPU Torch differs from fresh official index')
    torch = {'path': str(wheels / c.TORCH_NAME), 'url': urllib.parse.urlunsplit(parts._replace(fragment='')),
             'sha256': sha, 'bytes': size, 'official_index': index,
             'scope': 'retained original wheel revalidated against fresh official CPU index; not redownloaded'}
    c.finish_lock(wheels, metadata, torch, [index, torch], boot_raw, boot, workspace, recovered=True)


if __name__ == '__main__':
    main()
