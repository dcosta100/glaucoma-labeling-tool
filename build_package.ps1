# ============================================================================
#  build_package.ps1
#  Builds a self-contained package to hand to a labeler. Run this on YOUR
#  machine (which has internet). It produces dist/glaucoma-labeling-tool.zip
#  containing the app, the prepared data and a bundled uv.exe.
#
#  The labeler just unzips it and double-clicks "Start Labeling.bat".
#  No manual Python install required.
#
#  Usage:
#      powershell -ExecutionPolicy Bypass -File build_package.ps1
# ============================================================================
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$distRoot = Join-Path $root "dist"
$pkgName = "glaucoma-labeling-tool"
$pkg = Join-Path $distRoot $pkgName

Write-Host "Building package in $pkg ..."

# Fresh package folder
if (Test-Path $pkg) { Remove-Item $pkg -Recurse -Force }
New-Item -ItemType Directory -Path $pkg -Force | Out-Null

# ---- 1) App code and metadata ----
Copy-Item (Join-Path $root "app.py") $pkg
Copy-Item (Join-Path $root "pyproject.toml") $pkg
Copy-Item (Join-Path $root "requirements.txt") $pkg
Copy-Item (Join-Path $root "README.md") $pkg
Copy-Item (Join-Path $root "Start Labeling.bat") $pkg
Copy-Item (Join-Path $root "utils") (Join-Path $pkg "utils") -Recurse
Copy-Item (Join-Path $root "scripts") (Join-Path $pkg "scripts") -Recurse

# Reference guide
if (Test-Path (Join-Path $root "reference")) {
    Copy-Item (Join-Path $root "reference") (Join-Path $pkg "reference") -Recurse
}

# ---- 2) Prepared data (manifest + images), NOT the .dta / original PDFs ----
$prepSrc = Join-Path $root "data\prepared"
if (-not (Test-Path (Join-Path $prepSrc "manifest.csv"))) {
    throw "data\prepared\manifest.csv not found. Run prepare_data.py first."
}
$prepDst = Join-Path $pkg "data\prepared"
New-Item -ItemType Directory -Path $prepDst -Force | Out-Null
Copy-Item (Join-Path $prepSrc "manifest.csv") $prepDst
Copy-Item (Join-Path $prepSrc "images") (Join-Path $prepDst "images") -Recurse

# ---- 3) Config with an empty name (so the app asks the labeler) ----
$cfg = @'
# Labeler configuration (one per machine)
# The app will ask for your name the first time and save it here.
labeler_name: ""

manifest_path: data/prepared/manifest.csv
images_dir: data/prepared/images
output_dir: labels
reference_guide: reference/Visual_Field_Patterns_Revised.docx
'@
Set-Content -Path (Join-Path $pkg "labeler_config.yaml") -Value $cfg -Encoding utf8

# ---- 4) Bundle uv.exe ----
$uvDst = Join-Path $pkg "uv.exe"
$localUv = Join-Path $root "uv.exe"
if (Test-Path $localUv) {
    Copy-Item $localUv $uvDst
} else {
    Write-Host "Downloading uv.exe ..."
    $tmpZip = Join-Path $env:TEMP "uv-windows.zip"
    $tmpDir = Join-Path $env:TEMP "uv-extract"
    $url = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
    Invoke-WebRequest -Uri $url -OutFile $tmpZip
    if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
    Expand-Archive -Path $tmpZip -DestinationPath $tmpDir -Force
    Copy-Item (Join-Path $tmpDir "uv.exe") $uvDst
}

# ---- 5) Zip it ----
$zip = Join-Path $distRoot "$pkgName.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path "$pkg\*" -DestinationPath $zip

$sizeMB = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host ""
Write-Host "Done. Package: $zip ($sizeMB MB)"
Write-Host "Send the .zip to the labeler. They unzip it and double-click 'Start Labeling.bat'."
