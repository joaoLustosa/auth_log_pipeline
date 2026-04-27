from sqlalchemy import text
from src.db import get_engine

engine = get_engine()

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.scalar())
