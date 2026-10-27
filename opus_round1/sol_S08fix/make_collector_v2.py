"""Create forge_sol_S08_collect_profiles_v2.py from Sol's unchanged collector (17aa0cae) with exact,
assert-once replacements: AL1 bench pins as defaults (configurable), S08-4 table changes."""
import sys
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8', newline='').read()


def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, (n, old[:80])
    t = t.replace(old, new)


rep('''"""ADVICE: collect fixed-work search counters, never strength or dead-code proof.
''', '''"""ADVICE: collect fixed-work search counters, never strength or dead-code proof (S08 v2).

v2 (S08fix; v1 = Sol's forge_sol_S08_collect_profiles_substitute_20261026.py @ 17aa0cae, unchanged):
- bench pins are arguments (--bench11-nodes / --bench20-nodes), default the AL1 lock (312866 / 12389307);
  v1 hard-coded Sol's development base (308972 / 11901452) and refused AL1 builds;
- S08-4: the firing tables drop events whose feature is disabled by a default-zero tuning constant
  (capture_futility_prunes: tune::CaptureFutilityBase = 0) from the rare-event rows and list them in their own
  section; the table states the corpus limit (substitute corpus, not the specified 2,000 WAC/STS set).
''')
rep("""DATE = '20261026'""", """DATE = '20261026'
DEFAULT_BENCH11_NODES = 312866    # AL1 lock pins (forge-engine-verify)
DEFAULT_BENCH20_NODES = 12389307
# S08-4: events whose feature the locked defaults switch off; a zero count is not a dead-feature finding.
DISABLED_BY_DEFAULT = {
    'capture_futility_prunes': 'tune::CaptureFutilityBase = 0 in the lock defaults (src/search.cpp); the prune '
                               'requires CaptureFutilityBase > 0, the opportunity counter runs before that guard',
}
CORPUS_LIMIT = ('Corpus limit: the specified 2,000 WAC/STS set is not available (no STS file exists on the PC); '
                'this run uses Sol\\'s sealed substitute corpus: 300 WAC + 7 bench + 1,693 synthetic opening '
                'positions, 2,000 distinct. It is not a WAC/STS corpus.')""")
rep('''def _table_text(groups):
    text = ['# ADVICE: observed search-event frequencies', '',
            'Search only; board/FEN setup excluded. Zero opportunities are undefined.',
            'A frequency below 0.1% is advisory; it proves neither dead code nor strength.', '']
    for label, rows in groups:
        text += ['## '+label, '', '| Event | Count | Denominator | Opportunities | Percent | Below 0.1% |',
                 '|---|---:|---|---:|---:|---|']
        for row in rows:
            pct = 'unknown' if row['pct'] is None else format(row['pct'], '.8g')
            rare = 'undefined' if row['rare_below_0_1_pct'] is None else str(row['rare_below_0_1_pct']).lower()
            text.append('| {event} | {count} | {denominator} | {opportunities} | {pct} | {rare} |'.format(**{**row,'pct':pct,'rare':rare}))
        text.append('')
    return '\\n'.join(text)+'\\n'
''', '''def _table_text(groups):
    text = ['# ADVICE: observed search-event frequencies', '',
            'Search only; board/FEN setup excluded. Zero opportunities are undefined.',
            'A frequency below 0.1% is advisory; it proves neither dead code nor strength.',
            CORPUS_LIMIT, '']
    for label, rows in groups:
        kept = [row for row in rows if row['event'] not in DISABLED_BY_DEFAULT]
        text += ['## '+label, '', '| Event | Count | Denominator | Opportunities | Percent | Below 0.1% |',
                 '|---|---:|---|---:|---:|---|']
        for row in kept:
            pct = 'unknown' if row['pct'] is None else format(row['pct'], '.8g')
            rare = 'undefined' if row['rare_below_0_1_pct'] is None else str(row['rare_below_0_1_pct']).lower()
            text.append('| {event} | {count} | {denominator} | {opportunities} | {pct} | {rare} |'.format(**{**row,'pct':pct,'rare':rare}))
        dropped = [row for row in rows if row['event'] in DISABLED_BY_DEFAULT]
        if dropped:
            text += ['', 'Not a dead-feature row (disabled by default, so a zero count is expected):']
            text += ['- {event}: count {count} of {opportunities} {denominator}; '.format(**row) +
                     DISABLED_BY_DEFAULT[row['event']] for row in dropped]
        text.append('')
    return '\\n'.join(text)+'\\n'
''')
rep('''        rows.append({'event': name, 'count': count, 'denominator': registry[name],
                     'opportunities': opportunities, 'pct': pct, 'overflow': overflow,
                     'rare_below_0_1_pct': None if pct is None else pct < .1,
                     'interpretation': 'ADVICE; frequency is not strength or dead-code proof'})''',
    '''        disabled = DISABLED_BY_DEFAULT.get(name)
        rows.append({'event': name, 'count': count, 'denominator': registry[name],
                     'opportunities': opportunities, 'pct': pct, 'overflow': overflow,
                     'rare_below_0_1_pct': None if pct is None or disabled else pct < .1,
                     'disabled_by_default': disabled,
                     'interpretation': 'ADVICE; frequency is not strength or dead-code proof'})''')
