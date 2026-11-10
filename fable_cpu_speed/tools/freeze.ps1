# freeze.ps1 - identify and freeze the inputs of job fable4cpu (PowerShell 5.1, ASCII only).
# Reads outside the job folder, writes only inside it. Pins itself to 0x707F at BelowNormal first.
param([string]$Log = 'D:\forge_jobs_20261110\fable4cpu\repo\fable_cpu_speed\evidence\logs\freeze.log')
$ErrorActionPreference = 'Stop'
$env:PSModulePath = "$env:ProgramFiles\WindowsPowerShell\Modules;$env:WINDIR\system32\WindowsPowerShell\v1.0\Modules"
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]0x707F
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
$me.Refresh()
$J = 'D:\forge_jobs_20261110\fable4cpu'
$Repo = "$J\repo"   # not $R: PowerShell names are case-insensitive and a loop below uses $r
function Sha([string]$p) { $a = [System.Security.Cryptography.SHA256]::Create(); $s = [System.IO.File]::OpenRead($p); try { ([BitConverter]::ToString($a.ComputeHash($s))).Replace('-', '').ToLower() } finally { $s.Dispose(); $a.Dispose() } }
function Md5([string]$p) { $a = [System.Security.Cryptography.MD5]::Create(); $s = [System.IO.File]::OpenRead($p); try { ([BitConverter]::ToString($a.ComputeHash($s))).Replace('-', '').ToLower() } finally { $s.Dispose(); $a.Dispose() } }
# Vienna time: the PC's UTC clock runs 25159.3 s ahead of github.com's Date header (measured at the clone).
function NowV { ([DateTime]::UtcNow.AddSeconds(-25159.3).AddHours(1)).ToString('yyyy-MM-dd HH:mm:ss') + ' Vienna' }
$L = New-Object 'System.Collections.Generic.List[string]'
function Say([string]$s) { $L.Add($s); [Console]::Out.WriteLine($s) }
$bad = 0
function Check([string]$what, [string]$got, [string]$want) {
    if ($got -eq $want) { Say ("OK    $what = $got") } else { Say ("DIFF  $what got $got want $want"); $script:bad++ }
}
New-Item -ItemType Directory -Force -Path (Split-Path $Log -Parent), "$J\out\base", "$Repo\fable_cpu_speed\tests" | Out-Null
Say ('FREEZE ' + (NowV) + '; script freeze.ps1 sha256 ' + (Sha $PSCommandPath))
Say (('self affinity=0x{0:X} priority={1}' -f [int64]$me.ProcessorAffinity, $me.PriorityClass))

# 1) lock exe: verify the original, copy once, verify the copy
$lockSrc = 'C:\Users\Administrator\grok-pc\forge_push\bin\forge_clang_combo29_trial_w6.exe'
$lockDst = "$J\out\base\combo29_lock.exe"
Check 'lock exe (original) md5' (Md5 $lockSrc) 'c0051c99695f48bf93272d96fe7548c3'
Check 'lock exe (original) sha256' (Sha $lockSrc) 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e'
if (-not (Test-Path -LiteralPath $lockDst)) { Copy-Item -LiteralPath $lockSrc -Destination $lockDst }
Check "lock exe copy $lockDst md5" (Md5 $lockDst) 'c0051c99695f48bf93272d96fe7548c3'
Check 'lock exe copy sha256' (Sha $lockDst) 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e'

# 2) training workload of the lock recipe and the 12,000-position file (from my job-3 folder, read only)
$b3 = 'D:\forge_jobs_20261109\fable2\out\base'
$wl = "$J\out\base\frozen_train_cmds.txt"
if (-not (Test-Path -LiteralPath $wl)) { Copy-Item -LiteralPath "$b3\frozen_train_cmds.txt" -Destination $wl }
Check 'training workload sha256' (Sha $wl) '1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30'
$fens = "$Repo\fable_cpu_speed\tests\fens_12k_v2.txt"
if (-not (Test-Path -LiteralPath $fens)) { Copy-Item -LiteralPath "$b3\fens_12k_v2.txt" -Destination $fens }
$nl = ([System.IO.File]::ReadAllLines($fens) | Where-Object { $_.Trim() -ne '' }).Count
Check 'corpus fens_12k_v2.txt positions' "$nl" '12000'
Check 'corpus equals job-3 copy (sha256)' (Sha $fens) (Sha "$b3\fens_12k_v2.txt")
Say ('corpus sha256 ' + (Sha $fens) + ' md5 ' + (Md5 $fens) + ' bytes ' + (Get-Item -LiteralPath $fens).Length)

