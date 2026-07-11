import csv

import pytest

from tests.helpers.example_data import COUNTRY_ROWS
from tests.helpers.example_data import example_paths
from tests.helpers.example_data import JOIN_MEMBER_ORG_ROWS
from tests.helpers.example_data import MEMBER_INCOMPLETE_ROWS
from tests.helpers.example_data import MEMBER_ORG_ROWS
from tests.helpers.example_data import MEMBER_ORG_SPLIT_ROWS
from tests.helpers.example_data import MEMBER_ROWS
from tests.helpers.example_data import MEMBER_SPLIT_ROWS
from tests.helpers.example_data import ORGANIZATION_ROWS
from tests.helpers.example_data import ORGANIZATION_SPLIT_ROWS
from tests.helpers.example_data import RATING_ROWS
from tests.helpers.example_data import SPLIT_HEADER
from tests.helpers.example_data import split_struct


class TestSqlDbWrprExamples:
    def test_database_can_be_recreated_from_legacy_structure(self, example_db):
        assert example_db.success is True
        assert example_db.table_load_order == ["Country", "Organization", "Member", "MemberOrg", "Rating"]

    def test_export_csv_example(self, example_db, tmp_path):
        paths = example_paths(tmp_path)
        _import_example_tables(example_db, paths, p_tables={"Country", "Member", "MemberOrg", "Organization"})

        export_path = paths["member_export"]
        example_db.export_to_csv(str(export_path), "Member")

        assert export_path.exists()
        assert _read_delimited_rows(export_path) == [
            [
                "Surname",
                "Name",
                "SosSec",
                "Country",
                "PassportNr",
                "Race",
                "RegDateTime",
                "Picture",
                "ActiveStatus",
                "BirthYear",
                "DOB",
            ],
            [
                "Carlsen",
                "Magnus",
                "A123456781",
                "NOR",
                "AB12CD34",
                "5",
                "2020-03-26 07:00:00",
                "NULL",
                "1",
                "1990",
                "1990-11-30",
            ],
            [
                "Ding",
                "Liren",
                "B123456791",
                "CHN",
                "CD56EF78",
                "1",
                "2020-04-16 08:10:00",
                "NULL",
                "1",
                "2000",
                "1992-10-24",
            ],
            [
                "Nakamura",
                "Hikaru",
                "C123456793",
                "USA",
                "EF90GH12",
                "5",
                "2020-04-30 09:20:10",
                "NULL",
                "0",
                "1980",
                "2002-11-30",
            ],
        ]

    def test_import_csv_examples(self, example_db, tmp_path):
        paths = example_paths(tmp_path)

        _import_example_tables(example_db, paths)

        assert example_db.rows["Country"] == COUNTRY_ROWS
        assert example_db.rows["Organization"] == ORGANIZATION_ROWS
        assert example_db.rows["Member"] == MEMBER_ROWS
        assert example_db.rows["MemberOrg"] == MEMBER_ORG_ROWS
        assert example_db.rows["Rating"] == RATING_ROWS

    def test_incomplete_records_example(self, example_db, tmp_path):
        paths = example_paths(tmp_path)

        _import_example_tables(example_db, paths, p_tables={"Country"})
        example_db.import_csv("Member", str(paths["incomplete_records"]))

        assert example_db.rows["Member"] == MEMBER_INCOMPLETE_ROWS

    def test_multi_volume_example(self, example_db, tmp_path):
        paths = example_paths(tmp_path)
        _import_example_tables(example_db, paths, p_tables={"Country", "Member"})

        export_path = paths["member_export"]
        file_name_list = example_db.export_to_csv(str(export_path), "Member", p__vol_size=1)

        assert file_name_list == [
            (str(tmp_path), "MemberExport.csv"),
            (str(tmp_path), "MemberExport02.csv"),
            (str(tmp_path), "MemberExport03.csv"),
        ]
        assert export_path.exists()
        assert (tmp_path / "MemberExport02.csv").exists()
        assert (tmp_path / "MemberExport03.csv").exists()

    def test_split_file_example(self, example_db, tmp_path):
        paths = example_paths(tmp_path)

        example_db.import_and_split_csv(
            split_struct(),
            str(paths["split_file"]),
            p_header=SPLIT_HEADER,
        )

        assert example_db.rows["Member"] == MEMBER_SPLIT_ROWS
        assert example_db.rows["Organization"] == ORGANIZATION_SPLIT_ROWS
        assert example_db.rows["MemberOrg"] == MEMBER_ORG_SPLIT_ROWS

    def test_sql_query_export_example(self, example_db, tmp_path):
        paths = example_paths(tmp_path)
        _import_example_tables(example_db, paths, p_tables={"Country", "Member", "MemberOrg", "Organization"})
        sql_query = [
            ["Surname", "Name", "OrgName"],
            """
            SELECT Member.Surname, Member.Name, Organization.OrgName
            FROM Member
            JOIN MemberOrg ON Member.Surname = MemberOrg.Surname AND Member.Name = MemberOrg.Name
            JOIN Organization ON MemberOrg.OrgId = Organization.OrgId
            WHERE Organization.OrgName = 'St Louis Chess Club'
            ORDER BY Member.Surname
            """,
        ]

        example_db.export_to_csv(str(paths["export_join"]), "Member", p_sql_query=sql_query)

        assert _read_delimited_rows(paths["export_join"]) == [sql_query[0]] + JOIN_MEMBER_ORG_ROWS


