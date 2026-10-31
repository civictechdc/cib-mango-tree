#!/usr/bin/env bash
set -euo pipefail

echo "CIB Mango Tree Codespaces: installing dependencies…"
echo "(First run often takes several minutes. This is normal.)"
uv sync
echo "Dependencies installed."
