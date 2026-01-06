# SqlDbWrpr

| **Category** | **Status' and Links**                                                                                                                                                                         |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| General      | [![][general_maintenance_y_img]][general_maintenance_y_lnk] [![][general_semver_pic]][general_semver_link] [![][general_license_img]][general_license_lnk]                                    |
| CD/CI        | [![][gh_tests_img]][gh_tests_lnk] [![][cicd_codestyle_img]][cicd_codestyle_lnk] [![][cicd_pre_commit_img]][cicd_pre_commit_lnk] [![][codecov_img]][codecov_lnk] [![][gh_doc_img]][gh_doc_lnk] |
| PyPI         | [![][pypi_release_img]][pypi_release_lnk] [![][pypi_py_versions_img]][pypi_py_versions_lnk] [![][pypi_format_img]][pypi_format_lnk] [![][pypi_downloads_img]][pypi_downloads_lnk]             |
| Github       | [![][gh_issues_img]][gh_issues_lnk] [![][gh_language_img]][gh_language_lnk] [![][gh_last_commit_img]][gh_last_commit_lnk] [![][gh_deployment_img]][gh_deployment_lnk]                         |

## Overview

SqlDbWrpr is a Python-based utility designed to simplify interactions with SQL databases, specifically MySQL and MSSQL. It provides a high-level abstraction for common database operations, making it easier to manage database schemas, import/export data, and handle user permissions.

### Key Features

- **Schema Management**: Define your database structure (tables, fields, types, primary keys, foreign keys, and indexes) using a simple Python dictionary. SqlDbWrpr handles the creation of the database and tables based on this definition.
- **Data Import/Export**:
  - Effortlessly import data from CSV files into your SQL tables. It supports both single and multi-volume CSV files and handles data type conversions and date formatting.
  - Export table data or custom SQL query results back to CSV files, with options for multi-volume exports if the data size is large.
- **User and Permission Management**: Create and delete database users and grant them specific rights across the database.
- **SSL Support**: Secure your database connections with built-in support for SSL CA, key, and certificate files.
- **Batch Processing**: Optimize performance during data imports with configurable batch sizes.
- **Multi-Database Support**: Includes dedicated classes for MySQL and MSSQL, ensuring compatibility across different SQL environments.

### Installation

```bash
pip install SqlDbWrpr
```

### Quick Start

```python
from sqldbwrpr.sqldbwrpr import MySQL

# Define your database structure
db_structure = {
    "Users": {
        "ID": {
            "Type": ["int"],
            "Params": {"PrimaryKey": ["Y", "A"], "NN": "Y", "AI": "Y"},
        },
        "Username": {"Type": ["varchar", 50], "Params": {"NN": "Y"}},
        "Email": {"Type": ["varchar", 100], "Params": {"NN": "Y"}},
    }
}

# Initialize the wrapper
db = MySQL(
    p_host_name="localhost",
    p_user_name="root",
    p_password="yourpassword",
    p_db_name="my_database",
    p_db_structure=db_structure,
    p_recreate_db=True,
)

# Import data from CSV
db.import_csv("Users", "users_data.csv")

# Export data to CSV
db.export_to_csv("exported_users.csv", "Users")
```

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
