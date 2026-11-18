$ python consume.py demo-readers
[demo-readers] partition 1 offset 0 key=PUMP-001 value={"pump": "PUMP-001", "alert": "HIGH_VIBRATION", "seq": 0}
[demo-readers] partition 1 offset 1 key=PUMP-001 value={"pump": "PUMP-001", "alert": "HIGH_VIBRATION", "seq": 2}
[demo-readers] partition 1 offset 2 key=PUMP-001 value={"pump": "PUMP-001", "alert": "HIGH_VIBRATION", "seq": 4}
[demo-readers] partition 2 offset 0 key=PUMP-002 value={"pump": "PUMP-002", "alert": "HIGH_VIBRATION", "seq": 1}
[demo-readers] partition 0 offset 0 key=PUMP-003 value={"pump": "PUMP-003", "alert": "HIGH_VIBRATION", "seq": 3}
[demo-readers] read 5 messages
$ python consume.py demo-readers        # the same group again
[demo-readers] read 0 messages
$ python consume.py audit-team          # a different group
...
[audit-team] read 5 messages
