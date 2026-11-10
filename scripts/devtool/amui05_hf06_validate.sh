#!/usr/bin/env sh
set -eu
# This is persistent repository source. Devtool's temporary metadata directory
# may disappear while the large regression suite is running; never depend on it
# after the test suite starts. Check syntax BEFORE running any tests.
sh -n "$0"
python3 -B scripts/devtool/check_amui05_acceptance.py --check
python3 -B scripts/devtool/test_amui05_hf06_scope.py
python3 -B scripts/devtool/test_amui05_hf06_recovery.py
python3 -B scripts/devtool/test_amui05_hf06_validation.py
python3 -B scripts/devtool/test_amui05_hf06_metadata.py
python3 -B scripts/devtool/test_amui05_hf03_recovery.py
python3 -B scripts/devtool/check_amui04d_final_gate.py --check
python3 -B scripts/devtool/check_amui02_theme.py --check
python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v
printf 'AMUI05_HF06_VALIDATION_FULL_SOURCE_AND_REGRESSION_SUITE_PASS\n'
