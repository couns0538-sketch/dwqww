# run_san.ps1 -Tag <san tag> [-Jobs 2] - runs of the sanitizer builds. Any report ends the program with a non-zero exit (halt_on_error, trap), which is logged.
# tb_root (heap copies under ASan) on all root fixtures; the engine: bench, then root fixtures and 5-man roots above the tables, switches off and all on.
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [int]$Jobs = 2
)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$dir = Join-Path $JobOut "san\$Tag"
$runs = Join-Path $dir 'runs'
New-Item -ItemType Directory -Force -Path $runs | Out-Null
$sum = Join-Path $runs 'SUMMARY.txt'
Add-Content -Path $sum -Value ('start ' + (Get-ViennaNow) + ' ' + (Get-JobPinLine))
foreach ($l in Get-Content (Join-Path $dir 'vcenv.txt')) { $i = $l.IndexOf('='); if ($i -gt 0) { Set-Item -Path ('env:' + $l.Substring(0, $i)) -Value $l.Substring($i + 1) } }
$env:TEMP = $JobTmp; $env:TMP = $JobTmp
$env:ASAN_OPTIONS = 'halt_on_error=1:detect_leaks=0'
$py = 'C:\Python315\python.exe'
$tools = Join-Path $JobRepo 'opus_syzygy_gaps\tools'
$fixtures = @{ clock = 'exp\root\clock.fens'; promo = 'exp\special\s1.promo.fens'; ep = 'exp\special\s1.ep.fens'; rep = 'exp\special\s1.rep.fens'; castle = 'exp\special\s1.castle.fens'; clock100 = 'exp\special\s1.clock100.fens' }
$on = 'SyzygyTbBounds=7 SyzygyRootExact=1 SyzygyRule50=3'
$onArgs = '--opt SyzygyTbBounds=7 --opt SyzygyRootExact=1 --opt SyzygyRule50=3'
function Log($name, $rc) { Add-Content -Path $sum -Value ("$name exit $rc " + (Get-ViennaNow)) }
foreach ($k in $fixtures.Keys) {
    $fen = Join-Path $JobOut $fixtures[$k]
    $env:TB_HEAP = '1'
    cmd /d /c "`"$dir\tb_root_asan.exe`" D:\syzygy345 `"$fen`" 1 $on > `"$runs\root_asan_$k.out`" 2> `"$runs\root_asan_$k.err`""
    Log "tb_root_asan heap $k" $LASTEXITCODE
    Remove-Item Env:TB_HEAP
    cmd /d /c "`"$dir\tb_root_ubsan.exe`" D:\syzygy345 `"$fen`" 1 $on > `"$runs\root_ubsan_$k.out`" 2> `"$runs\root_ubsan_$k.err`""
    Log "tb_root_ubsan $k" $LASTEXITCODE
}
foreach ($v in 'asan', 'ubsan') {
    $exe = Join-Path $dir "forge_$v.exe"
    Set-Content -Path "$runs\bench_in.txt" -Value @('uci', 'isready', 'bench 13', 'isready', 'quit')
    cmd /d /c "`"$exe`" < `"$runs\bench_in.txt`" > `"$runs\bench_$v.out`" 2> `"$runs\bench_$v.err`""
    Log "bench 13 $v $((Select-String -Path "$runs\bench_$v.out" -Pattern 'bench depth').Line)" $LASTEXITCODE
    foreach ($mode in 'off', 'on') {
        $opt = if ($mode -eq 'on') { $onArgs } else { '' }
        foreach ($k in 'clock', 'promo', 'ep', 'rep') {
            $fen = Join-Path $JobOut $fixtures[$k]
            cmd /d /c "`"$py`" -I -B `"$tools\uci_tb.py`" `"$exe`" `"$fen`" `"$runs\uci_${v}_${mode}_$k.jsonl`" --tables D:\syzygy345 --depth 4 --first 1500 --jobs $Jobs $opt > `"$runs\uci_${v}_${mode}_$k.log`" 2>&1"
            Log "uci $v $mode $k $(Get-Content "$runs\uci_${v}_${mode}_$k.log" -TotalCount 1)" $LASTEXITCODE
        }
        $fen = Join-Path $JobOut 'exp\e1\roots200k.fens'
        cmd /d /c "`"$py`" -I -B `"$tools\uci_tb.py`" `"$exe`" `"$fen`" `"$runs\uci_${v}_${mode}_above.jsonl`" --tables $JobOut\tb\man34 --depth 7 --first 1500 --jobs $Jobs $opt > `"$runs\uci_${v}_${mode}_above.log`" 2>&1"
        Log "uci $v $mode above $(Get-Content "$runs\uci_${v}_${mode}_above.log" -TotalCount 1)" $LASTEXITCODE
    }
}
Add-Content -Path $sum -Value ('end ' + (Get-ViennaNow))
