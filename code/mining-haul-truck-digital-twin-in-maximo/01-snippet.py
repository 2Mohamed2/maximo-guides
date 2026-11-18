TKPH_SITE =
    (
      np.maximum(
        ((40.005805 + (163.289 + SHIFT_PAYLOAD_MEAN_T) * 0.165) / 2),
        ((20.8193475 + (163.289 + SHIFT_PAYLOAD_MEAN_T) * 0.1675) / 2)
      )
      * (CYCLE_KM / (CYCLE_MIN / 60))
      * np.interp(
          CYCLE_KM,
          [5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30, 40, 50],
          [1, 1.04, 1.06, 1.09, 1.1, 1.12, 1.14, 1.16, 1.17, 1.18, 1.19, 1.2, 1.21, 1.22, 1.23]
        )
      * (
          1
          / (
              1
              - np.where(AMBIENT_MAX_C > 38, 0.4, 0.25)
                * (AMBIENT_MAX_C - 38)
                / (CYCLE_KM / (CYCLE_MIN / 60))
            )
        )
    )
