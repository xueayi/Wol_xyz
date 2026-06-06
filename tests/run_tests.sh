#!/bin/bash
set -e
cd "$(dirname "$0")/.."
pip install -q -r tests/requirements-test.txt 2>/dev/null
pytest tests/ -v --tb=short "$@"
