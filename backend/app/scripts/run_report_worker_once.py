import sys
import logging
import argparse
from app.core.config import settings
from app.persistence.factory import get_job_repository, get_report_repository
from app.services.report_worker_harness import run_report_worker_tick

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("report_worker_runner")

def main():
    parser = argparse.ArgumentParser(description="Run the report worker tick once.")
    parser.add_argument("--workspace-id", type=str, help="Optional workspace ID to process jobs for.")
    args = parser.parse_args()

    logger.info("Starting report worker single tick...")
    
    # In local storage mode, we don't need a real DB session
    # In database mode, we should create a session.
    db_session = None
    if settings.normalized_persistence_backend == "database":
        from app.db.session import SessionLocal
        db_session = SessionLocal()

    try:
        job_repo = get_job_repository(settings, db_session=db_session)
        report_repo = get_report_repository(settings, db_session=db_session)

        summary = run_report_worker_tick(
            settings=settings,
            job_repository=job_repo,
            report_repository=report_repo,
            workspace_id=args.workspace_id
        )

        logger.info(f"Report worker tick completed: {summary}")
        
    except Exception as e:
        logger.error(f"Error running report worker tick: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        if db_session:
            db_session.close()

if __name__ == "__main__":
    main()
