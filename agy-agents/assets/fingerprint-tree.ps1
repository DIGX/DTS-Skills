# Fingerprint a large guarded tree for .agy/tripwire.
#
# Emits one line per guarded file:  <size>:<mtime-ticks><TAB><relative/path>
#
# KEEP THIS FILE ASCII-ONLY. Windows PowerShell 5.1 reads a .ps1 in the system
# codepage unless it carries a UTF-8 BOM, so a stray em dash or curly quote
# arrives as mojibake and takes the parser down with it. That is not a
# hypothetical: an em dash in an error message did exactly that.
#
# This lives in PowerShell, rather than in the bash script that calls it, for a
# measured reason. Content-hashing a ~15,700-file tree means opening every one,
# which wakes Defender's real-time scanner and collapses throughput from ~3,500
# files/s to ~60 files/s. MSYS `find` is no better: it answers `-type f` from
# the directory entry (fast) but any mtime predicate forces a per-file stat()
# that opens the file (slow). Get-ChildItem returns Length and LastWriteTime as
# part of the directory enumeration, so the whole tree costs under a second and
# never opens a file.
#
# Exits non-zero if the root is missing or the walk yields nothing, so a broken
# fence reports as broken rather than as "clean".

[CmdletBinding()]
param(
	[Parameter(Mandatory = $true)]
	[string]$Root,

	# Semicolon-separated wildcard patterns, matched against the full path.
	# A bare name like "uploads" is expanded to match any directory of that
	# name; anything containing a wildcard or a slash is used as given.
	[string]$Skip = ''
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Root)) {
	[Console]::Error.WriteLine("fingerprint-tree: no such root: $Root")
	exit 2
}

$full = (Resolve-Path -LiteralPath $Root).ProviderPath.TrimEnd('\')
$prefix = $full.Length + 1

$patterns = New-Object System.Collections.Generic.List[string]
foreach ($s in $Skip.Split(';')) {
	$t = $s.Trim()
	if ($t.Length -eq 0) { continue }
	if ($t.Contains('*') -or $t.Contains('/') -or $t.Contains('\')) {
		$patterns.Add($t.Replace('/', '\'))
	} else {
		$patterns.Add("*\$t\*")
	}
}

$lines = New-Object System.Collections.Generic.List[string]

Get-ChildItem -LiteralPath $full -Recurse -File -Force -ErrorAction SilentlyContinue |
	ForEach-Object {
		$p = $_.FullName
		foreach ($s in $patterns) { if ($p -like $s) { return } }
		$rel = $p.Substring($prefix).Replace('\', '/')
		$lines.Add(("{0}:{1}`t{2}" -f $_.Length, $_.LastWriteTimeUtc.Ticks, $rel))
	}

if ($lines.Count -eq 0) {
	[Console]::Error.WriteLine("fingerprint-tree: walk of $full yielded no files, refusing to report an empty fence")
	exit 3
}

$lines.Sort([StringComparer]::Ordinal)
$out = [Console]::Out
foreach ($l in $lines) { $out.Write($l); $out.Write("`n") }
