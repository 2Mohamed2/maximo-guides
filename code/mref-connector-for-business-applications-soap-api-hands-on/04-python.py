import base64, requests

URL = "https://<mref-host>/ws/TririgaWS"
NS = ('xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope" '
      'xmlns:ws="http://ws.tririga.com" xmlns:dto="http://dto.ws.tririga.com"')

http = requests.Session()          # keeps the session cookie between calls

def call(body, user=None, password=None):
    env = f'<soapenv:Envelope {NS}><soapenv:Header/><soapenv:Body>{body}</soapenv:Body></soapenv:Envelope>'
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
    if user:
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        headers["Authorization"] = "Basic " + token
    return http.post(URL, data=env.encode("utf-8"), headers=headers)

# 1. sign-in call (see the trap below), 2. real calls with the cookie only
call("<ws:getApplicationInfo/>", USER, PASSWORD)
info = call("<ws:getApplicationInfo/>")
