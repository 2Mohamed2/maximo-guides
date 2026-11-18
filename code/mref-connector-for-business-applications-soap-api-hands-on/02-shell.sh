curl -s -X POST "https://<mref-host>/ws/TririgaWS" \
  -H "Content-Type: application/soap+xml; charset=utf-8" \
  -d '<soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope" xmlns:ws="http://ws.tririga.com">
        <soapenv:Body><ws:getApplicationInfo/></soapenv:Body></soapenv:Envelope>'
