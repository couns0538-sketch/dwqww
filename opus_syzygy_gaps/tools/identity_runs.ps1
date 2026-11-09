# identity_runs.ps1 -Exe <exe> -Tag <tag> [-Sets net_on,net_off,tb_12k,tb_roots,tb_clock,tb_special] [-Jobs 4] [-Opt 'N=V;N=V']
# One exe through the identity sets at Threads 1. Output: out/ident/<tag>/<set>.jsonl. Skips a set whose output exists (resume); compare with
# compare_runs.py. Sets: net_on / net_off: 12k FENs depth 13, no tables. tb_12k: 12k FENs depth 13, full tables. tb_roots: first 30000 5-man roots,
# depth 10, 3-4 piece tables. tb_clock: clock fixture depth 6, full tables. tb_special: promo, ep, rep, castle, clock100 fixtures depth 6, full tables.
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Sets = 'net_on,net_off,tb_12k,tb_roots,tb_clock,tb_special',
    [string]$Opt = '',
    [int]$Jobs = 4
)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$py = 'C:\Python315\python.exe'
$tool = Join-Path $JobRepo 'opus_syzygy_gaps\tools\uci_tb.py'
$out = Join-Path $JobOut "ident\$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$f12k = Join-Path $JobOut 'exp\fens_12k_v2.txt'
$optArgs = ''
foreach ($o in ($Opt -split ';')) { if ($o) { $optArgs += " --opt $o" } }
Set-Content -Path "$out\RUN.txt" -Value ('exe ' + $Exe + ' sha256 ' + (Get-FileHash -Algorithm SHA256 -LiteralPath $Exe).Hash + ' opts [' + $Opt + '] ' + (Get-ViennaNow) + ' ' + (Get-JobPinLine))
function Run([string]$name, [string]$fens, [string]$extra) {
    $o = Join-Path $out "$name.jsonl"
    if (Test-Path -LiteralPath $o) { Add-Content "$out\RUN.txt" "skip $name (exists)"; return }
    cmd /d /c "`"$py`" -I -B `"$tool`" `"$Exe`" `"$fens`" `"$o`" --jobs $Jobs $extra $optArgs > `"$out\$name.log`" 2>&1"
    Add-Content "$out\RUN.txt" ("$name exit $LASTEXITCODE " + (Get-ViennaNow) + ' ' + (Get-Content "$out\$name.log" -TotalCount 1))
}
foreach ($s in ($Sets -split ',')) {
    switch ($s) {
        'net_on' { Run 'net_on' $f12k '--depth 13' }
        'net_off' { Run 'net_off' $f12k '--depth 13 --opt UseNNUE=false' }
        'tb_12k' { Run 'tb_12k' $f12k '--depth 13 --tables D:\syzygy345' }
        'tb_roots' { Run 'tb_roots' (Join-Path $JobOut 'exp\e1\roots200k.fens') "--depth 10 --first 30000 --tables $JobOut\tb\man34" }
        'tb_clock' { Run 'tb_clock' (Join-Path $JobOut 'exp\root\clock.fens') '--depth 6 --tables D:\syzygy345' }
        'tb_special' {
            foreach ($k in 'promo', 'ep', 'rep', 'castle', 'clock100') { Run "tb_$k" (Join-Path $JobOut "exp\special\s1.$k.fens") '--depth 6 --tables D:\syzygy345' }
        }
    }
}
Add-Content "$out\RUN.txt" ('end ' + (Get-ViennaNow))
