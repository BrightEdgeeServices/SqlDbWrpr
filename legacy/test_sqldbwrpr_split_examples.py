from sqldbwrpr.sqldbwrpr import SQLDbWrpr
from tests.helpers.example_data import SPLIT_CSV_ROWS
from tests.helpers.example_data import SPLIT_HEADER
from tests.helpers.example_data import split_struct


class CapturingSqlDbWrpr(SQLDbWrpr):
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


class TestSqlDbWrprSplitExamples:
    def test_import_and_split_csv_transforms_legacy_example(self):
        sqldb = object.__new__(CapturingSqlDbWrpr)
        sqldb.bar_len = 50
        sqldb.imports = []
        sqldb.msg_width = 50

        sqldb.import_and_split_csv(split_struct(), SPLIT_CSV_ROWS, p_header=SPLIT_HEADER)

        assert sqldb.imports == [
            {
                "table_name": "Member",
                "header": (
                    "Surname",
                    "Name",
                    "SosSec",
                    "Country",
                    "PassportNr",
                    "Race",
                    "Picture",
                    "ActiveStatus",
                    "BirthYear",
                    "DOB",
                ),
                "replace": False,
                "csv_db": [
                    (
                        "Surname",
                        "Name",
                        "SosSec",
                        "Country",
                        "PassportNr",
                        "Race",
                        "Picture",
                        "ActiveStatus",
                        "BirthYear",
                        "DOB",
                    ),
                    ("Carlsen", "Magnus", "A123456781", "NOR", 100, 5, None, 1, "1990", "1990/01/01"),
                    ("Ding", "Liren", "B123456791", "CHN", 101, 1, None, 1, "2000", "2000/01/01"),
                    ("Nakamura", "Hikaru", "C123456793", "USA", 102, 5, None, 1, "1980", "1980/01/01"),
                ],
            },
            {
                "table_name": "Organization",
                "header": ("OrgId", "OrgName", "RegFee", "OpenTrading"),
                "replace": True,
                "csv_db": [
                    ("OrgId", "OrgName", "RegFee", "OpenTrading"),
                    ("6", "Ice Cold", "20", "08:00:00"),
                    ("3", "St Louis", "100", "09:00:00"),
                ],
            },
            {
                "table_name": "MemberOrg",
                "header": ("Surname", "Name", "OrgId"),
                "replace": False,
                "csv_db": [
                    ("Surname", "Name", "OrgId"),
                    ("Carlsen", "Magnus", "6"),
                    ("Nakamura", "Hikaru", "3"),
                ],
            },
        ]
