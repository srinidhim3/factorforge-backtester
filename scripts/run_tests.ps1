$env:PYTHONPATH = (Get-Location)
conda run -n factorforge python -m pytest -q tests/ --cov=. --cov-report=term-missing --maxfail=3 --disable-warnings -v