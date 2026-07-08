from sqldbwrpr.sqldbwrpr import MySQL
from sqldbwrpr.sqldbwrpr import PostgreSQL
from tests.conftest import DB_STRUCTURE
from tests.conftest import make_db_container_fixture
from tests.conftest import settings

mysql_container = make_db_container_fixture(db_class=MySQL)
postgresql_container = make_db_container_fixture(db_class=PostgreSQL)


class TestMySQL:
    def test_init_dict_structure(self, mysql_container):
        """MySQL.__init__ connects to the containerised database and opens a live cursor."""
        my_db = MySQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name="root",
            p_password=settings.MYSQL_ROOT_PASSWORD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            assert my_db.conn.is_connected()
            assert my_db.cur is not None
        finally:
            my_db.close()


class TestPostgreSQL:
    def test_init_dict_structure(self, postgresql_container):
        """PostgreSQL.__init__ connects to the containerised database and opens a live cursor."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            assert not pg_db.conn.closed
            assert pg_db.cur is not None
        finally:
            pg_db.close()
