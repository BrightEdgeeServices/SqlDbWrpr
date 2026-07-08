from sqldbwrpr.sqldbwrpr import MySQL
from sqldbwrpr.sqldbwrpr import PostgreSQL
from tests.conftest import DB_STRUCTURE
from tests.conftest import make_db_container_fixture
from tests.conftest import settings

mysql_container = make_db_container_fixture(db_class=MySQL)
postgresql_container = make_db_container_fixture(db_class=PostgreSQL)


class TestMySQL:
    def test_create_users_creates_missing_user(self, mysql_container):
        """MySQL.create_users creates a missing user in the live database."""
        my_db = MySQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name="root",
            p_password=settings.MYSQL_ROOT_PASSWORD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        user_host = settings.MYSQL_HOST
        user_name = "create_users_positive_user"
        user_password = "CreateUsersPositivePwd1!"
        try:
            my_db.cur.execute(f"DROP USER IF EXISTS '{user_name}'@'{user_host}'")
            my_db.conn.commit()

            my_db.create_users(["root", settings.MYSQL_ROOT_PASSWORD], [[user_name, user_password]])

            my_db.cur.execute(
                "SELECT CAST(User AS CHAR), Host FROM mysql.user WHERE User = %s AND Host = %s",
                (user_name, user_host),
            )
            assert my_db.cur.fetchone() == (user_name, user_host)
            assert my_db.success is True
        finally:
            my_db.cur.execute(f"DROP USER IF EXISTS '{user_name}'@'{user_host}'")
            my_db.conn.commit()
            my_db.close()

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
