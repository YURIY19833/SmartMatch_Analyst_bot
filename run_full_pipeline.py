import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Ensure FOOTBALL_API_KEY is set; don't proceed blindly without key for API fetch.
    try:
        from src.ingestion.get_data import fetch_and_save, API_KEY
        from src.features.build_features import create_ml_dataset
    except Exception:
        # Fallback to loading modules by file path when package imports are unavailable
        import importlib.util, pathlib

        ing_path = pathlib.Path('src.ingestion.get_data.py')
        spec = importlib.util.spec_from_file_location('ing', ing_path)
        ing = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ing)
        fetch_and_save = ing.fetch_and_save
        API_KEY = getattr(ing, 'API_KEY', None)

        bf_path = pathlib.Path('src.features.build_features.py')
        spec2 = importlib.util.spec_from_file_location('bf', bf_path)
        bf = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(bf)
        create_ml_dataset = bf.create_ml_dataset

    from predict import predict_match

    logger.info("Starting full pipeline")

    # Ingestion (archive will run regardless; API requires key)
    try:
        fetch_and_save()
    except Exception as e:
        logger.exception("fetch_and_save() failed: %s", e)

    # Feature build
    try:
        df = create_ml_dataset()
        logger.info("Feature build completed: %d rows", len(df))
    except Exception as e:
        logger.exception("create_ml_dataset() failed: %s", e)

    # Sample prediction (will use DB view v_team_analytics)
    try:
        out = predict_match('Liverpool FC', 'Chelsea FC')
        logger.info("Sample prediction:\n%s", out)
    except Exception as e:
        logger.exception("predict_match() failed: %s", e)


if __name__ == '__main__':
    main()
