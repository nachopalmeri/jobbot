#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"

echo "== Health =="
curl -fsS "$API_URL/health"
echo

echo "== Public stats =="
curl -fsS "$API_URL/stats"
echo

echo "== Root =="
curl -fsS "$API_URL/"
echo

echo "Sanity check finished"
