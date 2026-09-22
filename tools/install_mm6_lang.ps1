<#
.SYNOPSIS
  Installs GrayFace MM6 Patch + MMExtension + a built mm678-i18n language
  pack onto a standalone Might and Magic VI install (e.g. the Steam copy).

.DESCRIPTION
  Reproduces the manual steps in docs/dev/mm6-steam-manual-install.md:
    1. Download + silently install the GrayFace MM6 Patch (version read
       from config/versions.toml unless -GrayFaceVersion is given).
    2. Download MMExtension and merge its ExeMods/ and Scripts/ folders
       into the game directory.
    3. Apply this repo's built language pack for -Lang (build it first
       with `mm678 build --no-release --langs <lang>` if
       build/postprod/<lang>/mm6 doesn't exist yet).

  Run from anywhere; it locates the repo root from this script's own path.
  Requires 7-Zip (7z.exe) on PATH or at the default install location, to
  extract MMExtension's .rar archive.

.PARAMETER GameDir
  Path to the Might and Magic VI install directory (contains mm6.exe).

.PARAMETER Lang
  Language code matching a translations/<lang> folder, e.g. zh_CN, zh_TW.

.PARAMETER GrayFaceVersion
  Override the GrayFace MM6 Patch version to install. Defaults to the
  value in config/versions.toml ([grayface_versions] 6 = "...").

.EXAMPLE
  .\install_mm6_lang.ps1 -GameDir "C:\Program Files (x86)\Steam\steamapps\common\Might & Magic VI" -Lang zh_TW
#>
param(
	[Parameter(Mandatory = $true)][string]$GameDir,
	[Parameter(Mandatory = $true)][string]$Lang,
	[string]$GrayFaceVersion
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path (Join-Path $GameDir "mm6.exe"))) {
	throw "mm6.exe not found in $GameDir - verify game files (e.g. via Steam) first."
}

if (-not $GrayFaceVersion) {
	$versionsToml = Get-Content (Join-Path $RepoRoot "config\versions.toml") -Raw
	if ($versionsToml -match '\[grayface_versions\][^\[]*?\n6\s*=\s*"([^"]+)"') {
		$GrayFaceVersion = $Matches[1]
	} else {
		throw "Could not read grayface_versions.6 from config/versions.toml - pass -GrayFaceVersion explicitly."
	}
}
Write-Host "Using GrayFace MM6 Patch version $GrayFaceVersion"

$postprodDir = Join-Path $RepoRoot "build\postprod\$Lang\mm6"
if (-not (Test-Path $postprodDir)) {
	throw "$postprodDir does not exist yet. Run from the repo root: mm678 build --no-release --langs $Lang"
}

$sevenZip = Get-Command 7z.exe -ErrorAction SilentlyContinue
if (-not $sevenZip) {
	$candidate = "C:\Program Files\7-Zip\7z.exe"
	if (Test-Path $candidate) { $sevenZip = $candidate } else {
		throw "7z.exe not found (needed to extract MMExtension's .rar). Install 7-Zip or add it to PATH."
	}
} else {
	$sevenZip = $sevenZip.Source
}

$tmp = Join-Path $env:TEMP "mm6_lang_install_$([guid]::NewGuid().ToString('N').Substring(0,8))"
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
	# --- 1. GrayFace MM6 Patch ---
	Write-Host "`n== Step 1/3: GrayFace MM6 Patch v$GrayFaceVersion =="
	$patchExe = Join-Path $tmp "MM6.Patch.exe"
	Invoke-WebRequest -Uri "https://github.com/GrayFace/Misc/releases/download/MM6Patch-$GrayFaceVersion/MM6.Patch.v$GrayFaceVersion.exe" -OutFile $patchExe
	$p = Start-Process -FilePath $patchExe -ArgumentList `
		"/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/DIR=`"$GameDir`"" `
		-PassThru -Wait -WindowStyle Hidden
	if ($p.ExitCode -ne 0) { throw "GrayFace patch installer exited with code $($p.ExitCode)" }
	Write-Host "GrayFace MM6 Patch installed."

	# --- 2. MMExtension ---
	Write-Host "`n== Step 2/3: MMExtension =="
	# Dropbox link from https://grayface.github.io/mm/ext - check that page if this 404s,
	# hosting has changed before and may change again.
	$mmextUrl = "https://www.dropbox.com/s/qohxt8ijjh74mcw/MMExtensionTmp.rar?dl=1"
	$mmextRar = Join-Path $tmp "MMExtension.rar"
	Invoke-WebRequest -Uri $mmextUrl -OutFile $mmextRar -UserAgent "Mozilla/5.0"
	$mmextDir = Join-Path $tmp "mmext"
	& $sevenZip x $mmextRar "-o$mmextDir" -y | Out-Null
	robocopy (Join-Path $mmextDir "ExeMods") (Join-Path $GameDir "ExeMods") /E /NFL /NDL /NJH | Out-Null
	robocopy (Join-Path $mmextDir "Scripts") (Join-Path $GameDir "Scripts") /E /NFL /NDL /NJH | Out-Null
	if (-not (Test-Path (Join-Path $GameDir "ExeMods\MMExtension.dll"))) {
		throw "MMExtension.dll missing after copy - installation failed."
	}
	Write-Host "MMExtension installed."

	# --- 3. Language pack ---
	Write-Host "`n== Step 3/3: language pack ($Lang) =="
	Copy-Item -Path (Join-Path $postprodDir "*") -Destination $GameDir -Recurse -Force
	Write-Host "Language pack applied."

	Write-Host "`nDone. First launch will show an MMExtension dialog about generating text tables - this is normal and one-time."
} finally {
	Remove-Item -Path $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
