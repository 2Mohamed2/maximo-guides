LINING_EQ_MM =
    (
      2.8
      * (1400 - SHELL_MAX_C)
      / (
          5.103e-08
          * ((SHELL_MAX_C + 273.15) ** 4 - (AMBIENT_C + 273.15) ** 4)
          + 12 * (SHELL_MAX_C - AMBIENT_C)
        )
      * 1000
    )
