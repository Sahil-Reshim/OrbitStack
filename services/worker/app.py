import os
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
    
def update_job_status(job_id, status):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE jobs SET status = %s WHERE id = %s",
                (status, job_id)
            )
        connection.commit()

@app.get("/health")
def health():
    return jsonify(status="healthy", service="worker")


@app.get("/worker/redis-check")
def redis_check():
    try:
        redis_client.ping()

        return jsonify(
            status="available",
            redis="connected"
        )

    except Exception:
        return jsonify(
            status="unavailable",
            message="Redis is unavailable"
        ), 503

def process_jobs():
    print("Worker started. Waiting for jobs...", flush=True)

    while True:
        print("Waiting for job...", flush=True)

        job = redis_client.blpop("orbitstack_jobs", timeout=5)

        print(f"BLPOP returned: {job}", flush=True)

        if job:
            queue_name, job_id = job
            print(f"Processing job: {job_id}", flush=True)

            update_job_status(job_id, "running")

            # Simulate the actual work
            print(f"Completed job: {job_id}", flush=True)

            update_job_status(job_id, "completed")

if __name__ == "__main__":
    import threading

    worker_thread = threading.Thread(target=process_jobs, daemon=True)
    worker_thread.start()

    app.run(host="0.0.0.0", port=5002)