CT99_9_GIARDIA =
    np.where(
      TEMP_C < 12.5,
      1.059
      * (
          12.006
          + np.exp(
              2.46
              - 0.073 * TEMP_C
              + 0.125 * np.minimum(CL_OUT_A_MGL, CL_OUT_B_MGL)
              + 0.389 * PH
            )
        ),
      1.083
      * (
          -2.261
          + np.exp(
              2.69
              - 0.065 * TEMP_C
              + 0.111 * np.minimum(CL_OUT_A_MGL, CL_OUT_B_MGL)
              + 0.361 * PH
            )
        )
    )
