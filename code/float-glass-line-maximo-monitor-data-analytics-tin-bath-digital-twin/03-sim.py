for name, x in devs["devices"].items():
        kw = dict(client_id=f"d:{devs['tenant']}:{x['type']}:{name}")
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, **kw) if hasattr(mqtt, "CallbackAPIVersion") else mqtt.Client(**kw)
        c.username_pw_set("use-token-auth", x["token"])
        c.tls_set_context(ssl._create_unverified_context())      # the cluster's router certificate; demo only
        c.reconnect_delay_set(5, 60)
        c.connect(devs["host"], 443, keepalive=60)
        c.loop_start()
        clients[name] = c
