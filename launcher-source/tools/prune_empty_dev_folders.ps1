# Remove empty historical folders after verified file cleanup; never traverse links.
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$roots=@('test-fixtures','backups','builds\archive','designs\backups') | ForEach-Object { Join-Path $workspace $_ }
foreach($folder in [IO.Directory]::EnumerateDirectories((Join-Path $workspace 'builds'))) {
    if([IO.Path]::GetFileName($folder) -notin @('current','azahar-x','mod-hub','launcher-styled-dist','archive')) { $roots+=$folder }
}
$removed=0
foreach($root in $roots) {
    if(-not[IO.Directory]::Exists($root)) { continue }
    $pending=New-Object 'System.Collections.Generic.Stack[string]';$pending.Push($root)
    $directories=New-Object 'System.Collections.Generic.List[string]'
    while($pending.Count) {
        $directory=$pending.Pop()
        if([IO.File]::GetAttributes($directory) -band [IO.FileAttributes]::ReparsePoint) { continue }
        $directories.Add($directory)
        foreach($child in [IO.Directory]::EnumerateDirectories($directory)) { $pending.Push($child) }
    }
    for($index=$directories.Count-1;$index -ge 0;$index--) {
        $directory=[IO.Path]::GetFullPath($directories[$index])
        if(-not $directory.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Folder is outside the workspace.' }
        $cursor=$directory;$linked=$false
        while($true) {
            if([IO.File]::GetAttributes($cursor) -band [IO.FileAttributes]::ReparsePoint) { $linked=$true;break }
            if($cursor -eq $workspace) { break }
            $cursor=[IO.Path]::GetDirectoryName($cursor)
        }
        if(-not $linked -and @([IO.Directory]::EnumerateFileSystemEntries($directory)).Count -eq 0) {
            Remove-Item -LiteralPath $directory -Force
            $removed++
        }
    }
}
Write-Host ('Removed '+$removed+' empty historical folders.')
