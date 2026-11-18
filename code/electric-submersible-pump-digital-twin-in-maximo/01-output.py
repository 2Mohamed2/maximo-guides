HEAD_EXPECTED_FT =
    np.maximum(
      266
      * (np.maximum(VSD_FREQ_HZ, 1) / 60) ** 2
      * (29 - 0.0015206 * FLOW_60HZ_BPD - 2.527e-06 * FLOW_60HZ_BPD ** 2),
      1
    )