# 3) source manifest of the clone in QA's format (sha256, two spaces, forward-slash path, LF, ordinal order)
$Src = "$Repo\forge-combo29"
Say ('source folder entries: ' + ((Get-ChildItem -LiteralPath $Src -Force | ForEach-Object { $_.Name }) -join ', '))
$files = @(Get-ChildItem -LiteralPath (Join-Path $Src 'include') -Recurse -File) + @(Get-ChildItem -LiteralPath (Join-Path $Src 'src') -Recurse -File)
$rels = New-Object 'System.Collections.Generic.List[string]'
foreach ($f in $files) { $rels.Add($f.FullName.Substring($Src.Length + 1).Replace('\', '/')) }
$relArr = $rels.ToArray(); [Array]::Sort($relArr, [StringComparer]::Ordinal)
$sb = New-Object System.Text.StringBuilder
foreach ($r in $relArr) { [void]$sb.Append((Sha (Join-Path $Src $r.Replace('/', '\'))) + '  ' + $r + "`n") }
$manifestPath = "$J\out\base\SOURCE_INPUTS.sha256"
[System.IO.File]::WriteAllText($manifestPath, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
$mSha = Sha $manifestPath
Say ("source files in manifest: $($relArr.Count); manifest $manifestPath")
$receipt = [System.IO.File]::ReadAllText('D:\forge-qa\pack_combo29_20261108\pc_payload\build\RUN_RECEIPT.json')
$want = ''
if ($receipt -match '"source_manifest_sha256"\s*:\s*"([0-9a-fA-F]{64})"') { $want = $Matches[1].ToLower() }
Check 'source manifest sha256 vs lock RUN_RECEIPT.json' $mSha $want
Check 'source manifest sha256 vs job-3 snapshot manifest' $mSha (Sha "$b3\SOURCE_INPUTS.sha256")

# 4) compiler of the lock recipe
$lm = 'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'
Check 'clang++.exe sha256' (Sha "$lm\clang++.exe") 'd05fee2c3f79b15d998d3c3413c76aabd416ec789edff89c8f698a8be44a3970'
Check 'llvm-profdata.exe sha256' (Sha "$lm\llvm-profdata.exe") '55bfe8da39b548fb8b03736218c669aaec5234a14d964d4da323d7d4103b5e32'

# 5) git identity of the clone (git runs only inside the repo folder)
$env:GIT_NO_LAZY_FETCH = '1'
Push-Location $Repo
try {
    $git = 'C:\Program Files\Git\cmd\git.exe'
    $pc = (& $git config --get extensions.partialclone); if (-not $pc) { $pc = '(unset)' }
    Check 'git extensions.partialclone' "$pc" '(unset)'
    Check 'git HEAD' (& $git rev-parse HEAD) '16833ecc03b425586f91f4c8834dea8807bf4c22'
    Say ('git branch ' + (& $git rev-parse --abbrev-ref HEAD) + '; shallow ' + (& $git rev-parse --is-shallow-repository))
    $dirty = @(& $git status --porcelain -- forge-combo29).Count
    Check 'git status --porcelain -- forge-combo29 (lines)' "$dirty" '0'
} finally { Pop-Location }
Say ('D: free {0:N2} GiB' -f ((New-Object System.IO.DriveInfo('D')).AvailableFreeSpace / 1GB))
if ($bad -eq 0) { Say 'VERDICT FREEZE PASS (every check OK)' } else { Say "VERDICT FREEZE FAIL ($bad checks differ)" }
[System.IO.File]::WriteAllLines($Log, $L.ToArray(), [System.Text.Encoding]::ASCII)
if ($bad -ne 0) { exit 1 }
exit 0
