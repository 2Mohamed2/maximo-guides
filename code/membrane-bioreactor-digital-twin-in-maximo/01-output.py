PERM20_LMH_BAR =
    (
      FLUX_LMH
      / (TMP_KPA / 100)
      * np.exp(507.88 / (ML_TEMP_C + 123.85) - 3.53062217588)
    )
