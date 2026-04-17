# Project Mandates (Rappi Competitive Intelligence)

This project follows strict engineering and operational standards. All development must adhere to these rules:

## 1. Dependency Management
- **Tool:** Use `uv` for all dependency management.
- **Rule:** Never use `pip` or `conda` directly. 
- **Command:** `uv add <package>` or `uv add --dev <package>`.

## 2. Communication & Language
- **Development:** Code, variable names, comments, and internal documentation (like this file) must be in **English**.
- **Public Facing:** The final user-facing application (Plotly Dash) and the primary documentation (`README.md`) must be in **Spanish**.

## 3. Architecture
- **Layout:** Follow the `src/` layout.
  - `src/`: Main source code.
  - `notebooks/`: Jupyter notebooks for EDA and research.
  - `scripts/`: One-off or ad-hoc scripts.
  - `tests/`: Pytest test suite.
- **CLI:** Use `typer` for all command-line tools.
- **Pipelines:** Use custom Python scripts for pipelines initially.
- **Dashboard:** Use **Plotly Dash** for the dashboard.

## 4. Engineering Standards
- **Testing:** Use `pytest` for unit and integration tests.
- **Types:** Use Python type hints where possible.
- **Numerical Ops:** Use `numpy` and `pandas` for data manipulation.
- **Scraping:** Use `playwright` (Python) for browser automation.
