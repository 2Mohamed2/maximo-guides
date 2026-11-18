FLOAT_CURRENT_EXPECTED_A =
    (
      0.16275
      * np.power(2, (BATTERY_TEMP_C - 20) / 10)
      * np.power(2, ((BATTERY_VOLTAGE_V / 54) - 2.25) / 0.025)
    )

AUTONOMY_H =
    (
      SOC_PCT
      / 100
      * 465
      * np.interp(
          BATTERY_TEMP_C,
          [-10, 0, 10, 20, 30, 40],
          [0.6, 0.78, 0.9, 1, 1.05, 1.07]
        )
      * (1 - 0.65 * (RI_RATIO_MEAN - 1)).clip(lower=0.3, upper=1)
      / LOAD_CURRENT_A.clip(lower=1)
    )