rep('''def collect(command, suites, output, *, depth=None, nodes=None, required=2000,
            allow_incomplete=False, manifest=None, timeout=120, max_capture_bytes=32 << 20):''',
    '''def collect(command, suites, output, *, depth=None, nodes=None, required=2000,
            allow_incomplete=False, manifest=None, timeout=120, max_capture_bytes=32 << 20,
            bench11_nodes=DEFAULT_BENCH11_NODES, bench20_nodes=DEFAULT_BENCH20_NODES):''')
rep("""              'bench11_expected_nodes':308972, 'bench20_expected_nodes':11901452}""",
    """              'bench11_expected_nodes':bench11_nodes, 'bench20_expected_nodes':bench20_nodes,
              'corpus_limit':CORPUS_LIMIT, 'disabled_by_default':DISABLED_BY_DEFAULT}""")
rep("""        if (int(match.group(1)),int(match.group(2))) != (11,308972):""",
    """        if (int(match.group(1)),int(match.group(2))) != (11,bench11_nodes):""")
rep("""            if (int(match.group(1)),int(match.group(2))) != (20,11901452):""",
    """            if (int(match.group(1)),int(match.group(2))) != (20,bench20_nodes):""")
rep("""            verify_profile_work(packet,expected_nodes=11901452)""",
    """            verify_profile_work(packet,expected_nodes=bench20_nodes)""")
rep("""    parser.add_argument('--max-capture-bytes',type=int,default=32 << 20)
    args = parser.parse_args(argv)""", """    parser.add_argument('--max-capture-bytes',type=int,default=32 << 20)
    parser.add_argument('--bench11-nodes',type=int,default=DEFAULT_BENCH11_NODES,help='first bare bench 11 pin (AL1)')
    parser.add_argument('--bench20-nodes',type=int,default=DEFAULT_BENCH20_NODES,help='profiled bench 20 pin (AL1)')
    args = parser.parse_args(argv)""")
rep("""                         timeout=args.timeout,max_capture_bytes=args.max_capture_bytes)""",
    """                         timeout=args.timeout,max_capture_bytes=args.max_capture_bytes,
                         bench11_nodes=args.bench11_nodes,bench20_nodes=args.bench20_nodes)""")
