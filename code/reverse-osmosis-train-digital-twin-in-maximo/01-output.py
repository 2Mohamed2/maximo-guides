NDP_BAR =
    (
      MEMBRANE_FEED_PRESSURE_BAR
      - VESSEL_DP_BAR / 2
      - PERMEATE_PRESSURE_BAR
      - 0.00079
        * (
            ((MEMBRANE_FEED_TDS_MGL + CONCENTRATE_TDS_MGL) / 2)
            - PERMEATE_TDS_MGL
          )
    )
