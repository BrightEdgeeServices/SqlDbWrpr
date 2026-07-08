from sqldbwrpr.sqldbwrpr import MySQL
from sqldbwrpr.sqldbwrpr import PostgreSQL
from sqldbwrpr.sqldbwrpr import SQLDbWrpr
from tests.conftest import make_db_container_fixture
from tests.conftest import settings
from tests.test_data.fixture_data import DB_STRUCTURE
from tests.test_data.fixture_data import res_member
from tests.test_data.fixture_data import src_members
from tests.test_data.fixture_data import TBL_TUP_COUNTRY

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


class TestSQLDbWrpr:
    def test_build_column_sql_builds_varchar_column_sql(self, postgresql_container):
        """SQLDbWrpr.build_column_sql builds positive column SQL using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        field_params = {
            "AI": "",
            "DEF": "Active",
            "NN": "Y",
            "UN": "",
            "ZF": "",
        }
        try:
            column_sql = SQLDbWrpr.build_column_sql(
                pg_db,
                "Status",
                ["varchar", 20],
                field_params,
                "Current status",
            )

            assert column_sql == '"Status" VARCHAR(20) NOT NULL DEFAULT \'Active\' COMMENT "Current status"'
        finally:
            pg_db.close()

    def test_build_index_sql_builds_unique_index_sql(self, postgresql_container):
        """SQLDbWrpr.build_index_sql builds positive index SQL using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            index_sql = SQLDbWrpr.build_index_sql(
                pg_db,
                "Member",
                "idx_member_name",
                [["Surname", 1, "A"], ["Name", 2, "D"]],
                p_unique=True,
            )

            assert index_sql == 'UNIQUE INDEX "idx_member_name" ("Surname" ASC,"Name" DESC) VISIBLE, '
        finally:
            pg_db.close()

    def test_build_insert_sql_builds_insert_sql(self, postgresql_container):
        """SQLDbWrpr.build_insert_sql builds positive insert SQL using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            insert_sql = SQLDbWrpr.build_insert_sql(
                pg_db,
                "Member",
                ["Surname", "Name", "OrgMemberId"],
            )

            assert insert_sql == 'INSERT INTO "Member" ("Surname","Name","OrgMemberId") VALUES (%s,%s,%s)'
        finally:
            pg_db.close()

    def test_create_db_creates_postgresql_database(self, postgresql_container):
        """PostgreSQL.create_db creates a database using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        db_name = "sqldbwrpr_create_db_positive"
        try:
            pg_db.db_name = db_name

            assert pg_db.create_db() is True

            pg_db.cur.execute("SELECT current_database()")
            assert pg_db.cur.fetchone() == (db_name,)
        finally:
            pg_db.close()
            maintenance_db = PostgreSQL(
                p_host_name=settings.MYSQL_HOST,
                p_user_name=settings.INSTALLER_USERID,
                p_password=settings.INSTALLER_PWD,
                p_db_name=settings.MYSQL_DATABASE,
                p_db_port=str(settings.MYSQL_TCP_PORT),
                p_db_structure=DB_STRUCTURE,
            )
            try:
                maintenance_db.cur.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
            finally:
                maintenance_db.close()

    def test_create_tables_creates_postgresql_tables(self, postgresql_container):
        """SQLDbWrpr.create_tables creates schema tables using PostgreSQL infrastructure."""
        table_name = "BuildTablePositive"
        db_structure = {
            table_name: {
                "Id": {
                    "Type": ["int"],
                    "Params": {
                        "AI": "Y",
                        "DEF": "",
                        "FKey": [],
                        "Index": [],
                        "NN": "Y",
                        "PrimaryKey": ["Y", "A"],
                    },
                    "Comment": "Identifier",
                },
                "Name": {
                    "Type": ["varchar", 30],
                    "Params": {
                        "AI": "",
                        "DEF": "",
                        "FKey": [],
                        "Index": [],
                        "NN": "Y",
                        "PrimaryKey": ["", ""],
                    },
                    "Comment": "Name",
                },
            }
        }
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=db_structure,
        )
        try:
            pg_db.cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

            assert SQLDbWrpr.create_tables(pg_db) is True

            pg_db.cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name = %s
                """,
                (table_name,),
            )
            assert pg_db.cur.fetchone() == (table_name,)
            assert pg_db.table_load_order == [table_name]
        finally:
            pg_db.cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            pg_db.close()

    def test_export_to_csv_exports_member_table(self, postgresql_container, reset_db_structure_tables, working_dir):
        """SQLDbWrpr.export_to_csv exports populated member rows using PostgreSQL infrastructure."""
        table_name = "member"
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        export_path = working_dir / "member.csv"
        try:
            reset_db_structure_tables(pg_db)
            pg_db.import_csv(
                "country",
                p_csv_db=[("code", "description")] + TBL_TUP_COUNTRY,
                p_header=("code", "description"),
            )
            pg_db.import_csv(
                table_name,
                p_csv_db=src_members,
                p_header=src_members[0],
            )

            exported_files = SQLDbWrpr.export_to_csv(pg_db, str(export_path), table_name)

            assert exported_files == [(str(working_dir), "member.csv")]
            assert export_path.read_text() == res_member
        finally:
            pg_db.cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            pg_db.close()

    def test_get_db_field_types_populates_field_type_maps(self, postgresql_container):
        """SQLDbWrpr.get_db_field_types populates char and non-char field maps."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            pg_db.char_fields = {}
            pg_db.non_char_fields = {}

            SQLDbWrpr.get_db_field_types(pg_db)

            assert pg_db.char_fields["member"] == ["surname", "name", "country"]
            assert pg_db.non_char_fields["member"] == ["id", "race"]
            assert pg_db.char_fields["country"] == ["code", "description"]
            assert pg_db.non_char_fields["rating"] == ["id", "date", "rating", "member_org_id"]
        finally:
            pg_db.close()

    def test_param_placeholder_returns_percent_s(self, postgresql_container):
        """SQLDbWrpr.param_placeholder returns the DB-API placeholder using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            placeholder = SQLDbWrpr.param_placeholder(pg_db)

            assert placeholder == "%s"
        finally:
            pg_db.close()

    def test_quote_identifier_quotes_identifier(self, postgresql_container):
        """SQLDbWrpr.quote_identifier quotes identifiers using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            quoted_identifier = SQLDbWrpr.quote_identifier(pg_db, 'Member"Name')

            assert quoted_identifier == '"Member""Name"'
        finally:
            pg_db.close()

    def test_quote_identifier_list_quotes_identifier_list(self, postgresql_container):
        """SQLDbWrpr.quote_identifier_list quotes identifier lists using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            quoted_identifiers = SQLDbWrpr.quote_identifier_list(pg_db, ["Surname", "Name", 'Member"Id'])

            assert quoted_identifiers == '"Surname","Name","Member""Id"'
        finally:
            pg_db.close()

    def test_render_default_sql_builds_varchar_default_sql(self, postgresql_container):
        """SQLDbWrpr.render_default_sql builds positive default SQL using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            default_sql = SQLDbWrpr.render_default_sql(pg_db, ["varchar", 20], "Active")

            assert default_sql == ' DEFAULT "Active"'
        finally:
            pg_db.close()

    def test_render_field_type_builds_decimal_field_type(self, postgresql_container):
        """SQLDbWrpr.render_field_type builds positive field type SQL using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        field_params = {
            "AI": "",
        }
        try:
            field_type = SQLDbWrpr.render_field_type(pg_db, ["decimal", 10, 2], field_params)

            assert field_type == "decimal(10, 2)"
        finally:
            pg_db.close()


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
