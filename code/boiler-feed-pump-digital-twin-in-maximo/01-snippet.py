EFF_THERMO_PCT =
    100
    * (
        (DISCHARGE_PRESSURE_BAR - SUCTION_PRESSURE_BAR)
        * 100000
        / (913 - 0.98 * (((SUCTION_TEMP_C + DISCHARGE_TEMP_C) / 2) - 160))
        / (
            (
              0.0005973
              - 3.28e-06 * (((SUCTION_TEMP_C + DISCHARGE_TEMP_C) / 2) - 160)
            )
            * (DISCHARGE_PRESSURE_BAR - SUCTION_PRESSURE_BAR)
            * 100000
            + (
                4303.7
                + 2.74 * (((SUCTION_TEMP_C + DISCHARGE_TEMP_C) / 2) - 160)
              )
              * TEMP_RISE_K
          )
      )
