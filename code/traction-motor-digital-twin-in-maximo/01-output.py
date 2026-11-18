STATOR_EXPECTED_C =
    (
      AIR_IN_C
      + 125
        * (CURRENT_RMS30_A / 530) ** 2
        * (100 / np.maximum(BLOWER_FLOW_PCT, 10)) ** 0.8
    )
