# setup_oracles.ps1 - job-local test material. Exits by itself. Nothing outside the job root is written.
#  - out\tb\man34: copies of the 3-4 piece tables of D:\syzygy345 (read only), to search 5-man roots above the tables
#    while the full set stays the oracle;
#  - out\oracle\fathom_batch.exe: Fathom (MIT, c9c6fef0, read from the OSS scout's checkout) + the OSS scout's batch tool;
#  - out\src\p6_c1tests: the C1 Syzygy test program and fixtures (aa0b0a83) next to the P6 tree.
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$log = Join-Path $JobOut 'logs\setup_oracles.log'
Set-Content -Path $log -Value ('start ' + (Get-ViennaNow) + ' ' + (Get-JobPinLine))
function L($s) { Add-Content -Path $log -Value $s; Write-Output $s }

$src = 'D:\syzygy345'
$man34 = Join-Path $JobOut 'tb\man34'
New-Item -ItemType Directory -Force -Path $man34 | Out-Null
$n = 0
foreach ($f in Get-ChildItem -LiteralPath $src -File) {
    if ($f.Extension -ne '.rtbw' -and $f.Extension -ne '.rtbz') { continue }
    $stem = $f.BaseName -replace 'v', ''
    if ($stem.Length -le 4) {
        $dst = Join-Path $man34 $f.Name
        if (-not (Test-Path -LiteralPath $dst)) { Copy-Item -LiteralPath $f.FullName -Destination $dst }
        $n++
    }
}
L "man34 files $n"

$fathomSrc = 'C:\opus_5h\oss_scout\dl\fathom'
$fathom = Join-Path $JobOut 'oracle\fathom_src'
New-Item -ItemType Directory -Force -Path $fathom | Out-Null
foreach ($x in 'src\tbprobe.c', 'src\tbprobe.h', 'src\tbchess.c', 'src\tbconfig.h', 'src\stdendian.h', 'LICENSE') {
    $from = Join-Path $fathomSrc $x
    if (Test-Path -LiteralPath $from) { Copy-Item -LiteralPath $from -Destination (Join-Path $fathom (Split-Path -Leaf $x)) -Force }
    else { L "absent $from" }
}
$rev = (cmd /d /c "git -C `"$fathomSrc`" log -1 --format=%H 2>&1")
L "fathom rev $rev"
$batch = Join-Path $JobTmp 't5_fathom_batch.c'
$exe = Join-Path $JobOut 'oracle\fathom_batch.exe'
if (-not (Test-Path -LiteralPath $exe)) {
    cmd /d /c "gcc -O2 -std=c11 -march=x86-64-v3 -I`"$fathom`" `"$batch`" `"$fathom\tbprobe.c`" -static -o `"$exe`" > `"$JobOut\logs\fathom_build.log`" 2>&1"
    L "fathom build exit $LASTEXITCODE"
}
L ('fathom exe sha256 ' + (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash)

$t = Join-Path $JobOut 'src\p6_c1tests'
New-Item -ItemType Directory -Force -Path (Join-Path $t 'forge') | Out-Null
Set-Content -Path (Join-Path $t 'forge\search_options.hpp') -Value '// empty: the P6 port moved these options to forge/search.hpp' -Encoding ASCII
foreach ($x in 'syzygy_tests.cpp', 'syzygy_fixtures.tsv', 'syzygy_reference.tsv') {
    $dst = Join-Path $t $x
    if (-not (Test-Path -LiteralPath $dst)) {
        cmd /d /c "git -c core.autocrlf=false -C `"$JobRepo`" show aa0b0a83:tests/$x > `"$dst`""
    }
}
L ('end ' + (Get-ViennaNow))
