# sanitize_builds.ps1 -Src <tree> -Tag <new tag> [-Defines 'A=1,B=1'] - sanitizer builds of a Forge tree, Idle on CPUs 12-15, never overwrites.
#  UBSan: MSYS2 g++ -fsanitize=undefined -fsanitize-trap=all (engine and tb_root).
#  ASan: MSVC cl /fsanitize=address on a port copy (engine and tb_root), as the speed job: the only source change in the copy gives the TT index of
#        the g++ build through __umulh, because MSVC has no unsigned __int128. Output: out\san\<tag>\{forge_ubsan,tb_root_ubsan,forge_asan,tb_root_asan}.exe
param(
    [Parameter(Mandatory = $true)][string]$Src,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Defines = '',
    [switch]$SkipUbsan,
    [switch]$SkipAsan
)
$ErrorActionPreference = 'Stop'
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$dir = Join-Path $JobOut "san\$Tag"
if (Test-Path -LiteralPath $dir) { Write-Output "refusing: $dir exists"; exit 2 }
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$log = Join-Path $dir 'build.log'
function Say([string]$m) { $l = (Get-ViennaNow) + ' ' + $m; [Console]::Out.WriteLine($l); Add-Content -Path $log -Value $l }
function Run-Cmd([string]$line, [string]$cwd) {
    Add-Content -Path $log -Value "-- $line"
    Push-Location -LiteralPath $cwd
    cmd /d /c "$line >> `"$log`" 2>&1"
    $rc = $LASTEXITCODE
    Pop-Location
    return $rc
}
$tools = Join-Path $JobRepo 'opus_syzygy_gaps\tools'
$defs = @($Defines -split ',' | Where-Object { $_ })
$units = 'bitboard', 'board', 'book', 'eval', 'eval_params', 'nnue', 'search'
try {
    Say ((Get-JobPinLine) + " tag $Tag src $Src defines [$Defines]")
    if (-not $SkipUbsan) {
        $savedPath = $env:PATH
        $env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
        $f = '-std=c++20 -O1 -g -fno-omit-frame-pointer -fsanitize=undefined -fsanitize-trap=all -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -march=znver5 -static -pthread -Iinclude'
        foreach ($d in $defs) { $f += " -D$d" }
        $srcs = ($units | ForEach-Object { "src/$_.cpp" }) -join ' '
        $rc = Run-Cmd "g++ $f $srcs src/uci.cpp -o `"$dir\forge_ubsan.exe`"" $Src
        Say "ubsan engine exit $rc"
        if ($rc -ne 0) { throw 'ubsan engine build failed' }
        $rc = Run-Cmd "g++ $f `"$tools\tb_root.cpp`" $srcs -o `"$dir\tb_root_ubsan.exe`"" $Src
        Say "ubsan tb_root exit $rc"
        if ($rc -ne 0) { throw 'ubsan tb_root build failed' }
        $env:PATH = $savedPath
    }
    if (-not $SkipAsan) {
        $vcv = Get-ChildItem 'C:\Program Files (x86)\Microsoft Visual Studio\*\BuildTools\VC\Auxiliary\Build\vcvars64.bat' -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $vcv) { throw 'vcvars64.bat not found' }
        Say "vcvars $($vcv.FullName)"
        $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $lines = & cmd.exe /d /c "call `"$($vcv.FullName)`" >nul 2>&1 && set"
        $ErrorActionPreference = $eap
        $vcenv = Join-Path $dir 'vcenv.txt'
        Set-Content -Path $vcenv -Value $lines
        foreach ($l in $lines) { $i = $l.IndexOf('='); if ($i -gt 0) { Set-Item -Path ('env:' + $l.Substring(0, $i)) -Value $l.Substring($i + 1) } }
        # vcvars may set TEMP back; the job's TEMP stays
        $env:TEMP = $JobTmp; $env:TMP = $JobTmp
        $port = Join-Path $dir 'port'
        Copy-Item -Recurse -LiteralPath $Src -Destination $port
        Get-ChildItem -Recurse -File $port | ForEach-Object { $_.IsReadOnly = $false }
        $h = Join-Path $port 'include\forge\search.hpp'
        $t = [IO.File]::ReadAllText($h)
        $anchor = "#else`n        return clusters_[static_cast<std::size_t>(key % cluster_count_)];"
        if (([regex]::Matches($t, [regex]::Escape($anchor))).Count -ne 1) { throw 'TT index anchor not found once' }
        $t = $t.Replace($anchor, "#elif defined(_MSC_VER)`n        return clusters_[static_cast<std::size_t>(__umulh(key, static_cast<std::uint64_t>(cluster_count_)))];`n$anchor")
        [IO.File]::WriteAllText($h, ("#ifdef _MSC_VER`n#include <intrin.h>`n#endif`n" + $t), (New-Object Text.UTF8Encoding($false)))
        $common = '/nologo /std:c++20 /EHsc /O2 /Zi /fsanitize=address /arch:AVX512 /DFORGE_NNUE_HIDDEN=256 /DFORGE_EXPOSE_TUNABLES=1 /Iinclude /wd5030 /wd4244 /wd4267 /wd4146 /wd4834'
        foreach ($d in $defs) { $common += " /D$d" }
        if (Select-String -Path (Join-Path $port 'include\forge\*.hpp'), (Join-Path $port 'src\*.cpp') -SimpleMatch '__BMI2__' -List -Quiet) { $common += ' /D__BMI2__=1' }
        $obj1 = Join-Path $dir 'obj_engine'; $obj2 = Join-Path $dir 'obj_root'
        New-Item -ItemType Directory -Force -Path $obj1, $obj2 | Out-Null
        $srcs = (($units + 'uci') | ForEach-Object { "src\$_.cpp" }) -join ' '
        $rc = Run-Cmd "cl $common /Fd`"$dir\engine.compile.pdb`" /Fo`"$obj1\\`" $srcs /Fe`"$dir\forge_asan.exe`" /link /INCREMENTAL:NO /STACK:67108864" $port
        Say "asan engine exit $rc"
        if ($rc -ne 0) { throw 'asan engine build failed' }
        $srcs2 = ($units | ForEach-Object { "src\$_.cpp" }) -join ' '
        $rc = Run-Cmd "cl $common /Fd`"$dir\root.compile.pdb`" /Fo`"$obj2\\`" `"$tools\tb_root.cpp`" $srcs2 /Fe`"$dir\tb_root_asan.exe`" /link /INCREMENTAL:NO /STACK:67108864" $port
        Say "asan tb_root exit $rc"
        if ($rc -ne 0) { throw 'asan tb_root build failed' }
    }
    Say 'done'
    exit 0
} catch {
    Say "FAILED: $($_.Exception.Message)"
    exit 1
}
