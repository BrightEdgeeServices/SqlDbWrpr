# SqlDbWrpr

| **Category** | **Status' and Links**                                                                                                                                                                         |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| General      | [![][general_maintenance_y_img]][general_maintenance_y_lnk] [![][general_semver_pic]][general_semver_link] [![][general_license_img]][general_license_lnk]                                    |
| CD/CI        | [![][gh_tests_img]][gh_tests_lnk] [![][cicd_codestyle_img]][cicd_codestyle_lnk] [![][cicd_pre_commit_img]][cicd_pre_commit_lnk] [![][codecov_img]][codecov_lnk] [![][gh_doc_img]][gh_doc_lnk] |
| PyPI         | [![][pypi_release_img]][pypi_release_lnk] [![][pypi_py_versions_img]][pypi_py_versions_lnk] [![][pypi_format_img]][pypi_format_lnk] [![][pypi_downloads_img]][pypi_downloads_lnk]             |
| Github       | [![][gh_issues_img]][gh_issues_lnk] [![][gh_language_img]][gh_language_lnk] [![][gh_last_commit_img]][gh_last_commit_lnk] [![][gh_deployment_img]][gh_deployment_lnk]                         |

## Short description

SqlDbWrpr is a Python wrapper that streamlines schema creation plus CSV import/export workflows for SQL backends.

## Module Overview

SqlDbWrpr is a Python utility for creating SQL database schemas and moving CSV data into and out of those schemas. It currently provides wrappers for MySQL and PostgreSQL.

Schemas can be supplied in two ways:

1. A legacy `db_structure` dictionary.
2. SQLAlchemy metadata, either directly through `p_sqlalchemy_metadata` or through `p_sqlalchemy_base.metadata`.

When both are supplied, `p_db_structure` takes precedence for backward compatibility. If no supported schema source is supplied, `SchemaSourceError` is raised.

### Key Features

- **Schema Management**: Create databases, tables, primary keys, foreign keys, and indexes from a legacy dictionary or SQLAlchemy metadata.
- **Data Import/Export**:
  - Import CSV data from files or in-memory rows, including single-volume and numbered multi-volume files.
  - Export full tables or custom SQL query results to CSV, including optional multi-volume exports.
- **Database Support**: Includes MySQL and PostgreSQL wrappers with dialect-specific SQL rendering.
- **User and Permission Management**: Create MySQL users and grant database rights.
- **Batch Processing**: Configure import batch sizes for larger CSV loads.

### Project Structure

- `src/sqldbwrpr/`: Core library implementation, including MySQL and PostgreSQL wrappers.
- `tests/`: Unit and integration-oriented test coverage for wrapper behaviour.
- `scripts/`: SQL setup/bootstrap assets used for database initialization.
- Root automation scripts (`*.ps1`) and CI configuration under `.github/workflows/` support setup and delivery.

## Getting Started

### Installation

```bash
pip install SqlDbWrpr
```

### Quick Start With A Legacy Structure

```python
from sqldbwrpr.sqldbwrpr import MySQL

field_defaults = {
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

db_structure = {
    "Users": {
        "ID": {
            "Type": ["int"],
            "Params": {
                **field_defaults,
                "PrimaryKey": ["Y", "A"],
                "NN": "Y",
                "AI": "Y",
            },
            "Possible Values": "",
            "Comment": "",
        },
        "Username": {
            "Type": ["varchar", 50],
            "Params": {**field_defaults, "NN": "Y"},
            "Possible Values": "",
            "Comment": "",
        },
    }
}

db = MySQL(
    p_host_name="localhost",
    p_user_name="root",
    p_password="yourpassword",
    p_db_name="my_database",
    p_db_structure=db_structure,
    p_recreate_db=True,
)

db.import_csv("Users", p_csv_db=[("Username",), ("alice",)], p_vol_type="Single")
db.export_to_csv("exported_users.csv", "Users")
```

### Quick Start With SQLAlchemy Metadata

```python
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table

from sqldbwrpr.sqldbwrpr import PostgreSQL

metadata = MetaData()
Table(
    "Users",
    metadata,
    Column("ID", Integer, primary_key=True, autoincrement=True),
    Column("Username", String(50), nullable=False),
)

db = PostgreSQL(
    p_host_name="localhost",
    p_user_name="postgres",
    p_password="yourpassword",
    p_db_name="my_database",
    p_sqlalchemy_metadata=metadata,
    p_recreate_db=True,
)

db.import_csv("Users", p_csv_db=[("Username",), ("alice",)], p_vol_type="Single")
```

______________________________________________________________________

## Updating ReleaseNotes Instructions

1. Run the `pushpy.ps1` script or manually commit the current changes.
2. Generate the release notes
3. Use one of the following AI propmpts in Notion to generate the release notes.

