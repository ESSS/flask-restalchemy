# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv python pin 3.10
uv sync --group dev
source .venv/bin/activate
```

If `serialchemy` is a sibling repo, install it editable:
```bash
uv pip install -e ../serialchemy
```

## Commands

```bash
# Run all tests
pytest src/flask_restalchemy/tests/

# Run a single test
pytest src/flask_restalchemy/tests/test_api.py::test_post

# Run linting (pre-commit)
tox -e linting

# Run full tox matrix (SQLAlchemy 1.4 and 2.x)
tox
```

## Architecture

The library wraps a Flask app or Blueprint and exposes SQLAlchemy models as REST endpoints with zero boilerplate serialization.

### Core classes (`src/flask_restalchemy/`)

**`api.py` — `Api`**  
The public entry point. `add_model()`, `add_relation()`, and `add_property()` are the three main registration methods. Internally they all call `add_resource()`, which calls `register_view()` to set up the Flask URL rules. `register_view()` handles the four standard route patterns (GET collection, POST, GET/PUT/DELETE item) and respects a `methods` allowlist. `init_app()` supports lazy initialization (construct `Api()` with no blueprint, bind later).

**`resources/resources.py` — Resource classes**  
Each resource class inherits `BaseResource → BaseModelResource`:
- `ModelResource` — CRUD for a top-level model (`/employees`, `/employees/<id>`)
- `ToManyRelationResource` — LIST/CREATE/UPDATE/DELETE for a relationship (`/companies/<id>/employees`). Requires `lazy="dynamic"` on the SQLAlchemy relationship to support filtering and pagination; falls back to `InstrumentedList` with a warning otherwise.
- `CollectionPropertyResource` — read-only collection from a Python `@property`; POST always returns 405.
- `ViewFunctionResource` — wraps a plain function as a resource (used by `add_url_rule` / `@api.route`).

Request decorators are managed by `ResourceDecorators` (a `Mapping` subclass). Decorators can be a callable, a list, or a dict keyed by HTTP verb; API-level and resource-level decorators are merged.

**`resources/querybuilder.py`**  
Translates URL query params into SQLAlchemy query modifications:
- `?filter=<json>` — supports `$or`, `$and`, and per-field operators (`eq`, `like`, `ilike`, `between`, `in`, `startswith`, etc.)
- `?order_by=<col>` / `?order_by=-<col>` — case-insensitive for VARCHAR; handles `AssociationProxyInstance` via `outerjoin`
- `?limit=<n>` — hard cap on results
- `?page=<n>&per_page=<n>` — pagination (requires Flask-SQLAlchemy's `.paginate()`)

**`serialization.py`**  
Re-exports `ModelSerializer`, `ColumnSerializer`, and field classes from the `serialchemy` package. `Api.register_column_serializer()` appends to the global `ModelSerializer.EXTRA_SERIALIZERS` list — this is a class-level side effect and should be cleaned up in tests.

### Tests (`src/flask_restalchemy/tests/`)

Tests use `conftest.py` fixtures:
- `flask_app` — function-scoped Flask app with SQLite in-memory DB
- `db_session` — creates all tables, yields `db.session`, drops all tables on teardown
- `client` — Flask test client

Some tests use `data_regression` (from `pytest-regressions`) with golden `.yml` files stored alongside the test file (e.g., `test_api/test_get.yml`). To update golden files run `pytest --gen-files`.

The `filterwarnings` in `pyproject.toml` promotes `LegacyAPIWarning` to an error for SQLAlchemy, so avoid deprecated SQLAlchemy patterns.
