#!/bin/bash
# Test if Flask backend (Network Impact Analyzer) is running on port 5001.
# Start it first: cd backend && python3 app.py

set -e
BASE="${1:-http://127.0.0.1:5001}"

echo "Checking $BASE ..."
if curl -sf "$BASE/health" > /dev/null; then
  echo "  /health: OK"
  curl -s "$BASE/health" | python3 -m json.tool 2>/dev/null || curl -s "$BASE/health"
else
  echo "  /health: FAIL (is the backend running? cd backend && python3 app.py)"
  exit 1
fi

if curl -sf "$BASE/" > /dev/null; then
  echo "  /: OK"
else
  echo "  /: FAIL"
  exit 1
fi
echo "Backend is running."
