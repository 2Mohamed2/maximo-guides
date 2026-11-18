TOP_OIL_EXPECTED_C =
    (
      AMBIENT_AVG_C
      + 60
        * ((1 + 10.9668 * LOAD_EQ_PU.clip(lower=0) ** 2) / 11.9668) ** 0.8
    )
