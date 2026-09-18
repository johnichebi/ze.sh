from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def execute_query(query, bind_params={}):
    with engine.begin() as connection:
        result = connection.execute(text(query), bind_params)
        return result
