$ curl -s -o /dev/null -w "%{http_code}\n" -H "Content-Type: text/plain" -d "70.5,3.9,2.4,111" http://localhost:1880/pump/reading
401
$ curl -s -u pump:<password> -H "Content-Type: text/plain" -d "70.5,3.9,2.4,111" http://localhost:1880/pump/reading
{"accepted":true,"device":"PUMP-001","reading":{"temperature":70.5,"pressure":3.9,"vibration":2.4,"flow":111}}
$ curl -s -u pump:<password> -H "Content-Type: text/plain" -d "hello" http://localhost:1880/pump/reading
{"error":"expected: temperature,pressure,vibration,flow"}
