import datetime
from pathlib import Path

TEST_DATA_DIR = Path(__file__).resolve().parents[1] / "TestData"

COUNTRY_ROWS = [
    ("CHN", "China"),
    ("NOR", "Norway"),
    ("USA", "United States of America"),
]

JOIN_MEMBER_ORG_ROWS = [
    ["Ding", "Liren", "St Louis Chess Club"],
    ["Nakamura", "Hikaru", "St Louis Chess Club"],
]

MEMBER_ACTIVE_ROWS = [
    ("Carlsen", "Magnus", 1),
    ("Ding", "Liren", 1),
    ("Nakamura", "Hikaru", 0),
]

MEMBER_ORG_ROWS = [
    ("Carlsen", "Magnus", 6),
    ("Ding", "Liren", 3),
    ("Nakamura", "Hikaru", 3),
]

MEMBER_ORG_SPLIT_ROWS = [
    ("Carlsen", "Magnus", 6),
    ("Nakamura", "Hikaru", 3),
]

MEMBER_ROWS = [
    (
        "Carlsen",
        "Magnus",
        "A123456781",
        "NOR",
        "AB12CD34",
        5,
        datetime.datetime(year=2020, month=3, day=26, hour=7, minute=0),
        None,
        1,
        1990,
        datetime.date(1990, 11, 30),
    ),
    (
        "Ding",
        "Liren",
        "B123456791",
        "CHN",
        "CD56EF78",
        1,
        datetime.datetime(year=2020, month=4, day=16, hour=8, minute=10),
        None,
        1,
        2000,
        datetime.date(1992, 10, 24),
    ),
    (
        "Nakamura",
        "Hikaru",
        "C123456793",
        "USA",
        "EF90GH12",
        5,
        datetime.datetime(year=2020, month=4, day=30, hour=9, minute=20, second=10),
        None,
        0,
        1980,
        datetime.date(2002, 11, 30),
    ),
]

MEMBER_INCOMPLETE_ROWS = [row[:-1] + (None,) for row in MEMBER_ROWS]

MEMBER_SPLIT_ROWS = [
    (
        "Carlsen",
        "Magnus",
        "A123456781",
        "NOR",
        "100",
        5,
        None,
        None,
        1,
        1990,
        datetime.date(year=1990, month=1, day=1),
    ),
    (
        "Ding",
        "Liren",
        "B123456791",
        "CHN",
        "101",
        1,
        None,
        None,
        1,
        2000,
        datetime.date(year=2000, month=1, day=1),
    ),
    (
        "Nakamura",
        "Hikaru",
        "C123456793",
        "USA",
        "102",
        5,
        None,
        None,
        1,
        1980,
        datetime.date(year=1980, month=1, day=1),
    ),
]

ORGANIZATION_ROWS = [
    (2, "Boondocs Chess Club", 150.00, datetime.timedelta(seconds=68400)),
    (3, "St Louis Chess Club", 100.00, datetime.timedelta(seconds=32400)),
    (6, "Ice Cold Chess Club", 20.00, datetime.timedelta(seconds=28800)),
]

ORGANIZATION_SPLIT_ROWS = [
    (3, "St Louis", 100.00, datetime.timedelta(seconds=32400)),
    (6, "Ice Cold", 20.00, datetime.timedelta(seconds=28800)),
]

RATING_ROWS = [
    (datetime.date(2020, 2, 29), "Hikaru", "Nakamura", 2750, 123456),
    (datetime.date(2020, 2, 29), "Liren", "Ding", 2800, 234567),
    (datetime.date(2020, 2, 29), "Magnus", "Carlsen", 2850, 456789),
    (datetime.date(2020, 3, 31), "Hikaru", "Nakamura", 2760, 123456),
    (datetime.date(2020, 3, 31), "Liren", "Ding", 2830, 234567),
    (datetime.date(2020, 3, 31), "Magnus", "Carlsen", 2845, 456789),
]

