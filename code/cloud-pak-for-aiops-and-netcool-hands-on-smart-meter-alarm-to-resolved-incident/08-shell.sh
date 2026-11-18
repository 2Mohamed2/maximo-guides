curl -sk -X POST "$MAXIMO/api/os/mxapioperloc?lean=1" -H "apikey: $APIKEY" \
  -H 'Content-Type: application/json' -H 'properties: location,siteid,description' \
  -d '{"location":"4200-JCS-031500","siteid":"BEDFORD","type":"OPERATING",
       "description":"Substation 4200-JCS-031500 (smart meter station)"}'
curl -sk -X POST "$MAXIMO/api/os/mxapiasset?lean=1" -H "apikey: $APIKEY" \
  -H 'Content-Type: application/json' -H 'properties: assetnum,siteid,description' \
  -d '{"assetnum":"MTR-4200-0101","siteid":"BEDFORD",
       "description":"Smart meter MTR-4200-0101, station 4200-JCS-031500"}'
