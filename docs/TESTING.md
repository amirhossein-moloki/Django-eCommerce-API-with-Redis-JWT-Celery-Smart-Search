# Running tests and collecting coverage

This project ships with pytest configuration that automatically sets the test
settings module (`ecommerce_api.settings.test`), applies migrations at session
start, and flushes the database between individual tests. Coverage is collected
using Python's built-in `trace` module via the `--cov` flag rather than the
`coverage` package.

## Prerequisites (local)
- Python 3.11+
- Virtual environment tooling (e.g., `python -m venv`)
- Dependencies from `requirements-dev.txt`

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Running tests
- Run the entire suite with a short-circuit on the first failure:
  ```bash
  pytest --maxfail=1
  ```
- Run a specific test file or node:
  ```bash
  pytest tests/path/to/test_file.py -k test_name
  ```

## Collecting coverage
The `--cov` flag accepts one or more paths to trace. Reports are printed to the
terminal (default `term-missing`) and also written to `trace_coverage_report.txt`
for later inspection.

```bash
pytest --cov account --cov shop --cov ecommerce_api --cov-report term-missing
```

## Docker workflow
If you prefer containers, ensure the stack is up and the `web` service has
pytest installed:
```bash
docker-compose up -d
```

- Run tests inside the container:
  ```bash
  docker-compose exec web pytest --maxfail=1
  ```
- Collect coverage inside the container:
  ```bash
  docker-compose exec web pytest \
    --cov account --cov shop --cov ecommerce_api --cov-report term-missing
  ```

The coverage summary and `trace_coverage_report.txt` behave the same inside
Docker.
