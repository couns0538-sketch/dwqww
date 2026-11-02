# PowerShell-only verification before any Python process starts. Archive pins
# come from the immutable official NuGet/PyPI identities in the R10 receipt.
# Caller supplies Owned-Path and Hash; both refuse before filesystem traversal.
function Get-BootstrapSnapshot {
    $runtimeRoot='D:\a11\runtime'
    $specs=@(
        @{name='python.3.12.10.nupkg';sha256='0eb85c2dfccccf1b17352de4c397f69194035b7d37149eacc16f1147d93de3b8';prefix='python';nuget=$true},
        @{name='pip-25.3-py3-none-any.whl';sha256='9655943313a94722b7774661c21049070f6bbb0a1516bf02f7c8d5d9201514cd';prefix='bootstrap_packages';nuget=$false}
    )
    $files=@();$archives=@()
    foreach($spec in $specs){
        $archivePath=Owned-Path "$runtimeRoot\downloads\$($spec.name)"
        if((Hash $archivePath) -cne $spec.sha256){throw 'Official bootstrap archive pin mismatch'}
        $archives+=[ordered]@{path=$archivePath;sha256=$spec.sha256}
        $root=Owned-Path "$runtimeRoot\$($spec.prefix)"
        $declared=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        $zip=[IO.Compression.ZipFile]::OpenRead($archivePath)
        try {
            foreach($entry in $zip.Entries){
                $member=$entry.FullName.Replace('\','/')
                if($spec.nuget){if(-not $member.StartsWith('tools/',[StringComparison]::Ordinal)){continue};$member=$member.Substring(6)}
                if(-not $member -or $member.EndsWith('/')){continue}
                if($member.StartsWith('/') -or $member.Contains(':') -or @($member -split '/'|Where-Object{$_ -in @('','.','..') -or $_ -match '[. ]$'}).Count){throw 'Unsafe bootstrap archive member'}
                if(-not $declared.Add($member)){throw 'Duplicate bootstrap archive member'}
                if((($entry.ExternalAttributes -shr 16) -band 61440) -eq 40960){throw 'Bootstrap archive symlink refused'}
                $path=Owned-Path (Join-Path $root $member)
                $item=Get-Item -LiteralPath $path -Force -ErrorAction Stop
                if($item.PSIsContainer -or $item.Length -ne $entry.Length){throw 'Bootstrap extracted length/type mismatch'}
                $stream=$entry.Open();$sha=[Security.Cryptography.SHA256]::Create()
                try{$expected=([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose();$stream.Dispose()}
                if((Hash $path) -cne $expected){throw ('Bootstrap extracted bytes differ: '+$member)}
                $files+=[ordered]@{path=$path;bytes=$entry.Length;sha256=$expected}
            }
        }finally{$zip.Dispose()}
        $actual=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
        $directories=[Collections.Generic.Stack[string]]::new();$directories.Push($root)
        while($directories.Count){
            $directory=Owned-Path $directories.Pop()
            foreach($entry in Get-ChildItem -LiteralPath $directory -Force){
                $path=Owned-Path $entry.FullName
                if($entry.PSIsContainer){$directories.Push($path)}else{$null=$actual.Add($path.Substring($root.Length+1).Replace('\','/'))}
            }
        }
        if(-not $actual.SetEquals($declared)){throw 'Bootstrap extracted file census differs from official archive'}
    }
    return [ordered]@{schema=1;archives=$archives;files=@($files|Sort-Object path);scope='Every extracted CPython DLL/executable/stdlib/development file and pip bootstrap file matches its pinned official archive; exact file census, root-first reparse refusal; no Python process'}
}
function Assert-BootstrapSnapshot([object]$Expected) {
    $actual=Get-BootstrapSnapshot
    if(($actual|ConvertTo-Json -Compress -Depth 8) -cne ($Expected|ConvertTo-Json -Compress -Depth 8)){throw 'Prepared bootstrap identity/census changed'}
}
