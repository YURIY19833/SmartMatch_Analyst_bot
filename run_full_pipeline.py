import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Ensure FOOTBALL_API_KEY is set; don't proceed blindly without key for API fetch.
    from src.ingestion.get_data import fetch_and_save, API_KEY
    from src.features.build_features import create_ml_dataset
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
