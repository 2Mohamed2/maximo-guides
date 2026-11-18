GSV_M3 =
    (
      (
        (1256.637 * LEVEL_MM / 1000 - 1256.637 * WATER_LEVEL_MM / 1000)
        * CTSH
        - np.where(
            LEVEL_MM >= 1085.96928699,
            90000
            / (
                DENSITY15_KGM3
                * np.exp(
                    -(613.9723 / DENSITY15_KGM3 ** 2 + 0 / DENSITY15_KGM3)
                    * (PRODUCT_TEMP_C - 15)
                    * (
                        1
                        + 0.8
                          * (
                              613.9723 / DENSITY15_KGM3 ** 2
                              + 0 / DENSITY15_KGM3
                            )
                          * (PRODUCT_TEMP_C - 15)
                      )
                  )
              ),
            0
          )
      )
      * np.exp(
          -(613.9723 / DENSITY15_KGM3 ** 2 + 0 / DENSITY15_KGM3)
          * (PRODUCT_TEMP_C - 15)
          * (
              1
              + 0.8
                * (613.9723 / DENSITY15_KGM3 ** 2 + 0 / DENSITY15_KGM3)
                * (PRODUCT_TEMP_C - 15)
            )
        )
    )
