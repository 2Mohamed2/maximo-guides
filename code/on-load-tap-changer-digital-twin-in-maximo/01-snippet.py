TAP_EXPECTED =
    (
      9
      + (
          1
          - (HV_VOLTAGE_KV / 132)
            / (
                (AVR_SETPOINT_KV / 33)
                + (
                    LV_CURRENT_A
                    / 1049.7
                    * (
                        0.004333 * POWER_FACTOR
                        + 0.124925 * np.sqrt(1 - POWER_FACTOR ** 2)
                      )
                  )
              )
        )
        / 0.0125
    )
