TSAT_HOLD_C =
    (
      (
        650.175348448
        + (
            2
            * (
                -724213.167032
                * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                - 3232555.03223 * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                + 405113.405421
              )
            / (
                -(
                   1167.05214528
                   * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                   + 12020.8247025
                     * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                   - 4823.26573616
                 )
                - np.sqrt(
                    (
                      1167.05214528
                      * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                      + 12020.8247025
                        * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                      - 4823.26573616
                    )
                    ** 2
                    - 4
                      * (
                          ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                          - 17.0738469401
                            * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                          + 14.9151086135
                        )
                      * (
                          -724213.167032
                          * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                          - 3232555.03223
                            * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                          + 405113.405421
                        )
                  )
              )
          )
        - np.sqrt(
            (
              650.175348448
              + (
                  2
                  * (
                      -724213.167032
                      * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                      - 3232555.03223
                        * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                      + 405113.405421
                    )
                  / (
                      -(
                         1167.05214528
                         * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                         + 12020.8247025
                           * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                         - 4823.26573616
                       )
                      - np.sqrt(
                          (
                            1167.05214528
                            * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                            + 12020.8247025
                              * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                            - 4823.26573616
                          )
                          ** 2
                          - 4
                            * (
                                ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                                ** 2
                                - 17.0738469401
                                  * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                                + 14.9151086135
                              )
                            * (
                                -724213.167032
                                * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                                  ** 2
                                - 3232555.03223
                                  * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                                + 405113.405421
                              )
                        )
                    )
                )
            )
            ** 2
            - 4
              * (
                  -0.238555575678
                  + 650.175348448
                    * (
                        2
                        * (
                            -724213.167032
                            * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25) ** 2
                            - 3232555.03223
                              * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                            + 405113.405421
                          )
                        / (
                            -(
                               1167.05214528
                               * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                                 ** 2
                               + 12020.8247025
                                 * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                               - 4823.26573616
                             )
                            - np.sqrt(
                                (
                                  1167.05214528
                                  * ((CYC_HOLD_PRESSURE_BAR_A / 10) ** 0.25)
                                    ** 2
                                  + 12020.8247025
                                    * (
                                        (CYC_HOLD_PRESSURE_BAR_A / 10)
                                        ** 0.25
                                      )
                                  - 4823.26573616
                                )
                                ** 2
                                - 4
                                  * (
                                      (
                                        (CYC_HOLD_PRESSURE_BAR_A / 10)
                                        ** 0.25
                                      )
                                      ** 2
                                      - 17.0738469401
                                        * (
                                            (CYC_HOLD_PRESSURE_BAR_A / 10)
                                            ** 0.25
                                          )
                                      + 14.9151086135
                                    )
                                  * (
                                      -724213.167032
                                      * (
                                          (CYC_HOLD_PRESSURE_BAR_A / 10)
                                          ** 0.25
                                        )
                                        ** 2
                                      - 3232555.03223
                                        * (
                                            (CYC_HOLD_PRESSURE_BAR_A / 10)
                                            ** 0.25
                                          )
                                      + 405113.405421
                                    )
                              )
                          )
                      )
                )
          )
      )
      / 2
      - 273.15
    )
