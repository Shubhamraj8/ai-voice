#!/usr/bin/env sh
# Quick health check for local or Render API (ticket 1.17 verification)
BASE_URL="${1:-http://localhost:8000}"
URI="${BASE_URL%/}/health"

echo "GET $URI"
START=$(date +%s%3N 2>/dev/null || python -c "import time; print(int(time.time()*1000))")
HTTP_CODE=$(curl -sS -o /tmp/health-body.json -w "%{http_code}" "$URI")
END=$(date +%s%3N 2>/dev/null || python -c "import time; print(int(time.time()*1000))")
ELAPSED=$((END - START))

echo "Status: $HTTP_CODE"
echo "Time:   ${ELAPSED} ms"
cat /tmp/health-body.json
echo ""

if [ "$HTTP_CODE" != "200" ]; then
  exit 1
fi

if [ "$ELAPSED" -gt 200 ]; then
  echo "WARN: slower than 200ms target (may be cold start on Render free tier)"
fi