# Windows support (v2): select() works only on sockets on Windows, so the pipe reader uses two threads and a
# queue there; on failure the child gets EOF on stdin instead of a process-group kill (no killpg on Windows).
rep("""import selectors
import signal""", """import queue
import selectors
import signal
import threading""")
rep("""        self.receipt['pid'] = self.proc.pid
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ, 'stdout')
        self.selector.register(self.proc.stderr, selectors.EVENT_READ, 'stderr')
""", """        self.receipt['pid'] = self.proc.pid
        if os.name == 'nt':
            # v2: no select() on Windows pipes; reader threads feed one queue.
            self.selector, self.queue, self.live = None, queue.Queue(), {'stdout', 'stderr'}
            for name in ('stdout', 'stderr'):
                threading.Thread(target=self._reader, args=(name,), daemon=True).start()
        else:
            self.selector = selectors.DefaultSelector()
            self.selector.register(self.proc.stdout, selectors.EVENT_READ, 'stdout')
            self.selector.register(self.proc.stderr, selectors.EVENT_READ, 'stderr')

    def _reader(self, name):
        stream = getattr(self.proc, name)
        while True:
            try:
                data = os.read(stream.fileno(), 65536)
            except OSError:
                data = b''
            self.queue.put((name, data))
            if not data:
                return

    def _open_streams(self):
        return bool(self.live) if self.selector is None else bool(self.selector.get_map())
""")
rep("""    def _pump(self, wait=.05):
        for key, _ in self.selector.select(wait):
            data = os.read(key.fileobj.fileno(), 65536)
            if not data:
                self.selector.unregister(key.fileobj)
                if key.data == 'stdout' and self.pending:
                    self.lines.append(self.pending.decode('utf-8'))
                    self.pending = b''
                continue
            remaining = self.max_bytes-self.total
            self.total += len(data)
            if self.total > self.max_bytes:
                if remaining > 0:
                    self.handles[key.data].write(data[:remaining])
                    self.handles[key.data].flush()
                self.complete = False
                raise ValueError('raw output exceeded explicit capture limit; partial evidence retained')
            self.handles[key.data].write(data)
            self.handles[key.data].flush()
            if key.data == 'stdout':""", """    def _pump(self, wait=.05):
        if self.selector is None:
            events = []
            try:
                events.append(self.queue.get(timeout=wait))
                while True:
                    events.append(self.queue.get_nowait())
            except queue.Empty:
                pass
        else:
            events = [(key.data, os.read(key.fileobj.fileno(), 65536), key.fileobj)
                      for key, _ in self.selector.select(wait)]
        for event in events:
            name, data = event[0], event[1]
            if not data:
                if self.selector is None:
                    self.live.discard(name)
                else:
                    self.selector.unregister(event[2])
                if name == 'stdout' and self.pending:
                    self.lines.append(self.pending.decode('utf-8'))
                    self.pending = b''
                continue
            remaining = self.max_bytes-self.total
            self.total += len(data)
            if self.total > self.max_bytes:
                if remaining > 0:
                    self.handles[name].write(data[:remaining])
                    self.handles[name].flush()
                self.complete = False
                raise ValueError('raw output exceeded explicit capture limit; partial evidence retained')
            self.handles[name].write(data)
            self.handles[name].flush()
            if name == 'stdout':""")
rep("""            if not self.selector.get_map() and self.proc.poll() is not None:
                raise RuntimeError('process exited before expected protocol terminal')""",
    """            if not self._open_streams() and self.proc.poll() is not None:
                raise RuntimeError('process exited before expected protocol terminal')""")
rep("""                        while self.selector.get_map() or self.proc.poll() is None:""",
    """                        while self._open_streams() or self.proc.poll() is None:""")
rep("""                if not successful:
                    try:
                        os.killpg(self.proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    self.proc.wait(timeout=2)""", """                if not successful:
                    if os.name == 'nt':
                        # v2: no process-group kill on Windows; end the child's input and wait for it.
                        try:
                            self.proc.stdin.close()
                        except OSError:
                            pass
                        self.proc.wait(timeout=30)
                    else:
                        try:
                            os.killpg(self.proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        self.proc.wait(timeout=2)""")
rep("""                        while self.selector.get_map() and time.monotonic() < deadline:""",
    """                        while self._open_streams() and time.monotonic() < deadline:""")
rep("""                if hasattr(self, 'selector'):
                    try:
                        self.selector.close()""", """                if getattr(self, 'selector', None) is not None:
                    try:
                        self.selector.close()""")
open(dst, 'w', encoding='utf-8', newline='').write(t)
print('wrote', dst)
