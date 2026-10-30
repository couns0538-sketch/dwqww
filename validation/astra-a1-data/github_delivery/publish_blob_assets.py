#!/usr/bin/env python3
"""Deliver verified original Git blobs to one pre-existing Forge release.
Never clobbers/deletes an asset; only exact uploaded size+SHA256 permits a skip.
IDEA_SOURCE: user durable-evidence contract and documented GitHub REST metadata.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

REPOSITORY = 'couns0538-sketch/dwqww'
RELEASE_ID = 428684041
RELEASE_TAG = 'astra-a1-data-results-20261030'
MAX_CHUNK = 40 * 1024 * 1024
MAX_RESPONSE = 64 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def unique_object(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def validate(data):
    require(isinstance(data, dict) and data.get('format') == 'forge-github-blob-delivery-v1', 'manifest format')
    require(data.get('repository') == REPOSITORY and type(data.get('release_id')) is int and data.get('release_id') == RELEASE_ID
            and data.get('release_tag') == RELEASE_TAG, 'repository/release identity')
    assets = data.get('assets')
    require(isinstance(assets, list) and 1 <= len(assets) <= 32, 'asset count')
    names = set()
    for asset in assets:
        require(isinstance(asset, dict), 'asset object')
        name = asset.get('name')
        require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,199}', name)
                and not name.endswith('.') and not re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', name, re.I), 'unsafe asset name')
        require(name not in names, 'duplicate asset name'); names.add(name)
        require(type(asset.get('bytes')) is int and 0 <= asset['bytes'] <= 2_000_000_000, 'asset byte limit')
        require(isinstance(asset.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', asset['sha256']), 'asset SHA256')
        chunks = asset.get('chunks')
        require(isinstance(chunks, list) and len(chunks) <= 512, 'chunk count')
        offset = 0
        for chunk in chunks:
            require(isinstance(chunk, dict), 'chunk object')
            require(type(chunk.get('offset')) is int and chunk['offset'] == offset, 'chunk offset')
            require(type(chunk.get('bytes')) is int and 1 <= chunk['bytes'] <= MAX_CHUNK, 'chunk byte limit')
            require(isinstance(chunk.get('sha'), str) and re.fullmatch('[0-9a-f]{40}', chunk['sha']), 'Git SHA1')
            require(isinstance(chunk.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', chunk['sha256']), 'chunk SHA256')
            offset += chunk['bytes']
        require(offset == asset['bytes'], 'missing or extra chunk bytes')
    return data


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the token to a response-supplied host.


class API:
    def __init__(self, token):
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect)

    def get(self, path):
        require(path.startswith('/repos/' + REPOSITORY + '/') and '://' not in path, 'API path')
        request = urllib.request.Request('https://api.github.com' + path, headers={
            'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'forge-astra-a1-evidence-delivery'})
        with self.opener.open(request, timeout=120) as response:
            payload = response.read(MAX_RESPONSE + 1)
        require(len(payload) <= MAX_RESPONSE, 'API response exceeds bounded chunk size')
        return json.loads(payload, object_pairs_hook=unique_object)


def remote_assets(api):
    result = {}
    for page in range(1, 101):
        rows = api.get(f'/repos/{REPOSITORY}/releases/{RELEASE_ID}/assets?per_page=100&page={page}')
        require(isinstance(rows, list), 'release assets response')
        for row in rows:
            require(isinstance(row, dict) and isinstance(row.get('name'), str), 'release asset object')
            require(row['name'] not in result, 'duplicate remote asset name')
            result[row['name']] = row
        if len(rows) < 100:
            return result
    raise ValueError('release asset pagination exceeds limit')


def exact_remote(row, asset):
    return (row.get('state') == 'uploaded' and type(row.get('size')) is int
            and row['size'] == asset['bytes'] and row.get('digest') == 'sha256:' + asset['sha256'])


def decode_blob(response, chunk):
    require(isinstance(response, dict) and response.get('sha') == chunk['sha']
            and type(response.get('size')) is int and response.get('size') == chunk['bytes']
            and response.get('encoding') == 'base64', 'blob metadata mismatch')
    content = response.get('content')
    require(isinstance(content, str) and len(content) <= MAX_RESPONSE, 'blob content bound')
    binary = base64.b64decode(content.replace('\n', '').replace('\r', ''), validate=True)
    require(len(binary) == chunk['bytes'], 'decoded blob size')
    git_digest = hashlib.sha1(b'blob ' + str(len(binary)).encode() + b'\0' + binary).hexdigest()
    require(git_digest == chunk['sha'] and hashlib.sha256(binary).hexdigest() == chunk['sha256'], 'blob digest mismatch')
    return binary


def upload_with_gh(path, repository, tag, logs):
    command = ['gh', 'release', 'upload', tag, str(path), '--repo', repository]
    (logs / (path.name + '.command.json')).write_text(json.dumps(command) + '\n')
    environment = dict(os.environ, GH_TOKEN=os.environ['GITHUB_TOKEN'])
    with (logs / (path.name + '.stdout')).open('xb') as stdout, (logs / (path.name + '.stderr')).open('xb') as stderr:
        result = subprocess.run(command, env=environment, stdout=stdout, stderr=stderr, timeout=1200)
    (logs / (path.name + '.exit')).write_text(str(result.returncode) + '\n')
    require(result.returncode == 0, 'gh upload failed; original streams retained')


def publish(manifest, output, api, uploader=upload_with_gh):
    manifest, output = Path(manifest), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'FAIL', 'repository': REPOSITORY, 'release_id': RELEASE_ID,
               'release_tag': RELEASE_TAG, 'assets': [], 'remote_verification': 'GitHub uploaded-state size and SHA256 digest metadata'}
    try:
        with manifest.open('rb') as stream:
            raw = stream.read(4 * 1024 * 1024 + 1)
        require(len(raw) <= 4 * 1024 * 1024, 'manifest too large')
        original_hash = hashlib.sha256(raw).hexdigest(); receipt['manifest_sha256'] = original_hash
        (output / 'manifest.json').write_bytes(raw)
        data = validate(json.loads(raw, object_pairs_hook=unique_object))
        release = api.get(f'/repos/{REPOSITORY}/releases/{RELEASE_ID}')
        require(release.get('id') == RELEASE_ID and release.get('tag_name') == RELEASE_TAG, 'server release identity mismatch')
        existing = remote_assets(api)
        (output / 'server_assets_initial.json').write_text(json.dumps(existing, indent=2) + '\n')
        for asset in data['assets']:
            if asset['name'] in existing:
                require(exact_remote(existing[asset['name']], asset), 'existing asset collision: ' + asset['name'])
        assets_dir, logs = output / 'assets', output / 'logs'; assets_dir.mkdir(); logs.mkdir()
        with (output / 'events.jsonl').open('x', encoding='utf-8') as events:
            for asset in data['assets']:
                require(sha256(manifest) == original_hash, 'manifest changed during publication')
                record = {key: asset[key] for key in ('name', 'bytes', 'sha256')}
                if asset['name'] in existing:
                    record['decision'] = 'existing_verified'; receipt['assets'].append(record)
                    continue
                path = assets_dir / asset['name']; whole = hashlib.sha256()
                with path.open('xb') as target:
                    for chunk in asset['chunks']:
                        binary = decode_blob(api.get(f'/repos/{REPOSITORY}/git/blobs/{chunk["sha"]}'), chunk)
                        target.write(binary); whole.update(binary); del binary
                        events.write(json.dumps({'asset': asset['name'], 'verified_chunk': chunk}) + '\n'); events.flush()
                    target.flush(); os.fsync(target.fileno())
                require(path.stat().st_size == asset['bytes'] and whole.hexdigest() == asset['sha256']
                        and sha256(path) == asset['sha256'], 'assembled asset digest mismatch')
                require(sha256(manifest) == original_hash, 'manifest changed during assembly')
                uploader(path, REPOSITORY, RELEASE_TAG, logs)
                require(sha256(path) == asset['sha256'], 'local asset changed during upload')
                require(sha256(manifest) == original_hash, 'manifest changed during upload')
                remote = remote_assets(api).get(asset['name'], {})
                (logs / (asset['name'] + '.server.json')).write_text(json.dumps(remote, indent=2) + '\n')
                require(exact_remote(remote, asset), 'uploaded asset server digest mismatch')
                record['decision'] = 'uploaded_verified'; receipt['assets'].append(record)
                events.write(json.dumps(record) + '\n'); events.flush()
        final = remote_assets(api)
        (output / 'server_assets_final.json').write_text(json.dumps(final, indent=2) + '\n')
        require(all(exact_remote(final.get(asset['name'], {}), asset) for asset in data['assets']), 'final server asset verification failed')
        require(sha256(manifest) == original_hash, 'manifest changed before final verification')
        receipt['status'] = 'PASS'
    except Exception as error:
        receipt['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        with (output / 'receipt.json').open('x', encoding='utf-8') as target:
            json.dump(receipt, target, indent=2, sort_keys=True); target.write('\n')
        print(json.dumps(receipt, sort_keys=True), flush=True)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        parser.exit(1, 'GITHUB_TOKEN is required\n')
    try:
        publish(args.manifest, args.out, API(token))
    except Exception as error:
        parser.exit(1, f'Delivery failed: {type(error).__name__}: {error}\n')


if __name__ == '__main__':
    main()
