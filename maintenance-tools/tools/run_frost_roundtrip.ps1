param(
    [Parameter(Mandatory=$true)][string]$Rom,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$Editor,
    [switch]$PrepareFairyType
)
# Run with Windows PowerShell 5.1: Frost targets .NET Framework 4.8.
# Invoke the shipped editor's ROM parser/exporter without opening a window.
$ErrorActionPreference = 'Stop'
if (-not $Editor) { $Editor = Join-Path $PSScriptRoot 'external/gen5/Frost-5.0.1/app/FrostsGen5Editor.exe' }
$romPath = (Resolve-Path -LiteralPath $Rom).Path
$editorPath = (Resolve-Path -LiteralPath $Editor).Path
$editorHash = (Get-FileHash -LiteralPath $editorPath -Algorithm SHA256).Hash.ToLower()
if ($editorHash -ne '30601dceb0ca0a414a690b955bb082c3725352a4ed3c707e536bd3ada5626111') {
    throw 'This runner requires the reviewed Frost 5.0.1 executable. Run setup_gen5_editor.py.'
}
$outputPath = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $outputPath) { throw 'Use a fresh output directory.' }
[void][IO.Directory]::CreateDirectory($outputPath)
$utf8 = New-Object Text.UTF8Encoding($false)
$report = [ordered]@{ editor=$editorPath; editorSha256=$editorHash; originalSha256=(Get-FileHash -LiteralPath $romPath -Algorithm SHA256).Hash.ToLower(); parsePassed=$false; exportPassed=$false; gameplayVerified=$false }
try {
    [void][Reflection.Assembly]::LoadFrom($editorPath)
    # A C# bridge avoids PowerShell's case-insensitive romType/RomType collision.
    $bridgeSource = @'
using System.IO;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using NewEditor.Data;
public static class FrostRoundtripBridge {
    public static string Run(string input, string output, bool prepareFairy) {
        NDSFileSystem data;
        // Normal initialization is required: text decoding uses static ROM type.
        using (FileStream stream = File.OpenRead(input)) data = NDSFileSystem.FromRom(stream, true);
        if (data.RomType != NewEditor.Forms.RomType.BW2)
            throw new System.NotSupportedException("This runner supports Black 2 / White 2 only.");
        var curves = new List<int[]>();
        foreach (var curve in data.xpCurveNarc.curves) {
            int[] levels = new int[101];
            for (int level = 0; level <= 100; level++) levels[level] = curve.GetXPAtLevel(level);
            curves.Add(levels);
        }
        var result = new Dictionary<string, object>();
        result["romType"] = data.romType;
        result["fairyTypeStrings"] = data.textNarc.textFiles[398].text.ToArray();
        result["xpCurves"] = curves;
        bool added = prepareFairy && !data.textNarc.textFiles[398].text.Contains("Fairy");
        if (added) {
            data.textNarc.textFiles[398].text.Add("Fairy");
            data.textNarc.textFiles[398].CompressData();
        }
        result["fairyTypeAdded"] = added;
        result["exportTypeNames"] = data.textNarc.textFiles[398].text.ToArray();
        byte[] bytes = data.BuildRom();
        File.WriteAllBytes(output, bytes);
        result["exportBytes"] = bytes.Length;
        return new JavaScriptSerializer().Serialize(result);
    }
}
'@
    $compiler = New-Object Microsoft.CSharp.CSharpCodeProvider
    $parameters = New-Object CodeDom.Compiler.CompilerParameters
    $parameters.GenerateInMemory = $true
    foreach ($reference in @($editorPath, 'System.dll', 'System.Core.dll', 'System.Windows.Forms.dll', 'System.Drawing.dll', 'System.Web.Extensions.dll')) {
        [void]$parameters.ReferencedAssemblies.Add($reference)
    }
    $compiled = $compiler.CompileAssemblyFromSource($parameters, $bridgeSource)
    if ($compiled.Errors.HasErrors) { throw ($compiled.Errors | Out-String) }
    $outputName = if ($PrepareFairyType) { 'Redux-frost-editor-ready.nds' } else { 'Redux-frost-roundtrip.nds' }
    $details = [FrostRoundtripBridge]::Run($romPath, (Join-Path $outputPath $outputName), [bool]$PrepareFairyType) | ConvertFrom-Json
    foreach ($property in $details.PSObject.Properties) { $report[$property.Name] = $property.Value }
    $report.parsePassed = $true
    $report.exportPassed = $true
} catch {
    $report.error = $_.Exception.ToString()
    throw
} finally {
    $report.originalUnchanged = ((Get-FileHash -LiteralPath $romPath -Algorithm SHA256).Hash.ToLower() -eq $report.originalSha256)
    [IO.File]::WriteAllText((Join-Path $outputPath 'frost.json'), ($report | ConvertTo-Json -Depth 10), $utf8)
}
Write-Output "Frost parse/export completed; compare ROM data before using the export: $outputPath"
