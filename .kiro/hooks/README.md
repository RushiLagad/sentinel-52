# Hooks

Kiro agent hooks. Hooks used for testing or documentation are an explicitly listed submission
artifact, so everything configured for this project is in the repo rather than only in Kiro's UI.

| File | Fires on | Does |
|---|---|---|
| `h1-validate-category-rebuild.json` | an edit to `fsis_categories.py` | re-runs the category rebuild against all three posted FSIS windows |
| `h2-regenerate-data-dictionary.json` | an edit to a build script | agent decides whether the schema changed and updates `data/DATA_DICTIONARY.md` if so |
| `h3-app-data-contract.json` | an edit to any analysis script | re-runs the app-data contract test |
| `h4-decision-layer-guardrails.json` | an edit to the decision layer or any built payload | re-runs the five guardrails |

Each one guards a failure that would otherwise be silent. H1 and H3 both catch breakage that
produces wrong output rather than an error; H4 guards the licence and honesty constraints that no
test suite would catch on its own.

## Verifying they load

Kiro's documented hook schema is `{"version": "v1", "hooks": [{name, trigger, matcher, action}]}`
in `.kiro/hooks/*.json`. These use the `PostFileSave` trigger from Kiro's own documented example.
Kiro's hook-types page also lists the same event as **File Save**, so if a future version does not
recognise `PostFileSave`, change the `trigger` field in all four files to `FileSave` — nothing else
needs to change.

Open Kiro's hooks panel and confirm all four appear and are enabled before relying on them. A hook
that does not load fails silently, which is exactly the class of problem these exist to prevent.

## Running the same checks by hand

```bash
python analysis/scripts/17_build_app_data.py --check --out app/public/data
python analysis/scripts/04_validate_categories.py --data data/processed --posted-dir data/validation --out analysis/outputs
```
