from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CHAR
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import MetaData
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Time
from sqlalchemy.types import TypeEngine

import sqldbwrpr.sqldbwrpr as sqldbwrpr_module
from sqldbwrpr.sqldbwrpr import MySQL
from sqldbwrpr.sqldbwrpr import PostgreSQL
from sqldbwrpr.sqldbwrpr import SQLDbWrpr


class BranchConnection:
    def __init__(self, p_connected=True):
        self.autocommit = False
        self.closed = False
        self.commits = 0
        self.connected = p_connected
        self.cursor_obj = BranchCursor()
        self.init_db = None
        self.rollbacks = 0

    def close(self):
        self.closed = True

    def cmd_init_db(self, p_db_name):
        self.init_db = p_db_name

    def commit(self):
        self.commits += 1

    def cursor(self):
        return self.cursor_obj

    def is_connected(self):
        return self.connected

    def rollback(self):
        self.rollbacks += 1


class BranchCursor:
    def __init__(self, p_fetchall_results=None, p_fetchone_results=None):
        self.executed = []
        self.executemany_calls = []
        self.fetchall_results = list(p_fetchall_results or [])
        self.fetchone_results = list(p_fetchone_results or [])

    def execute(self, p_sql, p_params=None):
        self.executed.append((p_sql, p_params))

    def executemany(self, p_sql, p_rows):
        self.executemany_calls.append((p_sql, p_rows))

    def fetchall(self):
        return self.fetchall_results.pop(0)

    def fetchone(self):
        return self.fetchone_results.pop(0)


