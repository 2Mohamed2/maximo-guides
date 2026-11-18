HX_UA_RATIO =
    HEAT_DELIVERED_KW
    / (
        ((HW_SUPPLY_C - HX_SLUDGE_OUT_C) - (HW_RETURN_C - HX_SLUDGE_IN_C))
        / np.log(
            (HW_SUPPLY_C - HX_SLUDGE_OUT_C) / (HW_RETURN_C - HX_SLUDGE_IN_C)
          )
      )
    / 9
