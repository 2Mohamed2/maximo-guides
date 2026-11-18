# produce.py
import json
from kafka import KafkaProducer
from kc import cfg
p = KafkaProducer(**cfg(), key_serializer=str.encode,
                  value_serializer=lambda v: json.dumps(v).encode(), acks="all")
for i, pump in enumerate(["PUMP-001", "PUMP-002", "PUMP-001", "PUMP-003", "PUMP-001"]):
    md = p.send("demo.pump.alerts", key=pump,
                value={"pump": pump, "alert": "HIGH_VIBRATION", "seq": i}).get(15)
    print(f"sent key={pump} seq={i} -> partition {md.partition} offset {md.offset}")
p.flush()
