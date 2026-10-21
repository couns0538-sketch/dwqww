"""One unauthenticated GET, no redirects/retries; preserve original response."""
from pathlib import Path
import datetime
import hashlib
import json
import signal
import sys
import urllib.error
import urllib.request

OUT = Path(__file__).resolve().parent
URL = 'https://github.com/couns0538-sketch/dwqww/tree/forge/test-20261021-0330'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def digest(body):
    return hashlib.sha256(body).hexdigest()

def put(name, body):
    with (OUT / name).open('xb') as target:
        target.write(body)

def record(name, value):
    put(name, (json.dumps(value, indent=2) + '\n').encode())

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, target):
        return None

def alarm(signum, frame):
    raise TimeoutError('35-second aggregate HTTP deadline exceeded; no retry')

def main():
    started = now()
    request_headers = {'User-Agent': 'Mozilla/5.0 (compatible; ForgeReadOnlyAudit/1.0)',
                       'Accept-Encoding': 'identity'}
    record('FETCH-COMMAND.json', {
        'command': [sys.executable, '-B', str(Path(__file__).resolve())],
        'cwd': str(Path.cwd()), 'method': 'GET', 'url': URL,
        'script_sha256': digest(Path(__file__).read_bytes()),
        'started_utc': started, 'network_get_budget': 1,
        'per_operation_timeout_seconds': 20, 'aggregate_timeout_seconds': 35,
        'redirects_enabled': False, 'retries': 0,
        'request_headers': request_headers, 'credentials_supplied': False})
    info = {'requested_url': URL, 'method': 'GET', 'started_utc': started,
            'network_get_attempts': 0, 'redirects_followed': 0, 'retries': 0}
    body = bytearray()
    header_bytes = b''
    previous = signal.signal(signal.SIGALRM, alarm)
    signal.alarm(35)
    response = None
    try:
        opener = urllib.request.build_opener(NoRedirect())
        request = urllib.request.Request(URL, headers=request_headers, method='GET')
        info['network_get_attempts'] = 1
        try:
            response = opener.open(request, timeout=20)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            info.update(http_status=response.status, final_url=response.geturl(),
                        response_headers=list(response.headers.items()))
            header_bytes = response.headers.as_bytes()
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                body.extend(block)
        info['response_complete'] = True
    except Exception as error:
        info.update(error=type(error).__name__ + ': ' + str(error),
                    response_complete=False)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    original = bytes(body)
    put('response.body', original)
    put('response.headers.txt', header_bytes)
    info.update(completed_utc=now(), response_bytes=len(original),
                response_sha256=digest(original),
                response_headers_sha256=digest(header_bytes),
                header_qualification='Original ordered response header fields and library serialization; not a TCP wire capture.',
                body_qualification='Original response entity bytes; no HTML editing or reconstruction.')
    record('response.http.json', info)
    result = {'status': 'PUBLIC_HTML_RESPONSE_SAVED' if info.get('response_complete') else 'PUBLIC_REQUEST_FAILED_PRESERVED_NO_RETRY',
              'requested_url': URL, 'http_status': info.get('http_status'),
              'final_url': info.get('final_url'),
              'network_get_attempts': info['network_get_attempts'],
              'response_bytes': len(original), 'response_sha256': digest(original),
              'response_complete': info['response_complete'],
              'no_git_engine_build_or_message_actions': True}
    record('FETCH-RESULT.json', result)
    print(json.dumps(result, indent=2))
    return 0 if info['response_complete'] else 1

if __name__ == '__main__':
    sys.exit(main())