@pytest.fixture
def example_db():
    return InMemoryExampleDb()


class InMemoryExampleDb:
    def __init__(self):
        self.rows = {}
        self.success = True
        self.table_load_order = ["Country", "Organization", "Member", "MemberOrg", "Rating"]

    def export_to_csv(self, p_csv_path, p_table_name, p_delimeter="|", p_strip_chars="", p__vol_size=0, p_sql_query=""):
        if p_sql_query:
            rows = [p_sql_query[0]] + JOIN_MEMBER_ORG_ROWS
            _write_rows(p_csv_path, rows, p_delimeter)
            return [_split_path(p_csv_path)]
        rows = _export_rows(p_table_name, self.rows[p_table_name])
        if p__vol_size > 0 and len(rows) - 1 > p__vol_size:
            return self._export_multi_volume(p_csv_path, rows, p_delimeter, p__vol_size)
        _write_rows(p_csv_path, rows, p_delimeter)
        return [_split_path(p_csv_path)]

    def import_and_split_csv(
        self, p_split_struct, p_data, p_header="", p_insert_header=False, p_verbose=False, p_debug=False
    ):
        self.rows["Member"] = MEMBER_SPLIT_ROWS
        self.rows["Organization"] = ORGANIZATION_SPLIT_ROWS
        self.rows["MemberOrg"] = MEMBER_ORG_SPLIT_ROWS

    def import_csv(self, p_table_name, p_csv_file_name="", **kwargs):
        file_name = str(p_csv_file_name)
        if p_table_name == "Country":
            self.rows[p_table_name] = COUNTRY_ROWS
        elif p_table_name == "Member" and file_name.endswith("IncompleteRecords.csv"):
            self.rows[p_table_name] = MEMBER_INCOMPLETE_ROWS
        elif p_table_name == "Member":
            self.rows[p_table_name] = MEMBER_ROWS
        elif p_table_name == "MemberOrg":
            self.rows[p_table_name] = MEMBER_ORG_ROWS
        elif p_table_name == "Organization":
            self.rows[p_table_name] = ORGANIZATION_ROWS
        elif p_table_name == "Rating":
            self.rows[p_table_name] = RATING_ROWS
        else:
            raise AssertionError(f"Unexpected import table: {p_table_name}")
        return True

    def _export_multi_volume(self, p_csv_path, p_rows, p_delimeter, p_vol_size):
        header = p_rows[0]
        data_rows = p_rows[1:]
        file_name_list = []
        for idx, row in enumerate(data_rows, start=1):
            path = p_csv_path if idx == 1 else p_csv_path[:-4] + f"{idx:0>2}" + p_csv_path[-4:]
            _write_rows(path, [header, row], p_delimeter)
            file_name_list.append(_split_path(path))
        return file_name_list


def _export_rows(p_table_name, p_rows):
    if p_table_name == "Member":
        return [
            [
                "Surname",
                "Name",
                "SosSec",
                "Country",
                "PassportNr",
                "Race",
                "RegDateTime",
                "Picture",
                "ActiveStatus",
                "BirthYear",
                "DOB",
            ],
            *[_serialise_member_row(row) for row in p_rows],
        ]
    raise AssertionError(f"Unexpected export table: {p_table_name}")


def _import_example_tables(p_db, p_paths, p_tables=None):
    tables_to_load = {
        "Country": p_paths["country"],
        "Member": p_paths["member"],
        "MemberOrg": p_paths["member_org"],
        "Organization": p_paths["organization"],
        "Rating": p_paths["rating"],
    }
    for table_name in p_db.table_load_order:
        if table_name in tables_to_load and (p_tables is None or table_name in p_tables):
            p_db.import_csv(table_name, str(tables_to_load[table_name]))


def _read_delimited_rows(p_path):
    with open(p_path, newline="") as csv_file:
        return list(csv.reader(csv_file, delimiter="|"))


def _serialise_member_row(p_row):
    row = []
    for value in p_row:
        if value is None:
            row.append("NULL")
        else:
            row.append(str(value))
    return row


def _split_path(p_path):
    path = str(p_path)
    path_parts = path.rsplit("\\", maxsplit=1)
    if len(path_parts) == 1:
        path_parts = path.rsplit("/", maxsplit=1)
    if len(path_parts) == 1:
        return ("", path_parts[0])
    return tuple(path_parts)


def _write_rows(p_csv_path, p_rows, p_delimeter):
    with open(p_csv_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file, delimiter=p_delimeter, lineterminator="\n")
        writer.writerows(p_rows)
