import os
import urllib.request
import redis

import psycopg
from flask import Flask, jsonify

app = Flask(__name__)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True
)

def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "orbitstack"),
        user=os.getenv("DB_USER", "orbitstack"),
        password=os.getenv("DB_PASSWORD")
    )

def init_db():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    task VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        connection.commit()

@app.get("/health")
def health():
    return jsonify(status="healthy", service="api")


@app.get("/api/status")
def status():
    return jsonify(service="api", message="OrbitStack API is running")


@app.get("/api/db-check")

def db_check():
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return jsonify(
            status="available",
            database="postgres"
        )

    except Exception:
        return jsonify(
            status="unavailable",
            message="PostgreSQL is unavailable"
        ), 503

@app.post("/api/jobs")
def create_job():
    task = "generate_report"

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO jobs (task, status)
                VALUES (%s, %s)
                RETURNING id
                """,
                (task, "queued")
            )

            job_id = cursor.fetchone()[0]

        connection.commit()

    redis_client.rpush(
        "orbitstack_jobs",
        str(job_id)
    )

    return jsonify(
        job_id=job_id,
        status="queued"
    ), 202

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)