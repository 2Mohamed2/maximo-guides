CREATE STREAM readings (meter VARCHAR KEY, kwh DOUBLE, status VARCHAR, seq INT)
  WITH (KAFKA_TOPIC='lab.meter.readings', KEY_FORMAT='JSON', VALUE_FORMAT='JSON');
