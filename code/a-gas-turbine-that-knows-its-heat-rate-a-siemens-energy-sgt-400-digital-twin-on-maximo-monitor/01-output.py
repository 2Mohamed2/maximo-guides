HR_EXPECTED_KJ_KWH =
    (
      (0.0784 - 1.4e-05 * Y + ... + 0.0656 * X**3 + ...)
      * (INLET_PRESSURE_KPA / 101.325)
    )
    * 50000
    * 3600
    / (POWER_MW.clip(lower=0.2) * 1000)
  where X =
    POWER_MW / ((INLET_PRESSURE_KPA / 101.325) * 12.9),  Y = INLET_TEMP_C