- [Release - Update - General](https://www.notion.so/Release-Update-General-2c0bc8e6c6f38076b4cee82e3cf243fa?v=2c0bc8e6c6f3806e85db000c395f94ce&source=copy_link)
- [Release - Update - VenvIt](https://www.notion.so/Release-Update-VenvIt-2c0bc8e6c6f380de84a0f3fbb8b5dda5?v=2c0bc8e6c6f3806e85db000c395f94ce&source=copy_link)

or

1. Use the following template and manually update the ReleaseNotes.md file.

   ```
    # Release ?.?.?
    ## Summary of Changes
    - bla, bla, bla
    ## Next Heading
    - bla, bla, bla
    ---
   ```

2. You can repeat step 1 multiple times.

3. You can repeat step 2 multiple times but update the ReleaseNotes that has not been published.

4. Run the `pushpr.ps1` script once you are ready to create the PR to publish the release. TOy can also manually create
   the tag, touch a file, commit and push the changes.

5. Merge the PR in GitHub.

6. Confirm the following:

7. The release update reflects in GitHub

8. The release update notification was sent

______________________________________________________________________

[cicd_codestyle_img]: https://img.shields.io/badge/code%20style-black-000000.svg "Black"
[cicd_codestyle_lnk]: https://github.com/psf/black "Black"
[cicd_pre_commit_img]: https://img.shields.io/github/actions/workflow/status/BrightEdgeeServices/SqlDbWrpr/pre-commit.yml?label=pre-commit "Pre-Commit"
[cicd_pre_commit_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr/blob/master/.github/workflows/pre-commit.yml "Pre-Commit"
[codecov_img]: https://img.shields.io/codecov/c/gh/BrightEdgeeServices/SqlDbWrpr "CodeCov"
[codecov_lnk]: https://app.codecov.io/gh/BrightEdgeeServices/SqlDbWrpr "CodeCov"
[general_license_img]: https://img.shields.io/pypi/l/SqlDbWrpr "License"
[general_license_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr/blob/master/LICENSE "License"
[general_maintenance_y_img]: https://img.shields.io/badge/Maintenance%20Intended-%E2%9C%94-green.svg?style=flat-square "Maintenance - intended"
[general_maintenance_y_lnk]: http://unmaintained.tech/ "Maintenance - intended"
[general_semver_link]: https://semver.org/ "Sentic Versioning - 2.0.0"
[general_semver_pic]: https://img.shields.io/badge/Semantic%20Versioning-2.0.0-brightgreen.svg?style=flat-square "Sentic Versioning - 2.0.0"
[gh_deployment_img]: https://img.shields.io/github/deployments/BrightEdgeeServices/SqlDbWrpr/pypi "GitHub - PiPy Deployment"
[gh_deployment_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr/deployments/pypi "GitHub - PiPy Deployment"
[gh_doc_img]: https://img.shields.io/readthedocs/SqlDbWrpr "Read the Docs"
[gh_doc_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr/blob/master/.github/workflows/check-rst-documentation.yml "Read the Docs"
[gh_issues_img]: https://img.shields.io/github/issues-raw/BrightEdgeeServices/SqlDbWrpr "GitHub - Issue Counter"
[gh_issues_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr/issues "GitHub - Issue Counter"
[gh_language_img]: https://img.shields.io/github/languages/top/BrightEdgeeServices/SqlDbWrpr "GitHub - Top Language"
[gh_language_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr "GitHub - Top Language"
[gh_last_commit_img]: https://img.shields.io/github/last-commit/BrightEdgeeServices/SqlDbWrpr/master "GitHub - Last Commit"
[gh_last_commit_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr/commit/master "GitHub - Last Commit"
[gh_tests_img]: https://img.shields.io/github/actions/workflow/status/BrightEdgeeServices/SqlDbWrpr/ci.yml?label=ci "Test status"
[gh_tests_lnk]: https://github.com/BrightEdgeeServices/SqlDbWrpr/blob/master/.github/workflows/ci.yml "Test status"
[pypi_downloads_img]: https://img.shields.io/pypi/dm/SqlDbWrpr "Monthly downloads"
[pypi_downloads_lnk]: https://pypi.org/project/SqlDbWrpr/ "Monthly downloads"
[pypi_format_img]: https://img.shields.io/pypi/wheel/SqlDbWrpr "PyPI - Format"
[pypi_format_lnk]: https://pypi.org/project/SqlDbWrpr/ "PyPI - Format"
[pypi_py_versions_img]: https://img.shields.io/pypi/pyversions/SqlDbWrpr "PyPI - Supported Python Versions"
[pypi_py_versions_lnk]: https://pypi.org/project/SqlDbWrpr/ "PyPI - Supported Python Versions"
[pypi_release_img]: https://img.shields.io/pypi/v/SqlDbWrpr "Test status"
[pypi_release_lnk]: https://pypi.org/project/SqlDbWrpr/ "Test status"