class TestSQLDbWrprCoverageBranches:
    def test_build_column_sql_renders_auto_increment_unsigned_and_zero_fill(self):
        sqldb = _build_sqldb(_numeric_structure())

        auto_inc = sqldb.build_column_sql("Id", ["int"], _params(p_auto_increment="Y"), "")
        unsigned = sqldb.build_column_sql("Counter", ["int"], _params(p_unsigned="Y"), "")
        zero_fill = sqldb.build_column_sql("Code", ["int"], _params(p_zero_fill="Y"), "")

        assert auto_inc == "Id int AUTO_INCREMENT"
        assert unsigned == "Counter int UNSIGNED"
        assert zero_fill == "Code int ZEROFILL"

    def test_create_tables_orders_foreign_key_tables_and_removes_overlap(self):
        sqldb = _build_sqldb(_overlap_structure())

        assert sqldb.create_tables() is True

        executed_sql = [sql for sql, params in sqldb.cur.executed]
        assert executed_sql == [
            "CREATE TABLE Child (Id int NOT NULL, ParentId int NOT NULL, PRIMARY KEY (Id,ParentId))",
            "CREATE TABLE Parent (Id int NOT NULL, PRIMARY KEY (Id))",
        ]
        assert sqldb.db_structure["Child"]["ParentId"]["Params"]["FKey"] == []
        assert sqldb.table_load_order == ["Child", "Parent"]

    def test_export_to_csv_writes_multi_volume_files(self, tmp_path):
        sqldb = _build_sqldb(_sample_structure())
        sqldb.cur = BranchCursor(
            [
                [(3,)],
                [("A",), ("B",), ("C",)],
                [("Alice",)],
                [("Bob",)],
                [("Cara",)],
            ]
        )
        export_path = tmp_path / "Sample.csv"

        result = sqldb.export_to_csv(str(export_path), "Sample", p__vol_size=1)

        assert result == [(str(tmp_path), "Sample.csv"), (str(tmp_path), "Sample02.csv")]
        assert export_path.read_text() == "Name\nAlice\nBob\n"
        assert (tmp_path / "Sample02.csv").read_text() == "Name\nCara\n"

    def test_export_to_csv_uses_custom_sql_query(self, tmp_path):
        sqldb = _build_sqldb(_sample_structure())
        sqldb.cur = BranchCursor([[(1,)], [("Alice", "Club")]])
        export_path = tmp_path / "Join.csv"

        result = sqldb.export_to_csv(str(export_path), "Sample", p_sql_query=(["Name", "Club"], "SELECT Name, Club"))

        assert result == [(str(tmp_path), "Join.csv")]
        assert export_path.read_text() == "Name|Club\nAlice|Club\n"
        assert sqldb.cur.executed[-1] == ("SELECT Name, Club", None)

    def test_import_csv_batches_records_and_replaces_rows(self):
        sqldb = _build_sqldb(_sample_structure())
        sqldb.batch_size = 1

        result = sqldb.import_csv("Sample", p_csv_db=[("Name",), ("Alice",), ("Bob",)], p_replace=True)

        assert result is True
        assert sqldb.cur.executemany_calls == [
            ("REPLACE INTO Sample (Name) VALUES (%s)", [("Alice",)]),
            ("REPLACE INTO Sample (Name) VALUES (%s)", [("Bob",)]),
            ("REPLACE INTO Sample (Name) VALUES (%s)", []),
        ]
        assert sqldb.conn.commits == 3

    def test_import_csv_converts_date_datetime_and_blank_non_char_fields(self):
        sqldb = _build_sqldb(_date_structure())

        result = sqldb.import_csv(
            "Dates",
            p_csv_db=[("Created", "DOB", "Score"), ("20/03/26 07:00", "90/11/30", "")],
            p_vol_type="Single",
        )

        assert result is True
        assert sqldb.cur.executemany_calls == [
            (
                "INSERT INTO Dates (Created,DOB,Score) VALUES (%s,%s,%s)",
                [("20/03/26 07:00", "1990/11/30", None)],
            )
        ]

    def test_import_and_split_csv_accepts_inline_rows_and_insert_header(self):
        sqldb = _build_capturing_split_db()
        split_rows = [("Source", "Year"), ("AB", "2020")]
        split_config = {
            "Seq01": {
                "TableName": "Sample",
                "Key": "Part",
                "Replace": False,
                "Flds": [
                    ["Source", "Part", [5, [0, 1], True]],
                    ["Year", "Created", [3, "Date", True]],
                ],
            }
        }

        sqldb.import_and_split_csv(split_config, split_rows, p_header=["Source", "Year"], p_insert_header=True)

        assert sqldb.imports == [
            {
                "table_name": "Sample",
                "csv_db": [("Part", "Created"), ("S", "Year/01/01"), ("A", "2020/01/01")],
                "header": ("Part", "Created"),
                "replace": False,
            }
        ]

    def test_mysql_init_connects_and_selects_database(self, monkeypatch):
        connection = BranchConnection()

        def fake_connect(**kwargs):
            return connection

        monkeypatch.setattr(sqldbwrpr_module.mysql.connector, "connect", fake_connect)

        mysql_db = MySQL(p_user_name="root", p_password="pwd", p_db_name="SampleDb", p_db_structure=_sample_structure())

        assert mysql_db.success is True
        assert mysql_db.conn is connection
        assert connection.init_db == "SampleDb"
        assert connection.commits == 1

    def test_mysql_init_recreates_database(self, monkeypatch):
        connection = BranchConnection()
        calls = []

        monkeypatch.setattr(sqldbwrpr_module.mysql.connector, "connect", lambda **kwargs: connection)
        monkeypatch.setattr(MySQL, "create_db", lambda self: calls.append("create_db") or True)
        monkeypatch.setattr(MySQL, "create_tables", lambda self: calls.append("create_tables") or True)

        mysql_db = MySQL(p_user_name="root", p_password="pwd", p_recreate_db=True, p_db_structure=_sample_structure())

        assert mysql_db.success is True
        assert calls == ["create_db", "create_tables"]

    def test_postgresql_init_connects_to_target_database(self, monkeypatch):
        connection = BranchConnection()

        monkeypatch.setattr(sqldbwrpr_module.psycopg, "connect", lambda **kwargs: connection)

        pg_db = PostgreSQL(
            p_host_name="localhost",
            p_user_name="postgres",
            p_password="pwd",
            p_db_name="SampleDb",
            p_db_structure=_sample_structure(),
        )

        assert pg_db.success is True
        assert pg_db.conn is connection
        assert connection.autocommit is True

    def test_postgresql_create_db_drops_existing_database_and_reconnects(self):
        pg_db = object.__new__(PostgreSQL)
        first_connection = BranchConnection()
        second_connection = BranchConnection()
        first_connection.cursor_obj = BranchCursor(p_fetchone_results=[(1,)])
        pg_db.conn = first_connection
        pg_db.cur = first_connection.cursor_obj
        pg_db.db_error = Exception
        pg_db.db_name = "SampleDb"
        pg_db.identifier_quote = '"'
        pg_db._connect = lambda p_db_name: second_connection

        result = pg_db.create_db()

        assert result is True
        assert first_connection.cursor_obj.executed == [
            ("SELECT 1 FROM pg_database WHERE datname = %s", ("SampleDb",)),
            ('DROP DATABASE "SampleDb" WITH (FORCE)', None),
            ('CREATE DATABASE "SampleDb"', None),
        ]
        assert first_connection.closed is True
        assert pg_db.conn is second_connection
        assert second_connection.autocommit is True

    def test_postgresql_rendering_branches(self):
        pg_db = _build_postgresql_renderer()

        assert pg_db.build_column_sql("Name", ["varchar", 10], _params(p_not_null="Y", p_default="O'Reilly"), "") == (
            "\"Name\" VARCHAR(10) NOT NULL DEFAULT 'O''Reilly'"
        )
        assert pg_db.build_index_sql("Sample", "idx_name", [["Name", 1, "A", ""]], p_unique=False) == (
            'CREATE INDEX "idx_name" ON "Sample" ("Name" ASC)'
        )
        assert pg_db.build_insert_sql("NoPk", ["Name"], p_replace=True) == (
            'INSERT INTO "NoPk" ("Name") VALUES (%s) ON CONFLICT DO NOTHING'
        )
        assert pg_db.build_insert_sql("OnlyPk", ["Id"], p_replace=True) == (
            'INSERT INTO "OnlyPk" ("Id") VALUES (%s) ON CONFLICT ("Id") DO NOTHING'
        )
        assert pg_db.render_field_type(["custom"], _params()) == "CUSTOM"
        assert pg_db.render_default_sql(["int"], "1") == " DEFAULT 1"

    def test_sqlalchemy_type_conversion_branches(self):
        table = _metadata_type_columns()

        assert SQLDbWrpr._column_type_to_legacy(table.c.big) == ["bigint"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.flag) == ["boolean"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.fixed) == ["char", 3]
        assert SQLDbWrpr._column_type_to_legacy(table.c.unbounded) == ["varchar"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.created) == ["datetime"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.dob) == ["date"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.count) == ["int"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.data) == ["blob"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.price) == ["decimal", 8, 2]
        assert SQLDbWrpr._column_type_to_legacy(table.c.ratio) == ["decimal"]
        assert SQLDbWrpr._column_type_to_legacy(table.c.opened) == ["time"]
        assert SQLDbWrpr._column_type_to_legacy(Column("custom", CustomType())) == ["customtype"]


