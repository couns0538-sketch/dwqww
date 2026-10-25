#!/usr/bin/env python3
"""Original UCI warning regression; raw protocol evidence is losslessly encoded."""
import argparse,base64,hashlib,json,subprocess,sys
from pathlib import Path

def invoke(exe,commands):
    child=subprocess.run([str(exe)],input=commands.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return {'argv':[str(exe)],'commands_base64':base64.b64encode(commands.encode()).decode(),'actual_exit':child.returncode,'stdout_base64':base64.b64encode(child.stdout).decode(),'stderr_base64':base64.b64encode(child.stderr).decode(),'stdout_sha256':hashlib.sha256(child.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(child.stderr).hexdigest()},child.stdout,child.stderr

def parsed_lines(raw):
    return raw.replace(b'\r\n',b'\n').splitlines(keepends=True)

def handshake(raw):
    end=0
    for line in raw.splitlines(keepends=True):
        end+=len(line)
        if line.rstrip(b'\r\n')==b'uciok':return raw[:end]
    return b''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--expect-warning',choices=['on','off'],default='on')
    parser.add_argument('--reference-engine',type=Path)
    args=parser.parse_args();engine=args.engine.resolve(strict=True)
    commands='uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nsetoption name AspirationDelta value 18\nsetoption name Forge S02 Missing Option value 7\nsetoption name Hash value not-a-number\nsetoption name Ponder value invalid\nsetoption name Ponder value false\nisready\nquit\n'
    evidence,out,err=invoke(engine,commands)
    warning=b'info string unknown option Forge S02 Missing Option\n'
    lines=parsed_lines(out)
    warnings=[line for line in lines if line.startswith(b'info string unknown option ')]
    checks={'normal_exit':evidence['actual_exit']==0,'stderr_empty':not err,'handshake_and_ready':b'uciok\n' in lines and b'readyok\n' in lines,'unknown_full_name':warnings==([warning] if args.expect_warning=='on' else []),'known_invalid_hash_unchanged':lines.count(b'info string invalid value for option Hash\n')==1,'known_invalid_ponder_unchanged':lines.count(b'info string invalid value for option Ponder\n')==1,'no_unknown_option_advertised':not any(b'Forge S02 Missing Option' in x and x.startswith(b'option name ') for x in lines),'hidden_tunable_still_recognized':not any(b'unknown option AspirationDelta' in x for x in lines)}
    if args.reference_engine:
        reference,refout,referr=invoke(args.reference_engine.resolve(strict=True),'uci\nquit\n')
        handshake_bytes=handshake(out)
        checks['uci_handshake_byte_identical']=reference['actual_exit']==0 and not referr and handshake_bytes==refout
        evidence['reference']=reference
    result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'expect_warning':args.expect_warning,'engine_sha256':hashlib.sha256(engine.read_bytes()).hexdigest(),'test_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'evidence':evidence}
    print(json.dumps(result,indent=2));return 0 if all(checks.values()) else 1
if __name__=='__main__':sys.exit(main())
