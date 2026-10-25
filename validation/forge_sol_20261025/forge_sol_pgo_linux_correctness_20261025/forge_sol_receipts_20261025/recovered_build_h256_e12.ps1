# build_h256_e12.ps1 - copy of build_packb_epa.ps1 for fc_nnue_h256_e12_ep12_ep10base (ep10 tree + Engine NNUE run e epoch 12 H256 net md5 6d22f612; ONLY src\nnue_weights.inc differs; needs -DFORGE_NNUE_HIDDEN=256).
# Direct g++ (NOT CMake) with the FULL standard flag set of the ep10 exe + -DFORGE_NNUE_HIDDEN=256. Source zip h256_e12_src.zip = CR's 73-file manifest (CR_PASS_nnue_h256_e12_ep12_ep10base_sources.sha256), every file sha256-checked after extraction.
# One g++ at a time, BelowNormal. Never kills anything. No GPU. Judges success by exe existence + bench.
$ErrorActionPreference='Stop'
$fp='C:\Users\Administrator\grok-pc\forge_push'
$out='D:\grok-pc-data\forge_push\nnue_cand'
$gpp='C:\msys64\ucrt64\bin\g++.exe'
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
[Environment]::CurrentDirectory='C:\'
try{ [System.Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal' }catch{}
$name='h256_e12'
$report="$out\build_$name.log"
"" | Set-Content $report
function L($m){ Add-Content -LiteralPath $report -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $m" }
function Bench($exe,$d,$opts=@()){
  $psi=New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName=$exe; $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
  $bp=[System.Diagnostics.Process]::Start($psi)
  try{ $bp.PriorityClass='BelowNormal' }catch{}
  foreach($l in (@('uci','setoption name Threads value 1','setoption name Hash value 16','setoption name OwnBook value false')+$opts+@('isready',"bench $d",'quit'))){ $bp.StandardInput.WriteLine($l) }
  $txt=$bp.StandardOutput.ReadToEnd(); $bp.WaitForExit()
  $m=[regex]::Match($txt,'bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)')
  if(-not $m.Success){ L "BENCH $d no parse: $txt"; return -1 }
  L "bench d$d nodes $($m.Groups[2].Value) time_ms $($m.Groups[3].Value) nps $($m.Groups[4].Value)  [$(Split-Path $exe -Leaf)]"
  return [int64]$m.Groups[2].Value
}
$expBase=@{11=315955;13=851522}
$expCand=@{11=308972;13=745494}
$baseExe="$fp\bin\forge_nnue_ep10.exe"
L "BASE exe sha256 $((Get-FileHash $baseExe -Algorithm SHA256).Hash)"
if((Get-FileHash $baseExe -Algorithm SHA256).Hash -ne '42D387C646498F07B9A991152C27D995A74E54CCFE4754F4F880451DFD995B0B'){ L "STOP: base exe sha mismatch"; "BASE_SHA_MISMATCH" | Set-Content "$out\build_$name.STATUS"; exit 2 }
$baseOk=$true
foreach($d in 11,13){ $n=Bench $baseExe $d; if($n -ne $expBase[$d]){ $baseOk=$false; L "BASE MISMATCH d$d got $n want $($expBase[$d])" } }
if(-not $baseOk){ L "STOP: baseline ep10 exe bench != CR/Coder. Not building."; "BASE_MISMATCH" | Set-Content "$out\build_$name.STATUS"; exit 2 }
L "BASE BENCH MATCH d11/13 (315955/851522)"
if(@(Get-Process -Name g++,cc1plus,collect2 -ErrorAction SilentlyContinue).Count -gt 0){ L "another g++ is running; not building"; "BLOCKED_GPP" | Set-Content "$out\build_$name.STATUS"; exit 3 }
$tree="$fp\src_h256_e12"
if(Test-Path $tree){Remove-Item -Recurse -Force $tree}
New-Item -ItemType Directory -Force $tree | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("$fp\h256_e12_src.zip",$tree)
# sha256 of EVERY file vs CR's 73-line manifest (lowercase hex, "hash  relative/path")
$exp=@{}
foreach($ln in Get-Content "$fp\h256_e12_sources.sha256"){ if($ln.Trim().Length -eq 0){continue}; $parts=$ln -split '\s+',2; $exp[($parts[1].Trim() -replace '/','\')]=$parts[0].ToUpper() }
L "manifest entries: $($exp.Count) (expected 73)"
$bad=0; $cnt=0
foreach($f in Get-ChildItem -Recurse -File $tree){
  $rel=$f.FullName.Substring($tree.Length+1); $a=(Get-FileHash $f.FullName -Algorithm SHA256).Hash; $cnt++
  if(-not $exp.ContainsKey($rel)){ $bad++; L "UNEXPECTED file $rel"; continue }
  if($exp[$rel] -ne $a){ $bad++; L "SHA256 MISMATCH $rel got $a want $($exp[$rel])" }
}
foreach($k in $exp.Keys){ if(-not (Test-Path "$tree\$k")){ $bad++; L "MISSING $k" } }
L "source sha256 check: $cnt files, $bad problems (expected 73 files, 0 problems)"
$inc=(Get-FileHash "$tree\src\nnue_weights.inc" -Algorithm SHA256).Hash
$m=(Get-FileHash "$tree\src\nnue_weights.inc" -Algorithm MD5).Hash
L "nnue_weights.inc sha256 $inc ; md5 $m"
if($bad -ne 0 -or $cnt -ne 73 -or $exp.Count -ne 73 -or $inc -ne '74C4009D86B7D3A5AE9E6119D0890E5B923508F4063161BB4BC1539AAB275B1B' -or $m -ne '6D22F612C855E17C62D396D32DA99EA4'){ L "STOP: hash mismatch"; "HASH_MISMATCH" | Set-Content "$out\build_$name.STATUS"; exit 4 }
# the 20 compile files vs the verified ep10 PC tree: expected exactly ONE difference, src\nnue_weights.inc
$ref='D:\grok-pc-data\forge_push\cand\fc_ep10_1ab50b2d'
$diff=0; $cmp=0
foreach($rel in @($exp.Keys | Where-Object { $_ -like 'include\*' -or $_ -like 'src\*' } | Sort-Object)){
  $cmp++
  if((Get-FileHash "$tree\$rel").Hash -ne (Get-FileHash "$ref\$rel").Hash){ $diff++; L "DIFF vs PC ep10 tree: $rel" }
}
L "tree compare: $cmp compile files, $diff differ from PC ep10 tree (expected 20 compared, exactly src\nnue_weights.inc differs)"
if($cmp -ne 20 -or $diff -ne 1 -or ((Get-FileHash "$tree\src\nnue_weights.inc").Hash -eq (Get-FileHash "$ref\src\nnue_weights.inc").Hash)){ L "STOP: unexpected diff"; "TREE_DIFF_UNEXPECTED" | Set-Content "$out\build_$name.STATUS"; exit 4 }
$flags='-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread'
$srcs='src/bitboard.cpp','src/board.cpp','src/book.cpp','src/eval.cpp','src/eval_params.cpp','src/nnue.cpp','src/search.cpp','src/uci.cpp'
$exeName='forge_h256_e12.exe'
$argline="$flags -Iinclude $($srcs -join ' ') -o $exeName"
L "BUILD g++ $argline"
L "g++ version: $((& $gpp --version | Select-Object -First 1))"
$p=Start-Process -FilePath $gpp -ArgumentList $argline -WorkingDirectory $tree -NoNewWindow -PassThru -RedirectStandardOutput "$tree\build.out" -RedirectStandardError "$tree\build.err"
$null=$p.Handle
try{ $p.PriorityClass='BelowNormal' }catch{}
$p.WaitForExit(); $p.WaitForExit()
L "g++ exit code: [$($p.ExitCode)] (judging by exe existence + bench)"
$exe="$tree\$exeName"
if(-not (Test-Path $exe)){ L "BUILD FAILED: exe missing"; "BUILD_FAILED" | Set-Content "$out\build_$name.STATUS"; exit 5 }
Copy-Item $exe "$fp\bin\$exeName" -Force
Copy-Item $exe "$out\$exeName" -Force
Copy-Item "$tree\build.err" "$out\build_$name.stderr.txt" -Force
$sha=(Get-FileHash "$fp\bin\$exeName" -Algorithm SHA256).Hash
L "OK $name exe sha256 $sha"
"$sha *$exeName" | Set-Content "$out\$exeName.SHA256"
$allok=$true
foreach($d in 11,13){ $n=Bench "$fp\bin\$exeName" $d @(); if($n -eq $expCand[$d]){ L "CAND d$d MATCH CR $n" } else { $allok=$false; L "CAND d$d MISMATCH got $n want $($expCand[$d])" } }
# second, alternating nps pass (noise note: gates are running concurrently on this PC)
foreach($i in 1,2){ $null=Bench $baseExe 13; $null=Bench "$fp\bin\$exeName" 13 }
# check_nnue_simd on the exe (needs python + objdump; objdump from MSYS2 ucrt64 on PATH)
$ErrorActionPreference='Continue'
try{
  $r=& 'C:\Python314\python.exe' "$tree\tools\check_nnue_simd.py" $exe 2>&1 | Out-String
  L "check_nnue_simd (exe, exit $LASTEXITCODE): $($r.Trim())"
  $simdExe=$r
}catch{ L "check_nnue_simd on exe failed to run: $_"; $simdExe='ERR' }
# also on a separately compiled nnue.o with the same flags (fallback if the exe has no unstripped evaluate symbol)
$oargs="$flags -Iinclude -c src/nnue.cpp -o nnue_h256.o"
$p2=Start-Process -FilePath $gpp -ArgumentList $oargs -WorkingDirectory $tree -NoNewWindow -PassThru -RedirectStandardOutput "$tree\obj.out" -RedirectStandardError "$tree\obj.err"
$null=$p2.Handle; try{ $p2.PriorityClass='BelowNormal' }catch{}; $p2.WaitForExit(); $p2.WaitForExit()
if(Test-Path "$tree\nnue_h256.o"){
  try{ $r2=& 'C:\Python314\python.exe' "$tree\tools\check_nnue_simd.py" "$tree\nnue_h256.o" 2>&1 | Out-String; L "check_nnue_simd (nnue.o same flags, exit $LASTEXITCODE): $($r2.Trim())" }catch{ L "check_nnue_simd on nnue.o failed to run: $_" }
} else { L "nnue.o not produced" }
if($allok){
  L "H256-E12 BENCH MATCH CR (d11 308972 d13 745494)"; "MATCH" | Set-Content "$out\build_$name.STATUS"
  "CR_PASS h256_e12 (ep10 tree + Engine NNUE run e epoch 12 H256 net md5 6d22f612c855e17c62d396d32da99ea4, ONLY src\nnue_weights.inc differs, -DFORGE_NNUE_HIDDEN=256 + full ep10 flag set, gain route); PC bench d11/13 = 308972/745494 = CR. exe sha256 $sha. Source: /workspace/forge-hashes/CR_PASS_nnue_h256_e12_ep12_ep10base.txt (73-file manifest verified)" | Set-Content "$fp\CR_PASS_h256_e12.ok"
  L "wrote CR_PASS_h256_e12.ok"
} else { L "H256 BENCH MISMATCH; no .ok written"; "MISMATCH" | Set-Content "$out\build_$name.STATUS" }
