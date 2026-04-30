from sqlalchemy import text
from src.db import get_engine

engine = get_engine()

def insert_event(event: dict):
  query = text("""
      INSERT INTO logs (
          timestamp,
          host,
          process,
          event_type,
          auth_outcome,
          user_validity,
          failure_mode,
          user_name,
          ip,
          command,
          raw_message
      ) VALUES (
          :timestamp,
          :host,
          :process,
          :event_type,
          :auth_outcome,
          :user_validity,
          :failure_mode,
          :user_name,
          :ip,
          :command,
          :raw_message
      )
  """)

  with engine.begin() as conn:
      conn.execute(query, event)
