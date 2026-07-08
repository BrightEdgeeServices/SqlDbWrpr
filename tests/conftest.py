import time

import docker
import docker.errors
import pytest
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

DB_STRUCTURE = {
    "Rating": {
        "Date": {
            "Type": ["date"],
            "Params": {
                "PrimaryKey": ["Y", "A"],
                "FKey": [],
                "Index": [1, 1, "A", "U"],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Rate of publication",
        },
        "Name": {
            "Type": ["varchar", 30],
            "Params": {
                "PrimaryKey": ["Y", "A"],
                "FKey": [1, 2, "Member", "Name", "C", "C"],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Name from Member",
        },
        "Surname": {
            "Type": ["varchar", 45],
            "Params": {
                "PrimaryKey": ["Y", "A"],
                "FKey": [1, 1, "Member", "Surname", "C", "C"],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Surname from Member",
        },
        "Rating": {
            "Type": ["int"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Rating of member",
        },
        "OrgMemberId": {
            "Type": ["int"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [1, 2, "A", "U"],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Rating of member",
        },
    },
    "Member": {
        "Surname": {
            "Type": ["varchar", 45],
            "Params": {
                "PrimaryKey": ["Y", "A"],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Surname of member",
        },
        "Name": {
            "Type": ["varchar", 30],
            "Params": {
                "PrimaryKey": ["Y", "A"],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Name of the member",
        },
        "SosSec": {
            "Type": ["varchar", 10],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [1, 1, "D", "U"],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Social security nr filled with zeros",
        },
        "Country": {
            "Type": ["char", 3],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [1, 1, "Country", "Code", "R", "C"],
                "Index": [2, 2, "A", "U"],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Country passport",
        },
        "PassportNr": {
            "Type": ["char", 15],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [2, 1, "D", "U"],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Passport number",
        },
        "Race": {
            "Type": ["tinyint"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "Y",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "1",
            },
            "Possible Values": "1=White,2=Black",
            "Comment": "Race of member",
        },
        "RegDateTime": {
            "Type": ["datetime"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [3, 1, "D", "U"],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Registration date",
        },
        "Picture": {
            "Type": ["blob"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "Y",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Photo of member",
        },
        "ActiveStatus": {
            "Type": ["boolean"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Active | Inactive",
        },
        "BirthYear": {
            "Type": ["int"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "",
                "UN": "Y",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Birth year of member",
        },
        "DOB": {
            "Type": ["date"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Date of Birth",
        },
    },
    "Country": {
        "Code": {
            "Type": ["char", 3],
            "Params": {
                "PrimaryKey": ["Y", "D"],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "3 digit country code",
        },
        "Description": {
            "Type": ["varchar", 30],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Name of country",
        },
    },
    "Organization": {
        "OrgId": {
            "Type": ["bigint"],
            "Params": {
                "PrimaryKey": ["Y", "D"],
                "FKey": [],
                "Index": [1, 1, "A", "U"],
                "NN": "Y",
                "B": "",
                "UN": "Y",
                "ZF": "",
                "AI": "Y",
                "G": "Y",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Organization id auto generated",
        },
        "OrgName": {
            "Type": ["varchar", 20],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [2, 1, "A", ""],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Organization name",
        },
        "RegFee": {
            "Type": ["decimal", 5, 2],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Registration fee",
        },
        "OpenTrading": {
            "Type": ["time"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Opening time for trading",
        },
    },
    "MemberOrg": {
        "Surname": {
            "Type": ["varchar", 45],
            "Params": {
                "PrimaryKey": ["Y", "A"],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Surname from Member",
        },
        "Name": {
            "Type": ["varchar", 30],
            "Params": {
                "PrimaryKey": ["Y", "A"],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Name from Member",
        },
        "OrgId": {
            "Type": [
                "bigint",
            ],
            "Params": {
                "PrimaryKey": ["Y", "D"],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "Y",
                "ZF": "",
                "AI": "",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "OrgId from Organization",
        },
    },
}
TBL_TXT_COUNTRY = """\
Code;Description
NOR;Norway
CHN;China
USA;United States of America
"""
TBL_TUP_COUNTRY = [
    ("CHN", "China"),
    ("NOR", "Norway"),
    ("USA", "United States of America"),
]


class DevAutoSettings(BaseSettings):
    DEV_AUTO_OVERRIDE: bool = False
    DEV_DB_ROLLBACK_OVERRIDE: bool = False
    DEV_AUTO_MYSQL_HOST: str = ""
    DEV_AUTO_MYSQL_TCP_PORT: int = ""


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}
    INSTALLER_USERID: str = ""
    INSTALLER_PWD: str = ""
    MYSQL_HOST: str = ""
    MYSQL_TCP_PORT: int = "3306"
    MYSQL_DATABASE: str = ""
    MYSQL_PWD: str = ""
    MYSQL_ROOT_PASSWORD: str = ""
    VENV_ENVIRONMENT: str = "prod"


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
