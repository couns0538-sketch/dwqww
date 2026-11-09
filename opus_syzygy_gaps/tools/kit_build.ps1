# kit_build.ps1 - LTO+PGO build of a Forge tree: QA's kit v2.3 lines token for token, as in the speed job's
# build_variants.ps1 variant lp_v1 (-Expose default, frozen workload v1, sha256 checked), with this job's placement
# (Idle, CPUs 12-15) and folders. Never overwrites: a new -Tag for each build. Exits by itself.
# usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File kit_build.ps1 -SrcDir <tree> -Tag <new tag> [-Defines 'A=1,B=1'] [-WantSha <sha256>]
param(
    [Parameter(Mandatory = $true)][string]$SrcDir,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Defines = '',
    [string]$WantSha = ''
)
$ErrorActionPreference = 'Stop'
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$x = [Diagnostics.Process]::GetCurrentProcess()
if ([int64]$x.ProcessorAffinity -ne 0xF000 -or $x.PriorityClass -ne [Diagnostics.ProcessPriorityClass]::Idle) { Write-Output 'FAIL pin'; exit 90 }
[Threading.Thread]::CurrentThread.CurrentCulture = [Globalization.CultureInfo]::InvariantCulture
$Kit = 'C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23'
$KitWl = Join-Path $Kit 'workload\frozen_train_cmds.txt'
$WlSha = '1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30'
$Gpp = 'C:\msys64\ucrt64\bin\g++.exe'
$Objdump = 'C:\msys64\ucrt64\bin\objdump.exe'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$Dir = Join-Path $JobOut "builds\$Tag"
if (Test-Path -LiteralPath $Dir) { Write-Output "refusing: $Dir exists"; exit 2 }
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
$log = Join-Path $Dir 'build_log.txt'
function Say([string]$m) { $l = (Get-ViennaNow) + ' ' + $m; [Console]::Out.WriteLine($l); Add-Content -Path $log -Value $l }
function Invoke-Gpp([string]$What, [string]$StageLog, [object[]]$GppArgs) {
    Add-Content -Path $StageLog -Value ("-- $What : g++ " + ($GppArgs -join ' '))
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $o = @(& $Gpp @GppArgs 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE } finally { $ErrorActionPreference = $eap }
    foreach ($l in $o) { Add-Content -Path $StageLog -Value $l }
    if ($rc -ne 0) { throw "g++ failed ($What), exit $rc; see $StageLog" }
}
try {
    Say ((Get-JobPinLine) + " tag $Tag src $SrcDir defines [$Defines]")
    $tree = Join-Path $Dir 'src_copy'
    Copy-Item -Recurse -LiteralPath $SrcDir -Destination $tree
    Get-ChildItem -Recurse -File $tree | ForEach-Object { $_.IsReadOnly = $false }
    Push-Location $tree
    $units = @(Get-ChildItem src -Filter *.cpp | Sort-Object Name | ForEach-Object { $_.BaseName })
    $F = @('-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread', '-Iinclude', '-DFORGE_EXPOSE_TUNABLES=1')
    foreach ($d in ($Defines -split ',')) { if ($d) { $F += ('-D' + $d) } }
    $L = @('-flto=1', '-fuse-linker-plugin')
    $gver = (& $Gpp --version | Select-Object -First 1)
    Say "compiler $gver units $($units -join ' ')"
    $objDir = 'obj_ltopgo'
    $P2 = Join-Path $tree 'pgo_profile_lto'
    New-Item -ItemType Directory $P2, $objDir -Force | Out-Null
    $genLog = Join-Path $Dir 'build_gen.log'
    $useLog = Join-Path $Dir 'build_use.log'
    foreach ($u in $units) { Invoke-Gpp "gen $u" $genLog (@($F) + $L + "-fprofile-generate=$P2" + '-fprofile-update=single' + '-c' + "src/$u.cpp" + '-o' + "$objDir/$u.o") }
    Invoke-Gpp 'gen link' $genLog (@($F) + $L + "-fprofile-generate=$P2" + '-static' + @((Get-ChildItem "$objDir\*.o").FullName) + '-o' + 'forge_instr.exe')
    Say 'instrumented exe built; training'
    $wl = Join-Path $tree 'frozen_train_cmds.txt'
    Copy-Item -LiteralPath $KitWl -Destination $wl
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $wl).Hash.ToLower() -ne $WlSha) { throw 'frozen workload sha256 mismatch' }
    $out = Join-Path $tree 'train_out.txt'
    cmd /d /c "`"$tree\forge_instr.exe`" < `"$wl`" > `"$out`" 2> `"$out.stderr.txt`""
    if ($LASTEXITCODE -ne 0) { throw "training exit $LASTEXITCODE" }
    $n = @(Select-String -Path $out -Pattern 'bench depth').Count
    if ($n -ne 3) { throw "training gave $n bench lines (want 3)" }
    Say ('training done: ' + ((Select-String -Path $out -Pattern 'bench depth' | ForEach-Object { $_.Line }) -join ' | '))
    $gc = @(Get-ChildItem $P2 -Filter *.gcda -Recurse).Count
    if ($gc -ne $units.Count) { throw "gcda count $gc != units $($units.Count)" }
    foreach ($u in $units) {
        Remove-Item -LiteralPath "$objDir/$u.o"
        Invoke-Gpp "use $u" $useLog (@($F) + $L + "-fprofile-use=$P2" + '-fprofile-correction' + '-Wmissing-profile' + '-c' + "src/$u.cpp" + '-o' + "$objDir/$u.o")
    }
    $exe = Join-Path $Dir "forge_$Tag.exe"
    Invoke-Gpp 'use link' $useLog (@($F) + $L + "-fprofile-use=$P2" + '-fprofile-correction' + '-Wmissing-profile' + '-static' + '-Wl,--no-insert-timestamp' + @((Get-ChildItem "$objDir\*.o").FullName) + '-o' + $exe)
    $useLines = @(Get-Content $useLog | Where-Object { $_ -notlike '-- *' })
    $miss = @($useLines | Where-Object { $_ -match 'warning:' -and $_ -match 'Wmissing-profile|profile count data|coverage mismatch|Wcoverage-mismatch' }).Count
    if ($miss -ne 0) { throw "missing-profile warnings: $miss" }
    foreach ($u in $units) { $s = @(& $Objdump -h "$objDir/$u.o" | Select-String '\.gnu\.lto_'); if ($s.Count -eq 0) { throw "$u.o has no LTO IR" } }
    $fma = @(& $Objdump -d $exe | Select-String 'vfmadd').Count
    if ($fma -ne 0) { throw "vfmadd count $fma (lock rule: 0)" }
    $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash
    $md5 = (Get-FileHash -Algorithm MD5 -LiteralPath $exe).Hash
    Pop-Location
    Say "EXE $exe sha256 $sha md5 $md5 vfmadd 0 gcda $gc missing-profile 0"
    Set-Content -Path (Join-Path $Dir 'SUMMARY.txt') -Value @("tag $Tag", "source $SrcDir", "defines [$Defines]", "compiler $gver", "flags g++ $(($F + $L) -join ' ')", "exe $exe", "sha256 $sha", "md5 $md5")
    if ($WantSha) {
        if ($sha -eq $WantSha.ToUpper()) { Say "BYTE-IDENTICAL to $WantSha"; Write-Output 'IDENTITY PASS'; exit 0 }
        Say "DIFFERS from $WantSha"; Write-Output 'IDENTITY FAIL'; exit 3
    }
    exit 0
} catch {
    Say "FAILED: $($_.Exception.Message)"
    Set-Content -Path (Join-Path $Dir 'FAILED') -Value $_.Exception.Message
    exit 1
}
