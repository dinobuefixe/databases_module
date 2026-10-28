from sqlalchemy import Engine,create_engine
import os

def build_connection_string(user, password, host, port, database)-> str:
    """
    Build a PostgreSQL connection string.

    Args:
        user (str): Database username.
        password (str): Database password.
        host (str): Database host.
        port (int): Database port.
        database (str): Database name.

    Returns:
        str: PostgreSQL connection string.
    """
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def get_inputs_connstr() -> str:
    return build_connection_string(
        os.environ["POSTGRES_USER"],
        os.environ["POSTGRES_PASSWORD"],
        "localhost",
        5432,
        "inputs"
    )

def get_insights_connstr() -> str:
    return build_connection_string(
        os.environ["POSTGRES_USER"],
        os.environ["POSTGRES_PASSWORD"],
        "localhost",
        5433,
        "insights"
    )


def get_engine(connstr: str|None = None)-> Engine:
    """
    Get a SQLAlchemy engine for the specified PostgreSQL database.

    Args:
        connstr (str): PostgreSQL connection string. If None, uses inputs connection string.

    Returns:
        Engine: SQLAlchemy engine instance.
    """
    return create_engine(connstr)