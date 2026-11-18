# consume.py
import sys
from kafka import KafkaConsumer
from kc import cfg
group = sys.argv[1]
c = KafkaConsumer("demo.pump.alerts", **cfg(), group_id=group,
                  auto_offset_reset="earliest", consumer_timeout_ms=12000)
n = 0
for m in c:
    n += 1
    print(f"[{group}] partition {m.partition} offset {m.offset} key={m.key.decode()} value={m.value.decode()}")
print(f"[{group}] read {n} messages")
c.close()
