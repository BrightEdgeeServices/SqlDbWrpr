from copy import deepcopy

from sqldbwrpr.sqldbwrpr import PostgreSQL


class RecordingConnection:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class RecordingCursor:
    def __init__(self):
        self.executed = []
        self.executemany_calls = []

    def execute(self, p_sql, p_params=None):
        self.executed.append((p_sql, p_params))

    def executemany(self, p_sql, p_rows):
        self.executemany_calls.append((p_sql, p_rows))


class TestPostgreSQL:
    def test_build_insert_sql_uses_on_conflict_for_replace(self):
        pg_db = self._build_postgresql_wrapper()

        result = pg_db.build_insert_sql("member", ["id", "name"], p_replace=True)

        assert result == (
            'INSERT INTO "member" ("id","name") VALUES (%s,%s) '
            'ON CONFLICT ("id") DO UPDATE SET "name" = EXCLUDED."name"'
        )

    def test_create_tables_generates_postgresql_table_and_index_sql(self):
        pg_db = self._build_postgresql_wrapper()

        pg_db.create_tables()

        executed_sql = [sql for sql, params in pg_db.cur.executed]
        assert executed_sql == [
            'CREATE TABLE "country" ("code" VARCHAR(3) NOT NULL, "description" VARCHAR(30), PRIMARY KEY ("code"))',
            'CREATE TABLE "member" ("id" SERIAL, "country_code" VARCHAR(3) NOT NULL, "name" VARCHAR(30) NOT NULL, PRIMARY KEY ("id"), CONSTRAINT fk_member_country FOREIGN KEY ("country_code") REFERENCES "country" ("code") ON DELETE CASCADE ON UPDATE RESTRICT)',
            'CREATE UNIQUE INDEX "unq_name" ON "member" ("name" ASC)',
        ]

    def test_import_csv_uses_postgresql_insert_sql(self):
        pg_db = self._build_postgresql_wrapper()
        csv_db = [("id", "country_code", "name"), (1, "NOR", "Carlsen")]

        result = pg_db.import_csv("member", p_csv_db=csv_db, p_vol_type="Single")

        assert result is True
        assert pg_db.cur.executemany_calls == [
            (
                'INSERT INTO "member" ("id","country_code","name") VALUES (%s,%s,%s)',
                [(1, "NOR", "Carlsen")],
            )
        ]
        assert pg_db.conn.commits == 1

    def test_render_field_type_maps_legacy_types_to_postgresql(self):
        pg_db = self._build_postgresql_wrapper()

        assert pg_db.render_field_type(["bigint"], {"AI": "Y"}) == "BIGSERIAL"
        assert pg_db.render_field_type(["blob"], {"AI": ""}) == "BYTEA"
        assert pg_db.render_field_type(["datetime"], {"AI": ""}) == "TIMESTAMP"
        assert pg_db.render_field_type(["tinyint"], {"AI": ""}) == "SMALLINT"

    @staticmethod
    def _build_postgresql_wrapper():
        pg_db = object.__new__(PostgreSQL)
        pg_db.bar_len = 50
        pg_db.batch_size = 10000
        pg_db.char_fields = {}
        pg_db.conn = RecordingConnection()
        pg_db.cur = RecordingCursor()
        pg_db.db_error = Exception
        pg_db.db_structure = deepcopy(_db_structure())
        pg_db.fkey_ref_act = {
            "C": "CASCADE",
            "R": "RESTRICT",
            "D": "SET DEFAULT",
            "N": "SET NULL",
        }
        pg_db.identifier_quote = '"'
        pg_db.inline_indexes = False
        pg_db.logger = _Logger()
        pg_db.msg_width = 50
        pg_db.non_char_fields = {}
        pg_db.silent = False
        pg_db.sort_order = {"A": "ASC", "D": "DESC"}
        pg_db.table_load_order = []
        pg_db.get_db_field_types()
        return pg_db


class _Logger:
    def error(self, p_message):
        raise AssertionError(p_message)

    def warning(self, p_message):
        raise AssertionError(p_message)


def _field(p_type, p_primary_key=None, p_foreign_key=None, p_index=None, p_not_null="", p_auto_increment=""):
    return {
        "Type": p_type,
        "Params": {
            "PrimaryKey": p_primary_key or ["", ""],
            "FKey": p_foreign_key or [],
            "Index": p_index or [],
            "NN": p_not_null,
            "B": "",
            "UN": "",
            "ZF": "",
            "AI": p_auto_increment,
            "G": "",
            "DEF": "",
        },
        "Possible Values": "",
        "Comment": "",
    }


def _db_structure():
    return {
        "country": {
            "code": _field(["varchar", 3], p_primary_key=["Y", "A"], p_not_null="Y"),
            "description": _field(["varchar", 30]),
        },
        "member": {
            "id": _field(["int"], p_primary_key=["Y", "A"], p_auto_increment="Y"),
            "country_code": _field(
                ["varchar", 3],
                p_foreign_key=[1, 1, "country", "code", "C", "R"],
                p_not_null="Y",
            ),
            "name": _field(["varchar", 30], p_index=[1, 1, "A", "U"], p_not_null="Y"),
        },
    }
