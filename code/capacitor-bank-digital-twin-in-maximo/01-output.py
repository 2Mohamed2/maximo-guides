FAILED_ELEMENTS_EST =
    (
      (NEUTRAL_CURRENT_A - 0.0006791 * BUS_VOLTAGE_KV).clip(lower=0)
      / (0.0041187 * BUS_VOLTAGE_KV.clip(lower=1))
    )
