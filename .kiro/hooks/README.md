# Hooks

Kiro agent hooks live here. Hooks used for testing or documentation are an explicitly listed
submission artifact, so anything configured for this project belongs in the repo.

Worth considering for this project:
- regenerate `data/DATA_DICTIONARY.md` whenever a build script changes the schema of a processed table
- run the category-rebuild validation whenever `analysis/scripts/fsis_categories.py` is edited, since
  that module is load-bearing and silently breaking it would invalidate downstream results
