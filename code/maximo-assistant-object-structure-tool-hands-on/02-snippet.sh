curl -s -X POST https://wsp-mcp.manage.<instance>.<domain>/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "apikey: $APIKEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
