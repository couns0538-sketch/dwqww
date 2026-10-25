# Focused LF/CRLF parsing fixture; this is not native Windows execution.
import importlib.util,json
from pathlib import Path
p=Path(__file__).with_name('forge_sol_S02_unknownopt_test_20261025.py');spec=importlib.util.spec_from_file_location('test_subject',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
lf=b'id name fixture\nuciok\ninfo string unknown option Multi Word Name\nreadyok\n';crlf=lf.replace(b'\n',b'\r\n')
assert m.parsed_lines(lf)==m.parsed_lines(crlf)
assert m.handshake(lf)==b'id name fixture\nuciok\n'
assert m.handshake(crlf)==b'id name fixture\r\nuciok\r\n'
assert lf!=crlf
print(json.dumps({'status':'PASS','parsed_LF_CRLF_equal':True,'raw_handshake_line_endings_preserved':True,'native_Windows':'UNVERIFIED'},indent=2))