SPLIT_CSV_ROWS = [
    (
        "SurnameName",
        "IDNr",
        "Country",
        "PassportNr",
        "Race",
        "Picture",
        "ActiveStatus",
        "OrgId",
        "OrgName",
        "RegFee",
        "OpenTrading",
        "BirthYear",
    ),
    (
        "Carlsen,Magnus",
        "A123456781",
        "NOR",
        "AB12CD34",
        "White",
        "NULL",
        "1",
        "6",
        "Ice Cold Chess Club",
        "20",
        "08:00:00",
        "1990",
    ),
    (
        "Ding,Liren",
        "B123456791",
        "",
        "CD56EF78",
        "Asian",
        "NULL",
        "1",
        "",
        "St Louis Chess Club",
        "100",
        "09:00:00",
        "2000",
    ),
    (
        "Nakamura,Hikaru",
        "C123456793",
        "USA",
        "EF90GH12",
        "White",
        "NULL",
        "0",
        "3",
        "St Louis Chess Club",
        "100",
        "09:00:00",
        "1980",
    ),
]

SPLIT_HEADER = [
    "SurnameName",
    "IDNr",
    "Country",
    "PassportNr",
    "Race",
    "Picture",
    "ActiveStatus",
    "OrgId",
    "OrgName",
    "RegFee",
    "OpenTrading",
    "BirthYear",
]


def example_paths(p_tmp_path=None):
    export_dir = p_tmp_path or TEST_DATA_DIR
    return {
        "country": TEST_DATA_DIR / "Country.csv",
        "export_join": export_dir / "JoinExport.csv",
        "incomplete_records": TEST_DATA_DIR / "IncompleteRecords.csv",
        "member": TEST_DATA_DIR / "Member.csv",
        "member_export": export_dir / "MemberExport.csv",
        "member_org": TEST_DATA_DIR / "MemberOrg.csv",
        "member_org_export": export_dir / "MemberOrgExport.csv",
        "organization": TEST_DATA_DIR / "Organization.csv",
        "organization_export": export_dir / "OrganizationExport.csv",
        "rating": TEST_DATA_DIR / "Rating.csv",
        "split_file": TEST_DATA_DIR / "SplitFile01.csv",
    }


def split_struct():
    look_up_tbl = {"Asian": 1, "Black": 2, "White": 5}
    return {
        "Seq01": {
            "TableName": "Member",
            "Key": "Surname",
            "Replace": False,
            "Flds": [
                ["SurnameName", "Surname", [2, 0, True]],
                ["SurnameName", "Name", [2, 1, True]],
                ["IDNr", "SosSec", [0, 0, True, [[]]]],
                ["Country", "Country", [0, 0, True, [["", None], "CHN"]]],
                ["None", "PassportNr", [6, 100, True]],
                ["Race", "Race", [4, look_up_tbl, True]],
                ["Picture", "Picture", [1, None, False]],
                ["ActiveStatus", "ActiveStatus", [1, 1, True]],
                ["BirthYear", "BirthYear", [0, 0, True, [[]]]],
                ["BirthYear", "DOB", [3, "Date", True]],
            ],
        },
        "Seq02": {
            "TableName": "Organization",
            "Key": "OrgId",
            "Replace": True,
            "Flds": [
                ["OrgId", "OrgId", [0, 0, True]],
                ["OrgName", "OrgName", [5, [0, 8], True]],
                ["RegFee", "RegFee", [0, 0, True]],
                ["OpenTrading", "OpenTrading", [0, 0, True]],
            ],
        },
        "Seq03": {
            "TableName": "MemberOrg",
            "Key": "Surname",
            "Replace": False,
            "Flds": [
                ["SurnameName", "Surname", [2, 0, True]],
                ["SurnameName", "Name", [2, 1, True]],
                ["OrgId", "OrgId", [0, 0, True]],
            ],
        },
    }
