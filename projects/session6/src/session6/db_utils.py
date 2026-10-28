from session6.models import (
    User,
    Ingredient,
    Product,
    ProductIngredient,
    Order,
    OrderItem,
    Invoice,
)
from sqlalchemy.orm import Session
import faker
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("sqlalchemy.Session").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
faker = faker.Faker()


def get_engine():
    from session6.models import engine

    return engine


def seed_users(total_users):
    logger.info("Seeding users...")
    with Session(bind=get_engine()) as session:
        for i in range(total_users):
            user = User(name=faker.name(), email=faker.email())
            session.add(user)
        session.commit()


def seed_ingredients(total_ingredients):
    logger.info("Seeding ingredients...")
    with Session(bind=get_engine()) as session:
        for i in range(total_ingredients):
            ingredient = Ingredient(name=faker.word())
            session.add(ingredient)
        session.commit()


def seed_products(total_products):
    logger.info("Seeding products...")
    with Session(bind=get_engine()) as session:
        for i in range(total_products):
            product = Product(name=faker.word(), price=faker.random_number(digits=2))
            session.add(product)
        session.commit()


def seed_product_ingredients(total_product_ingredients):
    logger.info("Seeding product ingredients...")
    with Session(bind=get_engine()) as session:
        for i in range(total_product_ingredients):
            product_ingredient = ProductIngredient(
                product_id=faker.random_int(min=1, max=10),
                ingredient_id=faker.random_int(min=1, max=10),
            )
            session.add(product_ingredient)
        session.commit()


fake_status = ["pending", "completed", "canceled"]

def seed_orders(total_orders):
    logger.info("Seeding orders...")
    # get max id from users
    with Session(bind=get_engine()) as session:
        max_user_id = session.query(User).order_by(User.id.desc()).first().id
    with Session(bind=get_engine()) as session:
        for i in range(total_orders):
            order = Order(
                user_id=faker.random_int(min=2, max=max_user_id), 
                created_at=faker.date_time(),
                status=faker.random_element(fake_status)
            )
            session.add(order)
        session.commit()


def     seed_order_items(total_order_items):
    logger.info("Seeding order items...")
    with Session(bind=get_engine()) as session:
        max_order_id = session.query(Order).order_by(Order.id.desc()).first().id
        max_product_id = session.query(Product).order_by(Product.id.desc()).first().id

        for i in range(total_order_items):
            order_item = OrderItem(
                order_id=faker.random_int(min=2, max=max_order_id),
                product_id=faker.random_int(min=2, max=max_product_id),
                quantity=faker.random_int(min=1, max=5),
            )
            session.add(order_item)
            if i % 2000 == 0:
                session.commit()
                logging.log(logging.INFO, f"Committed {i} order items")
        session.commit()


def seed_invoices(total_invoices):
    logger.info("Seeding invoices...")
    with Session(bind=get_engine()) as session:
        max_order_id = session.query(Order).order_by(Order.id.desc()).first().id
        for i in range(total_invoices):
            invoice = Invoice(
                order_id=faker.random_int(min=1, max=max_order_id),
                paid=faker.random_number(digits=2),
                due=faker.date_time(),
            )
            session.add(invoice)
        session.commit()
