CLEARANCE_RATIO =
    (
      (
        1
        + np.maximum(0, 1 - SPECIFIC_RATE_RATIO)
          * 300
          / (0.00238 * np.maximum(P_SCREEN_IN_BAR, 1))
      )
      ** (1 / 3)
    )
