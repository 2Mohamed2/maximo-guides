CREATE STREAM high_readings AS
  SELECT meter, kwh, status
  FROM readings
  WHERE kwh > 5
  EMIT CHANGES;
