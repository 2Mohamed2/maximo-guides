FT_PEAK_RATIO =
    (
      FT_PEAK_NET_CORR_PSI
      / (
          112.909091
          + 1.035354 * (FT_PEAK_GPM_CORR / 1000)
          - 3.309091 * (FT_PEAK_GPM_CORR / 1000) ** 2
          - 3.620202 * (FT_PEAK_GPM_CORR / 1000) ** 3
        )
    )
