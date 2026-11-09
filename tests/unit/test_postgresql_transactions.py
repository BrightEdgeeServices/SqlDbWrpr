"""Real-driver checks of borrowed connections and import transaction ownership."""

from uuid import uuid4

import psycopg
import pytest
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table

from sqldbwrpr.sqldbwrpr import PostgreSQL


@pytest.fixture(params=["psycopg", "psycopg2"])
def transaction_wrapper(request, transaction_database):
    """Borrow either supported PostgreSQL driver with a committed, empty test table."""
    if request.param == "psycopg2":
        driver = pytest.importorskip("psycopg2")
    else:
        driver = psycopg
    connection = driver.connect(**transaction_database)
    metadata = MetaData()
    table = Table(
        f"imports_{uuid4().hex}", metadata, Column("id", Integer, primary_key=True), Column("name", String(50))
    )
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE TABLE "{table.name}" (id INTEGER PRIMARY KEY, name VARCHAR(50))')
    connection.commit()
    wrapper = PostgreSQL(p_connection=connection, p_sqlalchemy_metadata=metadata, p_batch_size=2)
    try:
        yield wrapper, table.name, driver
    finally:
        wrapper.close()
        connection.rollback()
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE "{table.name}"')
        connection.commit()
        connection.close()


class TestPostgreSQLTransactions:
    def test_borrowed_close_preserves_connection_and_autocommit(self, transaction_wrapper):
        wrapper, _, _ = transaction_wrapper
        connection = wrapper.conn
        assert connection.autocommit is False
        wrapper.close()
        assert not connection.closed
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)

    def test_default_import_still_commits(self, transaction_wrapper):
        wrapper, table, _ = transaction_wrapper
        wrapper.import_csv(table, p_csv_db=[("id", "name"), (1, "Committed")])
        wrapper.conn.rollback()
        wrapper.cur.execute(f'SELECT name FROM "{table}"')
        assert wrapper.cur.fetchall() == [("Committed",)]

    def test_failed_batch_propagates_without_commit_rollback_or_row_recovery(self, transaction_wrapper):
        wrapper, table, driver = transaction_wrapper
        with pytest.raises(driver.IntegrityError):
            wrapper.import_csv(
                table,
                p_csv_db=[("id", "name"), (1, "First"), (2, "Second"), (2, "Duplicate")],
                p_manage_transaction=False,
            )
        with pytest.raises(driver.errors.InFailedSqlTransaction):
            wrapper.cur.execute("SELECT 1")
        wrapper.conn.rollback()
        wrapper.cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        assert wrapper.cur.fetchone() == (0,)

    def test_import_batches_are_invisible_until_caller_commit(self, transaction_wrapper, transaction_database):
        wrapper, table, _ = transaction_wrapper
        wrapper.import_csv(
            table,
            p_csv_db=[("id", "name"), (1, "First"), (2, "Second"), (3, "Third")],
            p_manage_transaction=False,
        )
        with psycopg.connect(**transaction_database) as reader:
            assert reader.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone() == (0,)
        wrapper.conn.commit()
        with psycopg.connect(**transaction_database) as reader:
            assert reader.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone() == (3,)

    def test_invalid_modes_are_rejected(self, transaction_wrapper):
        wrapper, table, _ = transaction_wrapper
        with pytest.raises(ValueError, match="recreate"):
            PostgreSQL(p_connection=wrapper.conn, p_recreate_db=True)
        with pytest.raises(ValueError, match="positive"):
            PostgreSQL(p_connection=wrapper.conn, p_batch_size=0)
        wrapper.conn.autocommit = True
        with pytest.raises(ValueError, match="autocommit"):
            wrapper.import_csv(table, p_csv_db=[("id", "name"), (1, "Unsafe")], p_manage_transaction=False)
        with pytest.raises(ValueError, match="autocommit"):
            wrapper.update_rows(table, ("id", "name"), [(1, "Unsafe")])
        wrapper.conn.autocommit = False

    def test_split_import_leaves_transaction_to_caller(self, transaction_wrapper):
        wrapper, table, _ = transaction_wrapper
        split = {
            "Seq01": {
                "TableName": table,
                "Key": "id",
                "Replace": False,
                "Flds": [["id", "id", [0, 0, False, [[], ""]]], ["name", "name", [0, 0, False, [[], ""]]]],
            }
        }
        wrapper.import_and_split_csv(split, [("id", "name"), (1, "First"), (2, "Second")], p_manage_transaction=False)
        wrapper.conn.rollback()
        wrapper.cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        assert wrapper.cur.fetchone() == (0,)

    def test_updates_only_supplied_columns_and_never_inserts(self, transaction_wrapper):
        wrapper, table, _ = transaction_wrapper
        wrapper.import_csv(table, p_csv_db=[("id", "name"), (1, "Original")], p_manage_transaction=False)
        wrapper.update_rows(table, ("name", "id"), [("Updated", 1), ("Missing", 2)])
        wrapper.cur.execute(f'SELECT id, name FROM "{table}"')
        assert wrapper.cur.fetchall() == [(1, "Updated")]
        wrapper.conn.rollback()
        wrapper.cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        assert wrapper.cur.fetchone() == (0,)
