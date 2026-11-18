CAKE_DS_EXPECTED_PCT =
    (
      26 * (1 - np.exp(-POLYMER_KG_PER_TDS / 2))
      - 0.4 * np.maximum(POLYMER_KG_PER_TDS - 7, 0)
      + 1 * (np.minimum(TENSION_UPPER_BAR, TENSION_LOWER_BAR) - 5)
      - 4 * np.maximum(SOLIDS_RATIO - 1, 0)
    )
