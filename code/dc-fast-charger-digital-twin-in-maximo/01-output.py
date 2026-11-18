CONTACT_RATIO_C1 =
    (
      (CONTACT_TEMP_C1_C - COOLANT_RETURN_C)
      / (120 * (np.maximum(DC_CURRENT_C1_A, 150) / 1000) ** 2)
    )
