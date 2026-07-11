from types import SimpleNamespace

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table

from sqldbwrpr.sqldbwrpr import SQLDbWrpr


class FakeConnection:
    def __init__(self):
        self.closed = False
        self.commits = 0
        self.rollbacks = 0

    def close(self):
        self.closed = True

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FakeCursor:
    def __init__(self, p_fetchall_results=None):
        self.executed = []
        self.executemany_calls = []
        self.fetchall_results = list(p_fetchall_results or [])

    def execute(self, p_sql, p_params=None):
        self.executed.append((p_sql, p_params))

    def executemany(self, p_sql, p_rows):
        self.executemany_calls.append((p_sql, p_rows))

    def fetchall(self):
        return self.fetchall_results.pop(0)


class TestSQLDbWrprBaseFunctions:
    def test_action_to_legacy_code_returns_mapped_code(self):
        assert SQLDbWrpr._action_to_legacy_code("SET NULL") == "N"

    def test_build_column_sql_returns_mysql_column_definition(self):
        sqldb = _build_sqldb()

        result = sqldb.build_column_sql(
            "Name",
            ["varchar", 10],
            _params(p_primary_key=["Y", "A"], p_not_null="Y", p_default="Anon"),
            "Display name",
        )

        assert result == 'Name varchar (10) NOT NULL DEFAULT "Anon" COMMENT "Display name"'

    def test_build_default_field_params_returns_legacy_params(self):
        assert SQLDbWrpr._build_default_field_params() == _params()

    def test_build_index_sql_returns_mysql_inline_index(self):
        sqldb = _build_sqldb()

        result = sqldb.build_index_sql("Sample", "unq_Name", [["Name", 1, "A", "U"]], p_unique=True)

        assert result == "UNIQUE INDEX unq_Name (Name ASC) VISIBLE, "

    def test_build_insert_sql_returns_mysql_replace_sql(self):
        sqldb = _build_sqldb()

        result = sqldb.build_insert_sql("Sample", ["Name", "Code"], p_replace=True)

        assert result == "REPLACE INTO Sample (Name,Code) VALUES (%s,%s)"

    def test_close_closes_connection(self):
        sqldb = _build_sqldb()

        sqldb.close()

        assert sqldb.conn.closed is True

    def test_column_to_legacy_field_returns_field_definition(self):
        column = Column("Payload", LargeBinary, nullable=True, comment="Binary payload")

        result = SQLDbWrpr._column_to_legacy_field(column)

        assert result == {
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
            "Comment": "Binary payload",
        }

    def test_column_type_to_legacy_returns_boolean_type(self):
        assert SQLDbWrpr._column_type_to_legacy(Column("Active", Boolean)) == ["boolean"]

    def test_create_db_executes_mysql_database_recreate_flow(self):
        sqldb = _build_sqldb()
        sqldb.cur = FakeCursor([[("ExistingDb",)]])
        sqldb.db_name = "ExistingDb"

        result = sqldb.create_db()

        assert result is True
        assert sqldb.cur.executed == [
            ("SHOW DATABASES", None),
            ("DROP DATABASE ExistingDb", None),
            ('CREATE DATABASE ExistingDb DEFAULT CHARACTER SET "utf8"', None),
            ("USE ExistingDb", None),
        ]
        assert sqldb.conn.commits == 3

    def test_create_tables_executes_generated_sql(self):
        sqldb = _build_sqldb()

        result = sqldb.create_tables()

        assert result is True
        assert sqldb.cur.executed == [("CREATE TABLE Sample (Name varchar (10) NOT NULL, PRIMARY KEY (Name))", None)]
        assert sqldb.table_load_order == ["Sample"]

    def test_create_users_executes_create_user_for_new_user(self):
        sqldb = _build_sqldb()
        sqldb.cur = FakeCursor([[()]])

        sqldb.create_users(["root", "secret"], [["new_user", "pwd"]])

        assert sqldb.success is True
        assert sqldb.cur.executed == [
            ("SELECT User, Host FROM mysql.user", None),
            ("CREATE USER IF NOT EXISTS 'new_user'@'localhost' IDENTIFIED BY 'pwd'", None),
        ]
        assert sqldb.conn.commits == 1

    def test_delete_users_executes_drop_user_for_existing_user(self):
        sqldb = _build_sqldb()
        sqldb.cur = FakeCursor([[("old_user",)]])

        sqldb.delete_users(["root", "secret"], [["old_user", "pwd", "localhost"]])

        assert sqldb.success is True
        assert sqldb.cur.executed == [
            ("SELECT User FROM mysql.user", None),
            ("DROP USER 'old_user'@'localhost'", None),
        ]

    def test_err_broken_rec_commits_successful_rows(self):
        sqldb = _build_sqldb()

        sqldb._err_broken_rec("INSERT INTO Sample VALUES (%s)", [("A",)])

        assert sqldb.cur.executed == [("INSERT INTO Sample VALUES (%s)", ("A",))]
        assert sqldb.conn.commits == 1

    def test_export_to_csv_writes_single_volume_file(self, tmp_path):
        sqldb = _build_sqldb()
        sqldb.cur = FakeCursor([[(1,)], [("Alice",)]])
        export_path = tmp_path / "Sample.csv"

        result = sqldb.export_to_csv(str(export_path), "Sample")

        assert result == [(str(tmp_path), "Sample.csv")]
        assert export_path.read_text() == "Name\nAlice\n"
        assert sqldb.cur.executed == [
            ("SELECT COUNT(*) FROM Sample", None),
            ("SELECT Name FROM Sample", None),
        ]

    def test_from_sqlalchemy_metadata_returns_legacy_structure(self):
        metadata = _metadata_with_constraints()

        result = SQLDbWrpr.from_sqlalchemy_metadata(metadata)

        assert result["parent"]["id"]["Params"]["PrimaryKey"] == ["Y", "A"]
        assert result["child"]["parent_id"]["Params"]["FKey"] == [1, 1, "parent", "id", "C", "N"]

    def test_get_db_field_types_populates_char_and_non_char_fields(self):
        sqldb = _build_sqldb()

        sqldb.get_db_field_types()

        assert sqldb.char_fields == {"Sample": ["Name"]}
        assert sqldb.non_char_fields == {"Sample": []}

    def test_grant_rights_executes_grant_statements(self):
        sqldb = _build_sqldb()

        sqldb.grant_rights(["root", "secret"], [["app_user", "localhost", "SampleDb", "Sample", "SELECT", "INSERT"]])

        assert sqldb.success is True
        assert sqldb.cur.executed == [
            ("GRANT SELECT,INSERT ON SampleDb.Sample TO 'app_user'@'localhost'", None),
            ("GRANT SELECT,INSERT ON SampleDb.Sample TO 'app_user'@'localhost' WITH GRANT OPTION", None),
        ]
        assert sqldb.conn.commits == 2

    def test_import_csv_imports_inline_csv_rows(self):
        sqldb = _build_sqldb()

        result = sqldb.import_csv("Sample", p_csv_db=[("Name",), ("Alice",)], p_vol_type="Single")

        assert result is True
        assert sqldb.cur.executemany_calls == [("INSERT INTO Sample (Name) VALUES (%s)", [("Alice",)])]
        assert sqldb.conn.commits == 1

    def test_init_resolves_structure_and_field_types(self):
        sqldb = SQLDbWrpr(p_db_structure=_db_structure())

        assert sqldb.db_structure == _db_structure()
        assert sqldb.char_fields == {"Sample": ["Name"]}
        assert sqldb.non_char_fields == {"Sample": []}

    def test_param_placeholder_returns_percent_s(self):
        assert _build_sqldb().param_placeholder() == "%s"

    def test_print_err_msg_prints_generic_error_fields(self, capsys):
        SQLDbWrpr._print_err_msg(SimpleNamespace(errno=1, sqlstate="HY000", msg="Broken"), "Failure")

        assert "Failure" in capsys.readouterr().out

    def test_quote_identifier_returns_identifier_unchanged_for_mysql(self):
        assert _build_sqldb().quote_identifier("Sample") == "Sample"

    def test_quote_identifier_list_joins_identifiers(self):
        assert _build_sqldb().quote_identifier_list(["Name", "Code"]) == "Name,Code"

    def test_render_default_sql_returns_string_default(self):
        assert _build_sqldb().render_default_sql(["varchar", 10], "Anon") == ' DEFAULT "Anon"'

    def test_render_field_type_returns_decimal_type(self):
        assert _build_sqldb().render_field_type(["decimal", 5, 2], _params()) == "decimal(5, 2)"

    def test_resolve_db_structure_returns_explicit_structure(self):
        structure = _db_structure()

        assert SQLDbWrpr.resolve_db_structure(p_db_structure=structure) == structure

    def test_set_foreign_keys_sets_legacy_foreign_key_params(self):
        table = _metadata_with_constraints().tables["child"]
        table_structure = {column.name: SQLDbWrpr._column_to_legacy_field(column) for column in table.columns}

        SQLDbWrpr._set_foreign_keys(table, table_structure)

        assert table_structure["parent_id"]["Params"]["FKey"] == [1, 1, "parent", "id", "C", "N"]

    def test_set_indexes_sets_legacy_index_params(self):
        table = _metadata_with_constraints().tables["child"]
        table_structure = {column.name: SQLDbWrpr._column_to_legacy_field(column) for column in table.columns}

        SQLDbWrpr._set_indexes(table, table_structure)

        assert table_structure["code"]["Params"]["Index"] == [1, 1, "A", "U"]

    def test_set_primary_key_sets_legacy_primary_key_params(self):
        table = _metadata_with_constraints().tables["parent"]
        table_structure = {column.name: SQLDbWrpr._column_to_legacy_field(column) for column in table.columns}

        SQLDbWrpr._set_primary_key(table, table_structure)

        assert table_structure["id"]["Params"]["PrimaryKey"] == ["Y", "A"]

    def test_table_to_legacy_structure_returns_complete_table_structure(self):
        table = _metadata_with_constraints().tables["child"]

        result = SQLDbWrpr._table_to_legacy_structure(table)

        assert result["id"]["Params"]["PrimaryKey"] == ["Y", "A"]
        assert result["parent_id"]["Params"]["FKey"] == [1, 1, "parent", "id", "C", "N"]
        assert result["code"]["Params"]["Index"] == [1, 1, "A", "U"]


