COND_STAGE1_LIMIT =
    np.array([0.6, 0.8, 0.9, 1, 1.1, 1.3, 1.4, 1.5, 1.7, 1.8, 1.9, 2.1, 2.2, 2.4, 2.5, 2.7, 2.7, 2.7, 2.7, 2.9, 3.1])[np.clip(np.floor(RETURN_TEMP_C / 5), 0, 20).astype(int)]
