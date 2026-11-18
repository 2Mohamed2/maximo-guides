curl -sk -X POST "$MAXIMO/api/os/mxapisr?lean=1" -H "apikey: $APIKEY" -H 'Content-Type: application/json' \
  -H 'properties: ticketid,status,description,assetnum,location,reportedpriority,externalrecid' --data @sr.json
