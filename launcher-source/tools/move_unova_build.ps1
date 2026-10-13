<# Move the packaged Unova 1.0.5 build after a complete checksum-verified copy. #>
[CmdletBinding(SupportsShouldProcess=$true)]
param([switch]$Apply)
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$source=[IO.Path]::GetFullPath((Join-Path $workspace 'builds\release-1.0.5\Unova-Together'))
$destination='F:\unova-together'
if (-not $source.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Source is outside the project.' }
if (-not (Test-Path -LiteralPath (Join-Path $source 'builds\current\melonDS.exe'))) { throw 'Unova release 1.0.5 is missing.' }
if (Test-Path -LiteralPath $destination) { throw 'Destination already exists; nothing will be overwritten.' }
$items=@(Get-ChildItem -LiteralPath $source -Recurse -Force)
foreach($item in @((Get-Item -LiteralPath $workspace),(Get-Item -LiteralPath (Split-Path $source)),(Get-Item -LiteralPath $source))+$items) {
    if($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Linked path rejected: '+$item.FullName) }
}
$running=@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase) })
if($running.Count) { throw 'Close the packaged Unova build before moving it.' }
$files=@($items | Where-Object {-not $_.PSIsContainer})
Write-Host ('Move '+$source+' to '+$destination+' ('+$files.Count+' files).')
if(-not $Apply) { Write-Host 'Preview only. Run with -Apply to copy, verify every file, then remove the old package.';return }
if(-not $PSCmdlet.ShouldProcess($source,'Copy to F:\unova-together, verify SHA-256, then remove source')) { return }
$hashes=@{}
foreach($file in $files) { $hashes[$file.FullName.Substring($source.Length+1)]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash }
Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
foreach($relative in $hashes.Keys) {
    $copied=Join-Path $destination $relative
    if((Get-FileHash -LiteralPath $copied -Algorithm SHA256).Hash -ne $hashes[$relative]) { throw ('Copy mismatch. Source preserved: '+$relative) }
}
# Verify the source again immediately before removal, including its ancestors.
$cursor=$source
while($cursor -ne $workspace) {
    if((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source path changed. Source preserved.' }
    $cursor=Split-Path -Parent $cursor
}
$current=@(Get-ChildItem -LiteralPath $source -Recurse -Force)
if(@($current | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count -or @($current | Where-Object {-not $_.PSIsContainer}).Count -ne $files.Count) { throw 'Source changed. Both copies preserved.' }
foreach($file in $current | Where-Object {-not $_.PSIsContainer}) {
    $relative=$file.FullName.Substring($source.Length+1)
    if(-not $hashes.ContainsKey($relative) -or (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne $hashes[$relative]) { throw 'Source changed. Both copies preserved.' }
}
if(@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase) }).Count) { throw 'Source is running. Both copies preserved.' }
@{source=$source;destination=$destination;verifiedFiles=$files.Count;sha256=$hashes;date=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $destination '.migration.json') -Encoding UTF8
Remove-Item -LiteralPath $source -Recurse -Force
Write-Host ('Moved Unova 1.0.5. All '+$files.Count+' files verified; ROM and save paths elsewhere are preserved.')
