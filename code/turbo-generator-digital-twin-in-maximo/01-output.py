FIELD_CURRENT_EXPECTED_A =
    (
      845.496815
      * np.sqrt(
          (
            (TERMINAL_VOLTAGE_KV / 15.75)
            + (REACTIVE_POWER_MVAR / 300)
              * 2
              / (TERMINAL_VOLTAGE_KV / 15.75)
          )
          ** 2
          + ((ACTIVE_POWER_MW / 300) * 2 / (TERMINAL_VOLTAGE_KV / 15.75))
            ** 2
        )
    )
