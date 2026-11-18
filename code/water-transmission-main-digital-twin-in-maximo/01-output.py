LEAK_CH_KM =
    (
      ((H_PT0 - H_PT4) - S_out * 14000)
      / (S_in - S_out).clip(lower=1e-09)
      / 1000
    ).clip(lower=0, upper=14)
