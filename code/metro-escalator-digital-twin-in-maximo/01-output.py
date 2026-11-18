STOP_DIST_FULL_DOWN_M =
    np.where(
      ((BRAKE_FORCE_KN * 1000 - 20335.12763) / 21196.15242) > 0.02,
      0.5 * LAST_STOP_DELAY_S
      + 0.125
        / np.maximum(
            ((BRAKE_FORCE_KN * 1000 - 20335.12763) / 21196.15242),
            0.02
          ),
      9.99
    )
