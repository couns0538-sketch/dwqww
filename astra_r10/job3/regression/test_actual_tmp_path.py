"""Original real pytest fixture check; no NPT import or model execution."""
def test_real_tmp_path_still_writes_exact_payload(tmp_path):
    path=tmp_path/'sentinel.bin'
    path.write_bytes(b'owned pytest fixture target remains real')
    assert path.read_bytes()==b'owned pytest fixture target remains real'
    assert path.parent.is_dir()
