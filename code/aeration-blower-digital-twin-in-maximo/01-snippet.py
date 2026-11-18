GRID_PRESSURE_EXPECTED_MBAR =
    (
      441.29925
      + 25
      + 4 * (AIRFLOW_NM3H.clip(lower=1) / 1200)
      + 10 * (AIRFLOW_NM3H.clip(lower=1) / 4800) ** 2
    )

AIRFLOW_EXPECTED_NM3H =
    (
      O2_DEMAND_KGH
      / (
          0.2997
          * (
              0.065
              * 4.5
              * ((AIRFLOW_NM3H.clip(lower=1) / 1200) / 3) ** (-0.15)
            )
          * 0.55
          * (
              (
                0.95
                * (
                    (
                      14.652
                      - 0.41022 * WATER_TEMP_C
                      + 0.007991 * WATER_TEMP_C ** 2
                      - 7.7774e-05 * WATER_TEMP_C ** 3
                    )
                    * AMBIENT_PRESSURE_MBAR
                    / 1013.25
                    * (1 + 0.4 * 4.5 / 10.33)
                  )
                - ((DO_CONTROL_MGL + DO_OUTLET_MGL) / 2)
              ).clip(lower=0.1)
              / 10.5938558606
              * 1.024 ** (WATER_TEMP_C - 20)
            )
        )
    )
