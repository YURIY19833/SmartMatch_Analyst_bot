# srcingestion

This repository contains scripts to fetch football match data, build features, train a model, and run predictions.

Setup
-----
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure database and API key. Preferred options:

- Set `DATABASE_URL` environment variable with full DSN, or
- Set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

You can copy `.env.example` to `.env` and fill values. Use a tool like `python-dotenv` or set env vars in your shell.

3. (Optional) Run data ingestion:

```bash
# Run ingestion (requires FOOTBALL_API_KEY in environment to fetch current season). Archive CSVs import regardless.
python -m run_full_pipeline
```

4. Build features and train model:

```bash
python src.features.build_features.py
python train_model.py
```

5. Predict example:

```bash
python predict.py
```

Notes
-----
- `db_config.py` supports `DATABASE_URL` and environment overrides `DB_NAME`, `DB_USER`, etc.
- `src.ingestion.get_data.py` will prefer `FOOTBALL_API_KEY` from environment; if the API returns HTTP 400, check the API key and request limits.
