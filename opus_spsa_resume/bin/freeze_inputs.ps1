# freeze_inputs.ps1 - copy every pinned input of the job into <Out>\freeze (read-only sources, never modified),
# verify each against the identity recorded at planning time, and write FREEZE.json + MD5/SHA256 manifests.
# Windows PowerShell 5.1:  powershell.exe -NoProfile -ExecutionPolicy Bypass -File freeze_inputs.ps1
#   [-Out D:\forge_jobs_20261107\opus3\out] [-PackDir <repo>\opus_spsa_resume]
# Fails closed: any mismatch throws and FREEZE.json is not written. Refuses to overwrite an existing freeze.
param(
    [string]$Out = 'D:\forge_jobs_20261107\opus3\out',
    [string]$PackDir = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]0xF000; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne 0xF000 -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
$free = [Math]::Round((Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'").FreeSpace / 1GB, 3)
if ($free - 0.05 -lt 30) { throw "PENDING RESOURCE: D: free $free GiB" }

$fz = Join-Path $Out 'freeze'
if (Test-Path -LiteralPath (Join-Path $fz 'FREEZE.done')) { throw "refusing: $fz already frozen" }
New-Item -ItemType Directory -Force -Path $fz | Out-Null

$sdk = 'D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29'
$fp = 'C:\Users\Administrator\grok-pc\forge_push'
$g4 = Join-Path $fp 'sdk_speedonly_20261107\gate0415'
# name, source, expected sha256 (lower case; $null = record only), destination (relative to freeze)
$items = @(
    @('lock_exe', (Join-Path $fp 'bin\forge_clang_combo29_trial_w6.exe'), 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e', 'parent\forge_clang_combo29_trial_w6.exe'),
    @('lock_exe_lockdir', (Join-Path $fp 'locks\lock_combo29_clang_trial_w6_20261108\forge_clang_combo29_trial_w6.exe'), 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e', $null),
    @('lock_build_exe', (Join-Path $sdk 'm2use\forge_m2use.exe'), 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e', $null),
    @('run_receipt', (Join-Path $sdk 'RUN_RECEIPT.json'), $null, 'parent\RUN_RECEIPT.json'),
    @('source_manifest', (Join-Path $sdk 'SOURCE_INPUTS.sha256'), '3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645', 'parent\SOURCE_INPUTS.sha256'),
    @('build_log', (Join-Path $sdk 'build.log'), $null, 'parent\build.log'),
    @('lock_profdata', (Join-Path $sdk 'm2gen\m2.profdata'), 'c5d97fc7a94da332f3bb0c7a0b284c8afce5f2d71649f1f8d156282b5204110e', 'parent\m2.profdata'),
    @('workload', (Join-Path $sdk 'm2gen\frozen_train_cmds.txt'), '1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30', 'recipe\frozen_train_cmds.txt'),
    @('recipe', (Join-Path $g4 'detached1735_all31\adapter\clang_build.ps1'), '1fd8751755356c8a0ba386b48c1bc643401bcdeadf8e91cc5e7e5450d7584bfe', 'recipe\clang_build_1fd87517.ps1'),
    @('current_lock_json', (Join-Path $fp 'locks\CURRENT_LOCK.json'), $null, 'parent\CURRENT_LOCK.json.readonly_copy'),
    @('fens12k', 'D:\forge_qa\smp_c29_20261109\data\fens_12k_v2.txt', 'c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265', 'data\fens_12k_v2.txt'),
    @('book_8moves_v3', 'C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn', '5835239f88cc2c7511b177c32392a69f3ede21819cf0616f80a7f907cd21d17e', 'data\8moves_v3.pgn'),
    @('fastchess', 'C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe', 'c6d7e4458a58025983c81bf38c524cb213e6f27559657dcfd72543392a431a71', $null),
    @('qa_warm_identity_py', (Join-Path $g4 'warm_identity.py'), $null, 'qa_tools\warm_identity.py'),
    @('qa_soak_py', (Join-Path $g4 'soak.py'), $null, 'qa_tools\soak.py'),
    @('qa_ref_sig', (Join-Path $g4 'refcache\4181a589\sig_4181a5893f15e732.json'), $null, 'qa_refcache\sig_4181a5893f15e732.json'),
    @('qa_ref_fens_on', (Join-Path $g4 'refcache\4181a589\fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-true_Threads-1_Hash-16.tsv'), $null, 'qa_refcache\fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-true_Threads-1_Hash-16.tsv'),
    @('qa_ref_fens_off', (Join-Path $g4 'refcache\4181a589\fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-false_Threads-1_Hash-16.tsv'), $null, 'qa_refcache\fens_e7dbf2c8_n12000_d13_ob0_UseNNUE-false_Threads-1_Hash-16.tsv')
)
$rows = New-Object System.Collections.Generic.List[object]
foreach ($it in $items) {
    $name, $src, $want, $dst = $it
    if (-not (Test-Path -LiteralPath $src)) { throw "missing input $name : $src" }
    $sha = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower()
    $md5 = (Get-FileHash -LiteralPath $src -Algorithm MD5).Hash.ToLower()
    if ($want -and $sha -ne $want) { throw "HOLD: $name sha256 $sha != pinned $want" }
    $rel = $null
    if ($dst) {
        $target = Join-Path $fz $dst
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
        Copy-Item -LiteralPath $src -Destination $target
        $s2 = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower()
        if ($s2 -ne $sha) { throw "HOLD: copy of $name changed in transit" }
        (Get-Item -LiteralPath $target).IsReadOnly = $true
        $rel = $dst.Replace('\', '/')
    }
    $rows.Add([ordered]@{ name = $name; source = $src; bytes = (Get-Item -LiteralPath $src).Length; md5 = $md5; sha256 = $sha; pinned = [bool]$want; copy = $rel })
}
# The parent source tree: copy the snapshot and verify every file against the build's own manifest.
$snapSrc = Join-Path $sdk 'source_snapshot'
$snapDst = Join-Path $fz 'parent\source_snapshot'
Copy-Item -LiteralPath $snapSrc -Destination $snapDst -Recurse
$manifest = @{}
foreach ($line in [IO.File]::ReadAllLines((Join-Path $fz 'parent\SOURCE_INPUTS.sha256'))) {
    if (-not $line.Trim()) { continue }
    $h, $p = $line -split '  ', 2
    $manifest[$p] = $h
}
$seen = 0
foreach ($f in Get-ChildItem -LiteralPath $snapDst -Recurse -File) {
    $rel = $f.FullName.Substring($snapDst.Length + 1).Replace('\', '/')
    if (-not $manifest.ContainsKey($rel)) { throw "HOLD: snapshot file not in manifest: $rel" }
    $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLower()
    if ($h -ne $manifest[$rel]) { throw "HOLD: snapshot $rel sha256 $h != manifest" }
    $f.IsReadOnly = $true
    $seen++
}
if ($seen -ne $manifest.Count) { throw "HOLD: snapshot has $seen files, manifest $($manifest.Count)" }

$freeze = [ordered]@{
    schema = 'opus3-freeze/1'
    note = 'Inputs copied read-only into the job root; sources were never modified. Pinned items were checked against the identities recorded during planning.'
    parent = [ordered]@{
        exe = 'forge_clang_combo29_trial_w6.exe'
        exe_md5 = 'c0051c99695f48bf93272d96fe7548c3'
        exe_sha256 = 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e'
        source_snapshot_files = $seen
        source_manifest_sha256 = '3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645'
        net = 'embedded src/nnue_weights.inc sha256 a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638 (CURRENT_LOCK net_md5 22B4B9E2C61B37C0450F13A3A92C19B3)'
        pins_on = @(312866, 862329, 3024920, 12389307, 34048354)
        pins_off = @(375354, 907205, 2448617, 13573040, 24506465)
        perft5_startpos = 4865609
        perft5_kiwipete = 193690690
    }
    items = $rows
}
$fj = Join-Path $PackDir 'evidence\FREEZE.json'
[IO.File]::WriteAllText($fj, ($freeze | ConvertTo-Json -Depth 6) + "`n")   # UTF-8 without BOM
$md5Lines = @(); $shaLines = @()
foreach ($f in Get-ChildItem -LiteralPath $fz -Recurse -File | Sort-Object FullName) {
    $rel = $f.FullName.Substring($fz.Length + 1).Replace('\', '/')
    $md5Lines += (Get-FileHash -LiteralPath $f.FullName -Algorithm MD5).Hash.ToLower() + '  ' + $rel
    $shaLines += (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLower() + '  ' + $rel
}
[IO.File]::WriteAllText((Join-Path $PackDir 'evidence\FREEZE_FILES.md5'), ($md5Lines -join "`n") + "`n")
[IO.File]::WriteAllText((Join-Path $PackDir 'evidence\FREEZE_FILES.sha256'), ($shaLines -join "`n") + "`n")
Set-Content -LiteralPath (Join-Path $fz 'FREEZE.done') -Value ('frozen; files=' + $md5Lines.Count)
"FREEZE OK: $($rows.Count) identities, snapshot $seen files, $($md5Lines.Count) frozen files under $fz"
