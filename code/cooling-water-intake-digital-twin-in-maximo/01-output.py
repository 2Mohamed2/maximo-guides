BLINDING =
    np.clip(
      1
      - np.sqrt(DH_CLEAN_M / np.maximum((LEVEL_UP_M - LEVEL_DOWN_M), 0.001)),
      0,
      1
    )
