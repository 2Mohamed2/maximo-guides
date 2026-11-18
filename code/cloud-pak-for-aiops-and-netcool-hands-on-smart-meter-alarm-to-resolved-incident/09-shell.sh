ID=$(printf 'MTR-4200-0101/BEDFORD' | base64 | tr -d '=')
curl -sk -X POST "$MAXIMO/api/os/mxapiasset/_$ID?lean=1" -H "apikey: $APIKEY" \
  -H 'Content-Type: application/json' -H 'x-method-override: PATCH' -H 'patchtype: MERGE' \
  -H 'properties: assetnum,location,status' -d '{"location":"4200-JCS-031500"}'
