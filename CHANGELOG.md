# Changelog

All notable changes to this project should be documented in this file.

## [Unreleased] - 2026-06-06

### Added
- `requirements.txt` listing runtime dependencies.
- `.env.example` template (removed hard-coded API key; user must set `FOOTBALL_API_KEY`).
- `run_full_pipeline.py` to run ingestion -> feature build -> sample prediction.
- `CHANGELOG.md` (this file).

### Changed
- Centralized DB connection via `db_config.py` and removed import-time side effects.
- `src.ingestion.get_data.py`: read `FOOTBALL_API_KEY` from environment; added timeouts and robust error handling; switched to `logging`.
- `src.features.build_features.py`: removed duplicate code, return DataFrame, added logging.
- `predict.py`: removed console-unfriendly characters, fixed feature ordering and error handling; made outputs ASCII-friendly.

### Notes
- Archive CSV ingestion does not require an API key; fetching the current season from the football-data API requires `FOOTBALL_API_KEY`.
- Consider rotating and storing secrets securely (not in repo).
