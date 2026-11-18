DC_EXPECTED_KW =
    (
      375.84
      * POA_WM2
      / 1000
      * TEMP_FACTOR
      * 1.056
      * 0.98
      * (
          1
          - 0.01 * np.minimum(YEARS_IN_SERVICE, 1)
          - 0.004 * np.maximum(YEARS_IN_SERVICE - 1, 0)
        )
    )
