import time
from copy import deepcopy

import docker
import docker.errors
import pytest
from beetools.utils import get_tmp_dir
from beetools.utils import rm_tree
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class DevAutoSettings(BaseSettings):
    DEV_AUTO_OVERRIDE: bool = False
    DEV_DB_ROLLBACK_OVERRIDE: bool = False
    DEV_AUTO_MYSQL_HOST: str = ""
    DEV_AUTO_MYSQL_TCP_PORT: int = 0


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}
    INSTALLER_USERID: str = ""
    INSTALLER_PWD: str = ""
    MYSQL_HOST: str = ""
    MYSQL_TCP_PORT: int = 0
    MYSQL_DATABASE: str = ""
    MYSQL_PWD: str = ""
    MYSQL_ROOT_PASSWORD: str = ""
    PROJECT_NAME: str = ""
    VENV_ENVIRONMENT: str = ""


dev_auto_settings = DevAutoSettings()
settings = Settings()


def _wait_for_db_container(p_container, p_timeout=60):
    """Poll the container status until it reports running or the timeout expires."""
    deadline = time.monotonic() + p_timeout
    while time.monotonic() < deadline:
        p_container.reload()
        if p_container.status == "running":
            return
        time.sleep(1)
    raise RuntimeError(f"Database container {p_container.name!r} did not start within {p_timeout} seconds")


def _wait_for_mysql_ready(p_timeout=90):
    """Poll the MySQL server until it accepts a connection or the timeout expires.

    A running container does not mean the MySQL server is ready to serve queries, so this
    repeatedly attempts a real connection and swallows the transient startup errors (e.g. error
    2013 "Lost connection during query") until the server responds or the timeout is reached.
    """
    import mysql.connector

    deadline = time.monotonic() + p_timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            conn = mysql.connector.connect(
                host=settings.MYSQL_HOST,
                user="root",
                password=settings.MYSQL_ROOT_PASSWORD,
                port=settings.MYSQL_TCP_PORT,
                auth_plugin="mysql_native_password",
            )
            conn.close()
            return
        except mysql.connector.Error as err:
            last_error = err
            time.sleep(1)
    raise RuntimeError(f"MySQL server did not become ready within {p_timeout} seconds: {last_error}")


def _wait_for_postgres_ready(p_timeout=90):
    """Poll the PostgreSQL server until it accepts a connection or the timeout expires.

    A running container does not mean the PostgreSQL server is ready to serve queries, so this
    repeatedly attempts a real connection and swallows the transient startup errors until the
    server responds or the timeout is reached.
    """
    import psycopg

    deadline = time.monotonic() + p_timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            conn = psycopg.connect(
                host=settings.MYSQL_HOST,
                user=settings.INSTALLER_USERID,
                password=settings.INSTALLER_PWD,
                dbname=settings.MYSQL_DATABASE,
                port=settings.MYSQL_TCP_PORT,
            )
            conn.close()
            return
        except psycopg.Error as err:
            last_error = err
            time.sleep(1)
    raise RuntimeError(f"PostgreSQL server did not become ready within {p_timeout} seconds: {last_error}")


@pytest.fixture
def reset_db_structure_tables():
    """Drop and recreate every table configured in a wrapper db_structure."""

    def normalize_db_structure(p_db):
        """Return a create_tables-safe copy of a legacy db_structure."""
        db_structure = deepcopy(p_db.db_structure)
        lower_table_names = {table_name.lower(): table_name for table_name in db_structure}
        for table_name, table in db_structure.items():
            for field in table.values():
                params = field["Params"]
                if params["PrimaryKey"][0] == "Y" and not params["PrimaryKey"][1]:
                    params["PrimaryKey"][1] = "A"
                if params["FKey"]:
                    ref_table = params["FKey"][2]
                    if ref_table not in db_structure and ref_table.lower() in lower_table_names:
                        params["FKey"][2] = lower_table_names[ref_table.lower()]
                    ref_table = params["FKey"][2]
                    ref_field = params["FKey"][3]
                    if ref_table in db_structure and ref_field not in db_structure[ref_table]:
                        lower_field_names = {field_name.lower(): field_name for field_name in db_structure[ref_table]}
                        if ref_field.lower() in lower_field_names:
                            params["FKey"][3] = lower_field_names[ref_field.lower()]
        return db_structure

    def reset_tables(p_db):
        """Drop and recreate every table configured for p_db."""
        p_db.db_structure = normalize_db_structure(p_db)
        table_names = list(p_db.db_structure)
        if p_db.__class__.__name__ == "MySQL":
            p_db.cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table_name in reversed(table_names):
                p_db.cur.execute(f"DROP TABLE IF EXISTS {p_db.quote_identifier(table_name)}")
            p_db.cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            p_db.conn.commit()
        else:
            for table_name in reversed(table_names):
                p_db.cur.execute(f"DROP TABLE IF EXISTS {p_db.quote_identifier(table_name)} CASCADE")
        return p_db.create_tables()

    return reset_tables


@pytest.fixture
def working_dir():
    d = get_tmp_dir(settings.PROJECT_NAME)
    yield d
    rm_tree(d, p_crash=False)


def make_db_container_fixture(*, db_class):
    """Return a session-scoped pytest fixture that starts a Docker database container.

    The container image is chosen based on the wrapper class under test: a PostgreSQL image for
    the ``PostgreSQL`` wrapper and a MySQL image for the ``MySQL`` wrapper. The started container
    is yielded to the test and removed on teardown.
    """

    @pytest.fixture(scope="session")
    def db_container():
        client = docker.from_env()
        container_name = "DevTestContainer"
        if db_class.__name__ == "PostgreSQL":
            image = "postgres:16"
            container_port = "5432/tcp"
            command = None
            environment = {
                "POSTGRES_DB": settings.MYSQL_DATABASE,
                "POSTGRES_USER": settings.INSTALLER_USERID,
                "POSTGRES_PASSWORD": settings.INSTALLER_PWD,
            }
        else:
            image = "mysql:8.0"
            container_port = "3306/tcp"
            command = "--default-authentication-plugin=mysql_native_password"
            environment = {
                "MYSQL_DATABASE": settings.MYSQL_DATABASE,
                "MYSQL_ROOT_PASSWORD": settings.MYSQL_ROOT_PASSWORD,
            }
        try:
            existing = client.containers.get(container_name)
            existing.remove(force=True)
        except docker.errors.NotFound:
            pass
        container = client.containers.run(
            image,
            command=command,
            environment=environment,
            ports={container_port: ("127.0.0.1", settings.MYSQL_TCP_PORT)},
            detach=True,
            name=container_name,
        )
        try:
            _wait_for_db_container(container)
            if db_class.__name__ == "PostgreSQL":
                _wait_for_postgres_ready()
            else:
                _wait_for_mysql_ready()
            yield container
        finally:
            try:
                container.stop()
                container.remove()
            except docker.errors.NotFound:
                pass

    return db_container
