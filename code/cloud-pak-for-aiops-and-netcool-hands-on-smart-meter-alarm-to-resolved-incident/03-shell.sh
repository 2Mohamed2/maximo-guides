WEBHOOK='https://whconn-…/webhook-connector/…'     # paste your route
curl -sk -X POST "$WEBHOOK" -H 'Content-Type: application/json' -d '{
  "meter": "MTR-4200-0001", "station": "4200-JCS-027399", "office": "2201",
  "alarm": "Last Gasp", "severity": "critical", "state": "raised" }'
