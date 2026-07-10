from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CHAR
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import LargeBinary
from sqlalchemy import MetaData
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Time

from sqldbwrpr.sqldbwrpr import MySQL
from sqldbwrpr.sqldbwrpr import PostgreSQL
from sqldbwrpr.sqldbwrpr import SQLDbWrpr
from tests.conftest import make_db_container_fixture
from tests.conftest import settings
from tests.test_data.fixture_data import DB_STRUCTURE
from tests.test_data.fixture_data import res_member_delimited_pipe
from tests.test_data.fixture_data import res_member_org_split
from tests.test_data.fixture_data import res_member_split
from tests.test_data.fixture_data import res_member_split_only
from tests.test_data.fixture_data import res_member_tuple
from tests.test_data.fixture_data import split_struct_member
from tests.test_data.fixture_data import src_members
from tests.test_data.fixture_data import src_split_file_members
from tests.test_data.fixture_data import TBL_TUP_COUNTRY
from tests.test_data.fixture_data import TBL_TUP_ORGANIZATION

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
    def test_action_to_legacy_code_maps_sqlalchemy_actions(self):
        """SQLDbWrpr._action_to_legacy_code maps SQLAlchemy foreign-key actions to legacy codes."""
        action_map = {
            None: "N",
            "CASCADE": "C",
            "RESTRICT": "R",
            "SET DEFAULT": "D",
            "SET NULL": "N",
        }

        legacy_codes = {action: SQLDbWrpr._action_to_legacy_code(action) for action in action_map}

        assert legacy_codes == action_map

    def test_column_to_legacy_field_builds_legacy_field_definition(self):
        """SQLDbWrpr._column_to_legacy_field builds legacy field definitions from SQLAlchemy columns."""
        id_column = Column("id", Integer, primary_key=True, autoincrement=True, comment="Identifier")
        name_column = Column("name", String(30), nullable=False, default="Active")
        picture_column = Column("picture", LargeBinary)

        id_field = SQLDbWrpr._column_to_legacy_field(id_column)
        name_field = SQLDbWrpr._column_to_legacy_field(name_column)
        picture_field = SQLDbWrpr._column_to_legacy_field(picture_column)

        assert id_field == {
            "Type": ["int"],
            "Params": {
                "PrimaryKey": ["", ""],
                "FKey": [],
                "Index": [],
                "NN": "Y",
                "B": "",
                "UN": "",
                "ZF": "",
                "AI": "Y",
                "G": "",
                "DEF": "",
            },
            "Possible Values": "",
            "Comment": "Identifier",
        }
        assert name_field["Type"] == ["varchar", 30]
        assert name_field["Params"]["NN"] == "Y"
        assert name_field["Params"]["DEF"] == "Active"
        assert name_field["Comment"] == ""
        assert picture_field["Type"] == ["blob"]
        assert picture_field["Params"]["B"] == "Y"
        assert picture_field["Params"]["NN"] == ""
        assert picture_field["Possible Values"] == ""

    def test_column_type_to_legacy_maps_sqlalchemy_column_types(self):
        """SQLDbWrpr._column_type_to_legacy maps SQLAlchemy column types to legacy field types."""
        column_type_cases = [
            (Column("big_id", BigInteger), ["bigint"]),
            (Column("active", Boolean), ["boolean"]),
            (Column("code", CHAR(3)), ["char", 3]),
            (Column("created_date", Date), ["date"]),
            (Column("created_at", DateTime), ["datetime"]),
            (Column("id", Integer), ["int"]),
            (Column("payload", LargeBinary), ["blob"]),
            (Column("amount", Numeric(10, 2)), ["decimal", 10, 2]),
            (Column("ratio", Numeric), ["decimal"]),
            (Column("name", String(40)), ["varchar", 40]),
            (Column("description", String), ["varchar"]),
            (Column("start_time", Time), ["time"]),
            (Column("metadata", JSON), ["json"]),
        ]

        legacy_types = [SQLDbWrpr._column_type_to_legacy(column) for column, expected in column_type_cases]

        assert legacy_types == [expected for column, expected in column_type_cases]

    def test_set_foreign_keys_sets_legacy_foreign_key_metadata(self):
        """SQLDbWrpr._set_foreign_keys sets legacy foreign-key metadata on child fields."""
        metadata = MetaData()
        parent = Table(
            "parent",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("code", String(3), primary_key=True),
        )
        child = Table(
            "child",
            metadata,
            Column("parent_id", Integer),
            Column("parent_code", String(3)),
            ForeignKeyConstraint(
                ["parent_id", "parent_code"],
                [parent.c.id, parent.c.code],
                ondelete="CASCADE",
                onupdate="SET NULL",
            ),
        )
        table_structure = {column.name: SQLDbWrpr._column_to_legacy_field(column) for column in child.columns}

        SQLDbWrpr._set_foreign_keys(child, table_structure)

        assert table_structure["parent_id"]["Params"]["FKey"] == [1, 1, "parent", "id", "C", "N"]
        assert table_structure["parent_code"]["Params"]["FKey"] == [1, 2, "parent", "code", "C", "N"]

    def test_set_indexes_sets_legacy_index_metadata(self):
        """SQLDbWrpr._set_indexes sets legacy index metadata on indexed fields."""
        metadata = MetaData()
        member = Table(
            "member",
            metadata,
            Column("surname", String(30)),
            Column("name", String(30)),
            Column("country", String(3)),
        )
        Index("idx_member_country", member.c.country)
        Index("idx_member_name", member.c.surname, member.c.name, unique=True)
        table_structure = {column.name: SQLDbWrpr._column_to_legacy_field(column) for column in member.columns}

        SQLDbWrpr._set_indexes(member, table_structure)

        assert table_structure["country"]["Params"]["Index"] == [1, 1, "A", ""]
        assert table_structure["surname"]["Params"]["Index"] == [2, 1, "A", "U"]
        assert table_structure["name"]["Params"]["Index"] == [2, 2, "A", "U"]

    def test_build_default_field_params_builds_legacy_field_defaults(self):
        """SQLDbWrpr._build_default_field_params builds the legacy field parameter defaults."""
        field_params = SQLDbWrpr._build_default_field_params()
        second_field_params = SQLDbWrpr._build_default_field_params()

        assert field_params == {
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
        }
        assert field_params["PrimaryKey"] is not second_field_params["PrimaryKey"]
        assert field_params["FKey"] is not second_field_params["FKey"]
        assert field_params["Index"] is not second_field_params["Index"]

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
                p_csv_db=TBL_TUP_COUNTRY,
                p_header=("code", "description"),
            )
            pg_db.import_csv(
                table_name,
                p_csv_db=src_members,
                p_header=src_members[0],
            )

            exported_files = SQLDbWrpr.export_to_csv(pg_db, str(export_path), table_name)

            assert exported_files == [(str(working_dir), "member.csv")]
            assert export_path.read_text() == res_member_delimited_pipe
        finally:
            pg_db.close()

    def test_from_sqlalchemy_metadata_builds_legacy_schema_structure(self):
        """SQLDbWrpr.from_sqlalchemy_metadata builds a legacy schema from SQLAlchemy metadata."""
        metadata = MetaData()
        country = Table(
            "country",
            metadata,
            Column("code", String(3), primary_key=True, comment="Country code"),
            Column("description", String(30), nullable=False),
        )
        member = Table(
            "member",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column(
                "country_code",
                String(3),
                ForeignKey(country.c.code, ondelete="CASCADE", onupdate="RESTRICT"),
                nullable=False,
            ),
            Column("name", String(40), nullable=False, comment="Member name"),
            Column("rating", Numeric(6, 2), default=1500),
        )
        Index("idx_member_country_name", member.c.country_code, member.c.name, unique=True)

        db_structure = SQLDbWrpr.from_sqlalchemy_metadata(metadata)

        assert list(db_structure) == ["country", "member"]
        assert db_structure["country"]["code"]["Type"] == ["varchar", 3]
        assert db_structure["country"]["code"]["Params"]["PrimaryKey"] == ["Y", "A"]
        assert db_structure["country"]["code"]["Params"]["NN"] == "Y"
        assert db_structure["country"]["code"]["Comment"] == "Country code"
        assert db_structure["member"]["id"]["Type"] == ["int"]
        assert db_structure["member"]["id"]["Params"]["AI"] == "Y"
        assert db_structure["member"]["id"]["Params"]["PrimaryKey"] == ["Y", "A"]
        assert db_structure["member"]["country_code"]["Params"]["FKey"] == [1, 1, "country", "code", "C", "R"]
        assert db_structure["member"]["country_code"]["Params"]["Index"] == [1, 1, "A", "U"]
        assert db_structure["member"]["name"]["Params"]["Index"] == [1, 2, "A", "U"]
        assert db_structure["member"]["name"]["Comment"] == "Member name"
        assert db_structure["member"]["rating"]["Type"] == ["decimal", 6, 2]
        assert db_structure["member"]["rating"]["Params"]["DEF"] == "1500"

    def test_resolve_db_structure_uses_explicit_structure_metadata_and_base(self):
        """SQLDbWrpr.resolve_db_structure resolves explicit and SQLAlchemy schema sources."""
        explicit_structure = {"explicit_table": {}}
        metadata = MetaData()
        Table(
            "metadata_table",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(20), nullable=False),
        )
        base = type("SqlAlchemyBaseStub", (), {"metadata": metadata})

        explicit_db_structure = SQLDbWrpr.resolve_db_structure(
            p_db_structure=explicit_structure,
            p_sqlalchemy_metadata=metadata,
        )
        metadata_db_structure = SQLDbWrpr.resolve_db_structure(p_sqlalchemy_metadata=metadata)
        base_db_structure = SQLDbWrpr.resolve_db_structure(p_sqlalchemy_base=base)

        assert explicit_db_structure is explicit_structure
        assert list(metadata_db_structure) == ["metadata_table"]
        assert metadata_db_structure["metadata_table"]["id"]["Params"]["PrimaryKey"] == ["Y", "A"]
        assert metadata_db_structure["metadata_table"]["name"]["Type"] == ["varchar", 20]
        assert base_db_structure == metadata_db_structure

    def test_import_and_split_csv(self, postgresql_container, reset_db_structure_tables):
        """SQLDbWrpr.import_csv imports member rows using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            reset_db_structure_tables(pg_db)
            pg_db.import_csv(
                "country",
                p_csv_db=TBL_TUP_COUNTRY,
                p_header=("code", "description"),
            )
            pg_db.import_and_split_csv(
                split_struct_member,
                src_split_file_members,
            )

            pg_db.cur.execute(
                'SELECT "id", "surname", "name", "sos_sec", "picture", "country", "race" FROM "member" ORDER BY "id"'
            )
            assert pg_db.cur.fetchall() == res_member_split_only
        finally:
            pg_db.close()

    def test_import_and_split_csv_with_auto_increment_in_new_table(
        self, postgresql_container, reset_db_structure_tables
    ):
        """SQLDbWrpr.import_csv imports member rows using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            reset_db_structure_tables(pg_db)
            pg_db.import_csv(
                "country",
                p_csv_db=TBL_TUP_COUNTRY,
            )
            pg_db.import_csv(
                "organization",
                p_csv_db=TBL_TUP_ORGANIZATION,
            )
            pg_db.import_csv(
                "member",
                p_csv_db=src_members,
                p_header=src_members[0],
            )
            pg_db.import_and_split_csv(
                split_struct_member,
                src_split_file_members,
            )
            pg_db.cur.execute(
                'SELECT "id" FROM "organization" WHERE "organization_name" = %s',
                ("St Louis Chess Club",),
            )
            stlcc_id = pg_db.cur.fetchall()[0][0]
            pg_db.cur.execute(
                'SELECT "id" FROM "organization" WHERE "organization_name" = %s',
                ("Boondocs Chess Club",),
            )
            boondocs_id = pg_db.cur.fetchall()[0][0]

            surname_name_tuple = tuple(
                tuple(part.strip() for part in row[0].split(",", 1)) for row in src_split_file_members[1:]
            )
            values_sql = ",".join(["(%s, %s)" for row in surname_name_tuple])
            surname_name_params = tuple(part for row in surname_name_tuple for part in row)
            pg_db.cur.execute(
                f"""SELECT m.id, m.surname, m.name
                FROM (VALUES {values_sql}) AS sn(surname, name)
                JOIN member AS m
                  ON m.surname = sn.surname AND m.name = sn.name""",
                surname_name_params,
            )
            surname_name_ids = [("id", "surname", "name")] + pg_db.cur.fetchall()
            split_struct_02 = {
                "Seq01": {
                    "TableName": "member_org",
                    "Key": "id",
                    "Replace": True,
                    "Flds": [
                        [
                            "None",
                            "id",
                            [6, 1, False],
                        ],
                        [
                            "id",
                            "member_id",
                            [
                                0,
                                0,
                                True,
                                [
                                    [],
                                ],
                            ],
                        ],
                        ["None", "organization_id", [1, stlcc_id, False]],
                    ],
                },
                "Seq02": {
                    "TableName": "member_org",
                    "Key": "id",
                    "Replace": True,
                    "Flds": [
                        [
                            "None",
                            "id",
                            [6, 1, False],
                        ],
                        [
                            "id",
                            "member_id",
                            [
                                0,
                                0,
                                True,
                                [
                                    [],
                                ],
                            ],
                        ],
                        ["None", "organization_id", [1, boondocs_id, False]],
                    ],
                },
            }
            pg_db.import_and_split_csv(
                split_struct_02,
                surname_name_ids,
            )

            pg_db.cur.execute(
                'SELECT "id", "surname", "name", "sos_sec", "picture", "country", "race" FROM "member" ORDER BY "id"'
            )
            assert pg_db.cur.fetchall() == res_member_split
            pg_db.cur.execute(
                'SELECT "id", "member_id", "organization_id" FROM "member_org" ORDER BY "organization_id", "member_id"'
            )
            assert pg_db.cur.fetchall() == res_member_org_split
        finally:
            pg_db.close()

    def test_import_csv_imports_member_rows(self, postgresql_container, reset_db_structure_tables):
        """SQLDbWrpr.import_csv imports member rows using PostgreSQL infrastructure."""
        pg_db = PostgreSQL(
            p_host_name=settings.MYSQL_HOST,
            p_user_name=settings.INSTALLER_USERID,
            p_password=settings.INSTALLER_PWD,
            p_db_name=settings.MYSQL_DATABASE,
            p_db_port=str(settings.MYSQL_TCP_PORT),
            p_db_structure=DB_STRUCTURE,
        )
        try:
            reset_db_structure_tables(pg_db)
            pg_db.import_csv(
                "country",
                p_csv_db=TBL_TUP_COUNTRY,
                p_header=("code", "description"),
            )

            pg_db.import_csv(
                "member",
                p_csv_db=src_members,
                p_header=src_members[0],
            )

            pg_db.cur.execute('SELECT "surname", "name", "sos_sec", "country", "race" FROM "member" ORDER BY "id"')
            assert pg_db.cur.fetchall() == res_member_tuple
        finally:
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

            assert pg_db.char_fields["member"] == ["surname", "name", "sos_sec", "country"]
            assert pg_db.non_char_fields["member"] == ["id", "picture", "race"]
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
