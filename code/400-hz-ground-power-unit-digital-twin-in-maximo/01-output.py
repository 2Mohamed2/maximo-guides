CABLE_DROP_EXPECTED_V =
    (
      ((I_A + I_B + I_C) / 3)
      * (
          0.0084 * np.clip(P_OUT_KW / np.maximum(LOAD_KVA, 0.1), 0, 1)
          + 0.01792
            * np.sqrt(
                1 - np.clip(P_OUT_KW / np.maximum(LOAD_KVA, 0.1), 0, 1) ** 2
              )
        )
    )
