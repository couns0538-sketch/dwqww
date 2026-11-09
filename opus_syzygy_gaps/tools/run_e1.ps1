# run_e1.ps1 - false-claim experiment: 5-man roots searched with the 3-4 piece tables, full set = truth (Fathom batch).
# usage: run_e1.ps1 -Exe <exe> -Tag <tag> -Depths 10,14 [-Opt 'Name=V;Name2=V'] [-Fens <file>] [-First N] [-Jobs 4] [-Tables <dir>]
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Depths = '10',
    [string]$Opt = '',
    [string]$Fens = 'D:\forge_jobs_20261107\opus1\out\exp\e1\roots200k.fens',
    [string]$Labels = 'D:\forge_jobs_20261107\opus1\out\exp\e1\roots200k.fathom',
    [string]$Tables = 'D:\forge_jobs_20261107\opus1\out\tb\man34',
    [int]$First = 0,
    [int]$Jobs = 4
)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$py = 'C:\Python315\python.exe'
$tools = Join-Path $JobRepo 'opus_syzygy_gaps\tools'
$out = Join-Path $JobOut "exp\e1\$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
foreach ($d in ($Depths -split ',')) {
    $base = Join-Path $out "d$d"
    $optArgs = ''
    foreach ($o in ($Opt -split ';')) { if ($o) { $optArgs += " --opt $o" } }
    $firstArg = if ($First -gt 0) { "--first $First" } else { '' }
    cmd /d /c "`"$py`" -I -B `"$tools\uci_tb.py`" `"$Exe`" `"$Fens`" `"$base.jsonl`" --tables `"$Tables`" --depth $d --jobs $Jobs $firstArg $optArgs > `"$base.log`" 2>&1"
    Write-Output ("d$d exit $LASTEXITCODE " + (Get-Content "$base.log" -TotalCount 1))
    cmd /d /c "`"$py`" -I -B `"$tools\false_claims.py`" `"$Fens`" `"$Labels`" `"$base.jsonl`" --json `"$base.json`" --list `"$base.false.tsv`""
}
