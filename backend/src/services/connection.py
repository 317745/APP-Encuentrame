import time
import os

from dotenv import load_dotenv, find_dotenv
from sqlmodel import create_engine, Session, text

load_dotenv(find_dotenv())

SUPABASE_URI = os.getenv("SUPABASE_URI")

engine = create_engine(SUPABASE_URI, echo=True, pool_pre_ping=True)

def verify_connection(attempts: int = 5, wait: int = 3):
    print(f"Establishing the DB connection, attempt 1/{attempts}")

    for attempt in range(1, attempts + 1):
        try: 
            with Session(engine) as session:
                result = session.exec(text("SELECT NOW()")).first()
                print(f"Successful connection. DB time: {result[0]}")
                return True
        except Exception as e:
            print(f"The DB connection could not be established.")
            if attempt < attempts:
                print(f"Retrying the DB connection. Attempt: {attempt + 1}/{attempts}.")
                time.sleep(wait)
            else: 
                print("The DB connection could not be established after max attempts.")
                raise e

def get_connection():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()