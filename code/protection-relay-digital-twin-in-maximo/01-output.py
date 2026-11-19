OPERATE_EXPECTED_MS =
    (
      1000
      * 0.15
      * (0.14 / (np.maximum((FAULT_CURRENT_A / 360), 1.05) ** 0.02 - 1) + 0)
    )
