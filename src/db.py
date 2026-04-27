from sqlalchemy import create_engine

def get_engine():
    return create_engine(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/auth_logs"
    )