class CustomType(TypeEngine):
    pass


class CapturingSplitDb(SQLDbWrpr):
    def import_csv(
        self,
        p_table_name,
        p_csv_file_name="",
        p_key="",
        p_header="",
        p_del_head=False,
        p_csv_db="",
        p_csv_corr_str_file_name="",
        p_vol_type="Multi",
        p_verbose=False,
        p_replace=False,
    ):
        self.imports.append(
            {
                "table_name": p_table_name,
                "csv_db": p_csv_db,
                "header": p_header,
                "replace": p_replace,
            }
        )
        return True


def _build_capturing_split_db():
    sqldb = object.__new__(CapturingSplitDb)
    sqldb.bar_len = 50
    sqldb.imports = []
    sqldb.msg_width = 50
    return sqldb


def _build_postgresql_renderer():
    pg_db = object.__new__(PostgreSQL)
    pg_db.db_structure = {
        "NoPk": {"Name": {"Params": _params()}},
        "OnlyPk": {"Id": {"Params": _params(p_primary_key=["Y", "A"])}},
    }
    pg_db.identifier_quote = '"'
    pg_db.sort_order = {"A": "ASC", "D": "DESC"}
    return pg_db


def _build_sqldb(p_db_structure):
    sqldb = object.__new__(SQLDbWrpr)
    sqldb.bar_len = 50
    sqldb.batch_size = 10000
    sqldb.char_fields = {}
    sqldb.conn = BranchConnection()
    sqldb.cur = BranchCursor()
    sqldb.db_error = Exception
    sqldb.db_name = "SampleDb"
    sqldb.db_structure = p_db_structure
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
    sqldb.logger = SimpleLogger()
    sqldb.msg_width = 50
    sqldb.non_char_fields = {}
    sqldb.silent = False
    sqldb.sort_order = {"A": "ASC", "D": "DESC"}
    sqldb.success = False
    sqldb.table_load_order = []
    sqldb.get_db_field_types()
    return sqldb