def _build_sqldb():
    sqldb = object.__new__(SQLDbWrpr)
    sqldb.bar_len = 50
    sqldb.batch_size = 10000
    sqldb.char_fields = {}
    sqldb.conn = FakeConnection()
    sqldb.cur = FakeCursor()
    sqldb.db_error = Exception
    sqldb.db_name = "SampleDb"
    sqldb.db_structure = _db_structure()
    sqldb.fkey_ref_act = {
        "C": "CASCADE",
        "R": "RESTRICT",
        "D": "SET DEFAULT",
        "N": "SET NULL",
    }
    sqldb.host_name = "localhost"
    sqldb.identifier_quote = ""
    sqldb.idx_type = {"U": "UNIQUE", "F": "FULLTEXT", "S": "SPATIAL"}
    sqldb.inline_indexes = True
    sqldb.logger = SimpleNamespace(error=lambda p_message: None, warning=lambda p_message: None)
    sqldb.msg_width = 50
    sqldb.non_char_fields = {}
    sqldb.silent = False
    sqldb.sort_order = {"A": "ASC", "D": "DESC"}
    sqldb.success = False
    sqldb.table_load_order = []
    sqldb.get_db_field_types()
    return sqldb


def _db_structure():
    return {
        "Sample": {
            "Name": {
                "Type": ["varchar", 10],
                "Params": _params(p_primary_key=["Y", "A"], p_not_null="Y"),
                "Possible Values": "",
                "Comment": "",
            }
        }
    }


def _metadata_with_constraints():
    metadata = MetaData()
    parent = Table("parent", metadata, Column("id", Integer, primary_key=True))
    child = Table(
        "child",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey(parent.c.id, ondelete="CASCADE")),
        Column("code", String(10)),
    )
    Index("idx_child_code", child.c.code, unique=True)
    return metadata


def _params(p_primary_key=None, p_not_null="", p_default=""):
    return {
        "PrimaryKey": p_primary_key or ["", ""],
        "FKey": [],
        "Index": [],
        "NN": p_not_null,
        "B": "",
        "UN": "",
        "ZF": "",
        "AI": "",
        "G": "",
        "DEF": p_default,
    }
