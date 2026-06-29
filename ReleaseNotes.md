# Release 5.1.0

2026-06-29 23:22 UTC+02:00

### Added

- Added PostgreSQL-focused helper module files: `tests/helpers/__init__.py` and `tests/helpers/example_data.py`.
- Added dedicated unit test modules for base functions, branch coverage, examples, PostgreSQL behaviour, schema resolution, and split examples.
- Added workflow `.github/workflows/py-temp-pr-pub-no_docker-def.yaml`.
- Added repository agent guidance file `AGENTS.md`.

### Changed

- Expanded PostgreSQL backend support and related SQL handling in `src/sqldbwrpr/sqldbwrpr.py`.
- Updated project dependencies and metadata in `pyproject.toml` and refreshed `poetry.lock`.
- Updated CI and quality configuration: `.flake8`, `.pre-commit-config.yaml`, `.github/dependabot.yaml`, and `.github/workflows/py-temp-publish-pub-build_release_notify_after_merge-def.yaml`.
- Updated setup and automation scripts: `InstallDevEnv.ps1`, `SetUpDocker.ps1`, `SetupDotEnv.ps1`, and `SetupPrivateRepoAccess.ps1`.
- Updated project documentation and runtime assets in `README.md`, `docker-compose.yaml`, `coverage.xml`, and `tests/test_sqldbwrpr.py`.

### Removed

- Removed deprecated workflow/config files and scripts no longer used in this branch.

### Statistics

- **Changed files:** 32
- **Insertions:** 5452
- **Deletions:** 3625
- **Branch:** hendrik/bee-32-feat-sqldbwrpr-add-postgresql-backend-support
- **Files changed:**
  - .flake8
  - .github/dependabot.yaml
  - .github/workflows/py-temp-pr-pub-no_docker-def.yaml
  - .github/workflows/py-temp-pr-pub-with_docker-def.yaml
  - .github/workflows/py-temp-publish-pub-build_release_notify_after_merge-def.yaml
  - .gitignore
  - .pre-commit-config.yaml
  - .readthedocs.yaml
  - .rstcheck.cfg
  - AGENTS.md
  - DockerRebuild.ps1
  - InstallDevEnv.ps1
  - README.md
  - SetUpDocker.ps1
  - SetupDotEnv.ps1
  - SetupPrivateRepoAccess.ps1
  - coverage.xml
  - docker-compose.yaml
  - install.ps1
  - poetry.lock
  - pyproject.toml
  - src/sqldbwrpr/sqldbwrpr.py
  - tests/TestData/IncompleteRecords.csv
  - tests/helpers/__init__.py
  - tests/helpers/example_data.py
  - tests/test_sqldbwrpr.py
  - tests/unit/test_sqldbwrpr_base_functions.py
  - tests/unit/test_sqldbwrpr_coverage_branches.py
  - tests/unit/test_sqldbwrpr_examples.py
  - tests/unit/test_sqldbwrpr_postgresql.py
  - tests/unit/test_sqldbwrpr_schema_resolution.py
  - tests/unit/test_sqldbwrpr_split_examples.py

______________________________________________________________________

# Release 5.0.1

### Changed

- Updated `coverage.xml`.

### Removed

- Discontinued GitHub workflow: `.github/workflows/python-template-pypi-public-with-docker.yaml`.

### Statistics

- **Changed files:** 2
- **Insertions:** 1
- **Deletions:** 23
- **Branch:** hendrik/urs-314-feature-sqldbwrpr-remove-discontinued-workflow
- **Files changed:**
  - .github/workflows/python-template-pypi-public-with-docker.yaml
  - coverage.xml

______________________________________________________________________

# Release 5.0.0

### Added

- New PowerShell setup scripts: `CreateDbSqlScript.ps1`, `InstallDevEnv.ps1`, `SetUpDocker.ps1`, `SetupDotEnv.ps1`, `SetupGitHubAccess.ps1`, `SetupPrivateRepoAccess.ps1`, `install.ps1`.
- Docker configuration: `.dockerignore`.
- GitHub Action workflows for PR and Merge processes.
- SQL setup script `scripts/setup_db.sql`.
- `README.md` (extensively updated with Overview, Features, Installation, and Quick Start).
- `tests/conftest.py`.

### Changed

- Major project restructuring and infrastructure updates.
- Updated `pyproject.toml`: bumped version to `5.0.0`, updated dependencies, and added project metadata.
- Updated `.gitignore` with more comprehensive exclusions.
- Updated `.pre-commit-config.yaml`.
- Improved `src/sqldbwrpr/sqldbwrpr.py` to handle `bytearray` and `bytes` when fetching databases.
- Updated `docker-compose.yaml` and `coverage.xml`.

### Removed

- Discontinued GitHub workflows and issue templates (deleted `.github/CODEOWNERS`, issue templates).
- `.packageit` configuration (deleted `.packageit/packageit.ini`, `.packageit/release.toml`).

### Statistics

- **Changed files:** 32
- **Insertions:** 1695
- **Deletions:** 1549
- **Branch:** hendrik/urs-314-feature-sqldbwrpr-remove-discontinued-workflow
- **Files changed:**
  - .dockerignore
  - .gitattributes
  - .github/CODEOWNERS
  - .github/ISSUE_TEMPLATE/bugfix.md
  - .github/ISSUE_TEMPLATE/config.yaml
  - .github/ISSUE_TEMPLATE/enhancement.md
  - .github/ISSUE_TEMPLATE/hotfix.md
  - .github/ISSUE_TEMPLATE/release.md
  - .github/workflows/py-temp-pr-pub-with_docker-def.yaml
  - .github/workflows/py-temp-publish-pub-build_release_notify_after_merge-def.yaml
  - .gitignore
  - .packageit/packageit.ini
  - .packageit/release.toml
  - .pre-commit-config.yaml
  - CreateDbSqlScript.ps1
  - InstallDevEnv.ps1
  - LICENSE.txt
  - README.md
  - ReleaseNotes.md
  - SetUpDocker.ps1
  - SetupDotEnv.ps1
  - SetupGitHubAccess.ps1
  - SetupPrivateRepoAccess.ps1
  - coverage.xml
  - docker-compose.yaml
  - install.ps1
  - poetry.lock
  - pyproject.toml
  - scripts/setup_db.sql
  - src/sqldbwrpr/sqldbwrpr.py
  - tests/conftest.py
  - tests/test_sqldbwrpr.py

______________________________________________________________________

# Release 4.2.0

-

______________________________________________________________________
