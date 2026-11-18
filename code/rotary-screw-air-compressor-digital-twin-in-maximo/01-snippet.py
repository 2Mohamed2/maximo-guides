P_LOAD_EXPECTED_KW =
    (
      INLET_PRESSURE_BARA
      * 100000
      * FAD_EXPECTED_M3MIN
      / 60
      * 3.5
      * (
          (
            (DISCHARGE_PRESSURE_BARG + INLET_PRESSURE_BARA)
            / INLET_PRESSURE_BARA
          )
          ** 0.2857142857
          - 1
        )
      / 1000
      / 0.8144
    )
