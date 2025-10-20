# Copilot / AI agent instructions for FactorForge Backtester

Purpose: give AI coding agents the minimal, high-value context and rules needed to be productive immediately in this repository.

Keep edits small and focused. Preserve existing public APIs and tests unless the task explicitly requires refactoring.

1) Big picture & architecture (what to read first)
- Top-level purpose: modular, auditable backtesting for factor-based strategies (see `README.md`).
- Major components:
  - `data/` — ingestion & normalization (`price_fetcher.py`, `snapshot_store.py`, `normalizer.py`). These write and read immutable snapshots used downstream.
  - `features/` — feature computations and persistence (`feature_store.py`). Features are computed on price snapshots and saved with metadata to `features/store/`.
  - `engine/` — strategy interface and backtest orchestration (look for `engine/` files; this is where strategies, rebalancing, and P&L are coordinated).
  - `api/` — FastAPI endpoints (refer to `docs/API_REFERENCE.md` for expected shapes). `api/main.py` provides run/results/health endpoints.
  - `ui/` — Streamlit demo dashboard for interactive runs.
  - `reporting/` — exports and report generation.
  - `tests/` — unit tests; use them as a guide to expected behavior and edge cases.
- Dataflow summary: `data.fetch` -> raw snapshot -> `normalizer` -> `features.compute` -> `strategy` -> `engine.run_backtest` -> `reporting/export`.

2) Key files to reference for patterns and behavior
- `features/feature_store.py` — examples of how indicators are computed using `pandas_ta`, how results are normalized to DataFrames, and how features + metadata are saved/loaded. Tests for this file are in `tests/test_feature_store.py` and `tests/test_feature_store_more.py`.
- `data/price_fetcher.py` — use this to understand how price inputs are shaped and what columns to expect (Close, Adj Close, Volume, etc.).
- `data/snapshot_store.py` — shows snapshot persistence conventions (file naming, directories).
- `docs/UI_Strategy_Config.md` — canonical JSON schema and recommended server-side evaluation pattern for UI-created strategies.
- `docs/Algorithmic_Backtester_Tasks.md` and `docs/Ideation/*` — high-level design rationale and tradeoffs (provenance, vectorized vs event-driven, use of adjusted prices).

3) Developer workflows (how to run/tests/debug)
- Recommended environment (from `README.md`): Conda with Python 3.12. Run `pip install -r requirements.txt` after activating the environment.
- Tests: run `pytest` from the repo root. Use the provided `scripts/run_tests.ps1` via the VS Code task "Run Pytest with Coverage" if on Windows/PowerShell.
- Quick commands:
  - Run Streamlit UI: `streamlit run ui/dashboard.py`
  - Run API: `uvicorn api.main:app --reload`
  - Run a sample CLI backtest: `python cli/run_backtest.py --tickers AAPL MSFT --start 2022-01-01 --end 2023-01-01`
- When adding tests: prefer small, deterministic tests that avoid network calls. Use temp directories (`tmp_path`) for file-based tests and patch module-level paths if necessary (see `tests/test_feature_store_more.py` for an example of loading `features/feature_store.py` without package imports).

4) Project-specific conventions and patterns
- Features are vectorized and returned as DataFrames aligned exactly to input index. Preserve index alignment when modifying feature functions.
- Persist provenance: when adding new feature calculations or strategy configs, include metadata (params, created_by, timestamp) and store it alongside the data (see `FEATURE_DIR` usage).
- Avoid eval() on UI strings. Use an AST-based safe evaluator for boolean expressions (see `docs/UI_Strategy_Config.md`).
- Prefer functional, vectorized implementations (pandas/numpy) over row-wise loops for performance. The codebase generally expects vectorized outputs.
- Tests sometimes load modules directly by file path to avoid package import issues — keep this pattern when adding tests that need to import modules not installed as packages.

5) Integration points & external dependencies
- External libs used: `pandas`, `numpy`, `pandas_ta`, `yfinance` (in `data/price_fetcher.py`), `fastapi`/`uvicorn` (API), `streamlit` (UI). Avoid network calls in tests; mock or use cached snapshots.
- File-based persistence: snapshots and features are stored under `data/snapshots/` and `features/store/`. Respect these locations for provenance and avoid changing layout without updating tests and docs.

6) Guidance for common tasks (examples)
- Adding a new indicator:
  1. Add mapping in `features/feature_store.py` `UI_INDICATOR_MAP`.
  2. Implement or call a `pandas_ta` function via `compute_indicator` patterns.
  3. Add unit tests covering DataFrame shape, index alignment, and error conditions.
  4. Update `docs/UI_Strategy_Config.md` if the indicator should be exposed in the UI.

