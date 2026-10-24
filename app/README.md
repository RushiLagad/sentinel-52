# Decision-support application

A required deliverable: *"Provide a runnable web application along with build and deployment
instructions. We recommend React with GitHub Pages for consistency with the prior NAFSI Hub
application challenge."*

## Not yet started, deliberately

Two reasons:

1. **The challenge brief has not been published**, so what the app must answer is not yet fixed.
2. **Kiro artifacts are graded.** This app should be built *through* Kiro from a spec in
   `.kiro/specs/`, not hand-written and documented afterwards. Hand-writing it first would mean
   disclosing the whole thing as a substantial manual change and would waste the part of the grade
   that rewards spec-driven development.

## When it is built

Target stack: React + Vite, deployed to GitHub Pages via a workflow that is already written.

**First thing to do in this repo:** move `docs/deploy-pages.yml` to `.github/workflows/deploy-pages.yml`.
It could not be delivered at that path directly. It expects the app at `app/` with its build output in `app/dist`.

Set `base` in `vite.config.js` to `'/<repo-name>/'` or Pages will serve a blank page from a path that
does not resolve.

The app reads pre-computed JSON and CSV from `analysis/outputs/`. It must not need a backend, a
database or a live API call, because judges run it from a static Pages deploy.

Fill in before submission:

```
## Build
cd app && npm install && npm run build

## Run locally
cd app && npm run dev

## Deploy
Push to main. The Pages workflow builds and publishes.
```
