curl -s -u root:'<password>' \
  "http://localhost:8090/objectserver/restapi/alerts/status?collist=Node,Severity,Location,Customer,Tally&filter=Manager%3D%27SMOCLab%27"
