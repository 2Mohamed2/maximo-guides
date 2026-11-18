FILLING_PCT =
    100
    * (
        (
          CHARGE_MASS_T / (3.534291735 * D_EFF_M ** 2)
          - 0.7 * (BALL_CHARGE_PCT / 100) * (7.8 - ORE_SG)
        )
        / (0.7 * ORE_SG + 0.3 * (1 / (0.8 / ORE_SG + 0.2)))
      )
