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

    def test_delete_users_deletes_existing_user(self, mysql_container):
        """MySQL.delete_users deletes an existing user in the live database."""
        my_db = MySQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name="root",
            p_password=settings.MYSQL_ROOT_PASSWORD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        user_host = settings.MYSQL_HOST
        user_name = "delete_users_positive_user"
        user_password = "DeleteUsersPositivePwd1!"
        try:
            my_db.cur.execute(f"DROP USER IF EXISTS '{user_name}'@'{user_host}'")
            my_db.conn.commit()
            my_db.create_users(["root", settings.MYSQL_ROOT_PASSWORD], [[user_name, user_password]])

            my_db.delete_users(["root", settings.MYSQL_ROOT_PASSWORD], [[user_name, user_password, user_host]])

            my_db.cur.execute(
                "SELECT CAST(User AS CHAR), Host FROM mysql.user WHERE User = %s AND Host = %s",
                (user_name, user_host),
            )
            assert my_db.cur.fetchone() is None
            assert my_db.success is True
        finally:
            my_db.cur.execute(f"DROP USER IF EXISTS '{user_name}'@'{user_host}'")
            my_db.conn.commit()
            my_db.close()

    def test_grant_rights_grants_database_right_to_user(self, mysql_container):
        """MySQL.grant_rights grants a database right to an existing user."""
        my_db = MySQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name="root",
            p_password=settings.MYSQL_ROOT_PASSWORD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        user_host = settings.MYSQL_HOST
        user_name = "grant_rights_positive_user"
        user_password = "GrantRightsPositivePwd1!"
        try:
            my_db.cur.execute(f"DROP USER IF EXISTS '{user_name}'@'{user_host}'")
            my_db.conn.commit()
            my_db.create_users(["root", settings.MYSQL_ROOT_PASSWORD], [[user_name, user_password]])

            my_db.grant_rights(
                ["root", settings.MYSQL_ROOT_PASSWORD],
                [[user_name, user_host, settings.MYSQL_DATABASE, "*", "SELECT"]],
            )

            my_db.cur.execute(f"SHOW GRANTS FOR '{user_name}'@'{user_host}'")
            grants = [row[0] for row in my_db.cur.fetchall()]
            assert any(f"ON `{settings.MYSQL_DATABASE}`.*" in grant and "SELECT" in grant for grant in grants)
            assert any("WITH GRANT OPTION" in grant for grant in grants)
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
    def test_create_users_creates_missing_user(self, postgresql_container):
        """PostgreSQL.create_users creates a missing login role in the live database."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        user_name = "create_users_positive_user"
        user_password = "CreateUsersPositivePwd1!"
        try:
            pg_db.cur.execute(f'DROP USER IF EXISTS "{user_name}"')

            pg_db.create_users(
                [settings.INSTALLER_USERID, settings.INSTALLER_PWD],
                [[user_name, user_password]],
            )

            pg_db.cur.execute("SELECT rolname FROM pg_roles WHERE rolname = %s", (user_name,))
            assert pg_db.cur.fetchone() == (user_name,)
            assert pg_db.success is True
        finally:
            pg_db.cur.execute(f'DROP USER IF EXISTS "{user_name}"')
            pg_db.close()

    def test_delete_users_deletes_existing_user(self, postgresql_container):
        """PostgreSQL.delete_users deletes an existing login role in the live database."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        user_name = "delete_users_positive_user"
        user_password = "DeleteUsersPositivePwd1!"
        try:
            pg_db.cur.execute(f'DROP USER IF EXISTS "{user_name}"')
            pg_db.create_users(
                [settings.INSTALLER_USERID, settings.INSTALLER_PWD],
                [[user_name, user_password]],
            )

            pg_db.delete_users([settings.INSTALLER_USERID, settings.INSTALLER_PWD], [[user_name]])

            pg_db.cur.execute("SELECT rolname FROM pg_roles WHERE rolname = %s", (user_name,))
            assert pg_db.cur.fetchone() is None
            assert pg_db.success is True
        finally:
            pg_db.cur.execute(f'DROP USER IF EXISTS "{user_name}"')
            pg_db.close()

    def test_grant_rights_grants_database_right_to_user(self, postgresql_container):
        """PostgreSQL.grant_rights grants a database right to an existing login role."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        user_name = "grant_rights_positive_user"
        user_password = "GrantRightsPositivePwd1!"
        try:
            pg_db.cur.execute(f'DROP USER IF EXISTS "{user_name}"')
            pg_db.create_users(
                [settings.INSTALLER_USERID, settings.INSTALLER_PWD],
                [[user_name, user_password]],
            )

            pg_db.grant_rights(
                [settings.INSTALLER_USERID, settings.INSTALLER_PWD],
                [[user_name, settings.MYSQL_HOST, settings.MYSQL_DATABASE, "*", "CREATE"]],
            )

            pg_db.cur.execute(
                "SELECT has_database_privilege(%s, %s, 'CREATE')",
                (user_name, settings.MYSQL_DATABASE),
            )
            assert pg_db.cur.fetchone() == (True,)
            assert pg_db.success is True
        finally:
            pg_db.cur.execute(f'REVOKE CREATE ON DATABASE "{settings.MYSQL_DATABASE}" FROM "{user_name}"')
            pg_db.cur.execute(f'DROP USER IF EXISTS "{user_name}"')
            pg_db.close()

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
