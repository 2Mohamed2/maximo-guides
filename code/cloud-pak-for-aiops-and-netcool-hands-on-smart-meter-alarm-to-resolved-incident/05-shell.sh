send() { curl -sk -o /dev/null -w "%{http_code} " -X POST "$WEBHOOK" \
           -H 'Content-Type: application/json' -d "$1"; }
send '{"meter":"MTR-4200-0001","station":"4200-JCS-027399","office":"2201","alarm":"Last Gasp","severity":"critical","state":"raised"}'
send '{"meter":"MTR-4200-0002","station":"4200-JCS-027399","office":"2201","alarm":"Last Gasp","severity":"critical","state":"raised"}'
send '{"meter":"MTR-4200-0003","station":"4200-JCS-027399","office":"2201","alarm":"Last Gasp","severity":"critical","state":"raised"}'
send '{"meter":"MTR-4310-0107","station":"4310-RYD-001122","office":"2310","alarm":"Top Cover Open","severity":"minor","state":"raised"}'
