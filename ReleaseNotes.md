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
