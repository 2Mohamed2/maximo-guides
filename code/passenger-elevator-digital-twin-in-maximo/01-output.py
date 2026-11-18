BALANCE_APPARENT_PCT =
    (
      (
        UP_LOAD_KG
        + DOWN_LOAD_KG
        - ((UP_TORQUE_NM * 0.01) + (DOWN_TORQUE_NM * 0.01)) * 101.936799185
      )
      / 20
    )
