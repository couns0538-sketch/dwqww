# preprocess_diff.ps1 -Parent <tree> -Cand <tree> [-Defines 'A=1,..'] - g++ -E -P of every unit with the kit flags, blank lines removed,
# compared byte for byte. With the candidate macros off the code after preprocessing must be the parent's. Exits 0 if all equal.
param(
    [Parameter(Mandatory = $true)][string]$Parent,
    [Parameter(Mandatory = $true)][string]$Cand,
    [string]$Defines = ''
)
. 'D:\forge_jobs_20261107\opus1\env.ps1'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
$F = '-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1'
foreach ($d in ($Defines -split ',')) { if ($d) { $F += " -D$d" } }
$work = Join-Path $JobTmp ('pp_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $work | Out-Null
$bad = 0
foreach ($unit in Get-ChildItem (Join-Path $Parent 'src') -Filter *.cpp | Sort-Object Name) {
    $u = $unit.BaseName
    foreach ($side in @(@('p', $Parent), @('c', $Cand))) {
        $out = Join-Path $work "$u.$($side[0]).i"
        Push-Location -LiteralPath $side[1]
        cmd /d /c "g++ -E -P $F src/$u.cpp -o `"$out`" 2> `"$out.err`""
        if ($LASTEXITCODE -ne 0) { Write-Output "preprocess failed $u $($side[0])"; $bad++ }
        Pop-Location
    }
    $a = (Get-Content -LiteralPath (Join-Path $work "$u.p.i") | Where-Object { $_.Trim() -ne '' }) -join "`n"
    $b = (Get-Content -LiteralPath (Join-Path $work "$u.c.i") | Where-Object { $_.Trim() -ne '' }) -join "`n"
    if ($a -ceq $b) { Write-Output "same $u ($($a.Length) chars)" } else { Write-Output "DIFF $u"; $bad++ }
}
Write-Output ("preprocess_diff " + $(if ($bad -eq 0) { 'ALL EQUAL' } else { "BAD $bad" }))
exit $(if ($bad -eq 0) { 0 } else { 1 })
