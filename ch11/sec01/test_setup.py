import os
from dotenv import load_dotenv
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import IndexConfig
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

pg_id = os.getenv("PGVECTOR_ID", "postgres")
pg_pw = os.getenv("PGVECTOR_PW", "postgres")
pg_host = os.getenv("PGVECTOR_HOST", "localhost")
pg_port = os.getenv("PGVECTOR_PORT", "5432")
pg_db = os.getenv("PGVECTOR_DB", "postgres")

db_uri = f"postgresql://{pg_id}:{pg_pw}@{pg_host}:{pg_port}/{pg_db}?sslmode=disable"
print("DB URI:", db_uri)

try:
    with PostgresStore.from_conn_string(db_uri, index=IndexConfig(embed=lambda x: [[0.0]*3072 for _ in x], dims=3072)) as store:
        print("Setting up store...")
        store.setup()
        print("Store setup complete.")
except Exception as e:
    print("Error during setup:", e)
