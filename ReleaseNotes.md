# Release 5.0.0

### Added

- New PowerShell setup scripts: `CreateDbSqlScript.ps1`, `InstallDevEnv.ps1`, `SetUpDocker.ps1`, `SetupDotEnv.ps1`, `SetupGitHubAccess.ps1`, `SetupPrivateRepoAccess.ps1`.
- Docker configuration with `.dockerignore` and `docker-compose.yaml`.
- GitHub Action workflows for PR and Merge processes.
- SQL setup script `scripts/setup_db.sql`.
- `README.md` (migrated from `README.rst`).

### Changed

- Major project restructuring and infrastructure updates.
- Updated `pyproject.toml` to use PEP 621 project metadata.
- Updated `.gitignore` and `.pre-commit-config.yaml`.
- Renamed `LICENSE` to `LICENSE.txt`.
- Improved `sqldbwrpr.py` to handle `bytearray` and `bytes` when fetching databases.

### Removed

- Discontinued GitHub workflows and issue templates.
- Old `docs` directory and `README.rst`.
- `.packageit` configuration.
- `docker-compose.yml` (replaced by `.yaml`) and `docker-rebuild.ps1`.

### Statistics

- **Changed files:** 50
- **Insertions:** 2335
- **Deletions:** 1978
- **Branch:** hendrik/urs-314-feature-sqldbwrpr-remove-discontinued-workflow
- **Files changed:**
  - .dockerignore
  - .flake8
  - .gitattributes
  - .github/CODEOWNERS
  - .github/ISSUE_TEMPLATE/bugfix.md
  - .github/ISSUE_TEMPLATE/config.yaml
  - .github/ISSUE_TEMPLATE/enhancement.md
  - .github/ISSUE_TEMPLATE/hotfix.md
  - .github/ISSUE_TEMPLATE/release.md
  - .github/dependabot.yaml
  - .github/workflows/00-deployment-pipeline.yaml
  - .github/workflows/01-pre-commit-and-document-check.yaml
  - .github/workflows/03-ci.yaml
  - .github/workflows/04-build-and-publish-to-pypi.yaml
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
  - README.rst
  - SetUpDocker.ps1
  - SetupDotEnv.ps1
  - SetupGitHubAccess.ps1
  - SetupPrivateRepoAccess.ps1
  - coverage.xml
  - docker-compose.yaml
  - docker-compose.yml
  - docker-rebuild.ps1
  - docs/Makefile
  - docs/make.bat
  - docs/requirements_docs.txt
  - docs/source/Installation.rst
  - docs/source/api.rst
  - docs/source/conf.py
  - docs/source/conventions.rst
  - docs/source/examples.rst
  - docs/source/faq.rst
  - docs/source/index.rst
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
