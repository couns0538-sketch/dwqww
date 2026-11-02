# Reproduce the R10 suite under R11; assertions remain byte-identical.
$ErrorActionPreference='Stop'
$repo='D:\a11\wt';$source="$repo\astra_r10\job3\regression";$target="$repo\astra_r11\runtime\regression"
if(Test-Path -LiteralPath $target){throw 'Fresh suite copy required'}
$old=Get-Content -Raw -LiteralPath "$source\SOURCE_COPY.json"|ConvertFrom-Json
$expected=@{}
foreach($item in $old.final_files){$relative=$item.path.Substring($item.path.IndexOf('datafilter\')+11);$expected[$relative]=$item.sha256}
$original=@();$final=@()
foreach($file in Get-ChildItem -LiteralPath "$source\datafilter" -Recurse -File){
    $relative=$file.FullName.Substring(("$source\datafilter\").Length)
    if($file.Extension -ne '.py' -and $relative -ne 'sample\positions.jsonl'){continue}
    if($relative -eq 'finalize_handoff.py'){continue} # Unused historical F: pack tool is not part of tests.
    if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Source reparse refused'}
    $hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if(-not $expected.ContainsKey($relative) -or $expected[$relative] -ine $hash){throw "Original R10 suite hash differs: $relative"}
    $dst=Join-Path "$target\datafilter" $relative
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dst))|Out-Null
    [IO.File]::Copy($file.FullName,$dst,$false)
    $original+=[ordered]@{relative=$relative;source=$file.FullName;source_sha256=$hash;copy_sha256=$hash}
}
foreach($name in @('full_state.py','runtime_binding.py','toolchain_binding.py','pytest_alias_guard.py')){[IO.File]::Copy("$source\$name","$target\$name",$false)}
[IO.File]::Copy("$source\SOURCE_COPY.json","$target\ORIGIN_SOURCE_COPY.json",$false)
$changed=@()
foreach($name in @('datafilter\filter_positions.py','pytest_alias_guard.py')){
    $path=Join-Path $target $name;$body=[IO.File]::ReadAllText($path)
    $body=$body.Replace('D:/a10/job3/regression-runs','D:/a11/regression-runs').Replace('D:/a10','D:/a11')
    [IO.File]::WriteAllText($path,$body,[Text.UTF8Encoding]::new($false));$changed+=$name
}
# The staged CR runner supplies the lane guard; later R10 alias/runtime fixes
# are restored in this separately named R11 copy by the reviewed adaptation.
[IO.File]::Copy("$source\run_regression.py","$target\run_regression.py",$false)
[IO.File]::Copy("$repo\astra_r10\job1\lane_guard.py","$target\lane_guard.py",$false)
$lane="$target\lane_guard.py";$body=[IO.File]::ReadAllText($lane).Replace("sys.path.insert(0, 'D:/a10/pydeps')","sys.path.insert(0, 'D:/a11/runtime/packages')")
[IO.File]::WriteAllText($lane,$body,[Text.UTF8Encoding]::new($false))
foreach($file in Get-ChildItem -LiteralPath "$target\datafilter" -Recurse -File){$final+=[ordered]@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}}
$receipt=[ordered]@{source_commit='d8982bc0';r10_commit='e6868fd56ebb3991ee197af6be29f3dd14a4d1c2';source_root=$source;target_root=$target;original_files=$original;reviewed_overlays=@();policy_changes=@('Only artifact root changed from a10 to a11; all test assertions and R10 overlays retained');final_files=$final}
[IO.File]::WriteAllText("$target\SOURCE_COPY.json",($receipt|ConvertTo-Json -Depth 8)+"`n",[Text.UTF8Encoding]::new($false))
$tests=@($original|Where-Object relative -like 'tests\*')
foreach($test in $tests){$copied=Join-Path "$target\datafilter" $test.relative;if((Get-FileHash -LiteralPath $copied -Algorithm SHA256).Hash -ine $test.source_sha256){throw 'Original test bytes changed'}}
Write-Output ("Copied "+$original.Count+" pinned source/fixture files including "+$tests.Count+' unchanged test files; runner adaptation still required')
