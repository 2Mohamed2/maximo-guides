CHARGE_DEFICIT_KG =
    (
      (RECEIVER_LEVEL_EXPECTED_PCT - RECEIVER_LEVEL_PCT)
      / 100
      * 0.15
      * (
          -0.011526884 * LIQUID_TEMP_C ** 2
          - 3.8993434 * LIQUID_TEMP_C
          + 1197.0186
        )
    )
