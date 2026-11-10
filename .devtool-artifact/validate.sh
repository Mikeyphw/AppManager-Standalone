#!/usr/bin/env sh
set -eu
# HF06: this script is an explicit inventory payload (not skipped metadata).
# The long suite executes from ordinary source, not ephemeral archive metadata.
sh -n "$0"
sh -n scripts/devtool/amui05_hf06_validate.sh
exec sh scripts/devtool/amui05_hf06_validate.sh
