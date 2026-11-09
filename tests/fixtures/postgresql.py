"""Isolated, uniquely owned PostgreSQL container for transaction tests."""

import time
from uuid import uuid4

import docker
import psycopg
import pytest


@pytest.fixture(scope="session")
def transaction_database():
    """Start a disposable database without replacing any existing containers."""
    client = docker.from_env()
    container = client.containers.run(
        "postgres:16-alpine",
        detach=True,
        environment={"POSTGRES_PASSWORD": "wrapper-tests-only"},
        name=f"sqldbwrpr-transactions-{uuid4().hex}",
        ports={"5432/tcp": ("127.0.0.1", None)},
    )
    try:
        container.reload()
        port = container.attrs["NetworkSettings"]["Ports"]["5432/tcp"][0]["HostPort"]
        parameters = dict(
            host="127.0.0.1", port=port, dbname="postgres", user="postgres", password="wrapper-tests-only"
        )
        deadline = time.monotonic() + 60
        while True:
            try:
                with psycopg.connect(**parameters):
                    break
            except psycopg.OperationalError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.2)
        yield parameters
    finally:
        container.remove(force=True)
        client.close()
