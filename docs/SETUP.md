# Setting this repo up on your machine

One command does the whole thing. Open PowerShell in the repository folder:

```powershell
cd C:\Users\rlagad\Downloads\sentinel-52
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

That moves the Pages workflow into `.github/workflows/`, initialises git and makes the first commit.
It does not touch the network and it does not push anywhere.

If git has never been configured on this machine it will stop and tell you to run:

```powershell
git config --global user.name  "Rushikesh Lagad"
git config --global user.email "rlagad@uark.edu"
```

## Options

```powershell
# also rebuild data/processed from the FSIS bundle sitting in Downloads, about 3 minutes
.\setup.ps1 -BuildData

# also create the GitHub repo and push, requires `gh auth login` done first
.\setup.ps1 -CreateRepo

# create it private rather than public
.\setup.ps1 -CreateRepo -Private
```

If you would rather not use the GitHub CLI, create an empty repository on github.com and then:

```powershell
git remote add origin https://github.com/RushiLagad/sentinel-52.git
git push -u origin main
```

## Public or private

The submission is a repository link that judges must be able to open. Private works only if you add
the judges as collaborators, and nobody has told you who they are. **Public is the safer default**,
and nothing in this repository is sensitive: the data is USDA open data and the code is yours.

## The one rule that ends the entry

**No pushes after Monday 2026-11-02, 16:00 US Central.** Not a late fix, not a typo in the README.
Set your own cut-off a few hours earlier.