class SimpleLogger:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, p_message):
        self.errors.append(p_message)

    def warning(self, p_message):
        self.warnings.append(p_message)


def _date_structure():
    return {
        "Dates": {
            "Created": _field(["datetime"], p_primary_key=["Y", "A"]),
            "DOB": _field(["date"]),
            "Score": _field(["int"]),
        }
    }


def _numeric_structure():
    return {
        "Numeric": {
            "Id": _field(["int"], p_auto_increment="Y"),
            "Counter": _field(["int"], p_unsigned="Y"),
            "Code": _field(["int"], p_zero_fill="Y"),
        }
    }


def _overlap_structure():
    return {
        "Child": {
            "Id": _field(["int"], p_primary_key=["Y", "A"], p_not_null="Y"),
            "ParentId": _field(
                ["int"],
                p_primary_key=["Y", "A"],
                p_foreign_key=[1, 1, "Parent", "Id", "C", "C"],
                p_not_null="Y",
            ),
        },
        "Parent": {
            "Id": _field(["int"], p_primary_key=["Y", "A"], p_not_null="Y"),
        },
    }


def _sample_structure():
    return {
        "Sample": {
            "Name": _field(["varchar", 10], p_primary_key=["Y", "A"], p_not_null="Y"),
        }
    }


def _field(
    p_type,
    p_primary_key=None,
    p_foreign_key=None,
    p_index=None,
    p_not_null="",
    p_auto_increment="",
    p_unsigned="",
    p_zero_fill="",
    p_default="",
):
    return {
        "Type": p_type,
        "Params": _params(
            p_primary_key=p_primary_key,
            p_foreign_key=p_foreign_key,
            p_index=p_index,
            p_not_null=p_not_null,
            p_auto_increment=p_auto_increment,
            p_unsigned=p_unsigned,
            p_zero_fill=p_zero_fill,
            p_default=p_default,
        ),
        "Possible Values": "",
        "Comment": "",
    }


def _params(
    p_primary_key=None,
    p_foreign_key=None,
    p_index=None,
    p_not_null="",
    p_auto_increment="",
    p_unsigned="",
    p_zero_fill="",
    p_default="",
):
    return {
        "PrimaryKey": p_primary_key or ["", ""],
        "FKey": p_foreign_key or [],
        "Index": p_index or [],
        "NN": p_not_null,
        "B": "",
        "UN": p_unsigned,
        "ZF": p_zero_fill,
        "AI": p_auto_increment,
        "G": "",
        "DEF": p_default,
    }


def _metadata_type_columns():
    metadata = MetaData()
    return Table(
        "types",
        metadata,
        Column("big", BigInteger),
        Column("flag", Boolean),
        Column("fixed", CHAR(3)),
        Column("unbounded", String),
        Column("created", DateTime),
        Column("dob", Date),
        Column("count", Integer),
        Column("data", LargeBinary),
        Column("price", Numeric(8, 2)),
        Column("ratio", Numeric),
        Column("opened", Time),
    )
