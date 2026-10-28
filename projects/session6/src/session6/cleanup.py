import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    from session6.models import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables recreated successfully.")