- Implementing a new strategy from UI config:
  - Follow the `docs/UI_Strategy_Config.md` schema. Compute features once, evaluate signals safely, then map signals to weights. Persist config JSON with run metadata.

7) Safety rules for AI agents
- Never edit unrelated files in broad sweeping commits. Make focused changes and run local tests.
- Preserve public function signatures unless refactoring with tests and a clear migration path.
- When changing persistence paths or file formats, update tests and `docs/` concurrently.
- Avoid adding secrets or network calls to tests. If external data is needed, use cached snapshots under `data/snapshots/`.

8) Where to look when stuck
- Failing tests: open the failing test file in `tests/` to understand the expectation.
- Data shape issues: inspect `data/price_fetcher.py` and the snapshot files in `data/snapshots/`.
- Feature bugs: `features/feature_store.py` is the canonical location; its tests are the best spec.

If anything in this doc is unclear or you'd like me to include more examples (AST evaluator sample, JSON Schema file, or test templates), say so and I'll iterate.

---

Appendix: small recipes & examples

1) Safe AST evaluator (server-side)
- Purpose: evaluate boolean expressions produced by the UI (e.g. "sma20 > sma50 and rsi14 < 30") without using eval().
- Minimal recipe (conceptual):
  - Parse: `tree = ast.parse(expr, mode='eval')`
  - Walk: allow only nodes: Expression, BoolOp, Compare, Name, Load, Num/Constant, And/Or, Not, UnaryOp, Call (if you whitelist functions).
  - Replace `Name` nodes by looking up precomputed feature columns (DataFrame columns named by feature `id`).
  - Compile a safe function that receives a row or vectorized DataFrame and returns boolean mask.
  - See `docs/UI_Strategy_Config.md` for recommended config shape.

2) Test-loading pattern used in `tests/test_feature_store_more.py`
- The repo sometimes avoids package imports by loading modules from file path in tests. Example pattern:

```py
spec = importlib.util.spec_from_file_location('features.feature_store', path_to_file)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
# now use mod.compute_indicator(...)
```

Use this when importing the module as a package would fail in the test environment.

3) Quick pytest / coverage commands (Windows PowerShell)
- Run all tests:
```powershell
pytest
```
- Run a single test file:
```powershell
pytest .\tests\test_feature_store_more.py -q
```
- Run coverage for a specific module (used during development):
```powershell
pytest .\tests\test_feature_store_more.py --cov=features.feature_store --cov-report=term-missing
```

If you want more examples (e.g., a full AST evaluator implementation or a test template for adding indicators), tell me which one and I'll add a ready-to-run snippet.

🎯 1. Stop the Endless Loop (Tool Usage Constraint)

Primary Directive: Generate code that completes the immediate task based on the surrounding context.

Tool Priority: NEVER suggest or output runCommands or runTasks unless the user explicitly asks to "run" the code or "execute" a specific task. Default to providing code or explanations.

Improvement Rule: DO NOT suggest architectural, stylistic, or efficiency improvements on code that has already been accepted or written, unless the suggestion corrects a critical error (e.g., a security vulnerability, a name error, or a crash-inducing bug).

Focus: Aim for "good enough, now move on" code.

🧠 2. Stay on Target (Focus Constraint)

Scope: Limit suggestions strictly to the current function, class method, or script block being edited.

Context Window: Ignore surrounding files and broader project context unless explicitly relevant to resolving an import or a type definition.

Avoid: Do not suggest new functions, classes, or endpoints that were not directly implied by the prompt or the existing code structure. Do not introduce new libraries unless an import is missing for an established pattern.

📝 3. Be Succinct (Verbosity Constraint)

Suggestion Length: Prefer single-line completions. If a multiline suggestion is necessary (e.g., for a function body), limit the suggestion to a maximum of 6 lines of code or 2 lines of inline comment/docstring.

Documentation: DO NOT generate full, verbose docstrings for every function. Only provide minimal type hints and a single, brief comment explaining non-obvious logic, if necessary.

Preference: Always prioritize code over comments.

🔋 4. Code Quality & Style (Overriding Constraint)

OVERRIDE: The directives below MUST be followed, even if it slightly increases the suggestion length required by Section 3.

Strict Pylint/Flake8 Compliance: All generated Python code MUST adhere to PEP 8 standards (snake_case, 4-space indent).

Strict Typing: Use explicit type hints for ALL function signatures and variables. Use TypeAlias for complex types, and avoid Any where possible.

Specific Exceptions: Use specific exceptions (e.g., FileNotFoundError) and avoid bare except: or except Exception:.

Typing: Use modern Python type hints for all function signatures and variable assignments.

Summary to Copilot:

Be brief, stay in the immediate file and scope, but prioritize strict PEP 8 and Pylint/Flake8 compliance (specific exceptions, mandatory type hints) above all else. Do not suggest run commands unless explicitly asked.