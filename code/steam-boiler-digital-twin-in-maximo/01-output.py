EFF_INDIRECT_PCT =
    (
      100
      - FLUE_LOSS_PCT
      - (0.4 / np.maximum((STEAM_FLOW_KGH / 10000), 0.2))
    )
