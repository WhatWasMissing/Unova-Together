// Read-only validation through PKHeX by Kaphotics / Project Pokémon (GPL).
using System.Security.Cryptography;
using System.Text.Json;
using PKHeX.Core;

if (args.Length != 2)
    throw new ArgumentException("Usage: Inspector <input.sav> <output.json>");
var input = Path.GetFullPath(args[0]);
var output = Path.GetFullPath(args[1]);
if (string.Equals(input, output, StringComparison.OrdinalIgnoreCase))
    throw new ArgumentException("Output cannot overwrite the save");
var original = File.ReadAllBytes(input);
var save = SaveUtil.GetSaveFile(original.ToArray()) as SAV5B2W2
    ?? throw new InvalidDataException("Not a recognized Black 2 / White 2 save");
var party = save.PartyData.Select(p => new {
    pid = p.PID, species = p.Species, xp = p.EXP,
    level = p.Stat_Level, hp = p.Stat_HPCurrent,
    moves = new[] { p.Move1, p.Move2, p.Move3, p.Move4 },
    checksumValid = p.ChecksumValid,
}).ToArray();
var report = new {
    parser = "PKHeX.Core", libraryVersion = typeof(SaveFile).Assembly.GetName().Version?.ToString(),
    saveType = save.GetType().Name, version = save.Version.ToString(),
    checksumsValid = save.ChecksumsValid, badgeMask = save.Misc.Badges, party,
    sourceSha256 = Convert.ToHexString(SHA256.HashData(original)).ToLowerInvariant(),
    sourceUnchanged = original.AsSpan().SequenceEqual(File.ReadAllBytes(input)),
};
Directory.CreateDirectory(Path.GetDirectoryName(output)!);
File.WriteAllText(output, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine(JsonSerializer.Serialize(report));
return report.sourceUnchanged && report.checksumsValid && party.All(p => p.checksumValid) ? 0 : 1;
