LEAK_FRACTION =
    np.clip(
      (ACOUSTIC_LEVEL - ACOUSTIC_EXPECTED)
      / ((60 + 9 * DP_BAR) - ACOUSTIC_EXPECTED),
      0,
      1
    )
