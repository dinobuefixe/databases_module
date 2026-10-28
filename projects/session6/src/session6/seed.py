from session6.db_utils import (
    seed_users,
    seed_ingredients,
    seed_products,
    seed_orders,
    seed_order_items,
)

TOTAL_USERS = 5
TOTAL_INGREDIENTS = 10
TOTAL_PRODUCTS = 3
TOTAL_ORDERS = 50_000
TOTAL_ORDER_ITEMS = 200_000


if __name__ == "__main__":
    from session6.models import Base, engine

    Base.metadata.create_all(bind=engine)
    import logging

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.Session").setLevel(logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info("Database tables created successfully.")

    seed_users(TOTAL_USERS)
    seed_ingredients(TOTAL_INGREDIENTS)
    seed_products(TOTAL_PRODUCTS)
    seed_orders(TOTAL_ORDERS)
    seed_order_items(TOTAL_ORDER_ITEMS)
