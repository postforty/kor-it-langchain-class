import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

pg_id = os.getenv("PGVECTOR_ID", "postgres")
pg_pw = os.getenv("PGVECTOR_PW", "postgres")
pg_host = os.getenv("PGVECTOR_HOST", "localhost")
pg_port = os.getenv("PGVECTOR_PORT", "5432")
pg_db = os.getenv("PGVECTOR_DB", "postgres")

db_uri = f"postgresql://{pg_id}:{pg_pw}@{pg_host}:{pg_port}/{pg_db}?sslmode=disable"

with psycopg.connect(db_uri) as conn:
    with conn.cursor() as cur:
        # langgraph store 관련 테이블 모두 삭제
        tables_to_drop = ["store_vectors", "store", "store_migrations", "vector_migrations"]
        for t in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
            print(f"Dropped: {t}")
        conn.commit()
        print("All store tables dropped.")
