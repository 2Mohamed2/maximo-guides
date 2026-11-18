SOH_MODEL_PCT =
    (
      100
      - np.power(2, (LIFE_CELL_TEMP_AVG_C - 25) / 15)
        * (
            2 * np.sqrt(np.maximum(DAYS_IN_SERVICE, 1) / 365)
            + 0.00333333333333 * EFC_COUNT
          )
    )
