# Sentinel-52 one-shot setup.
#
# Run this once from the repository folder in PowerShell:
#     cd C:\Users\rlagad\Downloads\sentinel-52
#     powershell -ExecutionPolicy Bypass -File .\setup.ps1
#
# It puts the GitHub Pages workflow where it belongs, makes the first commit, and
# optionally rebuilds the data. It does not push anywhere unless you ask it to with
# -CreateRepo, and it never touches credentials.

param(
    [switch]$CreateRepo,                 # also create the GitHub repo and push, needs gh already logged in
    [string]$RepoName = "sentinel-52",
    [switch]$Private,                    # create it private instead of public
    [switch]$BuildData,                  # also rebuild data/ from the FSIS bundle, about 3 minutes
    [string]$Bundle = "..\fsis_sensd_raw_2026-10-09.zip"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
function Say($m) { Write-Host "  $m" }

Write-Host "`nSentinel-52 setup`n" -ForegroundColor Cyan

# 1. The Pages workflow could not be delivered into .github directly, so move it now.
$wfDir = Join-Path $PSScriptRoot ".github\workflows"
$wfDst = Join-Path $wfDir "deploy-pages.yml"
$wfSrc = Join-Path $PSScriptRoot "docs\deploy-pages.yml"
if (Test-Path $wfDst) {
    Say "Pages workflow already in place."
} elseif (Test-Path $wfSrc) {
    New-Item -ItemType Directory -Force -Path $wfDir | Out-Null
    # drop the two explanatory comment lines that were only there to say where the file goes
    (Get-Content $wfSrc | Select-Object -Skip 3) | Set-Content -Path $wfDst -Encoding utf8
    Remove-Item $wfSrc
    Say "Moved the Pages workflow to .github\workflows\deploy-pages.yml"
} else {
    Say "No workflow file found to move, skipping."
}

# 2. Git repository and first commit.
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Say "git is not installed or not on PATH. Install it, then run this again."
    exit 1
}
if (Test-Path (Join-Path $PSScriptRoot ".git")) {
    Say "Git repository already initialised."
} else {
    git init -b main | Out-Null
    Say "Initialised a git repository on branch main."
}

$name  = (git config user.name)  2>$null
$email = (git config user.email) 2>$null
if (-not $name -or -not $email) {
    Say ""
    Say "git has no name or email set, so a commit would fail. Set them first:"
    Say '    git config --global user.name  "Rushikesh Lagad"'
    Say '    git config --global user.email "rlagad@uark.edu"'
    Say "Then run this script again."
    exit 1
}

git add -A | Out-Null
$staged = git diff --cached --name-only
if ($staged) {
    git commit -q -m "Analysis pipeline, data provenance and Kiro steering for the Sens-D challenge"
    Say ("Committed " + ($staged | Measure-Object).Count + " files.")
} else {
    Say "Nothing new to commit."
}

# 3. Optionally rebuild the processed data from the FSIS bundle.
if ($BuildData) {
    $bundlePath = Resolve-Path -ErrorAction SilentlyContinue $Bundle
    if (-not $bundlePath) {
        Say "Bundle not found at $Bundle, skipping the data build."
    } else {
        Say "Rebuilding data from $bundlePath, this takes about three minutes..."
        Push-Location (Join-Path $PSScriptRoot "analysis")
        python run_all.py --from-bundle $bundlePath
        Pop-Location
        Say "Data rebuilt."
    }
}

# 4. Optionally create the GitHub repository and push.
if ($CreateRepo) {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        Say "gh (GitHub CLI) is not installed, so the repo was not created. Install it from https://cli.github.com/ or create the repo in the browser."
    } else {
        gh auth status 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Say "gh is installed but not logged in. Run 'gh auth login' first, then re-run with -CreateRepo."
        } else {
            $vis = if ($Private) { "--private" } else { "--public" }
            Say "Creating GitHub repository '$RepoName' and pushing..."
            gh repo create $RepoName $vis --source=. --remote=origin --push
            Say "Pushed. Repository URL:"
            gh repo view --json url -q .url
        }
    }
}

Write-Host "`nNext:" -ForegroundColor Cyan
Say "1. Submit the repository URL in the Sens-D Submission Workspace on nafsihub.org."
Say "2. No pushes after Mon 2026-11-02, 16:00 Central. A late push disqualifies the team."
Say "3. See docs\SUBMISSION_CHECKLIST.md for what still has to go in."
Write-Host ""
