curl -s -X POST https://wsp-mcp.manage.<instance>.<domain>/mcp ... -d '{"jsonrpc":"2.0","id":2,
  "method":"tools/call","params":{"name":"os_mxapiwoschedule-scheduleworkorder",
  "arguments":{"wonum":"1204","siteid":"BEDFORD","schedstart":"2026-10-27T08:00:00+03:00",
               "schedfinish":"2026-10-27T16:00:00+03:00","lead":"WILSON"}}}'

data: {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"Error calling tool
 'os_mxapiwoschedule-scheduleworkorder': Tool execution failed: HTTP error 400: BMXAA0029E - You are
 not authorized to perform this action for this record. ..."}],"isError":true}}
