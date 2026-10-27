#!/usr/bin/env python3
"""make_s35_variants.py (S35, opus 2026-10-27): derive the S35 watcher fixtures from the live-copy watcher.

Reads fixtures/watchers/conc7_watch.v2_conc8_20261025.ps1 (sha256 checked = live conc7_watch.ps1 15250b63...) and
fixtures/functions/autopromote_896663b0_tl_functions.ps1 (AST extract made by the harness -ExtractFrom mode) and writes:
  conc7_watch.v2_NEG_readalltext.ps1            Read-Shared body -> [IO.File]::ReadAllText (the spec's negative fixture)
  conc7_watch.v3_PROPOSED_rotation_fix.ps1      v2 + rotation/truncation-aware TL/crash dedupe (NOT deployed; for CR)
  autopromote_896663b0_tl_functions_NEG_readalltext.ps1
  conc7_watch.v2_PLANTED_bomblind.ps1          shared read kept, but bytes decoded with UTF8.GetString (BOM kept) -> S4 must FAIL
  conc7_watch.v2_PLANTED_missingfile.ps1       Test-Path guard dropped, Get-Content -ErrorAction Stop -> S3 must FAIL
plus a unified diff per variant. Every replacement must match exactly once. Stdlib only, deterministic, writes only
inside this job folder.
"""
import difflib
import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
W = HERE / 'fixtures' / 'watchers'
F = HERE / 'fixtures' / 'functions'
V2 = W / 'conc7_watch.v2_conc8_20261025.ps1'
V2_SHA = '15250b635973385780be0f643f3fb6f0fbf7e141d53d6e1f76dcf7514d572348'
AP = F / 'autopromote_896663b0_tl_functions.ps1'

READ_SHARED_V2 = ("$fs=[IO.File]::Open($p,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]'ReadWrite,Delete'); "
                  "$sr=New-Object IO.StreamReader($fs); return $sr.ReadToEnd()")
READ_ALL = 'return [IO.File]::ReadAllText($p)'
STATE_LINE = '$hotN=0; $tlSeen=@{}; $rev5=$false;'
READ_LINE = ("   if($ri){ $conc=[int]$ri.concurrency; $gl=\"$out\\$cur.log\"; "
             "$txt=if(Test-Path $gl){ Read-Shared $gl }else{ '' }\n")
SEG_LINE = ("    $rdFail=(-not $txt) -and (Test-Path $gl) -and ($(try{(Get-Item -LiteralPath $gl -ea Stop).Length}catch{0}) -gt 0); "
            "if(-not $rdFail){ $hd=if($txt.Length -gt 512){$txt.Substring(0,512)}else{$txt}; "
            "if($segSeen.ContainsKey($cur) -and ($txt.Length -lt $segSeen[$cur].len -or "
            "-not $txt.StartsWith($segSeen[$cur].hd,[StringComparison]::Ordinal))){ "
            "L \"log segment change on gate $($cur) (rotated or truncated: $($segSeen[$cur].len) -> $($txt.Length) chars); "
            "TL/crash counter reset\"; $tlSeen[$cur]=0 }; $segSeen[$cur]=@{len=$txt.Length;hd=$hd} }\n")
V3_NOTE = ("# v3 PROPOSED by S35 (opus 2026-10-27), NOT deployed: TL/crash dedupe resets when the gate log is rotated or "
           "truncated (shorter, or no longer starts with the head seen last tick); a failed read changes nothing.\n")
BOMBLIND = '$ms=New-Object IO.MemoryStream; $fs.CopyTo($ms); return [Text.Encoding]::UTF8.GetString($ms.ToArray())'
GUARDED = "$txt=if(Test-Path $gl){ Read-Shared $gl }else{ '' }"
UNGUARDED = '$txt=(Get-Content -LiteralPath $gl -Raw -ErrorAction Stop)'
AP_READ = "$fs=[IO.File]::Open($p,'Open','Read','ReadWrite'); $sr=New-Object IO.StreamReader($fs); $tx=$sr.ReadToEnd(); $sr.Close(); return $tx"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def once(text: str, old: str, new: str, what: str) -> str:
    n = text.count(old)
    if n != 1:
        sys.exit(f'{what}: expected exactly 1 occurrence, found {n}; refusing')
    return text.replace(old, new)


def write(path: pathlib.Path, text: str, src_name: str, src_text: str) -> None:
    raw = ('﻿' + text) if text.startswith('#') and src_text.startswith('﻿') else text
    path.write_bytes(raw.encode('utf-8'))
    diff = ''.join(difflib.unified_diff(src_text.lstrip('﻿').splitlines(True), text.lstrip('﻿').splitlines(True),
                                        fromfile=src_name, tofile=path.name))
    path.with_suffix('.diff').write_bytes(diff.encode('utf-8'))
    print(f'{path.relative_to(HERE)} sha256 {sha(raw.encode("utf-8"))} ({len(diff.splitlines())} diff lines)')


def main() -> None:
    raw = V2.read_bytes()
    if sha(raw) != V2_SHA:
        sys.exit(f'{V2.name}: sha256 {sha(raw)} != {V2_SHA}; refusing')
    src = raw.decode('utf-8')
    body = src.lstrip('﻿')
    neg = once(body, READ_SHARED_V2, READ_ALL, 'v2 Read-Shared body')
    write(W / 'conc7_watch.v2_NEG_readalltext.ps1', neg, V2.name, src)
    first_nl = body.index('\n') + 1
    v3 = body[:first_nl] + V3_NOTE + body[first_nl:]
    v3 = once(v3, STATE_LINE, '$hotN=0; $tlSeen=@{}; $segSeen=@{}; $rev5=$false;', 'v2 state line')
    v3 = once(v3, READ_LINE, READ_LINE + SEG_LINE, 'v2 gate-log read line')
    write(W / 'conc7_watch.v3_PROPOSED_rotation_fix.ps1', v3, V2.name, src)
    bl = once(body, '$sr=New-Object IO.StreamReader($fs); return $sr.ReadToEnd()', BOMBLIND, 'v2 Read-Shared decode')
    write(W / 'conc7_watch.v2_PLANTED_bomblind.ps1', bl, V2.name, src)
    mf = once(body, GUARDED, UNGUARDED, 'v2 Test-Path guard')
    write(W / 'conc7_watch.v2_PLANTED_missingfile.ps1', mf, V2.name, src)
    ap = AP.read_bytes().decode('utf-8')
    apneg = once(ap, AP_READ, 'return [IO.File]::ReadAllText($p)', 'autopromote Read-Shared body')
    write(F / 'autopromote_896663b0_tl_functions_NEG_readalltext.ps1', apneg, AP.name, ap)


if __name__ == '__main__':
    main()
