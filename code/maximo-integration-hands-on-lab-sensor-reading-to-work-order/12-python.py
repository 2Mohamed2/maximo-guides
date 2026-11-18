# pump.py
import json, random, ssl, time
import paho.mqtt.client as mqtt
HOST = "wsp.messaging.iot.<your-suite-domain>"
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="d:wsp:CoolingPump:PUMP-001")
c.username_pw_set("use-token-auth", open("PUMP-001.token").read().strip())
ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE   # lab only: load the suite CA instead
c.tls_set_context(ctx)
c.on_connect = lambda cl, u, flags, rc, props=None: print("connected:", rc)
c.connect(HOST, 443, keepalive=60)
c.loop_start(); time.sleep(2)
while True:
    reading = {"temperature": round(62 + random.uniform(-1, 1), 2),
               "pressure":    round(4.1 + random.uniform(-.1, .1), 3),
               "vibration":   round(2.1 + random.uniform(-.25, .25), 3),
               "flow":        round(120 + random.uniform(-2, 2), 2)}
    c.publish("iot-2/evt/status/fmt/json", json.dumps(reading), qos=1).wait_for_publish(10)
    print(time.strftime("%H:%M:%S"), reading)
    time.sleep(10)
