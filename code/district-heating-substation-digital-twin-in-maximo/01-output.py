UA_EXPECTED_KW_K =
    (
      4.2975
      / (
          0.5 * (0.906 / np.maximum(PRIMARY_FLOW_SH_M3H, 0.01)) ** 0.65
          + 0.5 * (1.0783 / np.maximum(SH_PUMP_FLOW_M3H, 0.01)) ** 0.65
        )
    )
