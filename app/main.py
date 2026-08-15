"""
Hello World Flask Application.

A simple two-tier web service that demonstrates Kubernetes deployment patterns
including ConfigMap-driven configuration, Secret-based credentials, and health probes.
"""

import logging
import os

import psycopg2
from flask import Flask, jsonify

# Structured logging — captured by log aggregators (e.g., LogDNA, Datadog)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_db_connection():
    """
    Create and return a PostgreSQL database connection using environment variables.

    Returns:
        psycopg2.connection | None: Active connection or None on failure.
    """
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "postgres"),
            port=int(os.environ.get("DB_PORT", 5432)),
            dbname=os.environ.get("DB_NAME", "appdb"),
            user=os.environ.get("DB_USER", "appuser"),
            password=os.environ.get("DB_PASSWORD", ""),
            connect_timeout=5,
        )
        logger.info("Database connection established successfully")
        return conn
    except psycopg2.OperationalError as exc:
        logger.error("Database connection failed: %s", exc)
        return None


@app.route("/")
def hello():
    """
    Root endpoint — returns Hello World JSON payload.

    Returns:
        flask.Response: JSON with message and status fields.
    """
    logger.info("GET / called")
    return jsonify({"message": "Hello, World!", "status": "ok"})


@app.route("/health")
def health():
    """
    Liveness and readiness probe endpoint for Kubernetes.

    Uses DEBUG level to avoid flooding logs — Kubernetes probes this every
    10-15 seconds and INFO-level entries would drown out meaningful events.

    Returns:
        flask.Response: 200 JSON when app is healthy.
    """
    logger.debug("GET /health called")
    return jsonify({"status": "healthy"}), 200


@app.route("/db-check")
def db_check():
    """
    Database connectivity check endpoint.

    Returns:
        flask.Response: 200 if DB is reachable, 503 otherwise.
    """
    logger.info("GET /db-check called")
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({"database": "connected"}), 200
    return jsonify({"database": "unreachable"}), 503


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting Flask app on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
