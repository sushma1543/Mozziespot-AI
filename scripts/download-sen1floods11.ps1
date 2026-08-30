param(
    [string]$Destination = ".\datasets\sen1floods11"
)

$ErrorActionPreference = "Stop"
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "Google Cloud CLI is required. Install it, then run this script again."
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
gcloud storage cp --recursive `
    "gs://sen1floods11/v1.1/data/flood_events/HandLabeled/S2Hand" `
    "gs://sen1floods11/v1.1/data/flood_events/HandLabeled/LabelHand" `
    $Destination

if ($LASTEXITCODE -ne 0) {
    throw "Sen1Floods11 download failed. gcloud exit code: $LASTEXITCODE"
}

Write-Host "Sen1Floods11 hand-labelled Sentinel-2 data downloaded to $Destination"
