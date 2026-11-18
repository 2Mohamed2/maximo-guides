EFF_EXPECTED_PCT =
    (
      100
      * (
          0.95
          - 0.45
            * np.minimum((Q_RATIO - 1 - 0.5 * (N_ED / 0.18 - 1)), 0) ** 2
          - 0.6
            * np.maximum((Q_RATIO - 1 - 0.5 * (N_ED / 0.18 - 1)), 0) ** 2
          - 1.2 * (N_ED / 0.18 - 1) ** 2
        )
    )
